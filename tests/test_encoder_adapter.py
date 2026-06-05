"""CPU-only unit tests for the encoder z-sweep adapter (no Isaac Sim, no GPU)."""
import importlib.util
import json
import os
import subprocess
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(REPO, ".omx", "profile", "metrics.yaml")
ADAPTER = os.path.join(REPO, ".omx", "profile", "encoder_adapter.py")
FIXTURE = os.path.join(REPO, "tests", "fixtures", "encoder", "mini_encoder_24d.pt")


def test_encoder_is_a_profile_source():
    """exp-analyze routes by profile sources; encoder must be one."""
    with open(PROFILE) as f:
        prof = yaml.safe_load(f)
    assert "encoder" in prof["sources"], f"sources={prof['sources']}"


def _load_adapter():
    spec = importlib.util.spec_from_file_location("encoder_adapter", ADAPTER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_adapter_is_sim_free_source():
    """Adapter must expose sweep_sensitivity and never import/boot Isaac Sim.

    Source-level check (NOT sys.modules): this repo runs in an Isaac Sim
    container whose interpreter wrapper may pre-load isaaclab independently of
    this adapter. "Sim-free" = the adapter source imports no Isaac Sim.
    """
    mod = _load_adapter()
    assert hasattr(mod, "sweep_sensitivity"), "adapter must expose sweep_sensitivity()"
    with open(ADAPTER) as f:
        src = f.read()
    for forbidden in ("import isaacsim", "import isaaclab", "from isaacsim",
                      "from isaaclab", "SimulationApp", "AppLauncher"):
        assert forbidden not in src, f"adapter must not reference {forbidden!r}"


def test_sweep_sensitivity_returns_matrix():
    """sweep_sensitivity assembles engine functions and returns a z-range matrix."""
    if not os.path.exists(FIXTURE):
        import pytest
        pytest.skip("fixture absent -- run Task 2")
    mod = _load_adapter()
    out = mod.sweep_sensitivity(FIXTURE, num_points=100)
    assert out["latent_dim"] == 9
    assert out["input_dim"] == 24
    assert out["activation"] == "softsign"
    assert len(out["params"]) == 24
    p0 = out["params"][0]
    assert "name" in p0 and "z_range" in p0 and "active_dims" in p0
    assert len(p0["z_range"]) == 9            # one per latent dim
    assert all(r >= 0.0 for r in p0["z_range"])  # max-min is non-negative
    assert 0 <= p0["active_dims"] <= 9
