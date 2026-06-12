"""Teacher actor export: model_state_dict -> weights_teacher.npz.

Verified 2026-06-11 from model_4999.pt: filter the 43-key ActorCriticEncoder
state_dict down to actor + normalizer, renaming the normalizer prefix. The runtime
needs only mean/std (not _var/count) and only the actor MLP (not encoder/critics)."""
from __future__ import annotations

import numpy as np
import torch.nn as nn

from constrained_albc.deploy.spec import ExportContractError, ExportSpec, ShapeSpec

_RENAME = {
    "actor_obs_normalizer._mean": "normalizer._mean",
    "actor_obs_normalizer._std": "normalizer._std",
    "actor.0.weight": "actor.0.weight",
    "actor.0.bias": "actor.0.bias",
    "actor.2.weight": "actor.2.weight",
    "actor.2.bias": "actor.2.bias",
    "actor.4.weight": "actor.4.weight",
    "actor.4.bias": "actor.4.bias",
    "actor.6.weight": "actor.6.weight",
    "actor.6.bias": "actor.6.bias",
}

_CONTRACT = {
    "normalizer._mean": ShapeSpec((1, 69)),
    "normalizer._std": ShapeSpec((1, 69)),
    "actor.0.weight": ShapeSpec((256, 78)),
    "actor.0.bias": ShapeSpec((256,)),
    "actor.2.weight": ShapeSpec((128, 256)),
    "actor.2.bias": ShapeSpec((128,)),
    "actor.4.weight": ShapeSpec((64, 128)),
    "actor.4.bias": ShapeSpec((64,)),
    "actor.6.weight": ShapeSpec((8, 64)),
    "actor.6.bias": ShapeSpec((8,)),
}


class TeacherActorSpec(ExportSpec):
    name = "teacher_actor"
    npz_filename = "weights_teacher.npz"
    key_contract = _CONTRACT

    def build_model(self, ckpt: dict, device) -> nn.Module:
        """Not used: the teacher is built by the engine (Task 5) from the checkpoint
        PATH, because FrozenTeacher self-loads. map_state_dict operates on that built
        model's full state_dict."""
        raise NotImplementedError(
            "teacher_actor.build_model is intentionally unused; the engine builds the "
            "teacher via FrozenTeacher from the checkpoint path (see deploy/engine.py)."
        )

    def map_state_dict(self, model: nn.Module) -> dict[str, np.ndarray]:
        sd = model.state_dict()
        out: dict[str, np.ndarray] = {}
        for src, dst in _RENAME.items():
            if src not in sd:
                raise ExportContractError(
                    f"teacher_actor: source key '{src}' absent in model_state_dict"
                )
            out[dst] = sd[src].detach().cpu().numpy().astype(np.float32)
        return out
