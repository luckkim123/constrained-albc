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
train.py / eval.py / common.py yet, so adding it does not change any training or
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
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Date-like prefix on a run_name tag (e.g. "20260527_" or "260527_"). run_id already prepends
# the timestamp, so a dated tag would double the date (e.g. 260527_..._trpo_20260527_foo). We
# strip it in make_run_id so a tag like "20260527_per_axis_floor" yields "..._trpo_per_axis_floor".
_TAG_DATE_PREFIX = re.compile(r"^(?:\d{8}|\d{6})_")

# Default roots (cwd-relative, matching common.py / train.py conventions).
EXPERIMENTS_ROOT = "experiments"
LEGACY_LOGS_ROOT = "logs/rsl_rl"
MANIFEST_NAME = "manifest.json"

# Experiments are grouped under experiments/<EXPERIMENTS_GROUP_PREFIX>/<experiment_name>/<run_id>/
# (2026-05-26), mirroring the logs/rsl_rl/<experiment_name>/ layout so teacher/student
# runs cluster by experiment_name (e.g. albc_trpo_teacher / albc_trpo_student) instead of
# sitting flat under experiments/. The run_id tree (manifest + train symlink + eval/) lives
# at the leaf. Detection (eval_dir_for_checkpoint / run_id_from_path) no longer assumes the
# run_id sits directly under experiments/ -- it locates the run_root via the `train` entry,
# so it is independent of how deep the grouping is.
EXPERIMENTS_GROUP_PREFIX = "rsl_rl"
TRAIN_LINK_NAME = "train"

# task_short extraction (design section 2-A). Ordered specific -> general so that
# superset substrings match first: "-TRPO-NoIPO-" before "-TRPO-", "-PPO-Enc-" before
# "-PPO-". A wrong order would classify Isaac-ConstrainedALBC-TRPO-NoIPO-v0 as "trpo".
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

    e.g. ``Isaac-ConstrainedALBC-TRPO-v0`` -> ``trpo``, ``Isaac-ConstrainedALBC-PPO-Enc-v0`` -> ``ppo-enc``.
    Falls back to a lowercased, dash-joined slug of the task ID if no pattern matches,
    so an unrecognized task still yields a usable (if verbose) tag rather than crashing.
    """
    for needle, short in _TASK_SHORT_PATTERNS:
        if needle in task_id:
            return short
    # Fallback: strip the Isaac- prefix / -v0 suffix and slugify.
    slug = task_id
    for prefix in ("Isaac-ConstrainedALBC-", "Isaac-"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
            break
    slug = slug.rsplit("-v", 1)[0]
    return slug.lower().replace("-", "_") or "run"


# run_id timestamp format. Shortened 2026-05-26 from "%Y-%m-%d_%H-%M-%S" (19 chars,
# e.g. 2026-05-25_16-02-48) to "%y%m%d_%H%M%S" (13 chars, e.g. 260525_160248) -- the
# user wanted a shorter run_id; task_short is kept. train.py emits the same format so
# the run_id timestamp matches the training folder leaf (no drift).
RUN_TS_FORMAT = "%y%m%d_%H%M%S"


def make_run_id(task_id: str, tag: str | None = None, ts: str | None = None) -> str:
    """Build a run_id ``<task_short>[_<tag>]_<ts>`` (label-before-date, 2026-06-05).

    The label (task_short + optional tag) leads; the timestamp is the TRAILING field so
    all output names read label-before-date consistently (matching the eval ``<mode>_<ts>``
    convention). The timestamp format (:data:`RUN_TS_FORMAT`, ``%y%m%d_%H%M%S``) matches
    train.py. ``tag`` reuses the existing ``run_name``. git_sha is NOT included (Open Q #3
    resolved 2026-05-25); the SHA lives in manifest.git.sha instead.
    """
    stamp = ts or datetime.now().strftime(RUN_TS_FORMAT)
    label = task_short(task_id)
    if tag:
        # Strip a leading date prefix from the tag so the run_id date is not doubled
        # (run_id already ends with the timestamp). "20260527_per_axis_floor" -> "per_axis_floor".
        tag = _TAG_DATE_PREFIX.sub("", tag)
        if tag:
            label += f"_{tag}"
    return f"{label}_{stamp}"


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


def _is_run_dir(d: Path) -> tuple[bool, dict | None]:
    """A directory is a run when it holds a manifest or a ``train`` entry."""
    manifest = _read_manifest_if_present(d)
    return (manifest is not None or (d / TRAIN_LINK_NAME).exists()), manifest


def find_runs(experiments_root: str = EXPERIMENTS_ROOT) -> list[RunHandle]:
    """List active run_id trees under ``experiments/``, newest first.

    Runs are grouped ``experiments/rsl_rl/<experiment_name>/<run_id>/`` (2026-05-26), with an
    optional purpose layer ``.../<experiment_name>/<group>/<run_id>/`` (e.g. ``dr_harder/``);
    a flat ``experiments/<run_id>/`` (legacy of this tree) is still recognized. The scan checks
    each top-level dir as a run and, if it is not one, descends (``rglob``) so grouped runs at
    any depth are found.

    Skipped during enumeration:
      - ``legacy/`` (frozen, no run_id convention),
      - symlinks (an alias such as a ``baseline`` -> run pointer is NOT a separate run; counting
        it would double-list the target run under the wrong run_id),
      - ``_``-prefixed dirs (backups/scratch like ``_pre_reanalysis_backup_*``; a real run_id is
        timestamped, never ``_``-prefixed).

    run_id sort is by directory name (timestamp-prefixed), newest first.
    """
    root = Path(experiments_root)
    if not root.exists():
        return []

    def _skip(p: Path, rel_to: Path) -> bool:
        # alias symlinks + frozen/legacy + backup/scratch dirs are not runs themselves.
        # rglob is a FLAT iterator (pruning a parent does not stop it descending into the
        # parent's children), so a backup like ``_pre_reanalysis_backup/analysis/<diagnose>``
        # would still surface the non-underscore leaf. Guard on ANY ancestor segment (relative
        # to the scan root) being legacy / ``_``-prefixed, not just the leaf name.
        if p.is_symlink():
            return True
        try:
            segs = p.relative_to(rel_to).parts
        except ValueError:
            segs = (p.name,)
        return any(s == "legacy" or s.startswith("_") for s in segs)

    runs: list[RunHandle] = []
    for d in root.iterdir():
        if not d.is_dir() or _skip(d, root):
            continue
        is_run, manifest = _is_run_dir(d)
        if is_run:
            runs.append(RunHandle(run_id=d.name, root=d, manifest=manifest))
            continue
        # Not a run itself -> a group dir (e.g. rsl_rl, rsl_rl/<exp>, rsl_rl/<exp>/<group>);
        # descend to find runs. Prune skipped subtrees so aliases/backups never count as runs.
        for sub in d.rglob("*"):
            if not sub.is_dir() or _skip(sub, root):
                continue
            is_run, manifest = _is_run_dir(sub)
            if is_run:
                runs.append(RunHandle(run_id=sub.name, root=sub, manifest=manifest))
    runs.sort(key=lambda r: r.run_id, reverse=True)
    return runs


def resolve_run(
    run_spec: str,
    experiments_root: str = EXPERIMENTS_ROOT,
    legacy_logs_root: str = LEGACY_LOGS_ROOT,
) -> RunHandle:
    """Resolve a run specifier to a :class:`RunHandle`.

    Resolution order (first match wins):
      1. ``run_spec`` is an existing directory path -> wrap it directly.
      2. ``experiments/<run_spec>/`` exists (flat layout) -> active run_id tree.
      3. Substring / index match against active runs under ``experiments/`` (this is the
         path that resolves grouped ``experiments/rsl_rl/<exp>/<run_id>/`` runs via find_runs).
      4. Legacy fallback: a directory under ``logs/rsl_rl/<exp>/`` whose name matches,
         wrapped as a legacy handle (``manifest=None``).

    Raises:
        FileNotFoundError: if nothing matches.
    """
    # 1. Direct path.
    p = Path(run_spec)
    if p.is_dir():
        manifest = _read_manifest_if_present(p)
        is_legacy = manifest is None and not (p / TRAIN_LINK_NAME).exists()
        return RunHandle(run_id=p.name, root=p, manifest=manifest, is_legacy=is_legacy)

    # 2. experiments/<run_spec>/ (flat layout only; grouped runs fall through to case 3).
    candidate = Path(experiments_root) / run_spec
    if candidate.is_dir():
        return RunHandle(
            run_id=run_spec,
            root=candidate,
            manifest=_read_manifest_if_present(candidate),
        )

    # 3. Active runs: integer index (0 = latest) or substring. Walks grouped subtrees.
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

    The timestamp uses :data:`RUN_TS_FORMAT` (the SAME format as the run_id), so a run's
    eval folder reads ``static_260606_054825`` matching the run_id's ``..._260606_004205``
    -- one date format across the whole run tree (no run_id %y%m%d vs eval %Y-%m-%d drift).
    RUN_TS_FORMAT is the single source of truth for every output-name timestamp.

    Args:
        run: Resolved run handle.
        mode: One of static / periodic / segmented.
        eval_ts: Optional explicit eval timestamp; defaults to now.
    """
    ts = eval_ts or datetime.now().strftime(RUN_TS_FORMAT)
    return run.eval_root / f"{mode}_{ts}"


def _run_root_from_path(path: str | Path) -> Path | None:
    """Return the run_root for a path that passes through a ``train`` entry, else None.

    The run_id tree's training output is reached via ``<run_root>/train`` (a symlink to
    the real ``logs/`` dir, design #1). A checkpoint the evaluator loads therefore looks
    like ``.../<run_root>/train/.../model.pt``. Locating the ``train`` segment and taking
    its parent gives the run_root **independent of how deeply ``experiments/`` is grouped**
    (flat ``experiments/<run_id>/`` or grouped ``experiments/rsl_rl/<exp>/<run_id>/``).

    Detection is on the **unresolved** path so the tree is recognized even though ``train``
    is a symlink back into ``logs/``: a checkpoint loaded directly from
    ``logs/rsl_rl/<exp>/<ts>/model.pt`` has no ``train`` ancestor and returns None.
    """
    parts = Path(path).parts
    for i in range(len(parts) - 1, -1, -1):  # rightmost train wins (closest to the ckpt)
        if parts[i] == TRAIN_LINK_NAME and i >= 1:
            return Path(*parts[:i])
    return None


def eval_dir_for_checkpoint(
    checkpoint_path: str | Path,
    mode: str,
    *,
    experiments_root: str | Path = EXPERIMENTS_ROOT,  # retained for signature compat (unused)
    eval_ts: str | None = None,
) -> Path | None:
    """Return ``<run_root>/eval/<mode>_<ts>/`` if *checkpoint_path* lives in a run_id tree,
    else ``None`` (caller keeps its legacy default).

    A checkpoint belongs to a run_id tree when one of its ancestor directories is the
    run_root's ``train`` entry (the symlink to ``logs/``, design #1). Detection is via the
    ``train`` segment (:func:`_run_root_from_path`), so it works regardless of the
    experiments grouping depth (flat or ``experiments/rsl_rl/<exp>/<run_id>/``). A checkpoint
    loaded directly from ``logs/rsl_rl/<exp>/<ts>/model.pt`` returns None.

    Args:
        checkpoint_path: Path the evaluator resolved the checkpoint to.
        mode: static / periodic / segmented.
        experiments_root: Unused (kept for call-site compatibility); detection is grouping-agnostic.
        eval_ts: Optional explicit eval timestamp.

    Returns:
        The eval output dir under the run_id tree, or None when not in a tree.
    """
    run_root = _run_root_from_path(checkpoint_path)
    if run_root is None:
        return None
    handle = RunHandle(
        run_id=run_root.name,
        root=run_root,
        manifest=_read_manifest_if_present(run_root),
    )
    return resolve_eval(handle, mode, eval_ts=eval_ts)


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


def experiments_group_dir(
    experiment_name: str | None,
    experiments_root: str | Path = EXPERIMENTS_ROOT,
    group: str | None = None,
) -> Path:
    """Return the grouped experiments dir ``<experiments_root>/<prefix>/<experiment_name>/[<group>/]``.

    Mirrors ``logs/rsl_rl/<experiment_name>/[<group>/]`` so a run's experiments tree clusters
    by experiment_name (e.g. ``albc_trpo_teacher`` / ``albc_trpo_student``) and, optionally, by
    a campaign/purpose *group* layer (e.g. ``att_dr_harder``). The group is the experiment-dir
    standard's ``<group>`` segment (docs/plans/2026-06-07-experiment-dir-standard.md SS3/4):
    ``rsl_rl/<exp>/<group>/<run_id>/``. When *experiment_name* is falsy the run lands directly
    under the group prefix (kept simple rather than failing -- experiment_name is always set in
    practice); a falsy *group* keeps the original 3-segment layout (back-compat).
    """
    root = Path(experiments_root) / EXPERIMENTS_GROUP_PREFIX
    if experiment_name:
        root = root / experiment_name
    if group:
        root = root / group
    return root


def emit_run_manifest(
    task: str,
    log_dir: str | Path,
    *,
    tag: str | None = None,
    config: dict | None = None,
    experiments_root: str | Path = EXPERIMENTS_ROOT,
    experiment_name: str | None = None,
    group: str | None = None,
    run_id: str | None = None,
    kind: str = "teacher",
    parent_run_id: str | None = None,
) -> RunHandle:
    """Create the single-tree entry point for a run without moving its training output.

    This is the **minimal-touch** wiring (chosen 2026-05-25): the existing training
    ``log_dir`` (``logs/rsl_rl/<exp>/<ts>``) keeps owning tb / checkpoints / resume, so
    training behavior is unchanged. Here we only add the run_id tree as a tracing entry,
    grouped by experiment_name to mirror the logs layout (2026-05-26):

        experiments/rsl_rl/<experiment_name>/<run_id>/
          manifest.json        # this run's metadata (entry point for analyze/compare)
          config/              # env.yaml + agent.yaml copied from <log_dir>/params (if present)
          train -> <log_dir>   # relative symlink, so RunHandle.tb_dir/checkpoints resolve

    The timestamp inside run_id is parsed from the log_dir leaf when it starts with one,
    so the run_id timestamp matches the training folder (no drift). git sha is captured
    here via a best-effort ``git rev-parse``; wandb is left empty (the runner populates it
    at runtime, after this is called).

    Args:
        task: Full task ID (e.g. ``Isaac-ConstrainedALBC-TRPO-v0``).
        log_dir: The training log directory train.py already created.
        tag: Optional run tag (reuses agent_cfg.run_name).
        config: Optional config snapshot for manifest.config (num_envs, seed, ...).
        experiments_root: Root for the run_id tree.
        experiment_name: Groups the run under ``experiments/rsl_rl/<experiment_name>/``
            (mirrors logs/rsl_rl/<experiment_name>/). Falls back to ``config["experiment_name"]``
            then ungrouped if neither is given.
        group: Optional campaign/purpose layer inserted as ``<experiment_name>/<group>/<run_id>/``
            (the experiment-dir standard's ``<group>`` segment, e.g. ``att_dr_harder``). Falls back
            to ``config["run_group"]``; falsy keeps the original 3-segment layout.
        run_id: Override the computed run_id (else derived from task + log_dir timestamp).
        kind: "teacher" (default) or "student" (design section 2-C Option B).
        parent_run_id: For a student, the teacher's run_id (manifest link to the teacher).

    Returns:
        The created run's :class:`RunHandle`.
    """
    log_dir = Path(log_dir)
    ts = _timestamp_from_log_dir(log_dir)
    rid = run_id or make_run_id(task, tag=tag, ts=ts)

    exp_name = experiment_name or (config or {}).get("experiment_name")
    grp = group or (config or {}).get("run_group")
    run_root = experiments_group_dir(exp_name, experiments_root, group=grp) / rid
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
    path: str | Path, experiments_root: str | Path = EXPERIMENTS_ROOT,  # noqa: ARG001 compat
) -> str | None:
    """Extract a run_id from a path that passes through a run_id tree's ``train`` entry, else None.

    Used to resolve a teacher's run_id from its run directory so a student manifest can
    link to it via ``parent_run_id`` (design section 2-C Option B). A teacher in the old
    ``logs/rsl_rl`` layout (no ``train`` ancestor) returns None -> the student omits the link.
    Detection is via the ``train`` segment (:func:`_run_root_from_path`), consistent with
    :func:`eval_dir_for_checkpoint` and independent of experiments grouping depth.
    """
    run_root = _run_root_from_path(path)
    return run_root.name if run_root is not None else None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _timestamp_from_log_dir(log_dir: Path) -> str | None:
    """Extract the timestamp prefix from the log_dir leaf, else None.

    train.py names runs ``<ts>[_<run_name>]``; reusing that ts keeps the run_id timestamp
    aligned with the training folder. Both the current ``%y%m%d_%H%M%S`` format and the
    legacy ``%Y-%m-%d_%H-%M-%S`` are accepted so older training folders still resolve.
    Returns None (caller generates a fresh ts) if the leaf does not start with a parseable
    timestamp.
    """
    leaf = log_dir.name
    parts = leaf.split("_")
    if len(parts) < 2:
        return None
    # Dual-accept (2026-06-05 label-before-date flip):
    #   new format -> ts is the TRAILING field-pair (trpo_main_teacher_260525_232805)
    #   legacy     -> ts is the LEADING field-pair  (260525_232805_trpo_main_teacher)
    # Try trailing first (current), then leading (older folders). RUN_TS_FORMAT (short)
    # is what train.py emits; the long legacy format is kept for older resolves.
    for candidate in (f"{parts[-2]}_{parts[-1]}", f"{parts[0]}_{parts[1]}"):
        for fmt in (RUN_TS_FORMAT, "%Y-%m-%d_%H-%M-%S"):
            try:
                datetime.strptime(candidate, fmt)
                return candidate
            except ValueError:
                continue
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
