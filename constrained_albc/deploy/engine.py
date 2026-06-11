"""Export orchestration: build -> dump keys -> map -> save fp32 -> round-trip verify."""
from __future__ import annotations

import logging
import os

import numpy as np
import torch
import torch.nn as nn

from constrained_albc.deploy._isolation import _isolate_training_imports
from constrained_albc.deploy.spec import ExportSpec
from constrained_albc.deploy.verify import ContractReport, verify_npz

logger = logging.getLogger("deploy.export")

# Re-exported so the CLI / tests can trigger import isolation explicitly.
__all__ = [
    "export_from_state_dict",
    "build_student_model",
    "build_teacher_model",
    "_isolate_training_imports",
]


def export_from_state_dict(spec: ExportSpec, model: nn.Module, out_dir: str) -> ContractReport:
    """Map a built model's state_dict to the contract, save fp32 .npz, verify round-trip."""
    os.makedirs(out_dir, exist_ok=True)
    raw_keys = list(model.state_dict().keys())
    logger.info("[%s] raw state_dict keys (%d): %s", spec.name, len(raw_keys), raw_keys)

    mapped = spec.map_state_dict(model)
    path = os.path.join(out_dir, spec.npz_filename)
    np.savez(path, **mapped)
    logger.info("[%s] saved %d keys -> %s", spec.name, len(mapped), path)

    report = verify_npz(path, spec.key_contract)
    logger.info("[%s] contract verified OK", spec.name)
    return report


def build_student_model(spec: ExportSpec, ckpt_path: str, device) -> nn.Module:
    """Student: load the checkpoint dict and build via the spec.

    Isolates the heavy training imports first so this runs on an export host
    without the Isaac Sim runtime (the student build is sim-free)."""
    _isolate_training_imports()
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    return spec.build_model(ckpt, device)


def _infer_teacher_dims(sd: dict) -> dict:
    """Derive the teacher's architecture dims from the checkpoint itself.

    The dims differ per campaign (main full-DOF teacher = 87 obs / 24 priv;
    attitude-only teacher = 69 obs / 27 priv), so hardcoding StudentCfg defaults
    would mis-shape the model and fail to load. The checkpoint is the single
    source of truth -- read the dims straight from its tensor shapes."""
    policy_obs_dim = sd["actor_obs_normalizer._mean"].shape[1]   # (1, obs)
    latent_dim = sd["_encoder_output_norm.weight"].shape[0]      # (latent,)
    privileged_dim = sd["encoder.0.weight"].shape[1]             # (256, priv)
    num_actions = sd["actor.6.weight"].shape[0]                  # (actions, 64)
    return {
        "policy_obs_dim": policy_obs_dim,
        "latent_dim": latent_dim,
        "privileged_dim": privileged_dim,
        "num_actions": num_actions,
    }


def build_teacher_model(ckpt_path: str, device) -> nn.Module:
    """Teacher: build ActorCriticEncoder directly and load model_state_dict.

    Mirrors FrozenTeacher's construction (constrained_albc/envs/main/student/
    teacher.py) but bypasses FrozenTeacher so we don't import rsl_rl_ppo_cfg --
    that import drags in isaaclab_rl -> the sim stack -> pxr, absent on export
    hosts. The architecture dims (obs/latent/priv/action) AND the encoder-obs
    bounds are taken straight from the checkpoint tensors, so any teacher variant
    (main full-DOF or attitude-only) loads correctly and architecture drift can
    never produce a silently mis-shaped export. The encoder-obs bounds are
    register_buffers that load_state_dict overwrites, so their init values don't
    reach the export (TeacherActorSpec filters them out anyway) -- only their
    *dim* must match, which is why we size them from the checkpoint.

    The returned module's state_dict is the 43-key ActorCriticEncoder dict that
    TeacherActorSpec.map_state_dict filters + renames. Training code is imported
    (encoder), never modified."""
    _isolate_training_imports()
    from constrained_albc.envs.main.encoder import ActorCriticEncoder
    from tensordict import TensorDict

    dev = torch.device(device)
    ckpt = torch.load(ckpt_path, map_location=dev, weights_only=False)
    sd = ckpt["model_state_dict"]
    dims = _infer_teacher_dims(sd)

    # Encoder-obs bounds: take dim + values from the checkpoint buffers so the
    # registered buffer shape matches; load_state_dict then restores them exactly.
    enc_lower = sd["_enc_obs_lower"].detach().cpu().tolist()
    enc_upper = sd["_enc_obs_upper"].detach().cpu().tolist()

    dummy_obs = TensorDict(
        {
            "policy": torch.zeros(1, dims["policy_obs_dim"]),
            "privileged": torch.zeros(1, dims["privileged_dim"]),
        },
        batch_size=[1],
    )
    obs_groups = {"policy": ["policy", "privileged"], "critic": ["policy", "privileged"]}
    # Non-dim arguments mirror FrozenTeacher.__init__ (teacher.py) verbatim;
    # dims come from the checkpoint.
    policy = ActorCriticEncoder(
        obs=dummy_obs,
        obs_groups=obs_groups,
        num_actions=dims["num_actions"],
        policy_obs_dim=dims["policy_obs_dim"],
        privileged_dim=dims["privileged_dim"],
        encoder_hidden_dims=(256, 128, 64),
        encoder_latent_dim=dims["latent_dim"],
        encoder_activation="elu",
        encoder_obs_normalization=False,
        encoder_obs_lower=enc_lower,
        encoder_obs_upper=enc_upper,
        encoder_output_norm=True,
        actor_obs_normalization=True,
        critic_obs_normalization=False,
        actor_hidden_dims=(256, 128, 64),
        critic_hidden_dims=(512, 256, 128),
        activation="elu",
        init_noise_std=0.7,
        critic_uses_z=True,
        num_constraints=10,
        cost_critic_hidden_dims=(512, 256, 128),
    )
    policy.to(dev)

    # strict=True: every checkpoint key must map exactly. A real arch drift then
    # raises here loudly instead of silently exporting mis-shaped weights.
    result = nn.Module.load_state_dict(policy, sd, strict=True)
    logger.info(
        "teacher loaded from %s (iter=%s, obs=%d priv=%d latent=%d act=%d); missing=%d unexpected=%d",
        ckpt_path, ckpt.get("iter", "?"),
        dims["policy_obs_dim"], dims["privileged_dim"], dims["latent_dim"], dims["num_actions"],
        len(result.missing_keys), len(result.unexpected_keys),
    )
    policy.eval()
    return policy
