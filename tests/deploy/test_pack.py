"""Pack assembly tests: parity self-close + MANIFEST + npforward runtime copy.

Uses tiny torch models with the SAME layer structure / state_dict key names as
the real StudentEncoderTCN / ActorCriticEncoder export surface, so the full
golden -> npforward(numpy) -> compare path runs for real (no mocks), just at
small dims. npforward's classes are dim-agnostic, which is what makes this work.
"""
import hashlib
import json
import os

import numpy as np
import pytest
import torch
import torch.nn as nn

from constrained_albc.deploy.golden import export_golden_tcn, export_golden_teacher
from constrained_albc.deploy.pack import copy_npforward, self_close, write_manifest

_D, _C, _H, _LAT, _ACT = 6, 4, 9, 3, 2


class _TinyTCN(nn.Module):
    """Mirrors StudentEncoderTCN's module names so state_dict keys match npforward."""

    def __init__(self):
        super().__init__()
        self.channel_transform = nn.Sequential(nn.Linear(_D, _C), nn.ELU())
        self.conv = nn.Sequential(
            nn.Conv1d(_C, _C, 3), nn.ELU(),
            nn.Conv1d(_C, _C, 3), nn.ELU(),
            nn.Conv1d(_C, _C, 3), nn.ELU(),
        )
        flat = _C * (_H - 6)  # three k=3 convs, stride 1, no pad
        self.head = nn.Sequential(nn.Linear(flat, 8), nn.ELU(), nn.LayerNorm(8), nn.Linear(8, _LAT))

    def forward(self, win):
        b, h, d = win.shape
        x = self.channel_transform(win.reshape(b * h, d)).reshape(b, h, -1)
        x = self.conv(x.transpose(1, 2))
        return torch.nn.functional.softsign(self.head(x.reshape(b, -1)))


class _Normalizer(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.register_buffer("_mean", torch.randn(1, dim) * 0.1)
        self.register_buffer("_std", torch.rand(1, dim) + 0.5)

    def forward(self, x):
        return (x - self._mean) / (self._std + 0.01)


class _TinyTeacher(nn.Module):
    def __init__(self):
        super().__init__()
        self.actor_obs_normalizer = _Normalizer(_D)
        self.actor = nn.Sequential(
            nn.Linear(_D + _LAT, 8), nn.ELU(),
            nn.Linear(8, 8), nn.ELU(),
            nn.Linear(8, 8), nn.ELU(),
            nn.Linear(8, _ACT),
        )


def _save_f32(path, tensors):
    np.savez(path, **{k: v.detach().numpy().astype(np.float32) for k, v in tensors.items()})


def _make_pack(out_dir: str) -> None:
    """Assemble a consistent tiny pack: weights + goldens from the SAME instances."""
    torch.manual_seed(0)
    tcn, teacher = _TinyTCN().eval(), _TinyTeacher().eval()
    _save_f32(os.path.join(out_dir, "weights_tcn.npz"), dict(tcn.state_dict()))
    _save_f32(
        os.path.join(out_dir, "weights_teacher.npz"),
        {k.replace("actor_obs_normalizer.", "normalizer."): v for k, v in teacher.state_dict().items()},
    )
    export_golden_tcn(tcn, out_dir, history=_H, obs_dim=_D)
    export_golden_teacher(teacher, out_dir, obs_dim=_D, latent_dim=_LAT)


def test_self_close_passes_on_consistent_pack(tmp_path):
    out = str(tmp_path)
    _make_pack(out)
    parity = self_close(out)
    assert parity["closed_in_container"] is True
    assert parity["teacher_closed"] is True and parity["tcn_closed"] is True
    assert parity["teacher_normalize_max_err"] <= 1e-5
    assert parity["teacher_act_max_err"] <= 1e-5
    assert parity["tcn_latent_max_err"] <= 1e-5


def test_self_close_fails_on_perturbed_weights(tmp_path):
    out = str(tmp_path)
    _make_pack(out)
    wpath = os.path.join(out, "weights_teacher.npz")
    w = dict(np.load(wpath))
    w["actor.0.weight"] = w["actor.0.weight"] + 0.05
    np.savez(wpath, **w)
    parity = self_close(out)
    assert parity["closed_in_container"] is False
    assert parity["teacher_closed"] is False
    assert parity["tcn_closed"] is True  # only the teacher was perturbed


def test_copy_npforward_copies_packaged_runtime(tmp_path):
    out = str(tmp_path)
    sha = copy_npforward(out)
    dst = os.path.join(out, "npforward.py")
    assert os.path.isfile(dst)
    assert sha == hashlib.sha256(open(dst, "rb").read()).hexdigest()


def test_write_manifest_records_dims_hashes_parity(tmp_path):
    out = str(tmp_path / "pack_tiny_260612_000000")
    os.makedirs(out)
    _make_pack(out)
    copy_npforward(out)
    parity = self_close(out)
    ckpts = {"student_tcn": {"file": "s.pt", "iter": 1, "path": "logs/s.pt"},
             "teacher": {"file": "t.pt", "iter": 2, "path": "logs/t.pt"}}
    mpath = write_manifest(out, checkpoints=ckpts, parity=parity)
    m = json.load(open(mpath))
    assert m["tag"] == "pack_tiny_260612_000000"
    assert m["checkpoints"] == ckpts
    assert m["dims"] == {"obs": _D, "action": _ACT, "latent": _LAT,
                         "teacher_input": _D + _LAT, "tcn_history": _H}
    assert m["parity"]["closed_in_container"] is True
    expected_files = {"weights_teacher.npz", "weights_tcn.npz", "npforward.py",
                      "golden/golden_tcn.npz", "golden/golden_teacher.npz"}
    assert set(m["files"]) == expected_files
    for rel, info in m["files"].items():
        p = os.path.join(out, rel)
        assert info["bytes"] == os.path.getsize(p)
        assert info["sha256"] == hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert m["npforward_sha256"] == m["files"]["npforward.py"]["sha256"]


def test_golden_internal_sanity_gate_raises_on_path_mismatch(tmp_path):
    """A model whose forward() diverges from the stagewise capture must fail loudly."""

    class _BrokenTCN(_TinyTCN):
        def forward(self, win):
            return super().forward(win) + 1.0  # diverges from softsign(head(...))

    with pytest.raises(RuntimeError, match="diverged"):
        export_golden_tcn(_BrokenTCN().eval(), str(tmp_path), history=_H, obs_dim=_D)
