"""Export orchestration: build -> dump keys -> map -> save fp32 -> round-trip verify."""
from __future__ import annotations

import logging
import os

import numpy as np
import torch
import torch.nn as nn

from constrained_albc.deploy.spec import ExportSpec
from constrained_albc.deploy.verify import ContractReport, verify_npz

logger = logging.getLogger("deploy.export")


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
    """Student: load the checkpoint dict and build via the spec."""
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    return spec.build_model(ckpt, device)


def build_teacher_model(ckpt_path: str, device) -> nn.Module:
    """Teacher: FrozenTeacher self-loads from a run dir + checkpoint filename.

    Returns the underlying ActorCriticEncoder (FrozenTeacher.policy) whose state_dict
    is the 43-key dict TeacherActorSpec.map_state_dict expects. Imports training code,
    never modifies it."""
    from constrained_albc.envs.main.student.config import StudentCfg
    from constrained_albc.envs.main.student.teacher import FrozenTeacher

    run_dir = os.path.dirname(ckpt_path)
    ckpt_name = os.path.basename(ckpt_path)
    cfg = StudentCfg()
    cfg.teacher_run_dir = run_dir
    cfg.teacher_checkpoint = ckpt_name
    frozen = FrozenTeacher(cfg, torch.device(device))
    return frozen.policy
