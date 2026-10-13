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


def _payload_files(arch: str) -> tuple[str, ...]:
    """Pack contents for one student architecture (the teacher half is common)."""
    if arch == "tcn":
        return _PAYLOAD_FILES
    if arch == "gru":
        return (
            "weights_teacher.npz",
            "weights_gru.npz",
            "npforward.py",
            "golden/golden_gru.npz",
            "golden/golden_teacher.npz",
        )
    raise ValueError(f"unknown student arch {arch!r} (expected 'tcn' or 'gru')")


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


def _close_gru(ws: dict, gs: dict) -> dict[str, float]:
    """Step the numpy GRU through the golden sequence, carrying its own hidden.

    Returns the latent error AND the final-hidden error: the hidden carry is the
    thing a single-step check cannot see, so it is compared directly rather than
    only through the latents it feeds.
    """
    student = npforward.StudentGRU(ws)
    seq = gs["input_seq"]
    hidden = student.init_hidden(batch=seq.shape[0])
    latents = []
    for t in range(seq.shape[1]):
        z, hidden = student.step(seq[:, t, :], hidden)
        latents.append(z)
    latent = np.stack(latents, axis=1)                      # (batch, T, latent)
    # torch hidden is (num_layers, batch, hidden); the runtime carries (batch, hidden).
    return {
        "latent": float(np.max(np.abs(latent - gs["latent_seq"]))),
        "hidden": float(np.max(np.abs(hidden - gs["hidden_final"][0]))),
    }


def self_close(out_dir: str, atol: float = _ATOL, arch: str = "tcn") -> dict:
    """Run npforward (pure numpy) against the pack's goldens; return the parity dict.

    Closes the same contract points the Mac/board test_npforward.py checks: teacher
    normalize, teacher act, and the student latent -- plus, for the stateful GRU, the
    final hidden state.
    """
    student_npz, golden_npz = {
        "tcn": ("weights_tcn.npz", "golden_tcn.npz"),
        "gru": ("weights_gru.npz", "golden_gru.npz"),
    }[arch]
    wt = dict(np.load(os.path.join(out_dir, "weights_teacher.npz")))
    ws = dict(np.load(os.path.join(out_dir, student_npz)))
    gt = dict(np.load(os.path.join(out_dir, "golden", "golden_teacher.npz")))
    gs = dict(np.load(os.path.join(out_dir, "golden", golden_npz)))

    teacher = npforward.TeacherActor(wt)
    norm_err = float(np.max(np.abs(teacher.normalize(gt["obs"]) - gt["obs_normalized"])))
    act_err = float(np.max(np.abs(teacher.act(gt["obs_normalized"], gt["latent"]) - gt["action"])))
    teacher_closed = norm_err <= atol and act_err <= atol

    parity = {
        "atol": atol,
        "teacher_normalize_max_err": norm_err,
        "teacher_act_max_err": act_err,
        "teacher_closed": teacher_closed,
    }
    if arch == "tcn":
        err = float(np.max(np.abs(npforward.StudentTCN(ws).forward(gs["input_window"]) - gs["latent"])))
        student_closed = err <= atol
        parity["tcn_latent_max_err"] = err
        parity["tcn_closed"] = student_closed
    else:
        errs = _close_gru(ws, gs)
        student_closed = errs["latent"] <= atol and errs["hidden"] <= atol
        parity["gru_latent_max_err"] = errs["latent"]
        parity["gru_hidden_max_err"] = errs["hidden"]
        parity["gru_closed"] = student_closed
    parity["closed_in_container"] = teacher_closed and student_closed
    return parity


def write_manifest(out_dir: str, checkpoints: dict, parity: dict, arch: str = "tcn") -> str:
    """Write MANIFEST.json. Dims are derived from the payload tensors themselves
    (never hardcoded), so the manifest can't drift from what was actually packed."""
    wt = dict(np.load(os.path.join(out_dir, "weights_teacher.npz")))
    if arch == "tcn":
        ws = dict(np.load(os.path.join(out_dir, "weights_tcn.npz")))
        gs = dict(np.load(os.path.join(out_dir, "golden", "golden_tcn.npz")))
        obs_dim = int(ws["channel_transform.0.weight"].shape[1])
        window = {"tcn_history": int(gs["input_window"].shape[1])}
    else:
        ws = dict(np.load(os.path.join(out_dir, "weights_gru.npz")))
        gs = dict(np.load(os.path.join(out_dir, "golden", "golden_gru.npz")))
        obs_dim = int(ws["gru.weight_ih_l0"].shape[1])
        # The GRU carries state instead of a window; record the hidden width and the
        # golden's sequence length (what the carry was actually verified over).
        window = {"gru_hidden": int(ws["gru.weight_hh_l0"].shape[1]),
                  "gru_golden_steps": int(gs["input_seq"].shape[1])}
    dims = {
        "obs": obs_dim,
        "action": int(wt["actor.6.weight"].shape[0]),
        "latent": int(ws["head.3.weight"].shape[0]),
        "teacher_input": int(wt["actor.0.weight"].shape[1]),
        **window,
    }
    files = {}
    for rel in _payload_files(arch):
        p = os.path.join(out_dir, rel)
        files[rel] = {"sha256": _sha256(p), "bytes": os.path.getsize(p)}
    manifest = {
        "tag": os.path.basename(os.path.normpath(out_dir)),
        "student_arch": arch,
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
