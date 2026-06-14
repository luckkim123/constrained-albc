"""CPU-only unit tests for the eval analysis wiring (no Isaac Sim)."""
import importlib.util
import json
import os
import subprocess
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(REPO, ".omx", "profile", "metrics.yaml")
ADAPTER = os.path.join(REPO, ".omx", "profile", "eval_adapter.py")
FIXTURE_DIR = os.path.join(REPO, "tests", "fixtures", "eval")
_FIXTURE_NPZ = os.path.join(FIXTURE_DIR, "data_none.npz")
SEG_FIXTURE_DIR = os.path.join(REPO, "tests", "fixtures", "segmented")


def _load_adapter():
    spec = importlib.util.spec_from_file_location("eval_adapter", ADAPTER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_eval_is_a_profile_source():
    """exp-analyze routes by profile sources; eval must be one."""
    with open(PROFILE) as f:
        prof = yaml.safe_load(f)
    assert "eval" in prof["sources"], f"sources={prof['sources']}"


def test_adapter_imports_sim_free_engine():
    """Adapter must expose analyze_eval and never import or boot Isaac Sim.

    We do NOT assert isaaclab is absent from sys.modules: this repo runs inside an
    Isaac Sim container whose interpreter wrapper may already have isaaclab loaded,
    independently of this adapter. "Sim-free" is a source-level property -- the
    adapter must not IMPORT Isaac Sim or instantiate a SimulationApp -- so assert
    the adapter source carries no such reference.
    """
    mod = _load_adapter()
    assert hasattr(mod, "analyze_eval"), "adapter must expose analyze_eval()"
    with open(ADAPTER) as f:
        src = f.read()
    for forbidden in ("import isaacsim", "import isaaclab", "from isaacsim",
                      "from isaaclab", "SimulationApp", "AppLauncher"):
        assert forbidden not in src, f"adapter must not reference {forbidden!r}"


def test_analyze_eval_returns_driver_dict():
    """analyze_eval delegates to _ed_analyze_run and returns its structure."""
    if not os.path.exists(_FIXTURE_NPZ):
        import pytest
        pytest.skip("fixture absent — copy from SOURCE.txt")
    mod = _load_adapter()
    out = mod.analyze_eval(FIXTURE_DIR)
    assert "levels" in out
    assert "none" in out["levels"], f"levels present: {list(out['levels'])}"
    roll = out["levels"]["none"]["axes"]["roll"]["heavy_tail"]
    assert "peak_max" in roll and "peak_mean" in roll and "pct_peak_gt_thresh" in roll
    assert roll["peak_max"] >= roll["peak_mean"] >= 0.0


def test_cli_emits_json():
    """The adapter is runnable as a subprocess emitting JSON (exp-analyze code-exec)."""
    result = subprocess.run(
        [sys.executable, ADAPTER, "heavy-tail", FIXTURE_DIR],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["levels"]["none"]["axes"]["roll"]["heavy_tail"]["peak_max"] >= 0.0


def test_adapter_matches_engine_directly():
    """Adapter output must be byte-equal to calling _ed_analyze_run directly."""
    sys.path.insert(0, os.path.join(REPO, "constrained_albc", "analysis"))
    from _analyze.eval_dr import _ed_analyze_run  # noqa: E402

    ref = _ed_analyze_run(FIXTURE_DIR, ["none", "soft", "medium", "hard"], 20.0, 0.5, 0.5)
    mod = _load_adapter()
    out = mod.analyze_eval(FIXTURE_DIR)
    assert out == ref


# --- segmented coverage (2026-06-05): post-switch transient via switching.py delegation ---

def test_adapter_exposes_analyze_segmented():
    """The adapter must expose analyze_segmented() for the segmented eval mode."""
    mod = _load_adapter()
    assert hasattr(mod, "analyze_segmented"), "adapter must expose analyze_segmented()"


def _seg_fixture_or_skip():
    import pytest
    if not os.path.exists(os.path.join(SEG_FIXTURE_DIR, "summary_segmented.json")):
        pytest.skip("segmented fixture absent — regenerate from SOURCE.txt")


def test_analyze_segmented_returns_per_axis_transient():
    """analyze_segmented delegates to _analyze.switching and returns per-level
    per-axis post-switch transient stats (mean/p95/max), computed via numpy
    reductions over the engine's _sw_all_post_switch extraction (no metric math
    re-implemented in the adapter)."""
    _seg_fixture_or_skip()
    mod = _load_adapter()
    out = mod.analyze_segmented(SEG_FIXTURE_DIR)
    assert "levels" in out
    assert "none" in out["levels"] and "hard" in out["levels"]
    roll = out["levels"]["none"]["axes"]["roll"]["post_switch"]
    assert "peak_mean" in roll and "peak_p95" in roll and "peak_max" in roll
    assert roll["peak_max"] >= roll["peak_p95"] >= roll["peak_mean"] >= 0.0


def test_analyze_segmented_handles_single_segment_gracefully(tmp_path):
    """A level whose per_seg has only seg 0 (no DR switch) has no post-switch data.
    The adapter must skip it gracefully, NOT crash on np.concatenate([])."""
    import json
    seg_dir = tmp_path / "seg_single"
    seg_dir.mkdir()
    summary = {
        "metrics": {
            "none": {"per_seg": [
                {"seg_idx": 0, "peak_roll_deg": [1.0], "peak_pitch_deg": [0.5], "peak_yaw_deg": [2.0]},
            ], "num_envs": 1, "num_segments": 1},
        },
        "config": {"num_envs": 1, "num_segments": 1},
    }
    (seg_dir / "summary_segmented.json").write_text(json.dumps(summary))
    mod = _load_adapter()
    out = mod.analyze_segmented(str(seg_dir))
    # 'none' has no post-switch segments -> skipped (not a crash), so levels is empty here.
    assert out["levels"] == {}, f"expected empty levels, got {out['levels']}"


def test_segmented_cli_emits_json():
    """The adapter's segmented subcommand is runnable and emits JSON."""
    _seg_fixture_or_skip()
    result = subprocess.run(
        [sys.executable, ADAPTER, "segmented", SEG_FIXTURE_DIR],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["levels"]["hard"]["axes"]["yaw"]["post_switch"]["peak_max"] >= 0.0


# --- failure_dr coverage: per-env DR/FAULT <-> failure join surfaced to omx report ---

def _write_failure_npz(eval_dir: str, level: str = "none", n: int = 64, t: int = 120) -> None:
    """Write a data_<level>.npz whose worst-roll envs have the lowest fault_thruster_3.

    Self-contained (no Isaac Sim): a dead thruster drives roll error, so the adapter's
    join must surface fault_thruster_3 as the top fault correlate.
    """
    import numpy as np

    rng = np.random.default_rng(0)
    health3 = rng.uniform(0.2, 1.0, n).astype(np.float32)
    err_roll = (1.0 - health3)[None, :] * 100.0 + rng.normal(0, 0.05, (t, n)).astype(np.float32)
    np.savez(
        os.path.join(eval_dir, f"data_{level}.npz"),
        error_roll=err_roll,
        error_pitch=rng.normal(0, 0.1, (t, n)).astype(np.float32),
        terminated=np.zeros((t, n), dtype=bool),
        warmup_steps=np.int64(t // 2),
        fault_thruster_3=health3,
        fault_sensor_noise=rng.normal(0, 0.01, n).astype(np.float32),
        dr_cog_y=rng.normal(0, 0.01, n).astype(np.float32),
    )


def test_adapter_exposes_analyze_failure_dr():
    """The adapter must expose analyze_failure_dr() for the per-env DR/FAULT join."""
    mod = _load_adapter()
    assert hasattr(mod, "analyze_failure_dr"), "adapter must expose analyze_failure_dr()"


def test_analyze_failure_dr_separates_dr_and_fault(tmp_path):
    """analyze_failure_dr delegates to the join engine and returns dr+fault rankings."""
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    _write_failure_npz(str(eval_dir), "none")
    mod = _load_adapter()
    out = mod.analyze_failure_dr(str(eval_dir), levels=["none"])
    lvl = out["levels"]["none"]
    assert "dr_ranking" in lvl and "fault_ranking" in lvl
    assert lvl["fault_ranking"][0]["name"] == "fault_thruster_3"
    assert lvl["fault_ranking"][0]["correlation"] < -0.5  # low health <-> failing


def test_failure_dr_cli_emits_json(tmp_path):
    """The adapter's failure-dr subcommand is runnable and emits JSON for omx report."""
    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()
    _write_failure_npz(str(eval_dir), "none")
    result = subprocess.run(
        [sys.executable, ADAPTER, "failure-dr", str(eval_dir), "--levels", "none"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["levels"]["none"]["fault_ranking"][0]["name"] == "fault_thruster_3"
