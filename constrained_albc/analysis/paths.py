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
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Default roots (cwd-relative, matching common.py / train.py conventions).
EXPERIMENTS_ROOT = "experiments"
LEGACY_LOGS_ROOT = "logs/rsl_rl"
MANIFEST_NAME = "manifest.json"

# task_short extraction (design section 2-A). Ordered specific -> general so that
# superset substrings match first: "-TRPO-NoIPO-" before "-TRPO-", "-PPO-Enc-" before
# "-PPO-". A wrong order would classify Isaac-FullDOF-TRPO-NoIPO-v0 as "trpo".
_TASK_SHORT_PATTERNS: list[tuple[str, str]] = [
    ("-TRPO-NoIPO-", "trpo-noipo"),
    ("-PPO-Enc-", "ppo-enc"),
    ("-NoEncoder-", "noenc"),
    ("-TDC-", "tdc"),
    ("-TRPO-", "trpo"),
    ("-PPO-", "ppo"),
]


def task_short(task_id: str) -> str:
    """Map a registered task ID to its run_id short tag (design section 2-A).

    e.g. ``Isaac-FullDOF-TRPO-v0`` -> ``trpo``, ``Isaac-FullDOF-PPO-Enc-v0`` -> ``ppo-enc``.
    Falls back to a lowercased, dash-joined slug of the task ID if no pattern matches,
    so an unrecognized task still yields a usable (if verbose) tag rather than crashing.
    """
    for needle, short in _TASK_SHORT_PATTERNS:
        if needle in task_id:
            return short
    # Fallback: strip the Isaac- prefix / -v0 suffix and slugify.
    slug = task_id
    for prefix in ("Isaac-FullDOF-", "Isaac-"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
            break
    slug = slug.rsplit("-v", 1)[0]
    return slug.lower().replace("-", "_") or "run"


def make_run_id(task_id: str, tag: str | None = None, ts: str | None = None) -> str:
    """Build a run_id ``<ts>_<task_short>[_<tag>]`` (design section 2-A).

    The timestamp format matches train.py (``%Y-%m-%d_%H-%M-%S``) so it is compatible
    with existing runs. ``tag`` reuses the existing ``run_name``. git_sha is NOT included
    (Open Q #3 resolved 2026-05-25); the SHA lives in manifest.git.sha instead.
    """
    stamp = ts or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    rid = f"{stamp}_{task_short(task_id)}"
    if tag:
        rid += f"_{tag}"
    return rid


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


def eval_dir_for_checkpoint(
    checkpoint_path: str | Path,
    mode: str,
    *,
    experiments_root: str | Path = EXPERIMENTS_ROOT,
    eval_ts: str | None = None,
) -> Path | None:
    """Return ``experiments/<run_id>/eval/<mode>_<ts>/`` if *checkpoint_path* lives in a
    run_id tree, else ``None`` (caller keeps its legacy default).

    A checkpoint belongs to a run_id tree when one of its ancestor directories is
    ``<experiments_root>/<run_id>/`` (i.e. the path passes through ``experiments/``).
    The match is on the **unresolved** path so the run_id tree is detected even when its
    ``train`` entry is a symlink back to ``logs/`` (the minimal-touch layout, design #1):
    a checkpoint loaded as ``experiments/<run_id>/train/.../model.pt`` is recognized, while
    one loaded directly from ``logs/rsl_rl/<exp>/<ts>/model.pt`` returns None.

    Args:
        checkpoint_path: Path the evaluator resolved the checkpoint to.
        mode: static / periodic / segmented / sudden.
        experiments_root: Root of the run_id tree.
        eval_ts: Optional explicit eval timestamp.

    Returns:
        The eval output dir under the run_id tree, or None when not in a tree.
    """
    ckpt = Path(checkpoint_path)
    exp_root = Path(experiments_root)
    exp_name = exp_root.name  # "experiments"

    # Walk ancestors looking for <experiments_root>/<run_id>/ ; the run_id is the child
    # of the experiments dir on the path.
    parts = ckpt.parts
    for i, part in enumerate(parts):
        if part == exp_name and i + 1 < len(parts):
            run_id = parts[i + 1]
            run_root = exp_root / run_id if not exp_root.is_absolute() else Path(*parts[: i + 2])
            handle = RunHandle(
                run_id=run_id,
                root=run_root,
                manifest=_read_manifest_if_present(run_root),
            )
            return resolve_eval(handle, mode, eval_ts=eval_ts)
    return None


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


def emit_run_manifest(
    task: str,
    log_dir: str | Path,
    *,
    tag: str | None = None,
    config: dict | None = None,
    experiments_root: str | Path = EXPERIMENTS_ROOT,
    run_id: str | None = None,
    kind: str = "teacher",
    parent_run_id: str | None = None,
) -> RunHandle:
    """Create the single-tree entry point for a run without moving its training output.

    This is the **minimal-touch** wiring (chosen 2026-05-25): the existing training
    ``log_dir`` (``logs/rsl_rl/<exp>/<ts>``) keeps owning tb / checkpoints / resume, so
    training behavior is unchanged. Here we only add the run_id tree as a tracing entry:

        experiments/<run_id>/
          manifest.json        # this run's metadata (entry point for analyze/compare)
          config/              # env.yaml + agent.yaml copied from <log_dir>/params (if present)
          train -> <log_dir>   # relative symlink, so RunHandle.tb_dir/checkpoints resolve

    The timestamp inside run_id is parsed from the log_dir leaf when it starts with one,
    so the run_id timestamp matches the training folder (no drift). git sha is captured
    here via a best-effort ``git rev-parse``; wandb is left empty (the runner populates it
    at runtime, after this is called).

    Args:
        task: Full task ID (e.g. ``Isaac-FullDOF-TRPO-v0``).
        log_dir: The training log directory train.py already created.
        tag: Optional run tag (reuses agent_cfg.run_name).
        config: Optional config snapshot for manifest.config (num_envs, seed, ...).
        experiments_root: Root for the run_id tree.
        run_id: Override the computed run_id (else derived from task + log_dir timestamp).
        kind: "teacher" (default) or "student" (design section 2-C Option B).
        parent_run_id: For a student, the teacher's run_id (manifest link to the teacher).

    Returns:
        The created run's :class:`RunHandle`.
    """
    log_dir = Path(log_dir)
    ts = _timestamp_from_log_dir(log_dir)
    rid = run_id or make_run_id(task, tag=tag, ts=ts)

    run_root = Path(experiments_root) / rid
    (run_root / "config").mkdir(parents=True, exist_ok=True)

    # Copy the configs train.py dumps to <log_dir>/params, if they exist yet.
    params_dir = log_dir / "params"
    for fname in ("env.yaml", "agent.yaml"):
        src = params_dir / fname
        if src.is_file():
            (run_root / "config" / fname).write_text(src.read_text())

    # train/ -> log_dir relative symlink (so RunHandle.tb_dir / checkpoints_dir resolve).
    train_link = run_root / "train"
    if not train_link.exists():
        try:
            train_link.symlink_to(os.path.relpath(log_dir.resolve(), run_root))
        except OSError:
            pass  # symlink may be unsupported; manifest paths still point callers to log_dir

    manifest = Manifest(
        run_id=rid,
        task=task,
        kind=kind,
        parent_run_id=parent_run_id,
        config=config or {},
        git=_git_state(),
        paths={"tb": "train", "checkpoints": "train", "evals": []},
    )
    write_manifest(run_root, manifest)
    return RunHandle(run_id=rid, root=run_root, manifest=manifest.to_dict())


def run_id_from_path(
    path: str | Path, experiments_root: str | Path = EXPERIMENTS_ROOT,
) -> str | None:
    """Extract a run_id from a path that passes through ``experiments/<run_id>/``, else None.

    Used to resolve a teacher's run_id from its run directory so a student manifest can
    link to it via ``parent_run_id`` (design section 2-C Option B). A teacher in the old
    ``logs/rsl_rl`` layout (not in a run_id tree) returns None -> the student omits the link.
    Matches on the unresolved path, consistent with :func:`eval_dir_for_checkpoint`.
    """
    exp_name = Path(experiments_root).name
    parts = Path(path).parts
    for i, part in enumerate(parts):
        if part == exp_name and i + 1 < len(parts):
            return parts[i + 1]
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _timestamp_from_log_dir(log_dir: Path) -> str | None:
    """Extract a ``%Y-%m-%d_%H-%M-%S`` prefix from the log_dir leaf, else None.

    train.py names runs ``<ts>[_<run_name>]``; reusing that ts keeps the run_id timestamp
    aligned with the training folder. Returns None (caller generates a fresh ts) if the
    leaf does not start with a parseable timestamp.
    """
    leaf = log_dir.name
    parts = leaf.split("_")
    if len(parts) >= 2:
        candidate = f"{parts[0]}_{parts[1]}"
        try:
            datetime.strptime(candidate, "%Y-%m-%d_%H-%M-%S")
            return candidate
        except ValueError:
            return None
    return None


def _git_state() -> dict:
    """Best-effort current git sha / branch / dirty flag (empty dict on failure)."""
    import subprocess

    def _run(args: list[str]) -> str | None:
        try:
            return subprocess.check_output(
                args, cwd=os.path.dirname(__file__), stderr=subprocess.DEVNULL,
            ).decode().strip()
        except (subprocess.CalledProcessError, OSError):
            return None

    sha = _run(["git", "rev-parse", "HEAD"])
    if sha is None:
        return {}
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = _run(["git", "status", "--porcelain"])
    return {"sha": sha, "branch": branch, "dirty": bool(status)}


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
