import numpy as np
import torch
from constrained_albc.deploy.specs.teacher_actor import TeacherActorSpec

FULL_SD = {
    "log_std": (8,),
    "encoder.0.weight": (256, 27), "encoder.0.bias": (256,),
    "critic.0.weight": (512, 105), "critic.0.bias": (512,),
    "cost_critic.6.weight": (10, 128),
    "_encoder_output_norm.weight": (9,),
    "actor_obs_normalizer._mean": (1, 69),
    "actor_obs_normalizer._var": (1, 69),
    "actor_obs_normalizer._std": (1, 69),
    "actor_obs_normalizer.count": (),
    "actor.0.weight": (256, 78), "actor.0.bias": (256,),
    "actor.2.weight": (128, 256), "actor.2.bias": (128,),
    "actor.4.weight": (64, 128), "actor.4.bias": (64,),
    "actor.6.weight": (8, 64), "actor.6.bias": (8,),
}

CONTRACT_KEYS = {
    "normalizer._mean", "normalizer._std",
    "actor.0.weight", "actor.0.bias", "actor.2.weight", "actor.2.bias",
    "actor.4.weight", "actor.4.bias", "actor.6.weight", "actor.6.bias",
}


class _FakeTeacher(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self._sd = {k: torch.zeros(s, dtype=torch.float64) if s != ()
                    else torch.tensor(5, dtype=torch.int64) for k, s in FULL_SD.items()}
    def state_dict(self, *a, **k):
        return self._sd


def test_contract_keys_match_guide_section_b():
    spec = TeacherActorSpec()
    assert set(spec.key_contract.keys()) == CONTRACT_KEYS
    assert spec.npz_filename == "weights_teacher.npz"
    assert spec.name == "teacher_actor"


def test_actor_input_dim_is_78():
    spec = TeacherActorSpec()
    assert spec.key_contract["actor.0.weight"].shape == (256, 78)


def test_normalizer_shape_is_1x69():
    spec = TeacherActorSpec()
    assert spec.key_contract["normalizer._mean"].shape == (1, 69)
    assert spec.key_contract["normalizer._std"].shape == (1, 69)


def test_map_filters_and_renames():
    spec = TeacherActorSpec()
    mapped = spec.map_state_dict(_FakeTeacher())
    assert set(mapped.keys()) == CONTRACT_KEYS
    assert "actor_obs_normalizer._mean" not in mapped
    assert mapped["normalizer._mean"].shape == (1, 69)
    for v in mapped.values():
        assert v.dtype == np.float32
