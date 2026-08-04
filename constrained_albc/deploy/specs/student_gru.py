"""StudentGRU export: student_state_dict -> weights_gru.npz (identity map).

Verified 2026-07-30 against trpo_sdeint_a0g_gru_s30_260729_151017/student_999.pt
(the adopted A0g student): the 10 state_dict keys already match the keys
``npforward.StudentGRU`` loads, so map_state_dict is an identity rename + fp32 cast.

Two cfg geometries are NOT exportable and are rejected here rather than at the
board: the numpy runtime reads ``head.2``/``head.3`` (so it needs the DEEP head,
``gru_head_hidden > 0``) and only ``*_l0`` via a single-layer ``gru_cell`` (so it
needs ``gru_layers == 1``). A shallow-head checkpoint would otherwise fail with a
bare missing-key error far from the cause.
"""
from __future__ import annotations

import numpy as np
import torch.nn as nn

from constrained_albc.deploy.spec import ExportContractError, ExportSpec, ShapeSpec


def _contract(obs_dim: int, hidden: int, head_hidden: int, latent_dim: int) -> dict[str, ShapeSpec]:
    """Contract for one GRU geometry.

    Unlike the TCN's, every dim here is a live cfg knob (``gru_hidden``,
    ``gru_head_hidden``), so nothing is hardcoded: the caller reads them from the
    checkpoint's own cfg. ``obs_dim`` is the TEACHER's width (see
    student_tcn._contract) so a student distilled against a different-width
    teacher fails here instead of shipping a mispaired pack.
    """
    gates = 3 * hidden  # torch nn.GRU packs [r, z, n] on the row axis
    return {
        "gru.weight_ih_l0": ShapeSpec((gates, obs_dim)),
        "gru.weight_hh_l0": ShapeSpec((gates, hidden)),
        "gru.bias_ih_l0": ShapeSpec((gates,)),
        "gru.bias_hh_l0": ShapeSpec((gates,)),
        "head.0.weight": ShapeSpec((head_hidden, hidden)),
        "head.0.bias": ShapeSpec((head_hidden,)),
        "head.2.weight": ShapeSpec((head_hidden,)),  # LayerNorm gamma
        "head.2.bias": ShapeSpec((head_hidden,)),    # LayerNorm beta
        "head.3.weight": ShapeSpec((latent_dim, head_hidden)),
        "head.3.bias": ShapeSpec((latent_dim,)),
    }


class StudentGRUSpec(ExportSpec):
    name = "student_gru"
    npz_filename = "weights_gru.npz"
    key_contract = _contract(72, 128, 64, 9)

    def __init__(self, obs_dim: int = 72, hidden: int = 128,
                 head_hidden: int = 64, latent_dim: int = 9) -> None:
        self.key_contract = _contract(obs_dim, hidden, head_hidden, latent_dim)

    def build_model(self, ckpt: dict, device) -> nn.Module:
        """Build StudentEncoderGRU and load student_state_dict.

        cfg is stored in the checkpoint as a dict; rebuild StudentCfg from it so the
        architecture matches exactly. Training code is imported, never modified."""
        from constrained_albc.envs.main.student.config import StudentCfg
        from constrained_albc.envs.main.student.models import StudentEncoderGRU

        cfg_dict = ckpt.get("cfg", {})
        cfg = StudentCfg(**{k: v for k, v in cfg_dict.items()
                            if k in StudentCfg.__dataclass_fields__}) if cfg_dict else StudentCfg()
        self._assert_board_runnable(cfg)
        model = StudentEncoderGRU(cfg).to(device)
        model.load_state_dict(ckpt["student_state_dict"])
        model.eval()
        return model

    @staticmethod
    def _assert_board_runnable(cfg) -> None:
        """Reject the two cfg geometries npforward.StudentGRU cannot run."""
        if getattr(cfg, "gru_layers", 1) != 1:
            raise ExportContractError(
                f"student_gru: gru_layers={cfg.gru_layers}, but the board runtime's "
                "gru_cell implements a SINGLE layer and npforward.StudentGRU reads only "
                "the *_l0 weights. A multi-layer student cannot be deployed as-is."
            )
        if not getattr(cfg, "gru_head_hidden", 0) > 0:
            raise ExportContractError(
                f"student_gru: gru_head_hidden={getattr(cfg, 'gru_head_hidden', 0)} "
                "(shallow head = Linear only), but npforward.StudentGRU reads head.2 "
                "(LayerNorm) and head.3 (second Linear). Only the deep-head variant is "
                "exportable to the board runtime."
            )
        if getattr(cfg, "extra_obs_dim", 0) > 0:
            raise ExportContractError(
                "student_gru: extra_obs_dim > 0 (E1/B2 gen-1 side-channel student). "
                "npforward has no extra-channel input or scaling contract; deploy support "
                "arrives with gen-2 (teacher obs76), where policy_obs itself is 76D."
            )
        if getattr(cfg, "extra_obs_from_policy_tail", False):
            raise ExportContractError(
                "student_gru: extra_obs_from_policy_tail=True (X1 tail-split student). "
                "npforward has no split+static-scale contract, so an exported pack would "
                "silently z-score the tail channels the student expects raw. Extend the "
                "deploy spec first if this recipe is adopted."
            )

    def map_state_dict(self, model: nn.Module) -> dict[str, np.ndarray]:
        sd = model.state_dict()
        out: dict[str, np.ndarray] = {}
        for key in self.key_contract:
            if key not in sd:
                raise ExportContractError(f"student_gru: source key '{key}' absent in state_dict")
            out[key] = sd[key].detach().cpu().numpy().astype(np.float32)
        return out
