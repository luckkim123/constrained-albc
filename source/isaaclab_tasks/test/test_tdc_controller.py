# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for TDC controller (standalone, no Isaac Sim required).

Tests verify:
    1. Lambda matrix structure (anti-diagonal)
    2. Lambda inverse with DLS regularization
    3. Restoring torque T_b computation
    4. First-step pure PD fallback (no TDE)
    5. Full TDC control loop over multiple steps
    6. Reset behavior
    7. Singularity handling (near-vertical pose)
"""

import importlib.util
import math
import sys
from pathlib import Path

import pytest
import torch

# Direct module loading to avoid isaaclab_tasks.__init__ importing Isaac Sim
_controllers_dir = (
    Path(__file__).resolve().parent.parent
    / "isaaclab_tasks"
    / "direct"
    / "hero_agent"
    / "controllers"
)


def _load_module(name: str, filepath: Path):
    """Load a Python module directly from file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_kin_mod = _load_module("_kinematics", _controllers_dir / "kinematics.py")
_tdc_mod = _load_module("_tdc", _controllers_dir / "tdc.py")
ALBCKinematics = _kin_mod.ALBCKinematics
TDCController = _tdc_mod.TDCController


DEVICE = "cpu"
NUM_ENVS = 4
F_BU = 26.24
H = 0.230


@pytest.fixture
def controller():
    """Create a TDCController with default parameters."""
    return TDCController(
        num_envs=NUM_ENVS,
        device=DEVICE,
        m_hat=(0.15, 0.15),
        kp=4.0,
        kd=3.0,
        F_bu=F_BU,
        h=H,
        dls_damping=0.01,
        dt=0.01,
        workspace_radius=0.45,
        nu_dot_ema_alpha=0.3,
    )


@pytest.fixture
def kinematics():
    """Create ALBCKinematics for FK/IK."""
    return ALBCKinematics(num_envs=NUM_ENVS, device=DEVICE)


class TestLambdaMatrix:
    """Test Lambda matrix computation."""

    def test_lambda_structure_zero_angles(self, controller):
        """Lambda at zero roll/pitch should be anti-diagonal with lf = F_bu."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        Lambda = controller._compute_lambda(roll, pitch)

        # lf = cos(0)*cos(0)*F_bu = F_bu
        assert Lambda.shape == (NUM_ENVS, 2, 2)
        torch.testing.assert_close(Lambda[:, 0, 0], torch.zeros(NUM_ENVS))
        torch.testing.assert_close(Lambda[:, 1, 1], torch.zeros(NUM_ENVS))
        torch.testing.assert_close(Lambda[:, 0, 1], torch.full((NUM_ENVS,), -F_BU))
        torch.testing.assert_close(Lambda[:, 1, 0], torch.full((NUM_ENVS,), F_BU))

    def test_lambda_with_tilt(self, controller):
        """Lambda should scale by cos(theta)*cos(phi)."""
        roll = torch.full((NUM_ENVS,), math.pi / 6)  # 30 deg
        pitch = torch.zeros(NUM_ENVS)

        Lambda = controller._compute_lambda(roll, pitch)

        expected_lf = math.cos(math.pi / 6) * F_BU
        torch.testing.assert_close(Lambda[0, 1, 0], torch.tensor(expected_lf), atol=1e-5, rtol=1e-5)


class TestLambdaInverse:
    """Test DLS-regularized Lambda inverse."""

    def test_lambda_inv_structure(self, controller):
        """Lambda_inv should be anti-diagonal with opposite sign pattern."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        Lambda_inv = controller._compute_lambda_inv(roll, pitch)

        assert Lambda_inv.shape == (NUM_ENVS, 2, 2)
        # Diagonal should be zero
        torch.testing.assert_close(Lambda_inv[:, 0, 0], torch.zeros(NUM_ENVS))
        torch.testing.assert_close(Lambda_inv[:, 1, 1], torch.zeros(NUM_ENVS))
        # Off-diagonal: [[0, lf_inv], [-lf_inv, 0]]
        lf = F_BU
        lf_inv = lf / (lf**2 + 0.01**2)
        torch.testing.assert_close(Lambda_inv[0, 0, 1], torch.tensor(lf_inv), atol=1e-5, rtol=1e-5)
        torch.testing.assert_close(Lambda_inv[0, 1, 0], torch.tensor(-lf_inv), atol=1e-5, rtol=1e-5)

    def test_lambda_times_inv_approx_identity(self, controller):
        """Lambda @ Lambda_inv should approximate identity (within DLS error)."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        Lambda = controller._compute_lambda(roll, pitch)
        Lambda_inv = controller._compute_lambda_inv(roll, pitch)

        product = torch.bmm(Lambda, Lambda_inv)
        identity = torch.eye(2).unsqueeze(0).expand(NUM_ENVS, -1, -1)

        # DLS introduces small error, but with large F_bu it should be tiny
        torch.testing.assert_close(product, identity, atol=1e-4, rtol=1e-4)

    def test_singularity_handling(self, controller):
        """Lambda_inv should remain bounded near singularity (90 deg pitch)."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.full((NUM_ENVS,), math.pi / 2 - 0.01)  # Near 90 deg

        Lambda_inv = controller._compute_lambda_inv(roll, pitch)

        # Should not contain NaN or Inf
        assert torch.isfinite(Lambda_inv).all()
        # Values should be bounded
        assert Lambda_inv.abs().max() < 200.0  # Reasonable upper bound


class TestRestoringTorque:
    """Test passive restoring torque T_b."""

    def test_zero_at_zero_angles(self, controller):
        """T_b should be zero when roll=pitch=0 (upright)."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        T_b = controller._compute_restoring_torque(roll, pitch)

        torch.testing.assert_close(T_b, torch.zeros(NUM_ENVS, 2), atol=1e-6, rtol=1e-6)

    def test_nonzero_with_tilt(self, controller):
        """T_b should be nonzero with tilted orientation."""
        roll = torch.full((NUM_ENVS,), 0.2618)  # 15 deg
        pitch = torch.full((NUM_ENVS,), 0.2618)

        T_b = controller._compute_restoring_torque(roll, pitch)

        # T_b_roll = cos(theta)*sin(phi)*F_bu*h
        expected_roll = math.cos(0.2618) * math.sin(0.2618) * F_BU * H
        # T_b_pitch = sin(theta)*F_bu*h
        expected_pitch = math.sin(0.2618) * F_BU * H

        torch.testing.assert_close(T_b[0, 0], torch.tensor(expected_roll), atol=1e-4, rtol=1e-4)
        torch.testing.assert_close(T_b[0, 1], torch.tensor(expected_pitch), atol=1e-4, rtol=1e-4)


class TestControlLoop:
    """Test full TDC control loop."""

    def test_first_step_pure_pd(self, controller, kinematics):
        """First step should use pure PD (no TDE)."""
        roll = torch.full((NUM_ENVS,), 0.2618)
        pitch = torch.full((NUM_ENVS,), 0.2618)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        target = torch.zeros(NUM_ENVS, 3)
        joint_pos = torch.zeros(NUM_ENVS, 2)

        p_EE = controller.compute(roll, pitch, ang_vel, target, joint_pos, kinematics)

        # Should produce valid output (no NaN/Inf)
        assert torch.isfinite(p_EE).all()
        assert p_EE.shape == (NUM_ENVS, 2)
        # Should be nonzero (PD drives toward zero attitude error)
        assert p_EE.abs().sum() > 0

    def test_second_step_uses_tde(self, controller, kinematics):
        """Second step should use full TDC with TDE."""
        roll = torch.full((NUM_ENVS,), 0.2618)
        pitch = torch.full((NUM_ENVS,), 0.2618)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        target = torch.zeros(NUM_ENVS, 3)
        joint_pos = torch.zeros(NUM_ENVS, 2)

        # First step (initializes history)
        controller.compute(roll, pitch, ang_vel, target, joint_pos, kinematics)
        assert controller._is_initialized.all()

        # Second step (uses TDE)
        p_EE = controller.compute(roll, pitch, ang_vel, target, joint_pos, kinematics)
        assert torch.isfinite(p_EE).all()

    def test_multi_step_no_nan(self, controller, kinematics):
        """Run multiple steps and verify no NaN/Inf appears."""
        target = torch.zeros(NUM_ENVS, 3)

        roll = torch.full((NUM_ENVS,), 0.2618)
        pitch = torch.full((NUM_ENVS,), 0.2618)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        joint_pos = torch.zeros(NUM_ENVS, 2)

        for _ in range(100):
            p_EE = controller.compute(roll, pitch, ang_vel, target, joint_pos, kinematics)
            assert torch.isfinite(p_EE).all(), f"NaN/Inf in p_EE: {p_EE}"

            # Update joint_pos via IK for next step
            joint_pos = kinematics.inverse(p_EE)
            assert torch.isfinite(joint_pos).all(), f"NaN/Inf in joint_pos: {joint_pos}"

    def test_output_within_workspace(self, controller, kinematics):
        """Controller output should always be within workspace radius."""
        target = torch.zeros(NUM_ENVS, 3)
        roll = torch.full((NUM_ENVS,), 0.5)  # Large tilt to stress-test
        pitch = torch.full((NUM_ENVS,), 0.5)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        ang_vel[:, 0] = 3.0  # Large angular velocity
        ang_vel[:, 1] = -2.0
        joint_pos = torch.zeros(NUM_ENVS, 2)

        for _ in range(50):
            p_EE = controller.compute(roll, pitch, ang_vel, target, joint_pos, kinematics)
            r = torch.norm(p_EE, dim=-1)
            assert (r <= controller.workspace_radius + 1e-6).all(), (
                f"p_EE outside workspace: r={r.max().item():.4f} > {controller.workspace_radius}"
            )
            joint_pos = kinematics.inverse(p_EE)

    def test_ik_round_trip(self, kinematics):
        """Verify FK(IK(p_EE)) approximately recovers p_EE."""
        # Target in workspace
        p_EE = torch.tensor([[0.3, 0.0], [0.0, 0.3], [-0.2, 0.1], [0.1, -0.2]])
        joint_angles = kinematics.inverse(p_EE)
        p_EE_recovered = kinematics.forward(joint_angles)

        torch.testing.assert_close(p_EE, p_EE_recovered, atol=1e-4, rtol=1e-4)


class TestReset:
    """Test controller reset behavior."""

    def test_reset_clears_initialization(self, controller, kinematics):
        """Reset should clear is_initialized flag."""
        roll = torch.full((NUM_ENVS,), 0.1)
        pitch = torch.zeros(NUM_ENVS)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        target = torch.zeros(NUM_ENVS, 3)
        joint_pos = torch.zeros(NUM_ENVS, 2)

        # Initialize
        controller.compute(roll, pitch, ang_vel, target, joint_pos, kinematics)
        assert controller._is_initialized.all()

        # Reset env 0 and 2
        reset_ids = torch.tensor([0, 2])
        controller.reset(reset_ids)

        assert not controller._is_initialized[0]
        assert controller._is_initialized[1]
        assert not controller._is_initialized[2]
        assert controller._is_initialized[3]

    def test_reset_zeroes_buffers(self, controller):
        """Reset should zero out history buffers for specified envs."""
        # Manually set some non-zero values
        controller._nu_prev[:] = 1.0
        controller._p_EE_prev[:] = 0.5

        reset_ids = torch.tensor([1, 3])
        controller.reset(reset_ids)

        # Reset envs should be zero
        torch.testing.assert_close(controller._nu_prev[1], torch.zeros(2))
        torch.testing.assert_close(controller._nu_prev[3], torch.zeros(2))
        # Non-reset envs should be unchanged
        torch.testing.assert_close(controller._nu_prev[0], torch.ones(2))
        torch.testing.assert_close(controller._nu_prev[2], torch.ones(2))
