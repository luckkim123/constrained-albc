"""Pure torch frame transforms for optional evaluation moment recording."""

from __future__ import annotations

import torch


def quat_rotate(q_wxyz: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Rotate batched vectors by quaternions in IsaacLab ``(w, x, y, z)`` order."""
    q_vec = q_wxyz[..., 1:]
    uv = torch.cross(q_vec, v, dim=-1)
    return v + 2.0 * (q_wxyz[..., :1] * uv + torch.cross(q_vec, uv, dim=-1))


def quat_rotate_inverse(q_wxyz: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Apply the inverse of batched unit quaternions to batched vectors."""
    q_inverse = torch.cat((q_wxyz[..., :1], -q_wxyz[..., 1:]), dim=-1)
    return quat_rotate(q_inverse, v)


def moment_about(
    p_ref_w: torch.Tensor,
    q_ref_wxyz: torch.Tensor,
    p_app_w: torch.Tensor,
    q_app_wxyz: torch.Tensor,
    force_local: torch.Tensor,
    torque_local: torch.Tensor,
) -> torch.Tensor:
    """Return a link-local wrench's moment about a reference link origin, in its frame."""
    force_w = quat_rotate(q_app_wxyz, force_local)
    torque_w = quat_rotate(q_app_wxyz, torque_local)
    moment_w = torch.cross(p_app_w - p_ref_w, force_w, dim=-1) + torque_w
    return quat_rotate_inverse(q_ref_wxyz, moment_w)


def gravity_moment_about(
    p_ref_w: torch.Tensor,
    q_ref_wxyz: torch.Tensor,
    p_com_w: torch.Tensor,
    mass: torch.Tensor,
    g_w: torch.Tensor,
) -> torch.Tensor:
    """Return a body's gravity moment about a reference link origin, in its frame."""
    gravity_force_w = mass.unsqueeze(-1) * g_w
    moment_w = torch.cross(p_com_w - p_ref_w, gravity_force_w, dim=-1)
    return quat_rotate_inverse(q_ref_wxyz, moment_w)
