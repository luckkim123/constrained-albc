# Full-DOF ALBC Sim-to-Real Deployment Guide

## Purpose

This document defines the procedure for deploying the ConstraintTRPO + Asymmetric Encoder policy trained in the `constrained_full_albc` project to actual UUV (Hero Agent-based) hardware. The main target task is `Isaac-FullDOF-TRPO-v0`.

This guide is based on the following experimental results:
- `r13a_layernorm` experiment (2026-04-21): replacing `EmpiricalNormalization` → `LayerNorm` gave reward -33%, yaw ss_error +1975%. **The actor obs-input LayerNorm destroys the relative scale across channels, so it must not be used as a deployment normalizer**.
- Relevant literature (Engstrom-Ilyas 2020, Andrychowicz 2020, HORA, RMA, RLPD): running stats + freeze is the standard practice for RL sim-to-real.

## Architecture Overview

Deployment target components:
- **Actor network**: `ActorCriticEncoder.actor` — MLP [256, 128, 64], input = 87D policy obs (based on hist_len=3), output = 8D action (mean).
- **Actor obs normalizer**: `EmpiricalNormalization(87)` — running `_mean`/`_std`/`count` buffers. Frozen at the end of training.
- **Encoder**: **excluded from deployment**. During training, the teacher provides context via privileged obs (23D). Since a student/adapter is absent, the deployed actor does not depend on the encoder latent (in the current r13a configuration, the encoder z is concatenated to the actor input, but at deployment there is no teacher privileged obs, so a replacement is needed — see Stage 2 for details).
- **Critic**: **excluded from deployment**. For training.

**Important**: the actor in the current `constrained_full_albc` may have a structure that does not operate without the latent z (9D) provided by the encoder. Before deploying, be sure to check the `actor_obs` composition in `actor_critic_encoder.py`, and if z is required:
(a) since privileged obs cannot be approximated on the real robot, a student/adapter module must be trained separately (HORA/RMA Phase 2 approach), or
(b) an ablation run in which z is excluded from the actor input must be performed first.

## Deployment Procedure

### Stage 1. Model Export

Immediately after training ends, extract the deployment bundle from the checkpoint.

```python
import torch

# At the end of training (modify scripts/reinforcement_learning/rsl_rl/train.py or use a separate script)
runner.alg.actor_critic.eval()   # disable EmpiricalNormalization.update()

export_bundle = {
    "state_dict": runner.alg.actor_critic.state_dict(),
    "obs_spec": {
        "dim": 87,
        "hist_len": 3,
        "hist_stride": 3,
        "hist_action_len": 2,
        "channel_layout": [
            # Copy the order from the config.py:_OBS_NOISE_STD comment verbatim
            ("cmd_lin", 3), ("cmd_ang", 3),
            ("euler", 3), ("ang_vel", 3), ("lin_vel", 3),
            ("joint_pos", 2), ("joint_vel", 2), ("manip", 1),
            ("thruster_state", 6),
            ("joint_hist", 12),      # (jp_err 2 + jv 2) * 3
            ("body_hist", 27),       # (lv_err 3 + ang_err 3 + rpy 3) * 3
            ("action_hist", 16),     # 8 * 2
            ("integral", 6),
        ],
    },
    "action_spec": {"dim": 8, "range": [-1.0, 1.0], "control_rate_hz": 50},
    "dr_train_range": {  # for comparison with real-robot measurements
        "payload_mass": (0.5, 2.5),
        "payload_cog_xy": 0.08,
        "buoyancy_force": (85, 95),
        "ocean_current_max": (0.5, 0.5, 0.25),
        # ... copy the HardDR values from config.randomization
    },
    "git_sha": subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip(),
    "checkpoint_path": resume_path,
}
torch.save(export_bundle, "deploy_model.pt")
```

### Stage 1 Verification

Validate the deployment bundle:

```python
# 1. Check that EmpNorm was actually trained
em = bundle["state_dict"]["actor_obs_normalizer._mean"]
assert em.abs().sum() > 0.01, "EmpNorm _mean is zero - not updated during training"

es = bundle["state_dict"]["actor_obs_normalizer._std"]
assert es.min() > 0.1 and es.max() < 100, "EmpNorm _std out of expected range"
assert (es == 1.0).sum() < 5, "EmpNorm _std mostly unchanged - update not fired"

# 2. Check that the state_dict includes all policy/encoder/normalizer buffers
assert "actor_obs_normalizer._mean" in bundle["state_dict"]
assert "actor_obs_normalizer._std" in bundle["state_dict"]
assert "actor_obs_normalizer.count" in bundle["state_dict"]
```

Analysis tool: use `scripts/analysis/encoder_tools.py debug` to check the per-channel `_mean`/`_std` values. Channels with extreme values (e.g., `_std < 0.01` or `> 10`) mean that obs dim is nearly constant or diverging — suspect a training problem.

### Stage 2. Real-Robot Obs Pipeline

**95% of sim-real failures occur at this stage**. The **exactly identical** 87D vector as `albc_env._get_observations()` must be reconstructed on the real robot.

#### Checklist — Obs reproduction accuracy

| Item | Check |
|------|------|
| Channel order | 1:1 match with `obs_spec.channel_layout` |
| Body-frame vs World-frame | `ang_vel`, `lin_vel` are body-frame (see config.py) |
| Quaternion → Euler conversion | `euler_xyz_from_quat` convention (roll→pitch→yaw) |
| Angle wrapping | `euler` range [-π, π] |
| Unit | joint_pos rad, joint_vel rad/s, lin_vel m/s, ang_vel rad/s |
| Command scaling | cmd_lin, cmd_ang use the same normalization range as training (check `config.cmd_lin_max`, `cmd_ang_max`) |
| Joint direction convention | Sign match between the robot MDH convention and the sim URDF convention |
| Thruster state definition | Unit match between the sim thruster model output (`self._thruster.state.abs()`) and the real-robot ESC feedback |
| History ring buffer | hist_stride=3 (sample every 3 physics steps), hist_len=3 (keep the most recent 3 samples) |
| Action history order | Check the config implementation for whether the most recent is at the front or back |
| Integral error | 0 at episode reset, identical `_bias_ema` decay coefficient |
| Control rate | 50Hz (control_decimation=4 × physics_dt=0.005) |

#### Recommendation: Shared Obs Construction Code

If the real-robot control code is implemented separately from the sim, the probability of drift increases sharply. It is recommended to separate the `albc_env._build_obs()` logic into a **utility function that does not depend on Isaac Sim**, so that the real robot imports the same function.

```
source/isaaclab_tasks/.../constrained_full_albc/obs_builder.py  (new)
  def build_obs_vector(
      proprio: ProprioState,     # dataclass shared by real robot/sim
      history: HistoryBuffer,    # ring buffer (hist_len x per-step features)
      commands: CommandState,    # cmd_lin, cmd_ang
      integral: torch.Tensor,    # 6D
  ) -> torch.Tensor:             # (batch, 87)
      ...
```

Share this function between the sim side (`albc_env._get_observations()`) and the real-robot ROS node.

### Stage 3. EmpNorm Offline Recalibration

If the difference between the sim training stats and the real-robot distribution is large, the policy input is distorted. Just before deployment, collect calibration data on the real robot and recompute `_mean`/`_std`.

#### Procedure

1. Enter the robot into **safe idle mode** (neutral thrust, arm hold). Tether or shallow tank.
2. **Zero-command**: keep cmd_lin = 0, cmd_ang = 0.
3. **Weak disturbance**: the operator applies a weak current in the tank or gently pushes the robot by hand (0.1 m/s or less). Within the range covered by sim DR.
4. **Obs collection**: 180 s × 50Hz = 9000 samples, recording only obs **without running** the policy.
5. **Recompute + overwrite stats**:

```python
import torch

real_obs = torch.tensor(collected_obs_batch)  # (9000, 87)

sim_mean = model.actor_obs_normalizer._mean.clone()
sim_std = model.actor_obs_normalizer._std.clone()

real_mean = real_obs.mean(dim=0, keepdim=True).unsqueeze(0)
real_std = real_obs.std(dim=0, keepdim=True).unsqueeze(0)

# Drift analysis — check the per-channel ratio
ratio_mean = (real_mean - sim_mean).abs() / (sim_std + 1e-3)
ratio_std = real_std / sim_std
print("Channels with |real_mean - sim_mean| > 2 sim_std:", (ratio_mean > 2).sum().item())
print("Channels with real_std / sim_std > 3:", (ratio_std > 3).sum().item())

# Acceptance criterion: the sim ↔ real std ratio must be between 0.3 and 3 to judge that the DR range covers the real robot
if (ratio_std < 0.3).any() or (ratio_std > 3).any():
    raise RuntimeError("DR range insufficient — retrain with wider DR before deploy")

# Overwrite
model.actor_obs_normalizer._mean.copy_(real_mean)
model.actor_obs_normalizer._std.copy_(real_std)
model.actor_obs_normalizer._var.copy_(real_std ** 2)
# count can be left as is (in eval mode it is not updated)
```

#### Acceptance Criteria

- Per channel, `|real_mean - sim_mean| < 2 * sim_std`
- `0.3 < real_std / sim_std < 3.0`
- 80% or more of the channels satisfy the above conditions

If there are channels that fail the conditions, sensor calibration of that channel or redesign of the DR range is required.

Note: `stable-baselines3`'s `VecNormalize.load_running_average()` follows the same pattern.

### Stage 4. Safety Layer

Multi-layered safety devices on the policy output and obs pipeline.

#### Obs Safety

```python
# Clipping after normalization (defense against sensor dropout/outliers)
normalized = (raw_obs - mean) / (std + eps)
normalized = torch.clamp(normalized, -5.0, 5.0)

# Stale obs detection
if time.time() - last_obs_ts > 0.1:  # exceeds 100ms
    return neutral_action
```

#### Action Safety

```python
# Action rate limit (70% of the max action rate allowed in sim)
ACTION_RATE_MAX = 0.5   # per 20ms step (based on the sim rate limit)
action = policy(normalized_obs).mean  # not stochastic, eval mode
action = torch.clamp(action, -1.0, 1.0)
delta = action - prev_action
delta = torch.clamp(delta, -ACTION_RATE_MAX, ACTION_RATE_MAX)
action = prev_action + delta

# Low-pass filter (suppress jitter)
action = 0.85 * action + 0.15 * prev_action
```

#### Watchdog

```python
# |action| > 0.95 for 5 consecutive steps → persistent thruster saturation → unsafe
saturation_count = saturation_count + 1 if action.abs().max() > 0.95 else 0
if saturation_count > 5:
    enter_safe_mode()  # neutral thrust, arm hold
```

#### DR Limit Monitor

If a real-robot-measured environment parameter (payload mass, buoyancy, etc.) is outside the sim DR range, warn the human operator. Halt mission progress until the user explicitly acks.

### Stage 5. Staged Rollout

Stage-by-stage validation. Each stage's acceptance criteria must pass before proceeding to the next.

| Stage | Environment | Cmd Envelope | Thruster cap | Duration | Pass Criteria |
|-------|------|--------------|---------------|----------|---------------|
| 5.1 Tethered hover | Tank, tether fixed | cmd = 0 | 50% | 30 min | pos drift < 0.1 m, att drift < 5° (free floating) |
| 5.2 Shallow tank | Tank, tether retained | att setpoint, lv = 0.1 m/s | 70% | 1 h | trajectory RMSE < 2x vs sim eval_dr soft level |
| 5.3 Progressive cmd | Tank | lv 0.1→0.5 m/s, yaw_rate 0→0.5 rad/s stepwise | 90% | 2 h | At each cmd level, ss_error is similar to the sim medium DR level |
| 5.4 Open water | Open sea | Mission cmd | 100% | Per mission | Passes the pre-mission safety checklist |

At each stage, replay the **real-robot trajectory log** in sim (`scripts/analysis/replay_realworld.py` needs to be newly created) — the difference between the sim and real-robot responses is a quantitative metric of the sim2real residual.

### Stage 5 Pre-flight Checklist (Stage 5.4 Open Water)

- [ ] `deploy_model.pt` git_sha matches the latest training run
- [ ] `obs_spec.channel_layout` diffed against the real-robot code
- [ ] EmpNorm stats recalibrated in Stage 3
- [ ] Battery > 80%
- [ ] Tether/surface buoy prepared
- [ ] GCS communication triple-redundancy confirmed
- [ ] E-stop accessible
- [ ] Safety watchdog threshold settings acked
- [ ] DR limit monitor enabled
- [ ] Logging: record all of raw_obs, normalized_obs, action, timestamp, sim_time_lag

## Troubleshooting

### Symptom: oscillation / jitter on the real robot

| Cause | Diagnosis | Remedy |
|------|------|------|
| EmpNorm stats mismatch | Check per-channel `real_std / sim_std` | Re-run Stage 3 recalibration |
| Control rate mismatch | Measure whether the real-robot loop is not 50Hz | Check dt consistency |
| Insufficient action low-pass | Measure action rate | Adjust filter α (0.8 → 0.9) |
| Sim DR does not cover the real robot | DR Limit Monitor warning | Widen DR range and retrain |

### Symptom: persistent pos drift on the real robot

| Cause | Diagnosis | Remedy |
|------|------|------|
| Integral saturation | Check the integral obs dim value | Add integral clamp |
| cmd scaling error | Check whether the sim cmd and real-robot cmd are in the same range | Re-match cmd normalization |
| Buoyancy mismatch | Real-robot-measured buoyancy vs sim default | Adjust payload or retrain DR |

### Symptom: only a specific axis worsens (e.g., yaw)

In the literature, yaw was most sensitive in the LayerNorm replacement experiment — first re-examine the scale/sign of that axis's obs channels (ang_vel[2], ang_err_hist[2 of 9]).

## References

- Engstrom L, Ilyas A et al. 2020. "Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO". arxiv:2005.12729.
- Andrychowicz M et al. 2020. "What Matters In On-Policy RL? A Large-Scale Empirical Study". arxiv:2006.05990.
- Kumar A, Fu Z, Pathak D, Malik J. 2021. "RMA: Rapid Motor Adaptation for Legged Robots". RSS. arxiv:2107.04034.
- Qi H, Kumar A et al. 2022. "In-Hand Object Rotation via Rapid Motor Adaptation". CoRL. arxiv:2210.04887.
- Ball P, Smith L, Kostrikov I, Levine S. 2023. "Efficient Online Reinforcement Learning with Offline Data (RLPD)". ICML. arxiv:2302.02948.
- Chaffre T et al. 2025. "Sim-to-real transfer of adaptive control parameters for AUV stabilisation under current disturbance". IJRR.
- Muratore F et al. 2022. "Robot Learning From Randomized Simulations: A Review". Frontiers in Robotics and AI.
- Coholich J. "A Bag of Tricks for Deep Reinforcement Learning". (practitioner guide)

## Related Internal Docs

- [system-overview.md](../explanation/system-overview.md) — Overall system structure + algorithm
- [reward-design.md](../explanation/reward-design.md) — reward structure
- [experiments-archive.md](../reference/experiments-archive.md) — Related experiment records

## Changelog

- 2026-04-21: Initial draft. Reflects the failure results of the r13a_layernorm (2026-04-21) experiment and the literature survey.
