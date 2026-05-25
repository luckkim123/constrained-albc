# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Velocity + Attitude Tracking ALBC Environment.

8D action (2D arm + 6D thruster). Roll/pitch: attitude command (+-45 deg, exp kernel).
Yaw: rate command. Linear: velocity command. Joint PD for arm, thruster for body.
"""

from __future__ import annotations

import math

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
from isaaclab.utils.math import euler_xyz_from_quat, quat_apply, quat_apply_inverse

from marinelab.physics import HydrodynamicsModel

from .config import ALBCEnvCfg
from .mdp.constraints import compute_all_costs
from .mdp.events import (
    DRSampler,
    randomize_body_mass,
    randomize_hydrodynamics,
    randomize_joint_effort_limit,
    randomize_joint_friction,
    randomize_joint_gains,
    randomize_joint_positions,
    randomize_ocean_current,
    randomize_payload,
    reset_joint_positions_default,
    reset_robot_pose_default,
)
from .mdp.observations import compute_policy_obs, compute_privileged_obs
from .mdp.rewards import RewardManager
from .utils import log_dr_metrics


class ALBCEnv(DirectRLEnv):
    """Velocity + attitude tracking ALBC environment with constrained RL.

    Obs (87D): current_proprio(26D) + temporal_history(55D) + integral_error(6D).
        Current: cmd(6) [lin_vel(3) + att_rp(2) + yaw_rate(1)], euler(3),
                 ang_vel(3), lin_vel(3), jpos(2), jvel(2), manipulability(1), thr(6).
        History: joint_tracking(12D) + body_tracking(27D) + action(16D).
    Action (8D): Delta arm targets (2D) + thruster commands (6D).
    """

    cfg: ALBCEnvCfg

    def __init__(self, cfg: ALBCEnvCfg, render_mode: str | None = None, **kwargs):
        """Initialize the ALBC environment.

        Args:
            cfg: Environment configuration.
            render_mode: Render mode for visualization.
            **kwargs: Additional arguments.
        """
        # Convert noise config tuples to tensors before DirectRLEnv creates the noise model.
        # Tuples are used in config for OmegaConf/Hydra serialization compatibility.
        self._convert_noise_cfg_tuples(cfg)

        super().__init__(cfg, render_mode, **kwargs)

        # Pre-expand the bias buffer to match observation dimensions.
        # NoiseModelWithAdditiveBias initializes bias as (num_envs, 1) and only expands
        # on first __call__. But the wrapper calls env.reset() before any step, which
        # triggers noise_model.reset() while bias is still (N, 1). With per-dimension
        # n_min/n_max tensors, the reset produces (N, obs_dim) which can't fit in (N, 1).
        if self.cfg.observation_noise_model is not None:
            nm = self._observation_noise_model
            if nm._sample_bias_per_component and nm._num_components is None:
                nm._num_components = self.cfg.observation_space
                nm._bias = nm._bias.repeat(1, nm._num_components)

        # Validate state_space value
        if self.cfg.state_space < 0:
            raise ValueError(f"state_space={self.cfg.state_space} must be non-negative")

        # Validate control frequency: control_decimation must be a positive divisor
        # of episode steps. step_dt * control_decimation gives the control period.
        if cfg.control_decimation < 1:
            raise ValueError(f"control_decimation={cfg.control_decimation} must be >= 1")
        control_dt = self.step_dt * cfg.control_decimation
        control_freq = 1.0 / control_dt
        if control_freq < 10.0 or control_freq > 1000.0:
            raise ValueError(
                f"Control frequency {control_freq:.1f}Hz (step_dt={self.step_dt}, "
                f"control_decimation={cfg.control_decimation}) outside valid range [10, 1000]Hz"
            )

        self._init_body_ids()
        self._init_hydrodynamics()
        self._init_payload()
        self._init_joints()
        self._init_task_and_rewards()
        self._init_state_buffers()
        self._init_thrusters()
        self._init_doraemon()
        self._init_payload_viz()

        # DR sampler shared between _reset_physics() and _reset_task_and_state()
        self._current_dr_sampler: DRSampler | None = None

        # Cache config-static values (avoids repeated attribute lookups)
        self._constraints_cfg = getattr(self.cfg, "constraints", None)
        self._vel_cmd_resample_steps = self.cfg.vel_cmd_resample_steps
        self._has_ocean_current = any(v > 0 for v in self.cfg.ocean_current.max_velocity)

        # Per-condition termination flags (for diagnostics logging)
        self._term_bad_state = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self._term_excessive_tilt = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

        # Validate observation dimension contract (fails loud at construction, not first step).
        # observation_space (config) must equal the actual o_t assembled in _get_observations():
        #   proprio (26D, compute_policy_obs) + history (13*hist_len + 8*hist_action_len) + integral.
        # Mirrors the existing state_space / control_freq guards above. Runs once -- obs dim is
        # step-invariant -- and survives `python -O` (unlike assert; cf. constraint_trpo hot-path assert).
        # TODO(user): implement the dimension check below.
        #   - PROPRIO_DIM = 26 is the documented compute_policy_obs() contract (6 cmd + 9 body + 5 arm + 6 thruster).
        #   - history contributes 0 when self._hist_buf is None (hist_len == 0).
        #   - integral contributes self.cfg.integral_dims only when self.cfg.use_integral_obs.
        #   - On mismatch, raise ValueError with expected vs computed and the relevant cfg flags,
        #     matching the f-string style of the state_space / control_freq guards.
        PROPRIO_DIM = 26
        expected_obs_dim = PROPRIO_DIM
        if self._hist_buf is not None:
            expected_obs_dim += 13 * self._hist_len + 8 * self._hist_action_len
        if self.cfg.use_integral_obs:
            expected_obs_dim += self.cfg.integral_dims
        if expected_obs_dim != self.cfg.observation_space:
            raise ValueError(
                f"observation_space={self.cfg.observation_space} != computed obs dim {expected_obs_dim} "
                f"(proprio={PROPRIO_DIM}, hist_len={self._hist_len}, hist_action_len={self._hist_action_len}, "
                f"use_integral_obs={self.cfg.use_integral_obs}, integral_dims={self.cfg.integral_dims})"
            )

        # Pre-build the integral error-gating sigma tensor once (step-invariant cfg constants).
        # Avoids re-allocating torch.tensor(...) every step in _get_rewards (hot loop).
        if self.cfg.use_integral_obs and self.cfg.integral_gated:
            sigmas = [self.cfg.reward.att_rp.sigma, self.cfg.reward.att_rp.sigma]
            if self.cfg.integral_dims == 6:
                sigmas += [self.cfg.reward.lin_vel.sigma] * 3 + [self.cfg.reward.yaw_vel.sigma]
            else:
                sigmas.append(self.cfg.reward.lin_vel.sigma)
            self._integral_gate_sigmas = torch.tensor(sigmas, device=self.device)
        else:
            self._integral_gate_sigmas = None

    @staticmethod
    def _iter_noise_params(cfg: ALBCEnvCfg):
        """Yield (sub_cfg, param_name, value) for all tuple/list noise params."""
        noise_model = getattr(cfg, "observation_noise_model", None)
        if noise_model is None:
            return
        for sub_cfg_attr in ("noise_cfg", "bias_noise_cfg"):
            sub_cfg = getattr(noise_model, sub_cfg_attr, None)
            if sub_cfg is None:
                continue
            for param in ("std", "mean", "n_min", "n_max"):
                val = getattr(sub_cfg, param, None)
                if isinstance(val, (list, tuple)):
                    yield sub_cfg, param, val

    @staticmethod
    def _convert_noise_cfg_tuples(cfg: ALBCEnvCfg) -> None:
        """Convert noise config tuple/list values to torch.Tensor in-place.

        Config uses tuples for OmegaConf/Hydra serialization compatibility.
        The noise model functions require float or torch.Tensor for arithmetic.
        Must be called before DirectRLEnv.__init__() which instantiates noise models.
        """
        for sub_cfg, param, val in ALBCEnv._iter_noise_params(cfg):
            setattr(sub_cfg, param, torch.tensor(val))

    def _init_body_ids(self) -> None:
        """Initialize body IDs and physics parameters."""
        self._body_id = self._robot.find_bodies(self.cfg.hydrodynamics.body_name)[0]
        self._buoy_body_id = self._robot.find_bodies(self.cfg.buoy_hydrodynamics.body_name)[0]
        self._gripper_body_id = self._robot.find_bodies("gripper")[0]
        self._gravity_magnitude = torch.tensor(self.sim.cfg.gravity, device=self.device).norm()

    def _init_hydrodynamics(self) -> None:
        """Initialize hydrodynamics models for main body and buoy."""
        prim_path = self.cfg.robot.prim_path.replace("env_.*", "env_0")
        self._hydro = HydrodynamicsModel(
            num_envs=self.num_envs,
            device=self.device,
            cfg=self.cfg.hydrodynamics,
            current_cfg=self.cfg.ocean_current,
            dt=self.physics_dt,
            articulation_prim_path=prim_path,
        )
        self._buoy_hydro = HydrodynamicsModel(
            num_envs=self.num_envs,
            device=self.device,
            cfg=self.cfg.buoy_hydrodynamics,
            current_cfg=None,  # buoy shares main body's current (injected below)
            dt=self.physics_dt,
            articulation_prim_path=prim_path,
            current=self._hydro.current,  # shared OceanCurrent component
        )

    def _init_payload(self) -> None:
        """Initialize payload physics buffers.

        Payload is applied to the gripper body (fixed to base via base_to_gripper joint).
        """
        self._payload_mass = torch.full((self.num_envs,), self.cfg.payload_mass, device=self.device)
        offset = torch.tensor(self.cfg.payload_attachment_offset, device=self.device, dtype=torch.float32)
        self._payload_attachment_offset = offset.expand(self.num_envs, -1).clone()
        self._payload_cog_offset = torch.zeros(self.num_envs, 3, device=self.device)
        self._payload_gravity_vec = torch.tensor(self.sim.cfg.gravity, device=self.device, dtype=torch.float32)

    def _init_joints(self) -> None:
        """Initialize ALBC joint IDs and limits."""
        self._albc_joint_ids = self._robot.find_joints(self.cfg.albc_joint_names)[0]
        if len(self._albc_joint_ids) != 2:
            raise ValueError(
                f"Expected 2 ALBC joints, found {len(self._albc_joint_ids)}. Joint names: {self.cfg.albc_joint_names}"
            )
        # Both joints are continuous rotation motors (no physical position limits).
        # Observation uses angular wrapping (atan2) instead of linear normalization.
        self._default_effort_limit = self._robot.data.joint_effort_limits[0, self._albc_joint_ids[0]].item()

    def _init_task_and_rewards(self) -> None:
        """Initialize reward manager for velocity tracking."""
        self._reward_manager = RewardManager(
            cfg=self.cfg.reward,
            num_envs=self.num_envs,
            device=self.device,
        )

    def _init_state_buffers(self) -> None:
        """Initialize all runtime state buffers."""
        self._init_action_buffers()
        self._init_history_buffers()
        self._init_velocity_buffers()
        self._init_tracking_buffers()
        self._init_force_buffers()
        # Euler angle cache (refreshed once per step in _get_dones, read by rewards/obs/constraints)
        self._euler_cache: tuple[torch.Tensor, torch.Tensor, torch.Tensor] | None = None

    def _init_action_buffers(self) -> None:
        """Action history (3-deep for smoothness penalty) and joint PD targets."""
        self._actions = torch.zeros(self.num_envs, self.cfg.action_space, device=self.device)
        self._prev_actions = torch.zeros(self.num_envs, self.cfg.action_space, device=self.device)
        self._prev_prev_actions = torch.zeros(self.num_envs, self.cfg.action_space, device=self.device)
        self._nominal_joint_pos = torch.tensor(self.cfg.nominal_joint_pos, device=self.device)
        self._delta_scale = self.cfg.delta_scale
        self._joint_pos_targets = self._nominal_joint_pos.expand(self.num_envs, -1).clone()
        self._control_step_counter = 0

    def _init_history_buffers(self) -> None:
        """Temporal history ring buffer: 21D per step (joint 4D + body 9D + action 8D)."""
        self._hist_len = self.cfg.hist_len
        self._hist_stride = self.cfg.hist_stride
        self._hist_action_len = self.cfg.hist_action_len
        if self._hist_len > 0:
            self._hist_buf = torch.zeros(
                self.num_envs,
                self._hist_len,
                self.cfg.hist_feature_dim,
                device=self.device,
            )
            self._hist_step_counter = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        else:
            self._hist_buf = None
            self._hist_step_counter = None

    def _init_velocity_buffers(self) -> None:
        """Command tracking buffers (mixed attitude + velocity)."""
        # Previous-step velocity for settling cost constraints (anti-overshoot)
        self._prev_root_lin_vel_b = torch.zeros(self.num_envs, 3, device=self.device)
        self._prev_root_ang_vel_z = torch.zeros(self.num_envs, device=self.device)
        self._vel_cmd_lin = torch.zeros(self.num_envs, 3, device=self.device)
        # [0:2] = roll/pitch attitude (rad), [2] = yaw rate (rad/s)
        self._ang_cmd = torch.zeros(self.num_envs, 3, device=self.device)
        self._lin_vel_err = torch.zeros(self.num_envs, 3, device=self.device)
        self._att_rp_err = torch.zeros(self.num_envs, 2, device=self.device)
        self._yaw_rate_err = torch.zeros(self.num_envs, device=self.device)
        # 3D mixed error for history buffer: [att_rp_err(2), yaw_rate_err(1)]
        self._ang_err = torch.zeros(self.num_envs, 3, device=self.device)
        # Leaky-integrated error for Hwangbo 2017 pattern
        # 3D: [roll, pitch, vy] (R7 legacy) | 6D: [roll, pitch, vx, vy, vz, yaw_rate] (R8+)
        self._error_integral = torch.zeros(self.num_envs, self.cfg.integral_dims, device=self.device)
        # EMA bias buffer (6D, ungated) for sustained offset penalization. Updated every
        # step regardless of error magnitude; meant to capture systematic per-env bias
        # that per-step tracking reward ignores.
        self._bias_ema = torch.zeros(self.num_envs, 6, device=self.device)
        self._vel_cmd_step_counter = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        # Per-env command range scales (DORAEMON-managed, default 1.0 if disabled)
        self._cmd_lin_scale = torch.ones(self.num_envs, device=self.device)
        self._cmd_att_scale = torch.ones(self.num_envs, device=self.device)
        self._cmd_yaw_scale = torch.ones(self.num_envs, device=self.device)

    def _init_tracking_buffers(self) -> None:
        """Manipulability, cumulative yaw, mid-episode dynamics, and OU process buffers."""
        self._manipulability = torch.zeros(self.num_envs, device=self.device)
        self._cumulative_yaw = torch.zeros(self.num_envs, device=self.device)
        self._prev_yaw = torch.zeros(self.num_envs, device=self.device)
        # Mid-episode payload toggle
        self._payload_toggle_counter = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self._payload_has_payload_at_reset = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self._payload_no_toggle_mask = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self._payload_toggled = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self._stashed_payload_mass = torch.zeros(self.num_envs, device=self.device)
        self._stashed_payload_cog_offset = torch.zeros(self.num_envs, 3, device=self.device)
        # OU process base current (mean-reversion target, set at reset)
        self._ou_base_current = torch.zeros(self.num_envs, 3, device=self.device)

    def _init_force_buffers(self) -> None:
        """Hydrodynamic force/torque accumulation buffers."""
        self._hydro_forces = torch.zeros(self.num_envs, 3, device=self.device)
        self._hydro_torques = torch.zeros(self.num_envs, 3, device=self.device)
        self._buoy_hydro_forces = torch.zeros(self.num_envs, 3, device=self.device)
        self._buoy_hydro_torques = torch.zeros(self.num_envs, 3, device=self.device)

    def _init_thrusters(self) -> None:
        """Initialize thruster model if configured (None = ALBC arm only)."""
        if self.cfg.thrusters is None:
            self._thruster = None
            return
        from marinelab.physics import ThrusterModel

        self._thruster = ThrusterModel(
            cfg=self.cfg.thrusters,
            num_envs=self.num_envs,
            device=self.device,
            enable_randomization=self.cfg.randomization.enable,
        )

    def _init_doraemon(self) -> None:
        """Initialize DORAEMON adaptive DR scheduler if enabled."""
        doraemon_cfg = getattr(self.cfg, "doraemon", None)
        if doraemon_cfg is not None and doraemon_cfg.enable:
            from .doraemon import _NOMINAL_OVERRIDES, _PARAM_DEFS, NDIMS, DoraemonScheduler

            self._doraemon = DoraemonScheduler(
                doraemon_cfg,
                self.device,
                dr_cfg=self.cfg.randomization,
                param_defs=_PARAM_DEFS,
                nominal_overrides=_NOMINAL_OVERRIDES,
            )
            self._doraemon_ndims = NDIMS
        else:
            self._doraemon = None
            self._doraemon_ndims = 0

        if self._doraemon is not None:
            ndims = self._doraemon_ndims
            self._episode_dr_xi = torch.zeros(self.num_envs, ndims, device=self.device)
            self._episode_dr_log_probs = torch.zeros(self.num_envs, device=self.device)
            self._episode_return_accum = torch.zeros(self.num_envs, device=self.device)

    def _setup_scene(self):
        """Setup simulation scene with robot and underwater lighting."""
        self._robot = Articulation(self.cfg.robot)
        self.scene.articulations["robot"] = self._robot
        self.scene.clone_environments(copy_from_source=False)

        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=[])

        # Dark underwater-style background with dim ambient lighting
        # visible_in_primary_ray=False makes the background black (no sky texture)
        light_cfg = sim_utils.DomeLightCfg(
            intensity=800.0,
            color=(0.3, 0.5, 0.7),
            visible_in_primary_ray=False,
        )
        light_cfg.func("/World/Light", light_cfg)

    def _update_action_buffers(self, actions: torch.Tensor) -> None:
        """Update action history buffers. Called at the start of _pre_physics_step().

        Args:
            actions: Raw actions from RL. Shape: (num_envs, action_space).
        """
        self._prev_prev_actions = self._prev_actions.clone()
        self._prev_actions = self._actions.clone()
        self._actions = actions.clone().clamp(-1.0, 1.0)
        self._control_step_counter += 1

    def _get_hist_features(self) -> torch.Tensor:
        """Compute temporal history features (21D per timestep).

        Called before ``_apply_joint_pd_action()`` so that ``_joint_pos_targets``
        still holds ``q_des_{t-1}`` (the previous step's target).

        Joint tracking (4D) -- actuator response:
            [0:2]   joint position error: q_des_{t-1} - q_actual_t
            [2:4]   joint velocity

        Body tracking (9D) -- system response:
            [4:7]   linear velocity tracking error: vel_cmd - lin_vel
            [7:9]   roll/pitch attitude error (radians, wrapped)
            [9]     yaw rate error (rad/s)
            [10:13] euler angles (roll, pitch, yaw)

        Action (8D) -- recent control input:
            [13:21] full action (2D arm + 6D thruster)
        """
        joint_pos = self._robot.data.joint_pos[:, self._albc_joint_ids]
        joint_pos_error = self._joint_pos_targets - joint_pos
        joint_vel = self._robot.data.joint_vel[:, self._albc_joint_ids]

        lin_vel_err = self._vel_cmd_lin - self._robot.data.root_lin_vel_b
        roll, pitch, yaw = euler_xyz_from_quat(self._robot.data.root_quat_w)

        # Roll/pitch: attitude error (wrapped to [-pi, pi])
        att_raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
        att_rp_err = torch.atan2(torch.sin(att_raw), torch.cos(att_raw))
        # Yaw: rate error
        yaw_rate_err = self._ang_cmd[:, 2] - self._robot.data.root_ang_vel_b[:, 2]
        ang_err = torch.cat([att_rp_err, yaw_rate_err.unsqueeze(-1)], dim=-1)

        return torch.cat(
            [
                joint_pos_error,  # 2D: q_des_{t-1} - q_actual_t
                joint_vel,  # 2D: joint velocities
                lin_vel_err,  # 3D: lin vel tracking error
                ang_err,  # 3D: [att_rp_err(2), yaw_rate_err(1)]
                torch.stack([roll, pitch, yaw], dim=-1),  # 3D: euler angles
                self._prev_actions,  # 8D: action that produced current state
            ],
            dim=-1,
        )

    def _update_hist(self) -> None:
        """Record history features into ring buffer with stride.

        With stride=N, records every N-th control step for wider temporal coverage.
        Effective span = hist_len * hist_stride * step_dt (e.g., 3 * 3 * 0.02 = 0.18s).
        """
        if self._hist_buf is None:
            return
        self._hist_step_counter += 1
        record_mask = (self._hist_step_counter % self._hist_stride) == 0
        if not record_mask.any():
            return
        new_entry = self._get_hist_features()
        ids = record_mask.nonzero(as_tuple=True)[0]
        self._hist_buf[ids, :-1] = self._hist_buf[ids, 1:].clone()
        self._hist_buf[ids, -1] = new_entry[ids]

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        """Process actions: compute joint PD targets and thruster dynamics.

        Called once per env step (50Hz). With decimation=4, the subsequent
        _apply_action() runs 4 times (200Hz PD) tracking these targets.

        Args:
            actions: Action commands [-1, 1]. Shape: (num_envs, action_space).
                     First 2 dims = arm delta, remaining = thruster commands.
        """
        self._update_action_buffers(actions)
        self._update_hist()

        # Velocity command resampling (mid-episode)
        self._vel_cmd_step_counter += 1
        resample_steps = self._vel_cmd_resample_steps
        if resample_steps > 0:
            resample_mask = self._vel_cmd_step_counter >= resample_steps
            if resample_mask.any():
                resample_ids = resample_mask.nonzero(as_tuple=True)[0]
                self._sample_velocity_command(resample_ids)

        # Payload toggle (counter-based, max 1 per episode, at midpoint)
        toggle_steps = self.cfg.payload_toggle_steps
        if toggle_steps != 0:
            actual_steps = self.max_episode_length // 2 if toggle_steps == -1 else toggle_steps
            self._payload_toggle_counter += 1
            toggle_mask = (
                (self._payload_toggle_counter >= actual_steps) & ~self._payload_no_toggle_mask & ~self._payload_toggled
            )
            if toggle_mask.any():
                toggle_ids = toggle_mask.nonzero(as_tuple=True)[0]
                self._apply_payload_toggle(toggle_ids)

        # Ocean current OU drift (per-step continuous update)
        if self.cfg.ou_enable:
            self._step_ocean_current_ou()

        # Update manipulability index (Yoshikawa)
        self._update_manipulability()

        # Update cumulative yaw for tether wrapping constraint
        self._update_cumulative_yaw()

        arm_actions = self._actions[:, :2]
        if self._control_step_counter % self.cfg.control_decimation == 0:
            self._apply_joint_pd_action(arm_actions)

        if self._thruster is not None:
            self._thruster.apply_dynamics(self._actions[:, 2:], self.physics_dt)

        self._update_payload_viz()

    def _apply_joint_pd_action(self, actions: torch.Tensor) -> None:
        """Accumulate delta joint targets: q_des += delta_scale * a_t.

        Delta parameterization limits per-step position change (max 0.08 rad/step),
        preventing PD actuator saturation. Both joints are continuous rotation
        motors with no physical position limits. Joint1 cable wrapping is
        protected by the joint1_position_cost constraint, not by clamping.

        Args:
            actions: Normalized actions [-1, 1]. Shape: (num_envs, 2).
        """
        self._joint_pos_targets += self._delta_scale * actions

    def _update_manipulability(self) -> None:
        """Compute Yoshikawa manipulability index from current arm configuration.

        w = sqrt(|l1 * l2 * sin(theta2)|), normalized by w_max = l1 * l2.
        Result in [0, 1]: 1.0 = max manipulability, 0.0 = singularity.
        """
        from marinelab.assets import ALBC_LINK1_LENGTH, ALBC_LINK2_LENGTH

        l1 = ALBC_LINK1_LENGTH  # 0.233
        l2 = ALBC_LINK2_LENGTH  # 0.233
        theta2 = self._robot.data.joint_pos[:, self._albc_joint_ids[1]]
        # w = sqrt(|l1*l2*sin(theta2)|), w_max = sqrt(l1*l2) (at sin=1)
        w = torch.sqrt((l1 * l2 * torch.sin(theta2)).abs())
        w_max = math.sqrt(l1 * l2)
        self._manipulability = w / w_max

    def _update_cumulative_yaw(self) -> None:
        """Track cumulative body yaw rotation for tether wrapping constraint.

        Accumulates delta yaw per step with wrapping correction (yaw in [-pi, pi]).
        Reset on episode reset via _reset_action_buffers().
        """
        _, _, yaw = euler_xyz_from_quat(self._robot.data.root_quat_w)
        delta_yaw = yaw - self._prev_yaw
        # Handle wrapping: yaw jumps +-2*pi at the -pi/+pi boundary
        delta_yaw = torch.where(delta_yaw > math.pi, delta_yaw - 2 * math.pi, delta_yaw)
        delta_yaw = torch.where(delta_yaw < -math.pi, delta_yaw + 2 * math.pi, delta_yaw)
        self._cumulative_yaw += delta_yaw
        self._prev_yaw = yaw.clone()

    def _sample_velocity_command(self, env_ids: torch.Tensor) -> None:
        """Sample random commands for specified environments.

        Roll/pitch: attitude command (radians) from att_cmd_rp_range.
        Yaw: rate command (rad/s) from yaw_rate_cmd_range.
        Linear: velocity command (m/s) from vel_cmd_lin_range.
        Ranges are scaled per-env by DORAEMON cmd_*_scale (default 1.0).
        With probability ``vel_cmd_zero_prob``, an env receives a zero command.

        In play_mode, all commands are fixed to zero (hovering/station-keeping).
        """
        if self.cfg.play_mode:
            self._vel_cmd_lin[env_ids] = 0.0
            self._ang_cmd[env_ids] = 0.0
            self._vel_cmd_step_counter[env_ids] = 0
            return

        n = len(env_ids)
        lin_max = abs(self.cfg.vel_cmd_lin_range[1])
        att_max = abs(self.cfg.att_cmd_rp_range[1])
        yaw_max = abs(self.cfg.yaw_rate_cmd_range[1])

        # Per-env DORAEMON scales (1.0 when DORAEMON disabled)
        lin_s = self._cmd_lin_scale[env_ids].unsqueeze(1)  # (n, 1)
        att_s = self._cmd_att_scale[env_ids].unsqueeze(1)  # (n, 1)
        yaw_s = self._cmd_yaw_scale[env_ids]  # (n,)

        self._vel_cmd_lin[env_ids] = torch.empty(n, 3, device=self.device).uniform_(-1, 1) * (lin_max * lin_s)
        self._ang_cmd[env_ids, :2] = torch.empty(n, 2, device=self.device).uniform_(-1, 1) * (att_max * att_s)
        self._ang_cmd[env_ids, 2] = torch.empty(n, device=self.device).uniform_(-1, 1) * (yaw_max * yaw_s)

        # Zero-command envs: hovering / station-keeping
        zero_mask = torch.rand(n, device=self.device) < self.cfg.vel_cmd_zero_prob
        if zero_mask.any():
            zero_ids = env_ids[zero_mask]
            self._vel_cmd_lin[zero_ids] = 0.0
            self._ang_cmd[zero_ids] = 0.0
        self._vel_cmd_step_counter[env_ids] = 0

    # ------------------------------------------------------------------
    # Mid-episode dynamics: payload toggle + ocean current OU drift
    # ------------------------------------------------------------------

    def _setup_payload_toggle(self, env_ids: torch.Tensor) -> None:
        """Setup payload toggle state for new episodes.

        Called from ``_reset_physics()`` after ``randomize_payload()``.
        Stashes DR-sampled payload values, then optionally zeroes mass for
        start-without-payload episodes.
        """
        toggle_steps = self.cfg.payload_toggle_steps
        if toggle_steps == 0:
            return

        n = len(env_ids)

        # Stash the DR/DORAEMON-sampled payload for later PICK events
        self._stashed_payload_mass[env_ids] = self._payload_mass[env_ids].clone()
        self._stashed_payload_cog_offset[env_ids] = self._payload_cog_offset[env_ids].clone()

        # Decide which envs start WITH payload
        start_with = torch.rand(n, device=self.device) < self.cfg.payload_start_with_prob
        self._payload_has_payload_at_reset[env_ids] = start_with

        # Decide which envs skip toggle entirely (constant payload)
        self._payload_no_toggle_mask[env_ids] = torch.rand(n, device=self.device) < self.cfg.payload_no_toggle_prob

        # Start-without-payload envs: zero mass and CoG offset
        no_payload_ids = env_ids[~start_with]
        if len(no_payload_ids) > 0:
            self._payload_mass[no_payload_ids] = 0.0
            self._payload_cog_offset[no_payload_ids] = 0.0

            # Ensure stash has meaningful mass for PICK events
            stash_too_small = self._stashed_payload_mass[no_payload_ids] < 0.1
            if stash_too_small.any():
                fix_ids = no_payload_ids[stash_too_small]
                lo = max(0.1, self.cfg.randomization.payload_mass_range[0])
                hi = self.cfg.randomization.payload_mass_range[1]
                self._stashed_payload_mass[fix_ids] = torch.empty(len(fix_ids), device=self.device).uniform_(lo, hi)
                self._sample_stashed_cog_offset(fix_ids)

        # If episode jitter placed this env past the toggle point, skip toggle
        actual_steps = self.max_episode_length // 2 if toggle_steps == -1 else toggle_steps
        past_toggle = self.episode_length_buf[env_ids] >= actual_steps
        if past_toggle.any():
            self._payload_toggled[env_ids] = self._payload_toggled[env_ids] | past_toggle

    def _apply_payload_toggle(self, env_ids: torch.Tensor) -> None:
        """Toggle payload for specified environments (max 1 per episode).

        - Started WITH payload (mass > 0) -> DROP: mass=0, cog_offset=0
        - Started WITHOUT payload (mass=0) -> PICK: mass=stashed, cog_offset=stashed
        """
        had_payload = self._payload_has_payload_at_reset[env_ids]

        # DROP events: mass -> 0
        drop_ids = env_ids[had_payload]
        if len(drop_ids) > 0:
            self._payload_mass[drop_ids] = 0.0
            self._payload_cog_offset[drop_ids] = 0.0

        # PICK events: mass -> stashed value (with stability clamp)
        pick_ids = env_ids[~had_payload]
        if len(pick_ids) > 0:
            self._payload_mass[pick_ids] = self._stashed_payload_mass[pick_ids]
            self._payload_cog_offset[pick_ids] = self._stashed_payload_cog_offset[pick_ids].clone()
            self._clamp_payload_cog(pick_ids)

        self._payload_toggled[env_ids] = True
        self._payload_toggle_counter[env_ids] = 0

    def _clamp_payload_cog(self, env_ids: torch.Tensor) -> None:
        """Clamp payload CoG offset for static stability: m*g*|r_eff_xy| <= F_bu * h."""
        from .mdp.events import _clamp_payload_cog_stability

        self._payload_cog_offset[env_ids] = _clamp_payload_cog_stability(
            attachment_offset=self._payload_attachment_offset[env_ids],
            cog_offset=self._payload_cog_offset[env_ids],
            buoyancy_force=self._buoy_hydro.buoyancy_force[env_ids],
            moment_arm=self.cfg.randomization.buoy_moment_arm,
            mass=self._payload_mass[env_ids],
            gravity=self._gravity_magnitude.item(),
        )

    def _sample_stashed_cog_offset(self, env_ids: torch.Tensor) -> None:
        """Sample CoG offset for stashed payload (PICK events starting without payload)."""
        cfg = self.cfg.randomization
        n = len(env_ids)

        # XY: uniform disk sampling
        r_max = cfg.payload_cog_offset_xy_radius
        if r_max > 0:
            angle = torch.rand(n, device=self.device) * 2.0 * torch.pi
            radius = r_max * torch.sqrt(torch.rand(n, device=self.device))
            self._stashed_payload_cog_offset[env_ids, 0] = radius * torch.cos(angle)
            self._stashed_payload_cog_offset[env_ids, 1] = radius * torch.sin(angle)
        else:
            self._stashed_payload_cog_offset[env_ids, :2] = 0.0

        # Z: uniform range
        lo, hi = cfg.payload_cog_offset_z
        self._stashed_payload_cog_offset[env_ids, 2] = torch.empty(n, device=self.device).uniform_(lo, hi)

    def _step_ocean_current_ou(self) -> None:
        """Advance OU process one step for ocean current drift.

        dx = -theta * (x - mu) * dt + sigma * sqrt(dt) * N(0,1)

        Only linear components (xyz). Angular stays zero. main_hydro and
        buoy_hydro share one OceanCurrent component, so a single write covers both.
        """
        theta = self.cfg.ou_theta
        sigma = self.cfg.ou_sigma
        dt = self.step_dt

        velocity_w = self._hydro.current.velocity_w  # (num_envs, 6) shared buffer
        current = velocity_w[:, :3]
        mu = self._ou_base_current

        drift = -theta * (current - mu) * dt
        diffusion = sigma * (dt**0.5) * torch.randn_like(current)
        new_current = current + drift + diffusion

        # Clamp to slightly beyond max_velocity (within encoder bounds).
        # Note: axes with max_velocity=0 have OU drift clamped to zero.
        max_vel = self._hydro.current.max_velocity[:3]
        clamp_bound = max_vel * 1.05
        new_current = new_current.clamp(-clamp_bound, clamp_bound)

        velocity_w[:, :3] = new_current  # shared buffer -> buoy sees it too

    def _apply_action(self):
        """Apply joint position targets and hydrodynamic forces."""
        self._robot.set_joint_position_target(self._joint_pos_targets, joint_ids=self._albc_joint_ids)

        # Update PhysX acceleration cache for added mass force
        if self._hydro.apply_added_mass:
            self._hydro.update_physx_state(
                body_com_acc_w=self._robot.data.body_com_acc_w,
                root_quat_w=self._robot.data.root_quat_w,
            )
        if self._buoy_hydro.apply_added_mass:
            buoy_body_idx = self._buoy_body_id[0]
            self._buoy_hydro.update_physx_state(
                body_com_acc_w=self._robot.data.body_com_acc_w[:, buoy_body_idx, :],
                root_quat_w=self._robot.data.body_quat_w[:, buoy_body_idx, :],
            )

        # Main body hydrodynamics
        self._hydro_forces, self._hydro_torques = self._hydro.compute_forces(
            root_lin_vel_w=self._robot.data.root_lin_vel_w,
            root_ang_vel_w=self._robot.data.root_ang_vel_w,
            root_quat_w=self._robot.data.root_quat_w,
        )

        # Combine hydro + thruster forces on main body (set overwrites, must pre-combine)
        main_forces = self._hydro_forces
        main_torques = self._hydro_torques
        if self._thruster is not None:
            thrust_f, thrust_t = self._thruster.compute_wrench()
            main_forces = main_forces + thrust_f
            main_torques = main_torques + thrust_t

        self._robot.permanent_wrench_composer.set_forces_and_torques(
            body_ids=self._body_id,
            forces=main_forces.unsqueeze(1),
            torques=main_torques.unsqueeze(1),
        )

        # Buoy hydrodynamics
        buoy_idx = self._buoy_body_id[0]
        self._buoy_hydro_forces, self._buoy_hydro_torques = self._buoy_hydro.compute_forces(
            root_lin_vel_w=self._robot.data.body_lin_vel_w[:, buoy_idx, :],
            root_ang_vel_w=self._robot.data.body_ang_vel_w[:, buoy_idx, :],
            root_quat_w=self._robot.data.body_quat_w[:, buoy_idx, :],
        )
        self._robot.permanent_wrench_composer.set_forces_and_torques(
            body_ids=self._buoy_body_id,
            forces=self._buoy_hydro_forces.unsqueeze(1),
            torques=self._buoy_hydro_torques.unsqueeze(1),
        )

        # Gripper payload (weight force applied at attachment point + CoG offset)
        payload_forces, payload_torques = self._compute_payload_wrench()
        self._robot.permanent_wrench_composer.set_forces_and_torques(
            body_ids=self._gripper_body_id,
            forces=payload_forces.unsqueeze(1),
            torques=payload_torques.unsqueeze(1),
        )

    def _compute_payload_wrench(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute payload weight force and torque in the gripper body frame.

        Returns:
            Tuple of (forces, torques) in gripper body frame.
        """
        gripper_idx = self._gripper_body_id[0]
        gripper_quat = self._robot.data.body_quat_w[:, gripper_idx, :]
        payload_weight_w = self._payload_mass.unsqueeze(-1) * self._payload_gravity_vec
        payload_weight_b = quat_apply_inverse(gripper_quat, payload_weight_w)
        effective_offset = self._payload_attachment_offset + self._payload_cog_offset
        payload_torque_b = torch.cross(effective_offset, payload_weight_b, dim=-1)
        return payload_weight_b, payload_torque_b

    def _init_payload_viz(self) -> None:
        """Create markers for payload CoG sphere and attachment->CoG bar. No-op unless
        cfg.enable_payload_viz is True."""
        self._payload_viz_markers: VisualizationMarkers | None = None
        if not getattr(self.cfg, "enable_payload_viz", False):
            return
        cfg = VisualizationMarkersCfg(
            prim_path="/Visuals/PayloadCoG",
            markers={
                "sphere": sim_utils.SphereCfg(
                    radius=1.0,
                    visual_material=sim_utils.PreviewSurfaceCfg(
                        diffuse_color=(0.9, 0.1, 0.1), opacity=0.5
                    ),
                ),
                "bar": sim_utils.CylinderCfg(
                    radius=1.0,
                    height=1.0,
                    axis="Z",
                    visual_material=sim_utils.PreviewSurfaceCfg(
                        diffuse_color=(0.7, 0.7, 0.7), opacity=0.6
                    ),
                ),
            },
        )
        self._payload_viz_markers = VisualizationMarkers(cfg)

    def _update_payload_viz(self) -> None:
        """Refresh marker translations/orientations/scales. No-op when disabled."""
        if self._payload_viz_markers is None:
            return
        gripper_idx = self._gripper_body_id[0]
        gripper_pos_w = self._robot.data.body_pos_w[:, gripper_idx, :]
        gripper_quat_w = self._robot.data.body_quat_w[:, gripper_idx, :]

        attach_w = gripper_pos_w + quat_apply(gripper_quat_w, self._payload_attachment_offset)
        cog_offset_w = quat_apply(gripper_quat_w, self._payload_cog_offset)
        cog_w = attach_w + cog_offset_w

        cfg = self.cfg
        m = self._payload_mass.clamp(min=0.0)
        mass_frac = (m / max(cfg.payload_viz_mass_ref, 1e-6)).clamp(0.0, 1.0)
        sphere_r = cfg.payload_viz_sphere_r_min + (
            cfg.payload_viz_sphere_r_max - cfg.payload_viz_sphere_r_min
        ) * mass_frac
        visible = m >= cfg.payload_viz_min_mass
        sphere_scale = torch.where(
            visible.unsqueeze(-1),
            sphere_r.unsqueeze(-1).expand(-1, 3),
            torch.zeros(self.num_envs, 3, device=self.device),
        )

        bar_len = cog_offset_w.norm(dim=-1)
        bar_visible = visible & (bar_len >= cfg.payload_viz_min_bar_len)
        bar_r = torch.full((self.num_envs,), cfg.payload_viz_bar_radius, device=self.device)
        bar_scale = torch.where(
            bar_visible.unsqueeze(-1),
            torch.stack([bar_r, bar_r, bar_len], dim=-1),
            torch.zeros(self.num_envs, 3, device=self.device),
        )
        bar_center = attach_w + 0.5 * cog_offset_w
        bar_quat = self._quat_align_z_to(cog_offset_w)

        identity_quat = torch.zeros(self.num_envs, 4, device=self.device)
        identity_quat[:, 0] = 1.0

        translations = torch.cat([cog_w, bar_center], dim=0)
        orientations = torch.cat([identity_quat, bar_quat], dim=0)
        scales = torch.cat([sphere_scale, bar_scale], dim=0)
        marker_indices = torch.cat(
            [
                torch.zeros(self.num_envs, dtype=torch.long, device=self.device),
                torch.ones(self.num_envs, dtype=torch.long, device=self.device),
            ],
            dim=0,
        )
        self._payload_viz_markers.visualize(
            translations=translations,
            orientations=orientations,
            scales=scales,
            marker_indices=marker_indices,
        )

    def _quat_align_z_to(self, v: torch.Tensor) -> torch.Tensor:
        """Quaternion (w,x,y,z) rotating +Z to direction of v. Identity when |v|~0."""
        eps = 1e-8
        norm = v.norm(dim=-1, keepdim=True)
        v_unit = v / norm.clamp(min=eps)
        z = torch.zeros_like(v)
        z[:, 2] = 1.0
        dot = (z * v_unit).sum(-1).clamp(-1.0, 1.0)
        axis = torch.cross(z, v_unit, dim=-1)
        axis_norm = axis.norm(dim=-1, keepdim=True)
        fallback_axis = torch.zeros_like(v)
        fallback_axis[:, 0] = 1.0
        axis_unit = torch.where(axis_norm > eps, axis / axis_norm.clamp(min=eps), fallback_axis)
        angle = torch.acos(dot)
        half = 0.5 * angle
        w = torch.cos(half).unsqueeze(-1)
        xyz = axis_unit * torch.sin(half).unsqueeze(-1)
        quat = torch.cat([w, xyz], dim=-1)
        small = (norm.squeeze(-1) < eps)
        identity = torch.zeros_like(quat)
        identity[:, 0] = 1.0
        quat = torch.where(small.unsqueeze(-1), identity, quat)
        return quat

    def _get_observations(self) -> dict:
        """Compute unified observation o_t (87D) and privileged p_t (24D).

        o_t = current proprioception (26D) + temporal history (55D):
            - Joint tracking: 4D x 3 steps = 12D (all hist_len steps)
            - Body tracking:  9D x 3 steps = 27D (all hist_len steps)
            - Action:         8D x 2 steps = 16D (newest hist_action_len steps)

        Returns:
            Observation dictionary with "policy" and "privileged" keys.
        """
        current_proprio = compute_policy_obs(self, self._robot)  # 26D

        if self._hist_buf is not None:
            # Joint tracking + body tracking: all steps, dims [0:13]
            jb_hist = self._hist_buf[:, :, :13].reshape(self.num_envs, -1)  # 13 * hist_len
            # Action: newest hist_action_len steps, dims [13:21]
            act_hist = self._hist_buf[:, -self._hist_action_len :, 13:].reshape(self.num_envs, -1)  # 8 * action_len
            policy_obs = torch.cat([current_proprio, jb_hist, act_hist], dim=-1)
        else:
            policy_obs = current_proprio

        # Append leaky-integrated error (3D) when enabled
        if self.cfg.use_integral_obs:
            policy_obs = torch.cat([policy_obs, self._error_integral], dim=-1)

        observations = {"policy": policy_obs}
        assert policy_obs.shape[-1] == self.cfg.observation_space, (
            f"emitted policy obs dim {policy_obs.shape[-1]} != "
            f"cfg.observation_space {self.cfg.observation_space}"
        )
        if self.cfg.state_space > 0:
            observations["privileged"] = compute_privileged_obs(self)
        return observations

    def _compute_ang_errors(self) -> None:
        """Compute roll/pitch attitude error + yaw rate error from current state."""
        roll, pitch, _ = self._euler_cache
        raw = self._ang_cmd[:, :2] - torch.stack([roll, pitch], dim=-1)
        self._att_rp_err = torch.atan2(torch.sin(raw), torch.cos(raw))
        self._yaw_rate_err = self._ang_cmd[:, 2] - self._robot.data.root_ang_vel_b[:, 2]
        self._ang_err[:, :2] = self._att_rp_err
        self._ang_err[:, 2] = self._yaw_rate_err

    def _get_rewards(self) -> torch.Tensor:
        """Compute tracking rewards and constraint costs.

        Returns:
            Reward tensor. Shape: (num_envs,).
        """
        # Linear velocity error
        self._lin_vel_err = self._vel_cmd_lin - self._robot.data.root_lin_vel_b
        # Roll/pitch attitude error + yaw rate error
        self._compute_ang_errors()

        # Update leaky-integrated error: I = leak * I + err * dt
        if self.cfg.use_integral_obs:
            self._error_integral.mul_(self.cfg.integral_leak)

            # Collect per-channel errors
            if self.cfg.integral_dims == 6:
                errs = [
                    self._att_rp_err[:, 0],  # roll
                    self._att_rp_err[:, 1],  # pitch
                    self._lin_vel_err[:, 0],  # vx
                    self._lin_vel_err[:, 1],  # vy
                    self._lin_vel_err[:, 2],  # vz
                    self._yaw_rate_err,  # yaw rate
                ]
            else:  # 3D legacy (R7)
                errs = [
                    self._att_rp_err[:, 0],  # roll
                    self._att_rp_err[:, 1],  # pitch
                    self._lin_vel_err[:, 1],  # vy only
                ]

            if self.cfg.integral_gated:
                # Error-gated: only accumulate when |error| < reward sigma.
                # Sigma tensor is pre-built in __init__ (step-invariant cfg constants).
                err_stack = torch.stack(errs, dim=-1)
                gate = (err_stack.abs() < self._integral_gate_sigmas).float()
                self._error_integral += gate * err_stack * self.step_dt
            else:
                self._error_integral += torch.stack(errs, dim=-1) * self.step_dt

            self._error_integral.clamp_(-self.cfg.integral_clamp, self.cfg.integral_clamp)

        # Update EMA bias buffer (6D ungated). Captures sustained per-env offset that
        # per-step tracking reward ignores. Consumed by bias_ema_penalty term.
        if self.cfg.reward.k_bias != 0.0:
            err6 = torch.stack(
                [
                    self._att_rp_err[:, 0],
                    self._att_rp_err[:, 1],
                    self._lin_vel_err[:, 0],
                    self._lin_vel_err[:, 1],
                    self._lin_vel_err[:, 2],
                    self._yaw_rate_err,
                ],
                dim=-1,
            )
            a = self.cfg.reward.bias_ema_alpha
            self._bias_ema = a * self._bias_ema + (1.0 - a) * err6

        reward = self._reward_manager.compute(
            robot=self._robot,
            dt=self.step_dt,
            env=self,
        )

        # Termination penalty: large one-time penalty on early termination
        if self.cfg.reward.termination_penalty != 0.0:
            reward += self.reset_terminated * self.cfg.reward.termination_penalty

        # Compute constraint costs for TRPO + IPO (if constraints configured)
        if self._constraints_cfg is not None and self._constraints_cfg.num_constraints > 0:
            self.extras["costs"] = compute_all_costs(self._robot, self, self._constraints_cfg)

        # Update previous-step velocity buffers (used by settling cost constraints).
        # Must be AFTER constraint computation so settling costs see the previous velocity.
        self._prev_root_lin_vel_b[:] = self._robot.data.root_lin_vel_b
        self._prev_root_ang_vel_z[:] = self._robot.data.root_ang_vel_b[:, 2]

        # DORAEMON: accumulate episode return for binary success criterion
        if self._doraemon is not None:
            self._episode_return_accum += reward

        return reward

    def _collect_episode_metrics(
        self,
        env_ids: torch.Tensor,
        reward_sums: dict[str, float],
    ) -> dict[str, float | torch.Tensor]:
        """Collect episode metrics for TensorBoard/WandB logging.

        Called from ``_reset_idx()`` before resetting state.
        """
        log: dict[str, float | torch.Tensor] = {}
        n = len(env_ids)
        log["_num_resets"] = float(n)

        # Reward sums (normalized by episode duration for length-independent metrics)
        total = 0.0
        for name, value in reward_sums.items():
            normalized = value / self.max_episode_length_s
            log[f"Reward/{name}"] = normalized
            total += normalized
        log["Reward/total"] = total

        self._collect_termination_metrics(log, env_ids, n)
        if n == 0:
            return log

        self._log_tracking_metrics(log, env_ids)
        self._log_action_metrics(log, env_ids)
        self._log_dynamics_metrics(log, env_ids)
        self._log_midep_metrics(log, env_ids)

        if hasattr(self.cfg, "randomization") and self.cfg.randomization.enable:
            log_dr_metrics({"log": log}, self)

        return log

    def _log_tracking_metrics(self, log: dict, env_ids: torch.Tensor) -> None:
        """Tracking errors, commands, and manipulability (2-level WandB hierarchy)."""
        # Attitude tracking (grouped in one WandB chart)
        att_err = self._att_rp_err[env_ids]
        log["Track/att/roll_err_deg"] = torch.rad2deg(att_err[:, 0]).abs().mean().item()
        log["Track/att/pitch_err_deg"] = torch.rad2deg(att_err[:, 1]).abs().mean().item()

        # Linear velocity tracking (grouped in one chart)
        lin_err = self._lin_vel_err[env_ids]
        log["Track/lin/err_x"] = lin_err[:, 0].abs().mean().item()
        log["Track/lin/err_y"] = lin_err[:, 1].abs().mean().item()
        log["Track/lin/err_z"] = lin_err[:, 2].abs().mean().item()

        # Yaw rate tracking
        log["Track/yaw/rate_err"] = self._yaw_rate_err[env_ids].abs().mean().item()

        # Command diagnostics (attitude + yaw grouped, linear grouped)
        log["Track/cmd_att/roll_deg"] = torch.rad2deg(self._ang_cmd[env_ids, 0]).abs().mean().item()
        log["Track/cmd_att/pitch_deg"] = torch.rad2deg(self._ang_cmd[env_ids, 1]).abs().mean().item()
        log["Track/cmd_att/yaw_rate"] = self._ang_cmd[env_ids, 2].abs().mean().item()
        log["Track/cmd_lin/vel_x"] = self._vel_cmd_lin[env_ids, 0].abs().mean().item()
        log["Track/cmd_lin/vel_y"] = self._vel_cmd_lin[env_ids, 1].abs().mean().item()
        log["Track/cmd_lin/vel_z"] = self._vel_cmd_lin[env_ids, 2].abs().mean().item()

        # Arm manipulability
        log["Track/arm/manip_mean"] = self._manipulability[env_ids].mean().item()
        log["Track/arm/manip_min"] = self._manipulability[env_ids].min().item()

    def _log_action_metrics(self, log: dict, env_ids: torch.Tensor) -> None:
        """Per-subsystem action diagnostics (arm 2D vs thruster 6D)."""
        actions = self._actions[env_ids]
        prev = self._prev_actions[env_ids]

        arm, arm_prev = actions[:, :2], prev[:, :2]
        log["Action/arm/norm"] = torch.linalg.norm(arm, dim=-1).mean().item()
        log["Action/arm/rate"] = torch.linalg.norm(arm - arm_prev, dim=-1).mean().item()

        thr, thr_prev = actions[:, 2:], prev[:, 2:]
        log["Action/thr/norm"] = torch.linalg.norm(thr, dim=-1).mean().item()
        log["Action/thr/rate"] = torch.linalg.norm(thr - thr_prev, dim=-1).mean().item()

    def _log_dynamics_metrics(self, log: dict, env_ids: torch.Tensor) -> None:
        """Angular velocity, joint state, actuator saturation, and thruster diagnostics."""
        ang_vel = self._robot.data.root_ang_vel_b[env_ids]
        log["Dynamics/ang_vel/rp_rms"] = ang_vel[:, :2].pow(2).mean().sqrt().item()
        log["Dynamics/ang_vel/yaw_rms"] = ang_vel[:, 2].pow(2).mean().sqrt().item()

        jids = self._albc_joint_ids
        joint_vel = self._robot.data.joint_vel[env_ids][:, jids]
        joint_pos = self._robot.data.joint_pos[env_ids][:, jids]
        log["Dynamics/joint/pos_abs"] = joint_pos.abs().mean().item()
        log["Dynamics/joint/vel_max"] = joint_vel.abs().max().item()

        effort_lim = self._robot.data.joint_effort_limits[env_ids][:, jids]
        computed = self._robot.data.computed_torque[env_ids][:, jids]
        applied = self._robot.data.applied_torque[env_ids][:, jids]
        log["Dynamics/joint/torque_max"] = applied.abs().max().item()
        log["Dynamics/joint/effort_sat"] = (computed.abs() >= effort_lim * 0.99).float().mean().item()

        vel_lim = self._robot.data.joint_vel_limits[env_ids][:, jids]
        log["Dynamics/joint/vel_sat"] = (joint_vel.abs() >= vel_lim.clamp(min=1e-6) * 0.95).float().mean().item()

        # Thruster diagnostics
        if self._thruster is not None:
            thr_abs = self._thruster.state[env_ids].abs()
            log["Dynamics/thr/util_mean"] = thr_abs.mean().item()
            log["Dynamics/thr/util_max"] = thr_abs.max().item()

    def _log_midep_metrics(self, log: dict, env_ids: torch.Tensor) -> None:
        """Mid-episode dynamics diagnostics (payload, OU current, cumulative yaw)."""
        if self.cfg.payload_toggle_steps != 0:
            log["Episode/payload_toggled"] = self._payload_toggled[env_ids].float().mean().item()
        if self.cfg.ou_enable:
            current = self._hydro.current.velocity_w[env_ids, :3]
            base = self._ou_base_current[env_ids]
            log["Episode/current_drift"] = (current - base).norm(dim=-1).mean().item()
            log["Episode/current_mag"] = current.norm(dim=-1).mean().item()

        log["Episode/cumul_yaw_deg"] = torch.rad2deg(self._cumulative_yaw[env_ids].abs()).mean().item()

    def _collect_termination_metrics(self, log: dict[str, float | torch.Tensor], env_ids: torch.Tensor, n: int) -> None:
        """Collect termination rate metrics (0.0~1.0, scale-invariant)."""

        def _term_rate(flag: torch.Tensor) -> float:
            return torch.count_nonzero(flag[env_ids]).item() / n if n > 0 else 0.0

        log["Term/terminated"] = _term_rate(self.reset_terminated)
        log["Term/time_out"] = _term_rate(self.reset_time_outs)
        log["Term/bad_state"] = _term_rate(self._term_bad_state)
        log["Term/excessive_tilt"] = _term_rate(self._term_excessive_tilt)
        # Velocity flags: computed at episode end only (not per-step)
        if n > 0:
            ang_vel_max = self._robot.data.root_ang_vel_b[env_ids].abs().max(dim=1).values
            too_fast_ang = ang_vel_max > self.cfg.max_angular_velocity
            too_fast_lin = self._robot.data.root_lin_vel_w[env_ids].norm(dim=-1) > self.cfg.max_linear_velocity
            log["Term/too_fast_ang"] = too_fast_ang.float().mean().item()
            log["Term/too_fast_lin"] = too_fast_lin.float().mean().item()

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Compute termination conditions.

        Only non-recoverable conditions trigger termination:
            1. NaN/Inf detected in root state (PhysX failure)
            2. Attitude angle exceeds max_attitude_angle (upside-down, buoyancy reversal)

        Velocity violations (angular > pi, linear > 2 m/s) are NOT terminated here.
        They are handled by soft constraints (rp_rate_cost, yaw_rate_cost) which
        provide per-step gradient. PhysX rigid body max_angular_velocity (4*pi) provides
        the hard physical clamp. Removing velocity termination eliminates the death
        spiral where early death was optimal under all-negative rewards.

        Per-condition flags are stored for diagnostics logging.
        """
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # NaN/Inf check on root state (position, quaternion, linear vel, angular vel)
        bad_state = (
            torch.isnan(self._robot.data.root_pos_w).any(dim=1)
            | torch.isnan(self._robot.data.root_quat_w).any(dim=1)
            | torch.isinf(self._robot.data.root_lin_vel_w).any(dim=1)
            | torch.isnan(self._robot.data.root_ang_vel_b).any(dim=1)
            | torch.isinf(self._robot.data.root_ang_vel_b).any(dim=1)
        )

        # Refresh euler cache (used by _get_rewards, _get_observations, constraints)
        self._euler_cache = euler_xyz_from_quat(self._robot.data.root_quat_w)
        roll, pitch, _ = self._euler_cache

        # Attitude angle check: terminate if roll or pitch exceeds limit.
        excessive_tilt = (roll.abs() > self.cfg.max_attitude_angle) | (pitch.abs() > self.cfg.max_attitude_angle)

        # Store per-condition flags for diagnostics
        self._term_bad_state = bad_state
        self._term_excessive_tilt = excessive_tilt

        terminated = bad_state | excessive_tilt
        return terminated, time_out

    def _coerce_env_ids(self, env_ids: torch.Tensor | None) -> torch.Tensor:
        """Normalize env_ids to a concrete tensor.

        Returns ALL_INDICES for None or full-batch inputs.
        """
        if env_ids is None or len(env_ids) == self.num_envs:
            return self._robot._ALL_INDICES
        return env_ids

    def _reset_idx(self, env_ids: torch.Tensor | None) -> None:
        """Reset specified environments.

        Phases:
            1. Logging and reward reset
            2. Framework reset (robot, parent class, episode jitter, action buffers)
            3. Physics reset (hydrodynamics, payload, domain randomization, ocean current)
            4. Task and state reset (attitude targets, robot pose, joint DR, error buffers)
        """
        env_ids_ = self._coerce_env_ids(env_ids)
        self._log_and_reset_rewards(env_ids_)
        self._reset_framework(env_ids_)
        self._reset_physics(env_ids_)
        self._reset_task_and_state(env_ids_)
        # Populate Euler cache from post-reset quaternion so _get_observations/_get_rewards,
        # which run before the next _get_dones, see valid roll/pitch/yaw values.
        self._euler_cache = euler_xyz_from_quat(self._robot.data.root_quat_w)

    def _log_and_reset_rewards(self, env_ids: torch.Tensor) -> None:
        """Collect episode metrics, record DORAEMON episodes, and reset accumulators."""
        # Record completed episodes to DORAEMON buffer.
        # Skip episodes with no steps (initial env.reset() produces return=0).
        # With binary success (return >= J_LB), these are naturally failures (0),
        # not fake successes, but filtering them avoids wasting buffer space.
        if self._doraemon is not None and len(env_ids) > 0:
            valid = self.episode_length_buf[env_ids] > 0
            valid_ids = env_ids[valid]
            if valid_ids.numel() > 0:
                returns = self._episode_return_accum[valid_ids]
                success = (returns >= self._doraemon.cfg.performance_lb).float()
                self._doraemon.record_episodes(
                    xi=self._episode_dr_xi[valid_ids],
                    returns=returns,
                    success=success,
                    log_probs=self._episode_dr_log_probs[valid_ids],
                )

        reward_sums = self._reward_manager.reset(env_ids)
        self.extras["log"] = self._collect_episode_metrics(env_ids, reward_sums)

    def _reset_framework(self, env_ids: torch.Tensor) -> None:
        """Reset robot, parent class, jitter episode lengths, and zero action buffers."""
        self._robot.reset(env_ids)
        super()._reset_idx(env_ids)

        # Randomize episode lengths to decorrelate environment terminations
        if len(env_ids) == self.num_envs:
            # Full batch (initial reset): spread across 0~50% of episode range.
            # This decorrelates terminations while ensuring every env collects
            # at least half an episode of meaningful experience.
            half_ep = max(1, int(self.max_episode_length * 0.5))
            self.episode_length_buf[:] = torch.randint_like(self.episode_length_buf, high=half_ep)
        else:
            # Individual resets: small jitter prevents re-synchronization
            max_jitter = max(1, int(self.max_episode_length * 0.1))
            self.episode_length_buf[env_ids] = torch.randint_like(self.episode_length_buf[env_ids], high=max_jitter)

        self._reset_action_buffers(env_ids)

    def _reset_action_buffers(self, env_ids: torch.Tensor) -> None:
        """Reset action buffers, temporal history, and cumulative yaw."""
        for buf in (self._actions, self._prev_actions, self._prev_prev_actions):
            buf[env_ids] = 0.0
        self._joint_pos_targets[env_ids] = self._robot.data.joint_pos[env_ids][:, self._albc_joint_ids]
        if self._hist_buf is not None:
            self._hist_buf[env_ids] = 0.0
            self._hist_step_counter[env_ids] = 0

        # Reset cumulative yaw tracking
        self._cumulative_yaw[env_ids] = 0.0
        _, _, yaw = euler_xyz_from_quat(self._robot.data.root_quat_w)
        self._prev_yaw[env_ids] = yaw[env_ids]

        # Reset previous-step velocity buffers (settling cost constraints)
        self._prev_root_lin_vel_b[env_ids] = self._robot.data.root_lin_vel_b[env_ids]
        self._prev_root_ang_vel_z[env_ids] = self._robot.data.root_ang_vel_b[env_ids, 2]

        # Reset mid-episode payload toggle state
        self._payload_toggle_counter[env_ids] = 0
        self._payload_toggled[env_ids] = False

    def _reset_physics(self, env_ids: torch.Tensor) -> None:
        """Reset hydrodynamics, thrusters, payload, and apply domain randomization."""
        self._hydro.reset(env_ids)
        self._buoy_hydro.reset(env_ids)
        if self._thruster is not None:
            self._thruster.reset(env_ids)

        self._payload_mass[env_ids] = self.cfg.payload_mass
        offset = torch.tensor(self.cfg.payload_attachment_offset, device=self.device, dtype=torch.float32)
        self._payload_attachment_offset[env_ids] = offset
        self._payload_cog_offset[env_ids] = 0.0

        rand_cfg = self.cfg.randomization
        if not rand_cfg.enable:
            # Non-DR path: setup mid-episode dynamics with default values
            self._setup_payload_toggle(env_ids)
            if self.cfg.ou_enable:
                self._ou_base_current[env_ids] = self._hydro.current.velocity_w[env_ids, :3].clone()
            return

        # Create DRSampler (bundles rand_cfg + num_envs + device)
        dr = DRSampler(rand_cfg, num_envs=len(env_ids), device=self.device)
        # Store for _reset_task_and_state (joint gains/friction)
        self._current_dr_sampler = dr

        # DORAEMON: sample from Beta distribution for curriculum-managed parameters
        sampled: dict[str, torch.Tensor] | None = None
        if self._doraemon is not None:
            n = len(env_ids)
            xi_physical, log_probs = self._doraemon.sample(n)
            sampled = {spec.name: xi_physical[:, i] for i, spec in enumerate(self._doraemon.dist.params)}
            self._episode_dr_xi[env_ids] = xi_physical
            self._episode_dr_log_probs[env_ids] = log_probs
            self._episode_return_accum[env_ids] = 0.0

            # Command scales fixed at 1.0 (not DORAEMON-managed).
            # DORAEMON optimizes physics DR only; command difficulty is a task knob.

        randomize_hydrodynamics(env=self, env_ids=env_ids, dr=dr, sampled=sampled)
        randomize_body_mass(env=self, env_ids=env_ids, dr=dr, sampled=sampled)
        randomize_payload(env=self, env_ids=env_ids, dr=dr, sampled=sampled)

        if self._has_ocean_current:
            randomize_ocean_current(env=self, env_ids=env_ids, sampled=sampled)

        # Mid-episode dynamics setup with DR'd values (once, after randomization)
        self._setup_payload_toggle(env_ids)
        if self.cfg.ou_enable:
            self._ou_base_current[env_ids] = self._hydro.current.velocity_w[env_ids, :3].clone()

        if self._thruster is not None:
            self._thruster.randomize_parameters(
                env_ids=env_ids,
                thrust_coeff_scale=rand_cfg.thrust_coefficient_scale,
                time_constant_scale=rand_cfg.time_constant_scale,
            )

    def _reset_task_and_state(self, env_ids: torch.Tensor) -> None:
        """Reset robot pose, joint DR, and velocity commands."""
        rand_cfg = self.cfg.randomization
        # Always reset to origin (no pose DR): position=(0,0,0), orientation=identity
        reset_robot_pose_default(env=self, env_ids=env_ids)

        # Joint initialization: random or default
        if rand_cfg.enable:
            randomize_joint_positions(env=self, env_ids=env_ids, joint_pos_range=self.cfg.initial_joint_pos_range)
        else:
            reset_joint_positions_default(env=self, env_ids=env_ids)

        # Joint actuator DR: only when DR enabled.
        # TDC envs override stiffness/damping in their own _reset_idx().
        if rand_cfg.enable:
            assert self._current_dr_sampler is not None, (
                "_reset_physics must run before _reset_task_and_state when DR is enabled"
            )
            dr = self._current_dr_sampler
            randomize_joint_gains(env=self, env_ids=env_ids, dr=dr)
            randomize_joint_effort_limit(env=self, env_ids=env_ids, dr=dr)
            randomize_joint_friction(env=self, env_ids=env_ids, dr=dr)
            self._current_dr_sampler = None  # Clear after use

        # Sample commands
        self._sample_velocity_command(env_ids)

        # Initialize errors
        self._lin_vel_err[env_ids] = self._vel_cmd_lin[env_ids] - self._robot.data.root_lin_vel_b[env_ids]
        roll_r, pitch_r, _ = euler_xyz_from_quat(self._robot.data.root_quat_w[env_ids])
        raw = self._ang_cmd[env_ids, :2] - torch.stack([roll_r, pitch_r], dim=-1)
        self._att_rp_err[env_ids] = torch.atan2(torch.sin(raw), torch.cos(raw))
        self._yaw_rate_err[env_ids] = self._ang_cmd[env_ids, 2] - self._robot.data.root_ang_vel_b[env_ids, 2]
        self._ang_err[env_ids, :2] = self._att_rp_err[env_ids]
        self._ang_err[env_ids, 2] = self._yaw_rate_err[env_ids]
        # Reset integral error on episode reset
        self._error_integral[env_ids] = 0.0
        self._bias_ema[env_ids] = 0.0

    # ------------------------------------------------------------------
    # Play-mode evaluation
    # ------------------------------------------------------------------

    def randomize_physics_mid_episode(self, env_ids: torch.Tensor | None = None) -> None:
        """Re-sample physics DR parameters without resetting motion state.

        Used by eval_dr_switching.py: holds robot pose/velocity constant while
        changing hydro/mass/payload/ocean/thruster params. Joint gains/friction
        intentionally left unchanged (mid-episode actuator change destabilizes
        control, not meaningful for policy-adaptation benchmark).
        """
        if env_ids is None:
            env_ids = torch.arange(self.num_envs, device=self.device)

        rand_cfg = self.cfg.randomization
        if not rand_cfg.enable:
            return

        dr = DRSampler(rand_cfg, num_envs=len(env_ids), device=self.device)

        sampled: dict[str, torch.Tensor] | None = None
        if self._doraemon is not None:
            n = len(env_ids)
            xi_physical, _ = self._doraemon.sample(n)
            sampled = {spec.name: xi_physical[:, i] for i, spec in enumerate(self._doraemon.dist.params)}

        randomize_hydrodynamics(env=self, env_ids=env_ids, dr=dr, sampled=sampled)
        randomize_body_mass(env=self, env_ids=env_ids, dr=dr, sampled=sampled)
        randomize_payload(env=self, env_ids=env_ids, dr=dr, sampled=sampled)

        if self._has_ocean_current:
            randomize_ocean_current(env=self, env_ids=env_ids, sampled=sampled)
            if self.cfg.ou_enable:
                self._ou_base_current[env_ids] = self._hydro.current.velocity_w[env_ids, :3].clone()

        if self._thruster is not None:
            self._thruster.randomize_parameters(
                env_ids=env_ids,
                thrust_coeff_scale=rand_cfg.thrust_coefficient_scale,
                time_constant_scale=rand_cfg.time_constant_scale,
            )

    def get_eval_snapshot(self) -> dict[str, float]:
        """Return current evaluation metrics for play-mode diagnostics.

        Provides instantaneous per-env averages of key quantities for
        periodic printing during play.py inference.

        Returns:
            Dict with keys: attitude_error_deg, lin_vel_error, action_rate,
            angular_velocity_rp_rms, angular_velocity_yaw_rms,
            thruster_utilization, joint_pos_mean_abs.
        """
        da = self._actions - self._prev_actions
        thr_util = self._thruster.state.abs().mean().item() if self._thruster is not None else 0.0

        return {
            "attitude_error_deg": torch.rad2deg(torch.linalg.norm(self._att_rp_err, dim=-1)).mean().item(),
            "lin_vel_error": self._lin_vel_err.norm(dim=-1).mean().item(),
            "action_rate": torch.linalg.norm(da, dim=-1).mean().item(),
            "angular_velocity_rp_rms": self._robot.data.root_ang_vel_b[:, :2].pow(2).mean().sqrt().item(),
            "angular_velocity_yaw_rms": self._robot.data.root_ang_vel_b[:, 2].pow(2).mean().sqrt().item(),
            "thruster_utilization": thr_util,
            "joint_pos_mean_abs": self._robot.data.joint_pos[:, self._albc_joint_ids].abs().mean().item(),
        }
