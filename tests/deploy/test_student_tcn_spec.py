import numpy as np
import torch
from constrained_albc.deploy.specs.student_tcn import StudentTCNSpec

# Ground-truth shapes from student_999.pt (verified 2026-06-11)
GT = {
    "channel_transform.0.weight": (32, 69), "channel_transform.0.bias": (32,),
    "conv.0.weight": (64, 32, 3), "conv.0.bias": (64,),
    "conv.2.weight": (128, 64, 3), "conv.2.bias": (128,),
    "conv.4.weight": (128, 128, 3), "conv.4.bias": (128,),
    "head.0.weight": (128, 384), "head.0.bias": (128,),
    "head.2.weight": (128,), "head.2.bias": (128,),
    "head.3.weight": (9, 128), "head.3.bias": (9,),
}


class _FakeStudent(torch.nn.Module):
    """Stands in for the real model: exposes the verified state_dict."""
    def __init__(self):
        super().__init__()
        self._sd = {k: torch.zeros(s, dtype=torch.float64) for k, s in GT.items()}
    def state_dict(self, *a, **k):
        return self._sd


def test_contract_keys_match_guide_byte_for_byte():
    spec = StudentTCNSpec()
    assert set(spec.key_contract.keys()) == set(GT.keys())
    assert spec.npz_filename == "weights_tcn.npz"
    assert spec.name == "student_tcn"


def test_contract_input_dim_is_69():
    spec = StudentTCNSpec()
    assert spec.key_contract["channel_transform.0.weight"].shape == (32, 69)


def test_contract_latent_dim_is_9():
    spec = StudentTCNSpec()
    assert spec.key_contract["head.3.weight"].shape == (9, 128)


def test_contract_follows_the_teacher_obs_width():
    """The batch export passes the TEACHER's obs width here, so a student distilled
    against a different-width teacher is rejected instead of shipping mispaired."""
    spec = StudentTCNSpec(obs_dim=72)
    assert spec.key_contract["channel_transform.0.weight"].shape == (32, 72)
    assert spec.key_contract["head.3.weight"].shape == (9, 128)  # fixed dims unchanged


def test_map_is_identity_and_fp32():
    spec = StudentTCNSpec()
    mapped = spec.map_state_dict(_FakeStudent())
    assert set(mapped.keys()) == set(GT.keys())
    for k, shape in GT.items():
        assert mapped[k].shape == shape
        assert mapped[k].dtype == np.float32  # cast from float64
