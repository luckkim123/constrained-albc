# Reward Functions

> **Status**: 2026-02-28 | **Source**: `mdp/rewards.py`, `config.py`
>
> Mathematical analysis, design rationale, and measured values for the Hero Agent ALBC reward function.
> Multi-scale gradient structure: Gaussian tracking + settling + linear error + regularization penalties.

---

## Overview

The reward of the Hero Agent ALBC environment consists of a weighted sum of 6 terms:

$$r_t = \underbrace{w_1 \cdot e^{-\phi_t^2 / \sigma^2} \cdot \Delta t}_{\text{tracking}} + \underbrace{w_2 \cdot \text{settling}(\phi_t) \cdot \Delta t}_{\text{settling}} + \underbrace{w_3 \cdot \text{PBRS}(\phi)}_{\text{progress}} + \underbrace{w_4 \cdot \text{hf}^2 \cdot \Delta t}_{\text{joint osc.}} + \underbrace{w_5 \cdot \|\dot\gamma\|^2 \cdot \Delta t}_{\text{joint vel.}} + \underbrace{w_7 \cdot \text{lin\_err}(\phi_t) \cdot \Delta t}_{\text{linear err.}}$$

Here $\phi_t = \|\mathbf{e}_t^{rp}\|_2$ (L2 norm of the roll/pitch error), $\Delta t$ = step_dt, and $\sigma$ = tracking sigma.

### Configuration

| Symbol | ALBCRewardCfg (Base RL) | Description |
|:---|:---|:---|
| $w_1$ | 5.0 | `tracking_weight` |
| $\sigma$ | 0.35 rad | `tracking_sigma` (~20.1 deg 1/e point) |
| $w_2$ | 3.0 | `settling_weight` |
| $\theta_{thr}$ | 0.175 rad | `settling_threshold` (~10 deg) |
| $k$ | 20.0 | `settling_sharpness` (1/rad) |
| $w_3$ | 0.3 | `progress_weight` (NOT dt-scaled) |
| $w_4$ | -2.5 | `joint_oscillation_weight` |
| $w_5$ | -1.0 | `joint_velocity_weight` |
| $w_6$ | 0.0 | `angular_velocity_weight` (disabled) |
| $w_7$ | -1.0 | `linear_error_weight` |
| max_err | 1.0 rad | `linear_error_max` (~57 deg) |
| curriculum ratio | 0.5 | `penalty_curriculum_ratio` |
| $\Delta t$ | 0.005 | `step_dt` (decimation=1, sim dt=0.005) |

**Source**: `mdp/rewards.py` (`ALBCRewardCfg`), `config.py`

### Design Principles

1. **Multi-scale gradient structure**: a 3-stage gradient covers the entire error range.
   - 0-10 deg: settling (sharpness=20, weight=3.0, near-target attraction)
   - 5-25 deg: tracking sigma=0.35 (main correction range, strengthened gradient)
   - 25 deg+: linear_error (constant gradient, tail coverage)
2. **Passive equilibrium prevention**: at sigma=0.35, "do nothing" tracking = 5.0*0.367 = 1.83. Improvement margin 5.0 - 1.83 = 3.17 (a 2.28x increase over the 1.39 of sigma=0.5/w=3.0).
3. **Gaussian kernel normalization**: the $e^{-\phi^2/\sigma^2}$ form is naturally bounded to [0, 1]. The weight interpretation is intuitive.
4. **dt-scaling rule**: terms measuring "instantaneous state quality" -> dt-scaled, while progress (PBRS) is based on state transition and is therefore NOT dt-scaled.
5. **Penalty curriculum**: all negative-weight terms (including linear_error) increase linearly from 0->1. Initial exploration is guaranteed, followed by gradual regularization.
6. **PBRS (Ng 1999)**: potential-based reward shaping preserves the optimal policy.

---

## Potential: Definition and Computation

### Attitude Error

The Euler angles $(\phi_r, \phi_p, \phi_y)$ are extracted from the robot's current quaternion $\mathbf{q}$, and the difference from the target attitude $(\phi_r^*, \phi_p^*, \phi_y^*)$ is computed:

$$\mathbf{e}_t = \text{atan2}\!\big(\sin(\boldsymbol{\phi}^* - \boldsymbol{\phi}_t),\; \cos(\boldsymbol{\phi}^* - \boldsymbol{\phi}_t)\big) \in [-\pi, \pi]^3$$

The `atan2(sin, cos)` wrapping ensures the angle difference is always within the $[-\pi, \pi]$ range.

**Source**: `base_env.py` (`compute_error`)

### Target Attitude Randomization

The target attitude $\boldsymbol{\phi}^*$ is randomized per episode according to the environment configuration:

| Config | `randomize_target_attitude` | Behavior |
|:---|:---|:---|
| `ALBCEnvCfg` (debug, DR off) | `False` | Fixed $(0, 0, 0)$ |
| `ALBCTrainEnvCfg` (training, DR on) | `True` | Random per episode |

When randomized, uniform sampling is performed over the `target_attitude_range = (0.5, 0.5, 0.0)` range:

$$\phi_r^* \in [-0.5, +0.5] \text{ rad} \;(\approx \pm28\degree), \quad \phi_p^* \in [-0.5, +0.5] \text{ rad}, \quad \phi_y^* = 0$$

The yaw target is always fixed at 0 (range=0.0).

**Source**: `base_env.py` (`reset_targets`), `config.py`

### Potential Value

The potential is the L2 norm of **only the roll and pitch components** of the attitude error:

$$\phi_t = \|\mathbf{e}_t^{rp}\|_2 = \sqrt{e_{roll}^2 + e_{pitch}^2}$$

**Reason for excluding yaw**: ALBC generates roll/pitch torque by adjusting the position of the buoy. Since it is structurally unable to produce Z-axis (yaw) torque, including yaw in the reward would amount to imposing an unsolvable task.

**Source**: `base_env.py` (`update_potentials`)

### Update Timing

On every step, `update_potentials()` is called exactly once upon entering `_get_rewards()`:

```python
def update_potentials(self, quat: torch.Tensor) -> None:
    self._prev_potentials = self._potentials.clone()
    self._attitude_error = self.compute_error(quat)
    self._potentials = torch.linalg.norm(self._attitude_error[:, :2], dim=-1)
```

### Initialization on Reset

Immediately after an episode reset, `initialize_potentials()` is called:

$$\phi_0 = \phi_{-1} = \|\mathbf{e}_0^{rp}\|_2$$

By setting the two values equal, the PBRS progress returns 0 immediately after reset.

---

## Individual Reward Terms

### Term 1: Tracking Reward (Gaussian Kernel)

$$r_{tracking} = e^{-\phi_t^2 / \sigma^2}, \quad \sigma = 0.35 \text{ rad}, \quad w = 5.0$$

**Source**: `mdp/rewards.py` (`tracking_reward`)

| $\phi_t$ (error) | $e^{-\phi_t^2/\sigma^2}$ | dt-scaled | weighted |
|:---|:---|:---|:---|
| 0.0 (perfect) | 1.0000 | 0.00500 | 0.02500 |
| 0.035 (~2 deg) | 0.9900 | 0.00495 | 0.02475 |
| 0.087 (~5 deg) | 0.9401 | 0.00470 | 0.02350 |
| 0.175 (~10 deg) | 0.7788 | 0.00389 | 0.01947 |
| 0.262 (~15 deg) | 0.5698 | 0.00285 | 0.01425 |
| 0.349 (~20 deg) | 0.3697 | 0.00185 | 0.00924 |
| 0.524 (~30 deg) | 0.1063 | 0.00053 | 0.00266 |
| 0.700 (~40 deg) | 0.0183 | 0.00009 | 0.00046 |

$\sigma = 0.35$ rad provides a strong gradient in the 5-25 deg range. Even at 30 deg it is 0.106 (a valid signal is retained). Above 40 deg, linear_error compensates.

**"Do nothing" analysis**: over the initialization ±30 deg range, the average tracking = $5.0 \times 0.367 = 1.83$. The improvement margin 5.0 - 1.83 = 3.17 (a 2.28x increase over the 1.39 of sigma=0.5/w=3.0) strongly prevents convergence to a passive equilibrium.

### Term 2: Settling Bonus (Sigmoid)

$$r_{settling} = \sigma(k \cdot (\theta_{thr} - \phi_t)), \quad k = 60, \; \theta_{thr} = 0.035 \text{ rad}, \quad w = 2.0$$

**Source**: `mdp/rewards.py` (`settling_bonus`)

| $\phi_t$ (error) | settling | dt-scaled | weighted |
|:---|:---|:---|:---|
| 0.0 (perfect) | 0.8909 | 0.00445 | 0.00891 |
| 0.017 (~1 deg) | 0.7311 | 0.00366 | 0.00731 |
| 0.035 (threshold) | 0.5000 | 0.00250 | 0.00500 |
| 0.052 (~3 deg) | 0.2689 | 0.00134 | 0.00269 |
| 0.070 (~4 deg) | 0.1091 | 0.00055 | 0.00109 |
| 0.10 (~5.7 deg) | 0.0180 | 0.00009 | 0.00018 |

Since sigma=0.5 tracking covers 5-30 deg, settling focuses on precise control in the 0-4 deg range. At sharpness=60, the max gradient near 2 deg = 60/4 = 15.0 (twice the previous 30/4 = 7.5).

### Term 3: Progress Reward (PBRS)

$$r_{progress} = \phi_{t-1} - \gamma \cdot \phi_t, \quad \gamma = 0.99, \quad w = 0.3$$

**Source**: `mdp/rewards.py` (`progress_reward_pbrs`)

Ng et al. (1999) potential-based reward shaping preserves the optimal policy. NOT dt-scaled. $\gamma$ must match the PPO discount factor (`ALBCRewardCfg.progress_gamma`).

Provides positive reward when the error decreases:
- $\phi_{t-1} = 0.30, \; \phi_t = 0.28$: $r = 0.30 - 0.99 \cdot 0.28 = 0.0228 \to w \cdot r = 0.0068$
- When the error increases, it switches to negative, providing a natural gradient.

It can be safely used even in an off-policy (SAC) replay buffer. An alternative is `progress_reward` (tanh-based), but PBRS has stronger theoretical guarantees.

### Term 4: Joint Oscillation Penalty (EMA High-Pass)

$$r_{osc} = \text{mean}((\dot{\gamma} - \text{EMA}(\dot{\gamma}))^2), \quad \alpha_{EMA} = 0.2, \quad w = -2.5$$

**Source**: `mdp/rewards.py` (`joint_oscillation_penalty`)

The EMA tracks the low-frequency component, and the difference (high-frequency residual) is imposed as a squared penalty. It allows smooth motion while selectively suppressing only high-frequency oscillation.

$\alpha = 0.2$ corresponds to approximately a 1.6Hz cutoff at the 50Hz control frequency.

### Term 5: Joint Velocity Penalty

$$r_{vel} = \text{mean}(\dot\gamma^2), \quad w = -1.0$$

**Source**: `mdp/rewards.py` (`joint_velocity_penalty`)

A mean-squared penalty on joint velocity. By suppressing fast joint motion, it improves control stability and energy efficiency. Unlike joint oscillation (high-frequency only), it penalizes all joint velocity.

### Term 6: Angular Velocity Penalty

$$r_{angvel} = \sum_{i \in \{p, q\}} \omega_i^2, \quad w = -1.5$$

**Source**: `mdp/rewards.py` (`angular_velocity_penalty`)

The squared sum of roll/pitch angular velocity (body frame). Yaw is excluded since it is uncontrollable. Uses `sum` (not `mean`): since the number of axes is fixed at 2, the result is identical, but it explicitly expresses a penalty proportional to the total angular velocity magnitude.

In the DR environment, it suppresses excessive angular velocity oscillation under strong disturbances. The weight -1.5 is half of tracking (3.0), tuned so that it does not completely suppress the tracking gradient even at ang_vel > 0.7 rad/s (lowered from the previous -3.0).

### Term 7: Linear Error Penalty

$$r_{lin} = \min(\phi_t / \phi_{max}, \; 1.0), \quad \phi_{max} = 1.0 \text{ rad}, \quad w = -1.0$$

**Source**: `mdp/rewards.py` (`linear_error_penalty`)

Provides a **constant gradient** when the Gaussian tracking gradient vanishes at large errors (>30 deg). Output [0, 1], clamped at max_err.

| $\phi_t$ (error) | raw | dt-scaled | weighted (full curriculum) |
|:---|:---|:---|:---|
| 0.087 (~5 deg) | 0.087 | 0.00044 | -0.00044 |
| 0.175 (~10 deg) | 0.175 | 0.00088 | -0.00088 |
| 0.349 (~20 deg) | 0.349 | 0.00175 | -0.00175 |
| 0.524 (~30 deg) | 0.524 | 0.00262 | -0.00262 |
| 0.785 (~45 deg) | 0.785 | 0.00393 | -0.00393 |
| 1.0 (= max_err) | 1.000 | 0.00500 | -0.00500 |

Gradient = $1/\phi_{max}$ = 1.0/rad, **constant at all error levels**. Since it ramps 0->1 according to the penalty curriculum, it is inactive initially and gradually strengthened. It acts in the same direction as tracking (both incentivize error reduction).

---

## Multi-Scale Gradient Design

A 3-stage gradient structure covers the entire error range:

```
error 0 deg ----[settling]---- 4 deg ----[tracking sigma=0.35]---- 25 deg+ ----[linear_error]----
          precision band         main correction range           tail coverage
          (sharpness=20)         (2.77x stronger gradient)       (constant gradient)
```

| Range | Main gradient source | Characteristics |
|:---|:---|:---|
| 0-4 deg | settling (k=20) | max gradient 5.0/rad, precise convergence |
| 4-25 deg | tracking (sigma=0.35) | Gaussian gradient, strengthened main correction |
| 25 deg+ | linear_error | constant 1.0/rad, tail coverage |

---

## Penalty Curriculum

A linear ramp curriculum is applied to all negative-weight terms:

$$w_{eff}(i) = w_{full} \cdot \min(1, \; i / i_{end})$$

| Parameter | Value |
|:---|:---|
| `penalty_curriculum_ratio` | 0.5 |
| Applies to | `joint_oscillation`, `joint_velocity`, `angular_velocity`, `linear_error` (all negative-weight terms) |
| Scale at iter 0 | 0.0 (penalties disabled) |
| Scale at 50% of max_iter | 1.0 (full penalties) |

### Implementation

The `RewardManager.update_curriculum(iteration)` method updates `penalty_scale`. Inside `compute()`, the scale is multiplied only into terms with `weight < 0`:

```python
if weight < 0:
    scaled_value = scaled_value * self._penalty_scale
```

Called every iteration in the runner's `log()` method:
```python
raw_env._reward_manager.update_curriculum(iteration)
```

In early training, it explores freely without penalty, then gradually strengthens regularization to converge to smooth and energy-efficient behavior.

---

## Scale Balance Analysis

### Expected Per-step Balance (15s episode)

#### Base RL (error ~ 15 deg = 0.262 rad, hf ~ 0.5 rad/s, full curriculum)

| Term | Raw | Weight | dt | Per-step | Share |
|:---|:---|:---|:---|:---|:---|
| tracking | 0.570 | 5.0 | 0.005 | **+0.01425** | **53%** |
| settling | ~0.045 | 3.0 | 0.005 | +0.00067 | 2.5% |
| progress | ~0.01 | 0.3 | no | +0.00300 | 11% |
| joint_oscillation | ~0.25 | -2.5 | 0.005 | -0.00312 | 12% |
| joint_velocity | ~0.04 | -1.0 | 0.005 | -0.00020 | 0.7% |
| angular_velocity | - | 0.0 | 0.005 | 0 | 0% |
| linear_error | 0.262 | -1.0 | 0.005 | -0.00131 | 5% |
| **Net** | | | | **+0.01329** | |

The positive terms (tracking+settling+progress=67%) dominate. At sigma=0.35, the tracking gradient is 2.77x stronger than at sigma=0.5. The marginal benefit of moving 15 deg->10 deg becomes positive (+0.00207), inducing active convergence.

### Episode Budget (15s, normalized per second, full curriculum)

| Error | Tracking/s | Settling/s | Linear err/s | Penalties/s | Total/s |
|:---|:---|:---|:---|:---|:---|
| 2 deg | +4.95 | +1.00 | -0.09 | -0.35 | **+5.51** |
| 5 deg | +4.70 | +0.04 | -0.17 | -0.35 | **+4.22** |
| 10 deg | +3.89 | ~0 | -0.35 | -0.35 | **+3.19** |
| 15 deg | +2.85 | ~0 | -0.52 | -0.35 | **+1.98** |
| 20 deg | +1.85 | ~0 | -0.70 | -0.35 | **+0.80** |
| 30 deg | +0.53 | ~0 | -1.05 | -0.35 | **-0.87** |
| 45 deg | +0.03 | ~0 | -1.57 | -0.35 | **-1.89** |

Thanks to sigma=0.35 + weight=5.0, a strong positive reward (+1.98/s) is retained even at 15 deg. It drops sharply above 20 deg and turns negative above 25 deg. Even at the end of the initialization range (±30 deg), linear_error provides a gradient.

### Key Observations

1. **Multi-scale gradient**: tracking (sigma=0.35, w=5.0) strongly covers 5-25 deg, settling covers 0-4 deg, and linear_error covers the 25 deg+ tail. No gradient dead zone across the full range.
2. **Passive equilibrium resolution**: "do nothing" expected reward 1.83 (w=5.0*0.367), with an improvement margin of 3.17, a 2.28x increase over the previous (1.39).
3. **Marginal benefit turns positive**: when moving 15 deg->10 deg, the tracking increase (+0.00519) exceeds the osc cost (-0.00312). Net marginal +0.00207/step induces active convergence.
4. **Joint oscillation penalty halved**: reduced to -2.5 (previously -5.0). Still 2.5x the original (-1.0), but the motion penalty does not dominate in its balance with tracking.
5. **Episode reward normalization**: in `_collect_episode_metrics()`, dividing by `/ max_episode_length_s` logs a per-second average independent of episode length.

---

## Reward Manager Architecture

### Pipeline

```
_get_rewards() [base_env.py]
    |
    +-- update_potentials()              # prev <- current, recompute current
    |
    +-- RewardManager.compute()           # iterate active terms
            |
            +-- tracking_reward()            --> * weight * dt
            +-- settling_bonus()             --> * weight * dt
            +-- progress_reward_pbrs()       --> * weight (no dt)
            +-- joint_oscillation_penalty()  --> * weight * dt * penalty_scale
            +-- joint_velocity_penalty()     --> * weight * dt * penalty_scale
            +-- angular_velocity_penalty()   --> * weight * dt * penalty_scale
            +-- linear_error_penalty()       --> * weight * dt * penalty_scale
            |
            +-- accumulate to _episode_sums
            |
            +-- return total_reward
```

### Zero-Weight Optimization

In `RewardManager.__init__`, terms with `weight=0.0` are not registered in `_term_cfgs`. Setting a specific reward term to 0 in the config automatically disables it.

### Environment-Specific Registration

In `_build_reward_terms()`, each weight in the config is checked and only non-zero terms are registered:

| Environment | Active Terms |
|:---|:---|
| RL (`Isaac-FullDOF-TRPO-v0`) | 7 (tracking, settling, progress, joint_osc, joint_vel, ang_vel, linear_error) |
| TDC (`Isaac-FullDOF-TDC-v0`) | 7 base + mhat_accuracy, tdc_torque (if weight != 0) |

In the TDC environment, `tdc_env._build_reward_terms()` inherits + extends the base.

### Logging Integration

When `RewardManager.reset(env_ids)` is called, it returns the average episode sum over the environments being reset. Via `base_env._collect_episode_metrics()`, it is recorded to WandB/TensorBoard **normalized as a per-second average**:

```python
log[f"Episode_Reward/{name}"] = value / self.max_episode_length_s
```

Logged items:
- `Episode_Reward/tracking`
- `Episode_Reward/settling`
- `Episode_Reward/progress`
- `Episode_Reward/joint_oscillation`
- `Episode_Reward/joint_velocity`
- `Episode_Reward/angular_velocity`
- `Episode_Reward/linear_error`

---

## Comparison with Reference Implementations

### Isaac Gym Reference (`references/isaacgym_agent/tasks/heroagent.py`)

```python
# line 770
pose_reward = 8 * torch.exp(-potentials)

# line 766
progress_reward = potentials - prev_potentials

# line 776
total_reward = pose_reward + progress_reward - 2 * actions_cost_scale * actions_cost
```

| Item | Isaac Gym | Isaac Lab (current) |
|:---|:---|:---|
| Tracking | $8 \cdot e^{-\phi}$ (Laplacian) | $5.0 \cdot e^{-\phi^2 / \sigma^2}$ (Gaussian, $\sigma=0.35$) |
| Progress | $\phi_{t-1} - \phi_t$ (raw delta) | $\phi_{t-1} - \gamma \phi_t$ (PBRS, $\gamma=0.99$) |
| Settling | none | $3.0 \cdot \sigma(20 \cdot (0.175 - \phi))$ |
| Linear error | none | $-1.0 \cdot \min(\phi/1.0, 1.0)$ |
| Action cost | $-2 \cdot \|a\|^2$ | none (removed) |
| Alive reward | 0.5/step | none |
| Joint oscillation | none | $-2.5 \cdot \text{EMA-HP}(\dot\gamma)^2$ |
| Joint velocity | none | $-1.0 \cdot \|\dot\gamma\|^2$ |
| Angular velocity | none | $0.0 \cdot \|\omega_{rp}\|^2$ (disabled) |
| dt scaling | none | applied to state-quality terms |
| Curriculum | none | all penalties, ratio=0.5 ramp |

**Kernel comparison**: Isaac Gym's Laplacian $e^{-|\phi|}$ provided a constant gradient (-1) at all errors, making training stable. Isaac Lab's Gaussian $e^{-\phi^2/\sigma^2}$ has a gradient that converges to 0 near the origin (compensated by settling), but it strengthens the mid-range gradient with sigma=0.5 and compensates the tail with linear_error, achieving full-range coverage.

### Cross-Environment Comparison

| Environment | Positive Weights | Penalty Weights | Pos:Neg Ratio |
|:---|:---|:---|:---|
| AnymalC | +1.0 | -0.05, -0.01, -2.5e-5, -2.5e-7 | ~100:1 |
| Quadcopter | +15.0 | -0.05, -0.01 | ~300:1 |
| Hero Agent | **+5.0, +3.0, +0.3** | **-2.5, -1.0, -1.0** | **~2.3:1** |

Hero Agent's pos:neg ratio (~2.3:1) is lower than other environments, but this is an intentional design. In a UUV environment with strong DR (added mass +-50%, etc.), penalties suppress excessive oscillation while the strengthened tracking weight (5.0) guarantees the marginal benefit of active convergence.

---

## Design Considerations

### Strengths

1. **Multi-scale gradient**: no gradient dead zone across the full error range. 3-stage coverage of settling (precision), tracking (mid-range), and linear_error (tail).
2. **Passive equilibrium prevention**: at sigma=0.35/w=5.0, the improvement margin is 3.17, a 2.28x increase over the previous (sigma=0.5/w=3.0, 1.39).
3. **dt-invariant**: with proper dt scaling, no re-tuning is needed when `decimation` changes.
4. **Episode-length-independent logging**: `/ max_episode_length_s` normalization enables quality comparison independent of survival time.
5. **PBRS theoretical guarantee**: preserves the optimal policy, off-policy safe.
6. **Penalty curriculum**: guarantees initial exploration -> gradual regularization -> final smooth control.

### Known Limitations

1. **Sharp drop in tracking above 30 deg**: at sigma=0.35, tracking = 0.106 at 30 deg and 0.018 at 40 deg. linear_error compensates, but a deliberately wider sigma than sigma=0.3 (0.047 at 30 deg) was chosen to retain a valid gradient across the initialization range (±30 deg).
2. **Angular velocity penalty disabled**: removed (0.0) since it can be sufficiently covered by joint_velocity + joint_oscillation.
3. **Progress weight relatively weak**: the 0.3 weight is 1/17 of tracking (5.0). Despite the theoretical advantage of PBRS, its actual gradient contribution may be small.

---

## Related Notes

- [tdc-control-law.md](tdc-control-law.md): TDC controller structure and control law derivation (independent of reward)
- [domain-randomization.md](../how-to/domain-randomization.md): Domain Randomization configuration (affects reward robustness)

---
**Created**: 2026-02-11
**Updated**: 2026-03-01 (Reward tuning: tracking_weight 3.0->5.0, tracking_sigma 0.5->0.35, joint_oscillation -5.0->-2.5, penalty_curriculum_ratio 0.75->0.5. Marginal benefit 15->10 deg now positive.)
