"""StudentGRU export contract.

Ground truth is the ADOPTED A0g student
(experiments/.../trpo_sdeint_a0g_gru_s30_260729_151017/train/models/student_999.pt),
read off disk 2026-07-30: obs 72, gru_hidden 128, gru_head_hidden 64, latent 9.
"""
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from constrained_albc.deploy.spec import ExportContractError
from constrained_albc.deploy.specs.student_gru import StudentGRUSpec

# Ground-truth shapes from student_999.pt (verified 2026-07-30)
GT = {
    "gru.weight_ih_l0": (384, 72), "gru.weight_hh_l0": (384, 128),
    "gru.bias_ih_l0": (384,), "gru.bias_hh_l0": (384,),
    "head.0.weight": (64, 128), "head.0.bias": (64,),
    "head.2.weight": (64,), "head.2.bias": (64,),
    "head.3.weight": (9, 64), "head.3.bias": (9,),
}


class _FakeStudent(torch.nn.Module):
    """Stands in for the real model: exposes the verified state_dict."""

    def __init__(self):
        super().__init__()
        self._sd = {k: torch.zeros(s, dtype=torch.float64) for k, s in GT.items()}

    def state_dict(self, *a, **k):
        return self._sd


def _cfg(**over):
    base = dict(gru_layers=1, gru_hidden=128, gru_head_hidden=64)
    base.update(over)
    return SimpleNamespace(**base)


def test_contract_keys_match_the_npforward_runtime():
    """The contract must be exactly the keys npforward.StudentGRU loads."""
    spec = StudentGRUSpec()
    assert set(spec.key_contract.keys()) == set(GT.keys())
    assert spec.npz_filename == "weights_gru.npz"
    assert spec.name == "student_gru"


def test_contract_shapes_match_the_adopted_checkpoint():
    spec = StudentGRUSpec()
    for key, shape in GT.items():
        assert spec.key_contract[key].shape == shape, key


def test_gate_rows_are_three_times_hidden():
    """torch nn.GRU packs [r, z, n] on the row axis -- a 1x/4x contract would load
    a wrong-sized npz without any shape error at the board."""
    spec = StudentGRUSpec(obs_dim=72, hidden=64, head_hidden=32, latent_dim=9)
    assert spec.key_contract["gru.weight_ih_l0"].shape == (192, 72)
    assert spec.key_contract["gru.weight_hh_l0"].shape == (192, 64)


def test_contract_follows_the_teacher_obs_and_latent_width():
    """The batch export passes the TEACHER's geometry, so a student distilled against
    a different-width teacher is rejected instead of shipping mispaired."""
    spec = StudentGRUSpec(obs_dim=69, hidden=128, head_hidden=64, latent_dim=12)
    assert spec.key_contract["gru.weight_ih_l0"].shape == (384, 69)
    assert spec.key_contract["head.3.weight"].shape == (12, 64)


def test_shallow_head_is_rejected():
    """gru_head_hidden=0 builds head = Linear only, so head.2/head.3 do not exist and
    npforward.StudentGRU cannot run it."""
    with pytest.raises(ExportContractError, match="gru_head_hidden"):
        StudentGRUSpec._assert_board_runnable(_cfg(gru_head_hidden=0))


def test_multi_layer_is_rejected():
    """npforward reads only *_l0 through a single-layer gru_cell."""
    with pytest.raises(ExportContractError, match="gru_layers"):
        StudentGRUSpec._assert_board_runnable(_cfg(gru_layers=2))


def test_extra_obs_is_rejected():
    """Gen-1 extra-obs students have no board-side input/normalization contract."""
    with pytest.raises(ExportContractError, match="extra_obs_dim"):
        StudentGRUSpec._assert_board_runnable(_cfg(extra_obs_dim=4))


def test_adopted_geometry_is_accepted():
    StudentGRUSpec._assert_board_runnable(_cfg())  # must not raise


def test_map_is_identity_and_fp32():
    spec = StudentGRUSpec()
    mapped = spec.map_state_dict(_FakeStudent())
    assert set(mapped.keys()) == set(GT.keys())
    for k, shape in GT.items():
        assert mapped[k].shape == shape
        assert mapped[k].dtype == np.float32  # cast from float64


def test_missing_source_key_fails_loudly():
    student = _FakeStudent()
    del student._sd["head.2.weight"]
    with pytest.raises(ExportContractError, match="head.2.weight"):
        StudentGRUSpec().map_state_dict(student)
