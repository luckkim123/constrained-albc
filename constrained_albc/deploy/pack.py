"""Pack assembly: parity self-close + MANIFEST + npforward runtime copy.

A deploy pack is self-verifying: weights + golden vectors + the torch-free numpy
runtime (npforward.py) + MANIFEST.json recording per-file hashes and the parity
result. self_close() re-runs npforward on the pack's own goldens exactly as the
board will, so MANIFEST's "closed_in_container" is evidence, not a claim.

Goldens MUST be CPU-generated (see golden.py): GPU cuDNN conv differs from the
standard conv (~1e-4) that the board numpy runtime implements.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil

import numpy as np

from constrained_albc.deploy import npforward

_ATOL = 1e-5
_PAYLOAD_FILES = (
    "weights_teacher.npz",
    "weights_tcn.npz",
    "npforward.py",
    "golden/golden_tcn.npz",
    "golden/golden_teacher.npz",
)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_npforward(out_dir: str) -> str:
    """Copy the packaged numpy runtime into the pack; return its sha256."""
    src = os.path.join(os.path.dirname(__file__), "npforward.py")
    dst = os.path.join(out_dir, "npforward.py")
    shutil.copyfile(src, dst)
    return _sha256(dst)


def self_close(out_dir: str, atol: float = _ATOL) -> dict:
    """Run npforward (pure numpy) against the pack's goldens; return the parity dict.

    Closes the same three contract points the Mac/board test_npforward.py checks:
    teacher normalize, teacher act, TCN latent.
    """
    wt = dict(np.load(os.path.join(out_dir, "weights_teacher.npz")))
    ws = dict(np.load(os.path.join(out_dir, "weights_tcn.npz")))
    gt = dict(np.load(os.path.join(out_dir, "golden", "golden_teacher.npz")))
    gs = dict(np.load(os.path.join(out_dir, "golden", "golden_tcn.npz")))

    teacher = npforward.TeacherActor(wt)
    norm_err = float(np.max(np.abs(teacher.normalize(gt["obs"]) - gt["obs_normalized"])))
    act_err = float(np.max(np.abs(teacher.act(gt["obs_normalized"], gt["latent"]) - gt["action"])))
    tcn_err = float(np.max(np.abs(npforward.StudentTCN(ws).forward(gs["input_window"]) - gs["latent"])))

    teacher_closed = norm_err <= atol and act_err <= atol
    tcn_closed = tcn_err <= atol
    return {
        "closed_in_container": teacher_closed and tcn_closed,
        "atol": atol,
        "teacher_normalize_max_err": norm_err,
        "teacher_act_max_err": act_err,
        "teacher_closed": teacher_closed,
        "tcn_latent_max_err": tcn_err,
        "tcn_closed": tcn_closed,
    }


def write_manifest(out_dir: str, checkpoints: dict, parity: dict) -> str:
    """Write MANIFEST.json. Dims are derived from the payload tensors themselves
    (never hardcoded), so the manifest can't drift from what was actually packed."""
    ws = dict(np.load(os.path.join(out_dir, "weights_tcn.npz")))
    wt = dict(np.load(os.path.join(out_dir, "weights_teacher.npz")))
    gs = dict(np.load(os.path.join(out_dir, "golden", "golden_tcn.npz")))
    dims = {
        "obs": int(ws["channel_transform.0.weight"].shape[1]),
        "action": int(wt["actor.6.weight"].shape[0]),
        "latent": int(ws["head.3.weight"].shape[0]),
        "teacher_input": int(wt["actor.0.weight"].shape[1]),
        "tcn_history": int(gs["input_window"].shape[1]),
    }
    files = {}
    for rel in _PAYLOAD_FILES:
        p = os.path.join(out_dir, rel)
        files[rel] = {"sha256": _sha256(p), "bytes": os.path.getsize(p)}
    manifest = {
        "tag": os.path.basename(os.path.normpath(out_dir)),
        "checkpoints": checkpoints,
        "dims": dims,
        "normalization": "(x - mean) / (std + 0.01)   # eps=0.01, _std=sqrt(var) eps NOT folded",
        "golden_device": "cpu  # standard conv, matches board numpy runtime",
        "files": files,
        "parity": parity,
        "npforward_sha256": files["npforward.py"]["sha256"],
    }
    path = os.path.join(out_dir, "MANIFEST.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return path
