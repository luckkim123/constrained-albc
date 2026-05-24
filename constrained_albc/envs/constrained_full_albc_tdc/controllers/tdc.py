# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Time Delay Controller (TDC) for Hero Agent roll/pitch attitude stabilization.

TDC uses Time Delay Estimation (TDE) to approximate uncertain nonlinear dynamics
without explicit modeling. The controller positions the buoyancy element
(end-effector) to generate restoring torques for attitude control.

TDE Control Law (from IROS 2026 derivation):
    U_hat = Lambda_prev @ p_EE_prev - M_hat * nu_dot_prev
    delta_T_b = T_b_prev - T_b
    tau = M_hat * u_pd + U_hat + delta_T_b
    p_EE = Lambda_inv @ tau

References:
    - 05_derivation.md (IROS 2026 notes)
    - T.C. Hsia & L.S. Lasky, "Robust independent joint controller design
      for industrial robot manipulators," IEEE Trans. Ind. Electron., 1991.
"""

from __future__ import annotations

import torch

from isaaclab.utils import configclass

from marinelab.assets import (
    HERO_AGENT_ALBC_LINK1_LENGTH,
    HERO_AGENT_ALBC_LINK2_LENGTH,
)


@configclass
class TDCControllerCfg:
    """TDC (Time Delay Control) controller configuration.

    Groups all parameters for the TDC attitude stabilization controller.
    Used as a nested config in HeroAgentTDCEnvCfg.
    """

    # Design inertia [roll, pitch] in kg*m^2
    m_hat: tuple[float, float] = (0.15, 0.16)

    # PD gains (tuned 2026-04-22 for OOD robustness: +20% kp, scaled kd)
    kp: float = 48.0  # omega_n = sqrt(48/0.15) = 17.9 rad/s (was 40, +20%)
    kd: float = 14.0  # zeta = 14/(2*sqrt(48*0.15)) = 2.61 (overdamped, was 2.45)

    # Physical geometry
    h: float = 0.180  # CoG-to-ABPC vertical offset (m), CoG at -0.05m

    # DLS regularization for Lambda matrix inverse
    dls_lambda_damping: float = 0.01

    # EMA filter for angular acceleration finite difference
    nu_dot_ema_alpha: float = 0.05

    # EE offset at zero error (avoids origin singularity)
    base_position: tuple[float, float] = (0.002, 0.002)

    # IK: closed-form 2-link planar solver (O(1), deployment-faithful).
    # Iterative DLS removed 2026-04-22: realtime-budget fairness requires non-iterative
    # IK, and the 2-link arm has an exact analytic solution.

    # Joint rate limiting (rad/s)
    max_joint_velocity: float = 2.5

    # Link lengths from URDF (used by kinematics)
    link1_length: float = HERO_AGENT_ALBC_LINK1_LENGTH
    link2_length: float = HERO_AGENT_ALBC_LINK2_LENGTH

    # Console log every N steps (0 = disabled)
    log_interval: int = 200

    # PhysX joint PD gains for TDC arm control (lower than RL default for smoother motion)
    joint_stiffness: float = 200.0
    joint_damping: float = 10.0


class TDCController:
    """GPU-parallel TDC for Hero Agent roll/pitch attitude stabilization.

    Computes desired end-effector position to stabilize roll/pitch angles
    using Time Delay Estimation (TDE) for dynamics compensation.

    The controller operates in a 2D task space [phi, theta] and outputs
    2D end-effector positions [x_EE, y_EE] for the ALBC arm.
    """

    def __init__(
        self,
        num_envs: int,
        device: str,
        cfg: TDCControllerCfg,
        F_bu: torch.Tensor | float = 26.24,
        dt: float = 0.02,
    ) -> None:
        """Initialize TDC controller.

        Args:
            num_envs: Number of parallel environments.
            device: Computation device (e.g., "cuda:0").
            cfg: TDC controller configuration.
            F_bu: Buoyancy force magnitude in N. Per-env tensor (num_envs,) or scalar.
            dt: Control timestep in seconds (= TDE delay L).
        """
        self.num_envs = num_envs
        self.device = device
        self.dt = dt

        self._base_position = torch.tensor(cfg.base_position, device=device, dtype=torch.float32)

        # Design inertia — per-env (num_envs, 2) for future encoder adaptation
        m_hat_base = torch.tensor(cfg.m_hat, device=device, dtype=torch.float32)
        self._m_hat = m_hat_base.unsqueeze(0).expand(num_envs, -1).clone()

        # PD gains — per-env (num_envs, 2) for adaptive gain integration
        self._kp_default = cfg.kp
        self._kd_default = cfg.kd
        self._kp = torch.full((num_envs, 2), cfg.kp, device=device, dtype=torch.float32)
        self._kd = torch.full((num_envs, 2), cfg.kd, device=device, dtype=torch.float32)

        # Physical constants
        self._h = cfg.h
        self._dls_damping = cfg.dls_lambda_damping
        self._nu_dot_ema_alpha = cfg.nu_dot_ema_alpha

        # Buoyancy force (per-env, updated at reset from hydrodynamics model)
        if isinstance(F_bu, torch.Tensor):
            self._F_bu = F_bu.to(device=device, dtype=torch.float32).clone()
        else:
            self._F_bu = torch.full((num_envs,), F_bu, device=device, dtype=torch.float32)

        # --- History buffers for TDE ---
        self._nu_prev = torch.zeros(num_envs, 2, device=device)
        self._nu_dot_filtered = torch.zeros(num_envs, 2, device=device)
        self._p_EE_prev = torch.zeros(num_envs, 2, device=device)
        self._Lambda_prev = torch.zeros(num_envs, 2, 2, device=device)
        self._T_b_prev = torch.zeros(num_envs, 2, device=device)
        self._is_initialized = torch.zeros(num_envs, dtype=torch.bool, device=device)

        # --- Diagnostic buffers (read-only, populated by compute()) ---
        self._u_hat = torch.zeros(num_envs, 2, device=device)
        self._m_hat_u_pd = torch.zeros(num_envs, 2, device=device)
        self._delta_T_b = torch.zeros(num_envs, 2, device=device)
        self._u_hat_prev = torch.zeros(num_envs, 2, device=device)
        self._epsilon_approx = torch.zeros(num_envs, 2, device=device)

        # --- Scratch buffers (reused each step to avoid per-step allocation) ---
        # WARNING: These are returned by reference from _compute_lambda_and_inv() and
        # _compute_restoring_torque(). Calling either method a second time within the
        # same compute() cycle will silently overwrite previously returned values.
        self._Lambda_scratch = torch.zeros(num_envs, 2, 2, device=device)
        self._Lambda_inv_scratch = torch.zeros(num_envs, 2, 2, device=device)
        self._T_b_scratch = torch.zeros(num_envs, 2, device=device)

        # Buffers zeroed on reset (excludes _kp/_kd which reset to defaults)
        self._zero_buffers = [
            self._nu_prev,
            self._nu_dot_filtered,
            self._p_EE_prev,
            self._Lambda_prev,
            self._T_b_prev,
            self._u_hat,
            self._m_hat_u_pd,
            self._delta_T_b,
            self._u_hat_prev,
            self._epsilon_approx,
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_ee_position(self, p_EE: torch.Tensor) -> None:
        """Update stored EE position for anti-windup correction.

        After rate limiting, the actual commanded EE position differs from
        what the controller computed. This method feeds back the actual
        position to prevent positive bias in TDE.

        Args:
            p_EE: Actual EE position from FK(rate-limited joints). Shape: (num_envs, 2).
        """
        self._p_EE_prev[:] = p_EE

    @staticmethod
    def _set_param(buf: torch.Tensor, value: torch.Tensor, env_ids: torch.Tensor | None) -> None:
        """Assign value to buffer, either all envs or indexed subset."""
        if env_ids is None:
            buf[:] = value
        else:
            buf[env_ids] = value

    def update_controller_params(
        self,
        m_hat: torch.Tensor | None = None,
        F_bu: torch.Tensor | None = None,
        env_ids: torch.Tensor | None = None,
    ) -> None:
        """Update controller parameters per-environment (for encoder integration).

        Args:
            m_hat: Design inertia [roll, pitch]. Shape: (N, 2) or (2,).
            F_bu: Buoyancy force. Shape: (N,) or scalar.
            env_ids: Environment indices. None = all.
        """
        if m_hat is not None:
            self._set_param(self._m_hat, m_hat, env_ids)
        if F_bu is not None:
            self._set_param(self._F_bu, F_bu, env_ids)

    def update_gains(
        self,
        kp: torch.Tensor,
        kd: torch.Tensor,
        env_ids: torch.Tensor | None = None,
    ) -> None:
        """Update per-env PD gains (for RL-adaptive gain tuning).

        Args:
            kp: Proportional gains. Shape: (N, 2) or (2,).
            kd: Derivative gains. Shape: (N, 2) or (2,).
            env_ids: Environment indices. None = all.
        """
        self._set_param(self._kp, kp, env_ids)
        self._set_param(self._kd, kd, env_ids)

    @property
    def F_bu(self) -> torch.Tensor:
        """Buoyancy force per environment. Shape: (num_envs,)."""
        return self._F_bu

    @property
    def u_hat(self) -> torch.Tensor:
        """TDE compensation torque from last compute(). Shape: (num_envs, 2)."""
        return self._u_hat

    @property
    def pd_torque(self) -> torch.Tensor:
        """PD torque (M_hat * u_pd) from last compute(). Shape: (num_envs, 2)."""
        return self._m_hat_u_pd

    @property
    def delta_T_b(self) -> torch.Tensor:
        """Restoring torque change from last compute(). Shape: (num_envs, 2)."""
        return self._delta_T_b

    @property
    def epsilon_approx(self) -> torch.Tensor:
        """TDE error proxy (consecutive U_hat difference). Shape: (num_envs, 2)."""
        return self._epsilon_approx

    def compute(
        self,
        roll: torch.Tensor,
        pitch: torch.Tensor,
        ang_vel_body: torch.Tensor,
        target_euler: torch.Tensor,
        external_u_pd: torch.Tensor | None = None,
        residual_tau: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute desired end-effector position using TDC law.

        Args:
            roll: Current roll angle (phi) in radians. Shape: (num_envs,).
            pitch: Current pitch angle (theta) in radians. Shape: (num_envs,).
            ang_vel_body: Body angular velocity [p, q, r]. Shape: (num_envs, 3).
            target_euler: Target [roll, pitch, yaw] in radians. Shape: (num_envs, 3).
            external_u_pd: External control input replacing linear PD. Shape: (num_envs, 2).
                When provided, skips internal _compute_pd_torque() and uses
                M_hat * external_u_pd directly. Used by Neural TDC (RL replaces PD).
            residual_tau: Additive residual torque from RL. Shape: (num_envs, 2).
                Added to tau_desired after TDC law, before Lambda_inv conversion.
                Used by Residual TDC (RL augments TDC, PD stays intact).

        Returns:
            Desired EE position [x, y] in meters. Shape: (num_envs, 2).
        """
        nu = ang_vel_body[:, :2]  # [p, q]

        # Step 1: Estimate angular acceleration (EMA-filtered finite difference)
        nu_dot = self._estimate_angular_acceleration(nu)

        # Step 2: Current Lambda, Lambda_inv, T_b
        Lambda, Lambda_inv = self._compute_lambda_and_inv(roll, pitch)
        T_b = self._compute_restoring_torque(roll, pitch)

        # Step 3: PD control torque (or external RL replacement)
        if external_u_pd is not None:
            m_hat_u_pd = self._m_hat * external_u_pd
            self._m_hat_u_pd.copy_(m_hat_u_pd)
        else:
            m_hat_u_pd = self._compute_pd_torque(roll, pitch, nu, target_euler)

        # Step 4: TDE compensation torque
        tde_term = self._compute_tde_torque(T_b)

        # Step 5: Combine — initialized envs use full TDE, first step uses pure PD
        tau_full = tde_term + m_hat_u_pd
        init_mask = self._is_initialized.unsqueeze(-1)
        tau_desired = torch.where(init_mask, tau_full, m_hat_u_pd)

        # Step 5b: Add residual torque from RL if provided (Residual TDC)
        if residual_tau is not None:
            tau_desired = tau_desired + residual_tau

        # Step 6: Convert torque to EE position
        p_EE = self._torque_to_ee_position(Lambda_inv, tau_desired)

        # Step 7: Update history buffers
        self._update_history(nu, nu_dot, p_EE, Lambda, T_b)

        return p_EE

    def reset(self, env_ids: torch.Tensor) -> None:
        """Reset controller state for specified environments.

        Args:
            env_ids: Environment indices to reset.
        """
        for buf in self._zero_buffers:
            buf[env_ids] = 0.0
        self._is_initialized[env_ids] = False

        # Reset PD gains to defaults for reset environments
        self._kp[env_ids] = self._kp_default
        self._kd[env_ids] = self._kd_default

    # ------------------------------------------------------------------
    # Internal: Physics computations
    # ------------------------------------------------------------------

    def _compute_lambda_and_inv(self, roll: torch.Tensor, pitch: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute Lambda coupling matrix and its DLS-regularized inverse.

        Lambda = [[0, lf], [-lf, 0]]
        Lambda_inv = [[0, -lf_inv], [lf_inv, 0]]

        where lf = cos(theta) * cos(phi) * F_bu
              lf_inv = lf / (lf^2 + damping^2)

        Uses pre-allocated scratch buffers to avoid per-step allocation.

        Note: This exploits the 2x2 anti-diagonal structure of Lambda for
        roll/pitch control. For 6-DOF extension, Lambda becomes a general
        coupling matrix and should use torch.linalg.solve instead of the
        scalar DLS formula (similar to ALBCKinematics._dls_solve).

        Args:
            roll: Roll angle (phi). Shape: (num_envs,).
            pitch: Pitch angle (theta). Shape: (num_envs,).

        Returns:
            Tuple of (Lambda, Lambda_inv), each shape (num_envs, 2, 2).
        """
        lf = torch.cos(pitch) * torch.cos(roll) * self._F_bu
        lf_inv = lf / (lf**2 + self._dls_damping**2)

        Lambda = self._Lambda_scratch
        Lambda.zero_()
        Lambda[:, 0, 1] = lf
        Lambda[:, 1, 0] = -lf

        Lambda_inv = self._Lambda_inv_scratch
        Lambda_inv.zero_()
        Lambda_inv[:, 0, 1] = -lf_inv
        Lambda_inv[:, 1, 0] = lf_inv

        return Lambda, Lambda_inv

    def _compute_restoring_torque(self, roll: torch.Tensor, pitch: torch.Tensor) -> torch.Tensor:
        """Compute buoy passive torque T_b (buoyancy torque at p_EE=0).

        From cross product r=[0,0,h] x F_body:
            T_b = [-cos(theta)*sin(phi)*F_bu*h, -sin(theta)*F_bu*h]

        Args:
            roll: Roll angle (phi). Shape: (num_envs,).
            pitch: Pitch angle (theta). Shape: (num_envs,).

        Returns:
            Restoring torque vector. Shape: (num_envs, 2).
        """
        self._T_b_scratch[:, 0] = -torch.cos(pitch) * torch.sin(roll) * self._F_bu * self._h
        self._T_b_scratch[:, 1] = -torch.sin(pitch) * self._F_bu * self._h
        return self._T_b_scratch

    # ------------------------------------------------------------------
    # Internal: Control law sub-steps
    # ------------------------------------------------------------------

    def _estimate_angular_acceleration(self, nu: torch.Tensor) -> torch.Tensor:
        """Estimate angular acceleration via finite difference + EMA filter.

        Args:
            nu: Current angular velocity [p, q]. Shape: (num_envs, 2).

        Returns:
            EMA-filtered angular acceleration. Shape: (num_envs, 2).
        """
        nu_dot_raw = (nu - self._nu_prev) / self.dt
        alpha = self._nu_dot_ema_alpha
        return alpha * nu_dot_raw + (1.0 - alpha) * self._nu_dot_filtered

    def _compute_pd_torque(
        self,
        roll: torch.Tensor,
        pitch: torch.Tensor,
        nu: torch.Tensor,
        target_euler: torch.Tensor,
    ) -> torch.Tensor:
        """Compute M_hat * u_pd (PD control torque scaled by design inertia).

        Args:
            roll: Current roll. Shape: (num_envs,).
            pitch: Current pitch. Shape: (num_envs,).
            nu: Angular velocity [p, q]. Shape: (num_envs, 2).
            target_euler: Target [roll, pitch, yaw]. Shape: (num_envs, 3).

        Returns:
            M_hat * u_pd. Shape: (num_envs, 2).
        """
        e = torch.stack([target_euler[:, 0] - roll, target_euler[:, 1] - pitch], dim=-1)
        e_dot = -nu
        u_pd = self._kd * e_dot + self._kp * e
        m_hat_u_pd = self._m_hat * u_pd
        self._m_hat_u_pd.copy_(m_hat_u_pd)
        return m_hat_u_pd

    def _compute_tde_torque(self, T_b: torch.Tensor) -> torch.Tensor:
        """Compute TDE compensation torque.

        U_hat = Lambda_prev @ p_EE_prev - M_hat * nu_dot_filtered_prev
        delta_T_b = T_b_prev - T_b  (exact, not filtered)

        Args:
            T_b: Current restoring torque. Shape: (num_envs, 2).

        Returns:
            TDE term (U_hat + delta_T_b). Shape: (num_envs, 2).
        """
        tde_lambda_p = torch.bmm(self._Lambda_prev, self._p_EE_prev.unsqueeze(-1)).squeeze(-1)
        U_hat = tde_lambda_p - self._m_hat * self._nu_dot_filtered
        delta_T_b = self._T_b_prev - T_b
        self._epsilon_approx.copy_(U_hat - self._u_hat_prev)
        self._u_hat_prev.copy_(U_hat)
        self._u_hat.copy_(U_hat)
        self._delta_T_b.copy_(delta_T_b)
        return U_hat + delta_T_b

    def _torque_to_ee_position(self, Lambda_inv: torch.Tensor, tau: torch.Tensor) -> torch.Tensor:
        """Convert desired torque to EE position via Lambda_inv.

        p_EE = Lambda_inv @ tau + base_position

        Args:
            Lambda_inv: DLS-regularized Lambda inverse. Shape: (num_envs, 2, 2).
            tau: Desired torque. Shape: (num_envs, 2).

        Returns:
            Desired EE position. Shape: (num_envs, 2).
        """
        p_EE = torch.bmm(Lambda_inv, tau.unsqueeze(-1)).squeeze(-1)
        return p_EE + self._base_position

    def _update_history(
        self,
        nu: torch.Tensor,
        nu_dot: torch.Tensor,
        p_EE: torch.Tensor,
        Lambda: torch.Tensor,
        T_b: torch.Tensor,
    ) -> None:
        """Store current-step values for next TDE cycle.

        Args:
            nu: Angular velocity [p, q]. Shape: (num_envs, 2).
            nu_dot: Filtered angular acceleration. Shape: (num_envs, 2).
            p_EE: Commanded EE position. Shape: (num_envs, 2).
            Lambda: Coupling matrix. Shape: (num_envs, 2, 2).
            T_b: Restoring torque. Shape: (num_envs, 2).
        """
        self._nu_prev.copy_(nu)
        self._nu_dot_filtered.copy_(nu_dot)
        self._p_EE_prev.copy_(p_EE)
        self._Lambda_prev.copy_(Lambda)
        self._T_b_prev.copy_(T_b)
        self._is_initialized[:] = True


# ======================================================================
# Module-level utilities
# ======================================================================


def compute_M_bb(
    I_ROV: torch.Tensor,
    m_A: torch.Tensor,
    x_bu: torch.Tensor,
    y_bu: torch.Tensor,
    h: float,
    m_body: torch.Tensor | None = None,
) -> torch.Tensor:
    """Compute configuration-dependent true inertia M_bb via parallel axis theorem.

    M_bb_roll  = I_ROV_roll  + m_total * (y_bu^2 + h^2)
    M_bb_pitch = I_ROV_pitch + m_total * (x_bu^2 + h^2)

    where m_total = m_body + m_A (buoy rigid body mass + hydrodynamic added mass).

    Args:
        I_ROV: Rigid body inertia [I_roll, I_pitch]. Shape: (num_envs, 2).
        m_A: Added mass (scalar diagonal entry). Shape: (num_envs,).
        x_bu: Buoy x-position from FK. Shape: (num_envs,).
        y_bu: Buoy y-position from FK. Shape: (num_envs,).
        h: CoG-to-ABPC vertical offset in meters.
        m_body: Buoy rigid body mass. Shape: (num_envs,). If None, uses m_A only
            (legacy behavior, underestimates M_true).

    Returns:
        True inertia M_bb [roll, pitch]. Shape: (num_envs, 2).
    """
    m_total = (m_body + m_A) if m_body is not None else m_A
    return torch.stack(
        [
            I_ROV[:, 0] + m_total * (y_bu**2 + h**2),
            I_ROV[:, 1] + m_total * (x_bu**2 + h**2),
        ],
        dim=-1,
    )
