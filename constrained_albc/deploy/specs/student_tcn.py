"""StudentTCN export: student_state_dict -> weights_tcn.npz (identity map).

Verified 2026-06-11: the 14 student_state_dict keys already match the guide
section-A contract exactly, so map_state_dict is an identity rename + fp32 cast."""
from __future__ import annotations

import numpy as np
import torch.nn as nn

from constrained_albc.deploy.spec import ExportContractError, ExportSpec, ShapeSpec

_CONTRACT = {
    "channel_transform.0.weight": ShapeSpec((32, 69)),
    "channel_transform.0.bias": ShapeSpec((32,)),
    "conv.0.weight": ShapeSpec((64, 32, 3)),
    "conv.0.bias": ShapeSpec((64,)),
    "conv.2.weight": ShapeSpec((128, 64, 3)),
    "conv.2.bias": ShapeSpec((128,)),
    "conv.4.weight": ShapeSpec((128, 128, 3)),
    "conv.4.bias": ShapeSpec((128,)),
    "head.0.weight": ShapeSpec((128, 384)),
    "head.0.bias": ShapeSpec((128,)),
    "head.2.weight": ShapeSpec((128,)),  # LayerNorm gamma
    "head.2.bias": ShapeSpec((128,)),    # LayerNorm beta
    "head.3.weight": ShapeSpec((9, 128)),
    "head.3.bias": ShapeSpec((9,)),
}


class StudentTCNSpec(ExportSpec):
    name = "student_tcn"
    npz_filename = "weights_tcn.npz"
    key_contract = _CONTRACT

    def build_model(self, ckpt: dict, device) -> nn.Module:
        """Build StudentEncoderTCN and load student_state_dict.

        cfg is stored in the checkpoint as a dict; rebuild StudentCfg from it so the
        architecture matches exactly. Training code is imported, never modified."""
        from constrained_albc.envs.attitude_only.student.config import StudentCfg
        from constrained_albc.envs.attitude_only.student.models import StudentEncoderTCN

        cfg_dict = ckpt.get("cfg", {})
        cfg = StudentCfg(**{k: v for k, v in cfg_dict.items()
                            if k in StudentCfg.__dataclass_fields__}) if cfg_dict else StudentCfg()
        model = StudentEncoderTCN(cfg).to(device)
        model.load_state_dict(ckpt["student_state_dict"])
        model.eval()
        return model

    def map_state_dict(self, model: nn.Module) -> dict[str, np.ndarray]:
        sd = model.state_dict()
        out: dict[str, np.ndarray] = {}
        for key in self.key_contract:
            if key not in sd:
                raise ExportContractError(f"student_tcn: source key '{key}' absent in state_dict")
            out[key] = sd[key].detach().cpu().numpy().astype(np.float32)
        return out
