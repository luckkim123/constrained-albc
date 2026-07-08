import numpy as np
import torch
from constrained_albc.deploy.engine import _infer_teacher_dims, export_from_state_dict
from constrained_albc.deploy.specs.student_tcn import StudentTCNSpec

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
    def __init__(self):
        super().__init__()
        self._sd = {k: torch.zeros(s, dtype=torch.float32) for k, s in GT.items()}
    def state_dict(self, *a, **k):
        return self._sd


def test_export_from_state_dict_saves_and_verifies(tmp_path):
    spec = StudentTCNSpec()
    report = export_from_state_dict(spec, _FakeStudent(), str(tmp_path))
    out = tmp_path / "weights_tcn.npz"
    assert out.exists()
    assert report.ok
    d = np.load(str(out))
    assert set(d.keys()) == set(GT.keys())
    assert d["channel_transform.0.weight"].dtype == np.float32


def _teacher_sd(obs, priv, latent, actions):
    """Minimal synthetic teacher state_dict carrying only the dim-defining keys."""
    return {
        "actor_obs_normalizer._mean": torch.zeros(1, obs),
        "_encoder_output_norm.weight": torch.zeros(latent),
        "encoder.0.weight": torch.zeros(256, priv),
        "actor.6.weight": torch.zeros(actions, 64),
    }


def test_infer_teacher_dims_attitude_only():
    """attitude-only teacher: 69 obs / 28 priv / 9 latent / 8 actions (verified).

    priv = 28 after the control-action delay tail (p_t[27]) was appended.
    """
    dims = _infer_teacher_dims(_teacher_sd(69, 28, 9, 8))
    assert dims == {
        "policy_obs_dim": 69, "privileged_dim": 28, "latent_dim": 9, "num_actions": 8,
        "num_constraints": 10,
    }


def test_infer_teacher_dims_main_fulldof():
    """main full-DOF teacher has different dims (87/24); inference adapts, so the
    same export path serves both without hardcoded config drift."""
    dims = _infer_teacher_dims(_teacher_sd(87, 24, 9, 8))
    assert dims["policy_obs_dim"] == 87
    assert dims["privileged_dim"] == 24
