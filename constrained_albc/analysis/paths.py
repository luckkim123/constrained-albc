# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""run_id single-tree path resolution (manifest-based, with legacy fallback).

Implements the resolver layer of the run_id design (docs/explanation/run-id-tree-design.md,
section 4 #4 and section 5). A single ``run_id`` keys a run's training output, evaluation
output, and config under ``experiments/<run_id>/``; ``manifest.json`` (section 3) is the
entry point for tracing.

This module is **read-mostly and standalone**: it neither imports nor is imported by
train.py / eval_dr.py / common.py yet, so adding it does not change any training or
evaluation behavior. The wiring (train.py emitting a manifest, common.resolve_run_path
delegating here) is deferred to the training-adjacent implementation phase that needs
explicit user approval (feedback_training_control).

Resolution is graceful: a run without a ``manifest.json`` (legacy frozen output, or a
run produced before train.py adopts this tree) still resolves to a best-effort
``RunHandle`` by scanning its directory layout. ``manifest`` is then ``None`` and the
``tb`` / ``checkpoints`` paths are inferred.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Default roots (cwd-relative, matching common.py / train.py conventions).
EXPERIMENTS_ROOT = "experiments"
LEGACY_LOGS_ROOT = "logs/rsl_rl"
MANIFEST_NAME = "manifest.json"


@dataclass
class RunHandle:
    """Resolved view of a single run's on-disk layout.

    Whether the run lives under the new ``experiments/<run_id>/`` tree or an older
    ``logs/rsl_rl/<exp>/<ts>/`` directory, the handle exposes the same path accessors.
    ``manifest`` is the parsed manifest dict when present, else ``None`` (legacy run).
    """

    run_id: str
    root: Path
    manifest: dict | None = None
    is_legacy: bool = False

    @property
    def tb_dir(self) -> Path:
        """TensorBoard event directory (``train/tb`` in the new tree; root for legacy)."""
        if self.manifest is not None:
            return self.root / self.manifest.get("paths", {}).get("tb", "train/tb")
        new = self.root / "train" / "tb"
        return new if new.exists() else self.root

    @property
    def checkpoints_dir(self) -> Path:
        """Checkpoint directory (``train/checkpoints`` in the new tree; root for legacy)."""
        if self.manifest is not None:
            return self.root / self.manifest.get("paths", {}).get("checkpoints", "train/checkpoints")
        new = self.root / "train" / "checkpoints"
        return new if new.exists() else self.root

    @property
    def eval_root(self) -> Path:
        """Parent directory holding per-mode eval folders (``eval/`` in the new tree)."""
        return self.root / "eval"

    def latest_checkpoint(self) -> Path | None:
        """Newest ``model_*.pt`` by numeric iteration (never alphabetic).

        Sorting is by the integer in ``model_<n>.pt`` so ``model_4999.pt`` beats
        ``model_999.pt`` (feedback_model_trim_disaster: alphabetic sort silently drops
        the final model).
        """
        ckpts = list(self.checkpoints_dir.glob("model_*.pt"))
        if not ckpts:
            return None

        def _iter(p: Path) -> int:
            stem = p.stem.split("_", 1)[-1]
            return int(stem) if stem.isdigit() else -1

        return max(ckpts, key=_iter)


def find_runs(experiments_root: str = EXPERIMENTS_ROOT) -> list[RunHandle]:
    """List active run_id trees under ``experiments/``, newest first.

    Skips the ``legacy/`` subtree (frozen outputs without a run_id convention).
    A directory counts as a run when it holds a manifest or a ``train/`` subdir.
    """
    root = Path(experiments_root)
    if not root.exists():
        return []
    runs: list[RunHandle] = []
    for d in sorted(root.iterdir(), reverse=True):
        if not d.is_dir() or d.name == "legacy":
            continue
        manifest = _read_manifest_if_present(d)
        if manifest is not None or (d / "train").exists():
            runs.append(RunHandle(run_id=d.name, root=d, manifest=manifest))
    return runs


def resolve_run(
    run_spec: str,
    experiments_root: str = EXPERIMENTS_ROOT,
    legacy_logs_root: str = LEGACY_LOGS_ROOT,
) -> RunHandle:
    """Resolve a run specifier to a :class:`RunHandle`.

    Resolution order (first match wins):
      1. ``run_spec`` is an existing directory path -> wrap it directly.
      2. ``experiments/<run_spec>/`` exists -> active run_id tree (manifest preferred).
      3. Substring / index match against active runs under ``experiments/``.
      4. Legacy fallback: a directory under ``logs/rsl_rl/<exp>/`` whose name matches,
         wrapped as a legacy handle (``manifest=None``).

    Raises:
        FileNotFoundError: if nothing matches.
    """
    # 1. Direct path.
    p = Path(run_spec)
    if p.is_dir():
        manifest = _read_manifest_if_present(p)
        is_legacy = manifest is None and not (p / "train").exists()
        return RunHandle(run_id=p.name, root=p, manifest=manifest, is_legacy=is_legacy)

    # 2. experiments/<run_spec>/
    candidate = Path(experiments_root) / run_spec
    if candidate.is_dir():
        return RunHandle(
            run_id=run_spec,
            root=candidate,
            manifest=_read_manifest_if_present(candidate),
        )

    # 3. Active runs: integer index (0 = latest) or substring.
    active = find_runs(experiments_root)
    if active:
        try:
            idx = int(run_spec)
            if 0 <= idx < len(active):
                return active[idx]
        except ValueError:
            pass
        matches = [r for r in active if run_spec in r.run_id]
        if matches:
            return matches[0]

    # 4. Legacy fallback: scan logs/rsl_rl/<exp>/<run>/ for a name match.
    legacy = _find_legacy_run(run_spec, legacy_logs_root)
    if legacy is not None:
        return legacy

    raise FileNotFoundError(
        f"No run matching '{run_spec}' under {experiments_root}/ or {legacy_logs_root}/"
    )


def resolve_eval(run: RunHandle, mode: str, eval_ts: str | None = None) -> Path:
    """Return the eval output directory for *mode* under a run's single tree.

    Layout: ``<run.root>/eval/<mode>_<eval_ts>/`` (design section 2-B). When *eval_ts*
    is omitted a fresh timestamp is generated. The directory is **not** created here;
    callers create it when they write (this module stays side-effect-free for reads).

    Args:
        run: Resolved run handle.
        mode: One of static / periodic / segmented / sudden.
        eval_ts: Optional explicit eval timestamp; defaults to now.
    """
    ts = eval_ts or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return run.eval_root / f"{mode}_{ts}"


# ---------------------------------------------------------------------------
# manifest.json read/write (design section 3). write_manifest is the hook
# train.py will call once approved; provided now so the schema lives in one place.
# ---------------------------------------------------------------------------


@dataclass
class Manifest:
    """Typed view of manifest.json (design section 3)."""

    run_id: str
    task: str
    kind: str = "teacher"  # teacher | student
    parent_run_id: str | None = None
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    git: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    wandb: dict = field(default_factory=dict)
    paths: dict = field(default_factory=lambda: {"tb": "train/tb", "checkpoints": "train/checkpoints", "evals": []})
    status: str = "running"  # running | completed | failed
    repro: dict = field(default_factory=dict)
    final_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "run_id": self.run_id,
            "kind": self.kind,
            "task": self.task,
            "created": self.created,
            "git": self.git,
            "config": self.config,
            "wandb": self.wandb,
            "paths": self.paths,
            "status": self.status,
            "repro": self.repro,
            "final_metrics": self.final_metrics,
        }
        if self.parent_run_id is not None:
            d["parent_run_id"] = self.parent_run_id
        return d


def write_manifest(run_root: str | Path, manifest: Manifest) -> Path:
    """Serialize *manifest* to ``<run_root>/manifest.json`` and return its path."""
    run_root = Path(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    out = run_root / MANIFEST_NAME
    out.write_text(json.dumps(manifest.to_dict(), indent=2))
    return out


def read_manifest(run_root: str | Path) -> dict:
    """Read ``<run_root>/manifest.json`` (raises if absent)."""
    out = Path(run_root) / MANIFEST_NAME
    return json.loads(out.read_text())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_manifest_if_present(run_root: Path) -> dict | None:
    """Parse ``manifest.json`` if it exists, else None (used for legacy fallback)."""
    out = run_root / MANIFEST_NAME
    if not out.is_file():
        return None
    try:
        return json.loads(out.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _find_legacy_run(run_spec: str, legacy_logs_root: str) -> RunHandle | None:
    """Scan ``logs/rsl_rl/<exp>/<run>/`` for a run-dir name matching *run_spec*.

    A run dir is one holding TensorBoard events. Returns the newest name match,
    or None. Matches are by substring against the run-dir name (the timestamped
    leaf), consistent with common.resolve_run_path's substring behavior.
    """
    root = Path(legacy_logs_root)
    if not root.exists():
        return None
    candidates: list[Path] = []
    for exp_dir in root.iterdir():
        if not exp_dir.is_dir():
            continue
        for run_dir in exp_dir.iterdir():
            if run_dir.is_dir() and list(run_dir.glob("events.out.tfevents.*")):
                candidates.append(run_dir)
    candidates.sort(key=lambda p: p.name, reverse=True)
    matches = [c for c in candidates if run_spec in c.name]
    if not matches:
        return None
    hit = matches[0]
    return RunHandle(run_id=hit.name, root=hit, manifest=None, is_legacy=True)
