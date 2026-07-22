"""Golden vector generation: run the SAME built torch model that produced the
weights through a fixed-seed input, save intermediate + output tensors.

The golden is the torch ORACLE the numpy runtime (npforward.py) is checked against.
It MUST come from the same in-memory model instance the weights were dumped from
(callers pass that instance in), otherwise "this .npz is 1e-5 to this torch" does
not hold. See CONTAINER_DEPLOY_PACK.md section 3 for the key contract.

Contracts verified 2026-06-11 against student_999.pt / model_4999.pt:
- TCN  input_window (1, 9, 69), H=9 D=69 from cfg (tcn_history=9, policy_obs_dim=69).
  after_head is the LayerNorm-passed head output, BEFORE softsign; latent=softsign(after_head).
- teacher action is the RAW actor-MLP output (no clip; TeacherActor returns raw).
  Normalization is eps-free (obs - mean) / std -- export keeps _std as-is (min<0.01),
  npforward.normalize is eps-free, and the torch normalizer's eps is variance-only.
"""
from __future__ import annotations

import logging
import os

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger("deploy.export")

# Fixed seeds / scales -- MUST match Mac test_npforward.py so the goldens compare.
_TCN_SEED = 0
_TEACHER_SEED = 1
_INPUT_SCALE_TCN = 0.3
_INPUT_SCALE_OBS = 0.3
_INPUT_SCALE_LATENT = 0.3


def export_golden_tcn(model: nn.Module, out_dir: str,
                      *, history: int = 9, obs_dim: int | None = None) -> dict[str, np.ndarray]:
    """Run StudentEncoderTCN forward, capturing every intermediate the numpy
    engine reproduces. Layer path mirrors models.py:54-65 exactly.

    obs_dim defaults to the model's own input width -- it is campaign-dependent
    (69 attitude-only, 72 with use_bias_ema_obs), so a fixed default silently
    mis-shapes the probe input."""
    if obs_dim is None:
        obs_dim = model.channel_transform[0].weight.shape[1]
    os.makedirs(os.path.join(out_dir, "golden"), exist_ok=True)
    rng = np.random.RandomState(_TCN_SEED)
    win_np = (rng.randn(1, history, obs_dim) * _INPUT_SCALE_TCN).astype(np.float32)

    dev = next(model.parameters()).device
    win = torch.from_numpy(win_np).to(dev)

    # Reproduce the forward path stagewise (not via hooks) so each saved tensor is
    # an explicit, named contract point. Must match StudentEncoderTCN.forward.
    with torch.no_grad():
        b, h, d = win.shape
        after_ct = model.channel_transform(win.reshape(b * h, d)).reshape(b, h, -1)
        after_tr = after_ct.transpose(1, 2)
        after_conv = model.conv(after_tr)
        after_flat = after_conv.reshape(b, -1)
        after_head = model.head(after_flat)        # Linear+ELU+LayerNorm+Linear, pre-softsign
        latent = torch.nn.functional.softsign(after_head)
        forward_out = model(win)                    # full forward() == softsign(head(...))

    g = {
        "input_window": win_np,
        "after_channel_transform": after_ct.cpu().numpy().astype(np.float32),
        "after_transpose": after_tr.cpu().numpy().astype(np.float32),
        "after_conv": after_conv.cpu().numpy().astype(np.float32),
        "after_flatten": after_flat.cpu().numpy().astype(np.float32),
        "after_head": after_head.cpu().numpy().astype(np.float32),
        "latent": latent.cpu().numpy().astype(np.float32),
        "forward_out": forward_out.cpu().numpy().astype(np.float32),
    }
    # Internal sanity: forward() must equal the stagewise latent (same model, same input).
    if not np.allclose(g["latent"], g["forward_out"], atol=1e-6):
        raise RuntimeError(
            "golden_tcn: forward() output diverged from stagewise latent "
            f"(max|err|={np.max(np.abs(g['latent'] - g['forward_out'])):.3e}); "
            "the captured path does not match the model's own forward."
        )
    path = os.path.join(out_dir, "golden", "golden_tcn.npz")
    np.savez(path, **g)
    logger.info("[golden_tcn] saved %d keys -> %s (H=%d D=%d)", len(g), path, history, obs_dim)
    return g


def export_golden_teacher(model: nn.Module, out_dir: str,
                          *, obs_dim: int | None = None,
                          latent_dim: int | None = None) -> dict[str, np.ndarray]:
    """Run the teacher's normalizer + actor MLP on fixed-seed obs/latent, capturing
    the contract points. action is the RAW actor output (no clip).

    obs and latent are drawn from ONE RandomState(1) in order (obs first, latent
    next), matching Mac test_npforward.py / the doc contract. Both dims default to
    the model's own geometry (see export_golden_tcn)."""
    if obs_dim is None:
        obs_dim = model.actor_obs_normalizer._mean.shape[1]
    if latent_dim is None:
        latent_dim = model.actor[0].weight.shape[1] - obs_dim
    os.makedirs(os.path.join(out_dir, "golden"), exist_ok=True)
    rng = np.random.RandomState(_TEACHER_SEED)
    obs_np = (rng.randn(1, obs_dim) * _INPUT_SCALE_OBS).astype(np.float32)
    latent_np = (rng.randn(1, latent_dim) * _INPUT_SCALE_LATENT).astype(np.float32)

    dev = next(model.parameters()).device
    obs = torch.from_numpy(obs_np).to(dev)
    latent = torch.from_numpy(latent_np).to(dev)

    with torch.no_grad():
        obs_normed = model.actor_obs_normalizer(obs)          # eps-free (x-mean)/std in effect
        actor_input = torch.cat([obs_normed, latent], dim=-1)  # (1, obs+latent)
        action = model.actor(actor_input)                     # raw MLP output, no clip

    g = {
        "obs": obs_np,
        "obs_normalized": obs_normed.cpu().numpy().astype(np.float32),
        "latent": latent_np,
        "actor_input": actor_input.cpu().numpy().astype(np.float32),
        "action": action.cpu().numpy().astype(np.float32),
    }
    path = os.path.join(out_dir, "golden", "golden_teacher.npz")
    np.savez(path, **g)
    logger.info("[golden_teacher] saved %d keys -> %s (obs=%d latent=%d, action raw range [%.3f, %.3f])",
                len(g), path, obs_dim, latent_dim,
                float(g["action"].min()), float(g["action"].max()))
    return g
