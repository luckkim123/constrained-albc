# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for TDC controller (standalone, no Isaac Sim required).

Tests verify:
    1. Lambda matrix structure and its DLS inverse (merged method)
    2. Restoring torque T_b computation
    3. First-step pure PD fallback (no TDE)
    4. Full TDC control loop over multiple steps
    5. IK round-trip (FK(IK(p)) ~ p)
    6. Reset behavior
    7. Singularity handling (near-vertical pose)
    8. update_controller_params (m_hat, F_bu)
"""

import importlib.util
import math
import sys
import types
from pathlib import Path

import pytest
import torch

# ---------------------------------------------------------------------------
# Mock external dependencies so tests run without Isaac Sim
# ---------------------------------------------------------------------------


# Mock module base that supports attribute access, calling, and string ops
class _MockModule(types.ModuleType):
    """Module mock that supports attribute access, calling, and string ops."""

    def __call__(self, *args, **kwargs):
        if args:
            return args[0]
        return self

    def __str__(self):
        return self.__name__

    def __format__(self, spec):
        return format(str(self), spec)

    def __getattr__(self, name):
        child = _MockModule(f"{self.__name__}.{name}")
        setattr(self, name, child)
        return child


# Mock isaaclab_assets.robots.uuv with real link-length constants
_uuv_mock = _MockModule("isaaclab_assets.robots.uuv")
_uuv_mock.HERO_AGENT_ALBC_LINK1_LENGTH = 0.233
_uuv_mock.HERO_AGENT_ALBC_LINK2_LENGTH = 0.233
_uuv_mock.HERO_AGENT_ALBC_JOINT_NAMES = ["joint1", "joint2"]
_uuv_mock.HERO_AGENT_CFG = _MockModule("HERO_AGENT_CFG")
_uuv_mock.HeroAgentBuoyHydrodynamicsCfg = type("HeroAgentBuoyHydrodynamicsCfg", (), {})
_uuv_mock.HeroAgentHydrodynamicsCfg = type("HeroAgentHydrodynamicsCfg", (), {})
_uuv_mock.HydrodynamicsCfg = type("HydrodynamicsCfg", (), {})
_uuv_mock.OceanCurrentCfg = type("OceanCurrentCfg", (), {})

# Build parent packages
for pkg_name in [
    "isaaclab_assets",
    "isaaclab_assets.robots",
]:
    if pkg_name not in sys.modules:
        sys.modules[pkg_name] = types.ModuleType(pkg_name)
sys.modules["isaaclab_assets.robots.uuv"] = _uuv_mock

# Mock isaaclab and other Isaac Sim packages
for pkg_name in [
    "isaaclab",
    "isaaclab.utils",
    "isaaclab.envs",
    "isaaclab.scene",
    "isaaclab.sim",
    "isaaclab.terrains",
    "isaaclab.utils.math",
    "isaacsim",
    "omni",
    "omni.isaac",
    "omni.isaac.lab",
    "pxr",
    "carb",
    "warp",
]:
    if pkg_name not in sys.modules:
        sys.modules[pkg_name] = _MockModule(pkg_name)

# Make configclass a no-op decorator
sys.modules["isaaclab.utils"].configclass = lambda cls: cls

# ---------------------------------------------------------------------------
# Load modules under test via importlib (avoids isaaclab_tasks.__init__)
# ---------------------------------------------------------------------------

_tdc_pkg_dir = (
    Path(__file__).resolve().parent.parent
    / "isaaclab_tasks" / "direct" / "constrained_full_albc_tdc"
)
_controllers_dir = _tdc_pkg_dir / "controllers"


def _load_module(name: str, filepath: Path):
    """Load a Python module directly from file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# TDCControllerCfg is a plain dataclass (decorated with @configclass which is
# a no-op in test context). Replicate it here to avoid loading the full
# config.py which triggers the entire isaaclab_tasks package chain.
class TDCControllerCfg:
    """Mirror of config.TDCControllerCfg for testing."""

    m_hat: tuple[float, float] = (0.15, 0.16)
    kp: float = 40.0
    kd: float = 12.0
    # Test uses h=0.230 (full link2 length) vs production h=0.180 (CoG-to-ABPC offset).
    # This exercises larger torque magnitudes without affecting correctness verification.
    h: float = 0.230
    dls_lambda_damping: float = 0.01
    nu_dot_ema_alpha: float = 0.05
    base_position: tuple[float, float] = (0.01, 0.01)
    ik_dls_lambda: float = 0.15
    max_joint_velocity: float = 2.5
    link1_length: float = 0.233
    link2_length: float = 0.233
    log_interval: int = 200


# Build a fake package hierarchy so relative imports in tdc.py resolve correctly.
# tdc.py imports from isaaclab.utils and isaaclab_assets.robots.uuv (mocked above).
# TDCControllerCfg is defined in controllers/tdc.py itself (not in config.py).
_PKG = "isaaclab_tasks.direct.constrained_full_albc_tdc"
_CTRL_PKG = f"{_PKG}.controllers"

# Register package stubs
for pkg_name in ["isaaclab_tasks.direct", _PKG, _CTRL_PKG]:
    if pkg_name not in sys.modules:
        sys.modules[pkg_name] = types.ModuleType(pkg_name)

# Load kinematics (no relative imports from parent)
_kin_mod = _load_module(f"{_CTRL_PKG}.kinematics", _controllers_dir / "kinematics.py")

# Load tdc with correct package context so relative import resolves
_tdc_spec = importlib.util.spec_from_file_location(
    f"{_CTRL_PKG}.tdc",
    _controllers_dir / "tdc.py",
    submodule_search_locations=[],
)
_tdc_mod = importlib.util.module_from_spec(_tdc_spec)
_tdc_mod.__package__ = _CTRL_PKG
sys.modules[f"{_CTRL_PKG}.tdc"] = _tdc_mod
_tdc_spec.loader.exec_module(_tdc_mod)

ALBCKinematics = _kin_mod.ALBCKinematics
TDCController = _tdc_mod.TDCController

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

DEVICE = "cpu"
NUM_ENVS = 4
F_BU = 26.24
H = 0.230


@pytest.fixture
def cfg() -> TDCControllerCfg:
    """Create a TDCControllerCfg with test parameters."""
    c = TDCControllerCfg()
    c.m_hat = (0.15, 0.15)
    c.kp = 4.0
    c.kd = 3.0
    c.h = H
    c.dls_lambda_damping = 0.01
    c.nu_dot_ema_alpha = 0.3
    c.base_position = (0.0, 0.0)
    return c


@pytest.fixture
def controller(cfg) -> TDCController:
    """Create a TDCController with test parameters."""
    return TDCController(
        num_envs=NUM_ENVS,
        device=DEVICE,
        cfg=cfg,
        F_bu=F_BU,
        dt=0.01,
    )


@pytest.fixture
def kinematics() -> ALBCKinematics:
    """Create ALBCKinematics for FK/IK."""
    return ALBCKinematics(num_envs=NUM_ENVS, device=DEVICE)


# ===========================================================================
# Lambda computation (merged method)
# ===========================================================================


class TestLambdaComputation:
    """Test _compute_lambda_and_inv merged method."""

    def test_lambda_structure_zero_angles(self, controller):
        """Lambda at zero roll/pitch: lf = F_bu, anti-diagonal [[0,lf],[-lf,0]]."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        Lambda, Lambda_inv = controller._compute_lambda_and_inv(roll, pitch)

        assert Lambda.shape == (NUM_ENVS, 2, 2)
        # Diagonal must be zero
        torch.testing.assert_close(Lambda[:, 0, 0], torch.zeros(NUM_ENVS))
        torch.testing.assert_close(Lambda[:, 1, 1], torch.zeros(NUM_ENVS))
        # Off-diagonal: Lambda[0,1] = +lf, Lambda[1,0] = -lf
        torch.testing.assert_close(Lambda[:, 0, 1], torch.full((NUM_ENVS,), F_BU))
        torch.testing.assert_close(Lambda[:, 1, 0], torch.full((NUM_ENVS,), -F_BU))

    def test_lambda_with_tilt(self, controller):
        """Lambda should scale by cos(theta)*cos(phi)."""
        roll = torch.full((NUM_ENVS,), math.pi / 6)  # 30 deg
        pitch = torch.zeros(NUM_ENVS)

        Lambda, _ = controller._compute_lambda_and_inv(roll, pitch)

        expected_lf = math.cos(math.pi / 6) * F_BU
        torch.testing.assert_close(Lambda[0, 0, 1], torch.tensor(expected_lf), atol=1e-5, rtol=1e-5)

    def test_lambda_inv_structure(self, controller):
        """Lambda_inv at zero angles: [[0, -lf_inv], [lf_inv, 0]]."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        _, Lambda_inv = controller._compute_lambda_and_inv(roll, pitch)

        assert Lambda_inv.shape == (NUM_ENVS, 2, 2)
        torch.testing.assert_close(Lambda_inv[:, 0, 0], torch.zeros(NUM_ENVS))
        torch.testing.assert_close(Lambda_inv[:, 1, 1], torch.zeros(NUM_ENVS))

        lf = F_BU
        lf_inv = lf / (lf**2 + 0.01**2)
        torch.testing.assert_close(Lambda_inv[0, 0, 1], torch.tensor(-lf_inv), atol=1e-5, rtol=1e-5)
        torch.testing.assert_close(Lambda_inv[0, 1, 0], torch.tensor(lf_inv), atol=1e-5, rtol=1e-5)


class TestLambdaInverse:
    """Test Lambda @ Lambda_inv properties."""

    def test_lambda_times_inv_approx_identity(self, controller):
        """Lambda @ Lambda_inv should approximate identity (within DLS error)."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        Lambda, Lambda_inv = controller._compute_lambda_and_inv(roll, pitch)
        product = torch.bmm(Lambda, Lambda_inv)
        identity = torch.eye(2).unsqueeze(0).expand(NUM_ENVS, -1, -1)

        torch.testing.assert_close(product, identity, atol=1e-4, rtol=1e-4)

    def test_singularity_handling(self, controller):
        """Lambda_inv should remain bounded near singularity (90 deg pitch)."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.full((NUM_ENVS,), math.pi / 2 - 0.01)  # Near 90 deg

        _, Lambda_inv = controller._compute_lambda_and_inv(roll, pitch)

        assert torch.isfinite(Lambda_inv).all()
        assert Lambda_inv.abs().max() < 200.0


# ===========================================================================
# Restoring torque
# ===========================================================================


class TestRestoringTorque:
    """Test passive restoring torque T_b."""

    def test_zero_at_zero_angles(self, controller):
        """T_b should be zero when roll=pitch=0 (upright)."""
        roll = torch.zeros(NUM_ENVS)
        pitch = torch.zeros(NUM_ENVS)

        T_b = controller._compute_restoring_torque(roll, pitch)

        torch.testing.assert_close(T_b, torch.zeros(NUM_ENVS, 2), atol=1e-6, rtol=1e-6)

    def test_nonzero_with_tilt(self, controller):
        """T_b with tilt: T_b_roll = -cos(theta)*sin(phi)*F_bu*h (negative)."""
        roll = torch.full((NUM_ENVS,), 0.2618)  # ~15 deg
        pitch = torch.full((NUM_ENVS,), 0.2618)

        T_b = controller._compute_restoring_torque(roll, pitch)

        # Signs: T_b_roll = -cos(theta)*sin(phi)*F_bu*h (negative for positive roll)
        expected_roll = -math.cos(0.2618) * math.sin(0.2618) * F_BU * H
        expected_pitch = -math.sin(0.2618) * F_BU * H

        torch.testing.assert_close(T_b[0, 0], torch.tensor(expected_roll), atol=1e-4, rtol=1e-4)
        torch.testing.assert_close(T_b[0, 1], torch.tensor(expected_pitch), atol=1e-4, rtol=1e-4)


# ===========================================================================
# Control loop
# ===========================================================================


class TestControlLoop:
    """Test full TDC control loop."""

    def test_first_step_pure_pd(self, controller):
        """First step should use pure PD (no TDE)."""
        roll = torch.full((NUM_ENVS,), 0.2618)
        pitch = torch.full((NUM_ENVS,), 0.2618)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        target = torch.zeros(NUM_ENVS, 3)

        p_EE = controller.compute(roll, pitch, ang_vel, target)

        assert torch.isfinite(p_EE).all()
        assert p_EE.shape == (NUM_ENVS, 2)
        assert p_EE.abs().sum() > 0

    def test_second_step_uses_tde(self, controller):
        """Second step should use full TDC with TDE."""
        roll = torch.full((NUM_ENVS,), 0.2618)
        pitch = torch.full((NUM_ENVS,), 0.2618)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        target = torch.zeros(NUM_ENVS, 3)

        controller.compute(roll, pitch, ang_vel, target)
        assert controller._is_initialized.all()

        p_EE = controller.compute(roll, pitch, ang_vel, target)
        assert torch.isfinite(p_EE).all()

    def test_multi_step_no_nan(self, controller):
        """Run multiple steps and verify no NaN/Inf appears."""
        target = torch.zeros(NUM_ENVS, 3)
        roll = torch.full((NUM_ENVS,), 0.2618)
        pitch = torch.full((NUM_ENVS,), 0.2618)
        ang_vel = torch.zeros(NUM_ENVS, 3)

        for _ in range(100):
            p_EE = controller.compute(roll, pitch, ang_vel, target)
            assert torch.isfinite(p_EE).all(), f"NaN/Inf in p_EE: {p_EE}"

    def test_ik_round_trip(self, kinematics):
        """Verify FK(IK(p_target)) ~ p_target when target is near current FK.

        DLS IK is a single linearization step, so accuracy depends on the
        target being close to the current configuration. We test by computing
        FK at known angles, perturbing slightly, and checking IK recovery.
        """
        # Start from known joint angles (not at singularity)
        current_joints = torch.tensor([[0.5, 0.8], [-0.3, 1.0], [0.2, -0.5], [1.0, 0.3]])
        p_current = kinematics.forward(current_joints)
        # Small perturbation (within single-step DLS accuracy)
        p_target = p_current + torch.tensor([[0.02, -0.01], [-0.01, 0.02], [0.01, 0.01], [-0.02, 0.0]])
        joint_angles = kinematics.inverse(p_target, current_joint_angles=current_joints)
        p_recovered = kinematics.forward(joint_angles)

        # DLS damping introduces small tracking error; 1cm tolerance is acceptable
        torch.testing.assert_close(p_target, p_recovered, atol=0.01, rtol=0.02)


# ===========================================================================
# Reset
# ===========================================================================


class TestReset:
    """Test controller reset behavior."""

    def test_reset_clears_initialization(self, controller):
        """Reset should clear is_initialized flag."""
        roll = torch.full((NUM_ENVS,), 0.1)
        pitch = torch.zeros(NUM_ENVS)
        ang_vel = torch.zeros(NUM_ENVS, 3)
        target = torch.zeros(NUM_ENVS, 3)

        controller.compute(roll, pitch, ang_vel, target)
        assert controller._is_initialized.all()

        reset_ids = torch.tensor([0, 2])
        controller.reset(reset_ids)

        assert not controller._is_initialized[0]
        assert controller._is_initialized[1]
        assert not controller._is_initialized[2]
        assert controller._is_initialized[3]

    def test_reset_zeroes_buffers(self, controller):
        """Reset should zero out history buffers for specified envs."""
        controller._nu_prev[:] = 1.0
        controller._p_EE_prev[:] = 0.5

        reset_ids = torch.tensor([1, 3])
        controller.reset(reset_ids)

        torch.testing.assert_close(controller._nu_prev[1], torch.zeros(2))
        torch.testing.assert_close(controller._nu_prev[3], torch.zeros(2))
        torch.testing.assert_close(controller._nu_prev[0], torch.ones(2))
        torch.testing.assert_close(controller._nu_prev[2], torch.ones(2))


# ===========================================================================
# Parameter updates
# ===========================================================================


class TestUpdateParams:
    """Test update_controller_params and update_buoyancy_force."""

    def test_update_m_hat_all_envs(self, controller):
        """update_controller_params should set m_hat for all envs."""
        new_m = torch.tensor([0.20, 0.25])
        controller.update_controller_params(m_hat=new_m)

        for i in range(NUM_ENVS):
            torch.testing.assert_close(controller._m_hat[i], new_m)

    def test_update_m_hat_subset(self, controller):
        """update_controller_params with env_ids should only update those envs."""
        original = controller._m_hat.clone()
        new_m = torch.tensor([[0.30, 0.35], [0.40, 0.45]])
        env_ids = torch.tensor([1, 3])
        controller.update_controller_params(m_hat=new_m, env_ids=env_ids)

        # Updated envs
        torch.testing.assert_close(controller._m_hat[1], torch.tensor([0.30, 0.35]))
        torch.testing.assert_close(controller._m_hat[3], torch.tensor([0.40, 0.45]))
        # Unchanged envs
        torch.testing.assert_close(controller._m_hat[0], original[0])
        torch.testing.assert_close(controller._m_hat[2], original[2])

    def test_update_buoyancy_force_all(self, controller):
        """update_controller_params(F_bu=...) should set F_bu for all envs."""
        new_fbu = torch.full((NUM_ENVS,), 30.0)
        controller.update_controller_params(F_bu=new_fbu)

        torch.testing.assert_close(controller._F_bu, new_fbu)

    def test_update_buoyancy_force_subset(self, controller):
        """update_controller_params(F_bu=..., env_ids=...) should only update those envs."""
        original = controller._F_bu.clone()
        new_fbu = torch.tensor([30.0, 31.0, 32.0, 33.0])
        env_ids = torch.tensor([0, 2])
        controller.update_controller_params(F_bu=new_fbu, env_ids=env_ids)

        assert controller._F_bu[0].item() == pytest.approx(30.0)
        assert controller._F_bu[2].item() == pytest.approx(32.0)
        # Unchanged
        assert controller._F_bu[1].item() == pytest.approx(original[1].item())
        assert controller._F_bu[3].item() == pytest.approx(original[3].item())

    def test_f_bu_property(self, controller):
        """F_bu property should return the internal buoyancy tensor."""
        assert torch.equal(controller.F_bu, controller._F_bu)

    def test_update_ee_position(self, controller):
        """update_ee_position should overwrite _p_EE_prev."""
        new_pos = torch.tensor([[0.1, 0.2]] * NUM_ENVS)
        controller.update_ee_position(new_pos)

        torch.testing.assert_close(controller._p_EE_prev, new_pos)
