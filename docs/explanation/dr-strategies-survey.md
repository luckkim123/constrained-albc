# Domain Randomization Training Strategies: Literature Survey

Date: 2026-02-24

To address the problem in Hero Agent training where attitude error increases monotonically as DR becomes stronger,
we survey the DR-handling strategies of leading studies. We compare and analyze major approaches such as
adaptive entropy, DR curriculum, use of privileged info, and contrastive learning.

---

## 1. DR Curriculum Approaches

### 1.1 Fixed DR (Uniform)

The simplest method. Uniform sampling over the entire DR range from the start.

- Pros: simple implementation, no hyperparameters
- Cons: if the DR range is wide, early training fails or yields an overly conservative policy
- Use cases: RMA, HORA (instead compensate for DR with privileged info)

### 1.2 Manual Linear Curriculum (current Hero Agent)

Start from a narrow DR range and expand linearly in proportion to iteration.

```
param_range(iter) = start + (end - start) * min(1, iter / end_iter)
```

- Pros: simple implementation, predictable progression
- Cons: **DR expands regardless of whether the policy is ready**
- Problem: when run concurrently with the reward curriculum, a death spiral is possible (observed in Hero Agent)

### 1.3 ADR (Automatic Domain Randomization) - OpenAI, 2019

> Solving Rubik's Cube with a Robot Hand. OpenAI, 2019.
> https://openai.com/index/solving-rubiks-cube/

**Performance-based DR expansion/contraction.** Core algorithm:

1. Start in a non-randomized environment (all parameters = nominal)
2. Each iteration: randomly select one DR parameter
3. **Boundary sampling**: fix that parameter at a boundary value (upper or lower limit), sample the rest from the current range
4. Evaluate performance over N episodes in that environment -> accumulate into a buffer
5. Mean performance > threshold_H -> **expand boundary** (make DR harder)
6. Mean performance < threshold_L -> **contract boundary** (make DR easier)
7. Repeat

```
For each iteration:
    i = random DR parameter index
    boundary = random choice (lower or upper)
    fix param_i to boundary value, sample others normally
    evaluate performance -> append to buffer[i][boundary]
    if mean(buffer) > phi_H:
        expand boundary by delta
    elif mean(buffer) < phi_L:
        contract boundary by delta
```

Key characteristics:
- **Expand when the policy is ready, contract when it fails** (the decisive difference from the linear curriculum)
- No human intervention required (automatic range determination)
- ADR entropy = a distribution-diversity metric, correlated with transfer performance
- Scaled from Dactyl up to solving the Rubik's Cube (100+ DR parameters)

### 1.4 DORAEMON (ICLR 2024)

> Domain Randomization via Entropy Maximization.
> Tiboni et al., ICLR 2024.
> https://arxiv.org/abs/2311.01885

**Optimize the DR distribution via constrained entropy maximization.**

```
max  H(p_phi)                    # maximize the entropy of the DR distribution
s.t. E_phi[success(pi)] >= eta   # current policy success rate >= threshold
```

- More principled than ADR: optimizes the distribution itself (unlike ADR, which only adjusts boundaries)
- Always superior to fixed DR (wider generalization)
- Naturally induces a curriculum: the success-rate constraint forces gradual expansion
- Successful sim-to-real zero-shot transfer (robotic manipulation)

### 1.5 Active Domain Randomization (CoRL 2019)

> Active Domain Randomization.
> Mehta et al., CoRL 2019.
> https://arxiv.org/abs/1904.04762

- An approach different from ADR: actively search for the "most informative" DR environments
- Use a discriminator to distinguish trajectories of randomized vs. reference environments
- Use the discriminator output as a reward -> optimize the sampling policy with SVPG
- Result: sample more from environments that are difficult for the policy (automatically induces a curriculum)

---

## 2. Exploration / Adaptive Entropy Strategies

### 2.1 axPPO (2024)

> Proximal Policy Optimization with Adaptive Exploration.
> 2024. https://arxiv.org/abs/2405.04664

**Entropy scaling based on recent return.**

```
L(theta) = E[L_CLIP - c1*L_VF + G_recent * c2 * S[pi](s)]

G_recent = (1/G_max) * mean(recent tau steps batch returns)
```

- G_recent in [0, 1]: high when performance is good, low when it is bad
- **Increase entropy when performance is good** (strengthen exploit) -- the opposite direction from Hero Agent
- Less sensitive to performance fluctuations compared to a fixed c2
- Note: targets pure exploration environments (sparse reward), not DR environments

### 2.2 SAC Automatic Alpha Tuning

> Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL.
> Haarnoja et al., 2018. + Meta-SAC, 2020.
> https://arxiv.org/abs/2007.01932

**Automatically adjust alpha via a target entropy.**

```
min_alpha  E[-alpha * log pi(a|s) - alpha * H_target]
H_target = -dim(action_space)   # common default
```

- Stable even in DR environments due to its off-policy nature
- Alpha automatically maintains the correct level (independent of DR strength)
- Unlike PPO, entropy is directly included in the objective

### 2.3 Entropy-Controlled Intrinsic Motivation (2024)

> Entropy-Controlled Intrinsic Motivation for Quadruped Robot Locomotion.
> 2024. https://arxiv.org/html/2512.06486

- Entropy-based intrinsic motivation on complex terrain
- When entropy drops (excessive exploitation) -> increase intrinsic reward -> force exploration
- Combined with a terrain curriculum

### 2.4 Commonalities Among Leading Studies

**Most do not explicitly adjust entropy.**

| Method | Entropy Strategy | DR Handling |
|------|-------------|---------|
| ADR (OpenAI) | Fixed | Fit the DR range to policy performance |
| DORAEMON | Fixed | Optimize the DR distribution itself |
| RMA/HORA | Fixed | Compensate for DR with privileged info |
| HIM | Fixed | Compensate for DR with a contrastive embedding |
| Extreme Parkour | Fixed | Terrain curriculum (performance-based) |
| axPPO | Adaptive | Increase entropy when performance is good (opposite direction) |
| Hero Agent (current) | Adaptive | Increase entropy when performance worsens |

---

## 3. Privileged Info / Adaptation Strategies

### 3.1 RMA (Rapid Motor Adaptation)

> Kumar et al., RSS 2021.
> https://ar5iv.labs.arxiv.org/html/2107.04034

**2-phase regression-based adaptation.**

Phase 1 (RL + Encoder):
- Train policy + encoder(mu) jointly (PPO)
- Encoder: privileged env parameters -> extrinsics vector z
- Policy: [proprioception, z] -> actions
- **Full DR, no curriculum** (privileged info compensates for DR)

Phase 2 (Adaptation):
- Freeze policy + encoder
- Train the adaptation module(phi): proprio history -> z_hat (supervised)
- z_hat replaces z to operate in the real environment

Key insight:
- With privileged info, learning is possible even when DR is hard (the policy "knows" the environment)
- The regression target (z) can be contaminated by DR noise (pointed out in HIM)

### 3.2 HIM (Hybrid Internal Model, ICLR 2024)

> Long et al., ICLR 2024.
> https://arxiv.org/abs/2312.11460

**Contrastive-learning-based environment embedding. An alternative to RMA regression.**

Architecture:
```
past 5-step proprioception history
    |
Embedding Extractor (MLP 512->256->128)
    |
    +-- Explicit: v_hat (velocity) -- MSE regression (ground truth)
    +-- Implicit: l_hat in R^16   -- SwAV contrastive learning
    |
Policy: [partial_obs, v_hat, l_hat] -> actions
Critic: [privileged_obs] -> value (only during training)
```

SwAV Contrastive Learning:
```
J_SwAV = -1/2 * sum(q_source * log(p_target) + q_target * log(p_source))
```
- Source: past observation history -> encoder -> embedding
- Target: future observation (successor state) -> encoder -> embedding
- Prototype: K learnable cluster centers
- Sinkhorn-Knopp: enforce uniform assignment within a batch (prevent collapse)

2-phase optimization (each iteration):
```
Phase A (HIO): update embedding with SwAV + velocity MSE, policy frozen
Phase B (PPO): embedding frozen, PPO updates actor/critic only
```

DR parameters (full range, without a curriculum):
| Parameter | Range |
|-----------|-------|
| Body/Link mass | +/-20% |
| CoM offset | +/-0.1m |
| Payload | -1~3 kg |
| Ground friction | 0.2~2.75 |
| Restitution | 0.0~1.0 |
| Motor strength | +/-20% |
| Joint Kp/Kd | +/-20% |
| System delay | 0~3dt |
| External force | +/-30N |

Performance (vs RMA):
| Environment | HIM | RMA |
|------|-----|-----|
| Short stairs success rate | 100% | 60% |
| Long stairs (cm) | 176.5 | 75.4 |
| Composite terrain | 85% | 45% |
| Deformed slope | 55% | 10% |

Key differences (vs RMA):
- RMA: estimate "friction is 0.5, mass is 1.2x" (regression)
- HIM: distinguish "this environment is similar to A, different from B" (contrastive)
- Regression has target contamination from DR noise, while contrastive learns only relative differences

### 3.3 Extreme Parkour (ICRA 2024)

> Cheng et al., ICRA 2024.
> https://ar5iv.labs.arxiv.org/html/2309.14341

**Teacher-Student distillation + performance-based terrain curriculum.**

Phase 1 (Teacher, RL):
- Input: proprioception + scandots (privileged) + heading + flag
- ROA (Regularized Online Adaptation): jointly train an environment-parameter estimator
- Train with PPO

Phase 2 (Student, DAgger):
- Input: proprioception + depth image (58x87, 10Hz) + heading prediction
- Imitate the teacher action with MSE
- Step the environment with the student's own action (resolves distribution shift)

Curriculum (performance-based):
```python
if distance_traveled > 0.5 * terrain_length:
    difficulty += 1  # promote
elif distance_traveled < 0.5 * v_cmd * T:
    difficulty -= 1  # demote
```

MTS (Mixture of Teacher and Student):
- Heading prediction within 0.6 rad of the oracle -> use the student prediction
- Otherwise -> force the oracle heading (training stability)

Achieved performance:
- High jump: 0.5m (2x robot height)
- Long jump: 0.8m (2x robot length)
- Slope: 37 degrees
- Capable of handstand walking

Exploration: **no explicit mechanism.** Terrain diversity serves the role of natural exploration.

---

## 4. Isaac Lab Community Practical Recommendations

> https://github.com/isaac-sim/IsaacLab/discussions/2813

### Staged Introduction Order
1. Confirm stable learning with no DR / minimal DR
2. Introduce gradually, starting with friction and actuator gains
3. Expand to complex factors such as sensor noise and perturbation

### Concrete Range Examples (AnymalC)
- Static friction: 0.7~1.3
- Stiffness scale: 0.75~1.5
- Damping scale: 0.3~3.0

### Core Principles
- Do not make learning easier by reducing the DR range (degrades real-environment robustness)
- Instead, solve it via hyperparameter tuning
- Set realistic ranges using actual sensor/environment measurements

---

## 5. Implications for Hero Agent

### Current Problem

The (linear) DR curriculum expands regardless of policy readiness -> monotonically increasing attitude error.
We are handling it with adaptive entropy, but this approach is rare in the literature.

### Literature-Based Alternative Analysis

#### Option A: ADR-style performance-based curriculum (recommendation: ★★★)

Switch the current linear ramp -> to boundary sampling + threshold-based expansion.

Pros:
- DR does not expand if the policy is not ready (prevents the death spiral at its source)
- Adaptive entropy may become unnecessary
- Validated up to 100+ parameters at OpenAI

Implementation complexity: medium
- Each DR parameter needs boundary sampling + a performance buffer
- Threshold settings required (phi_H, phi_L)
- Modify BaseRunner.log()

#### Option B: Stabilize encoder learning (recommendation: ★★☆)

The original HORA paper works with full DR + encoder, without a curriculum.
Diagnose why our encoder is unstable and focus on stabilization.

Pros:
- The curriculum itself may become unnecessary
- The validated pipeline of the original paper

Cons:
- Underwater robots have lower control authority than legged robots, so the same application may be difficult
- If the cause of encoder instability is regression-target contamination by DR noise, it is a fundamental limitation

#### Option C: HIM-style contrastive encoder (recommendation: ★★☆)

Replace the regression encoder -> with a contrastive encoder.

Pros:
- A representation robust to DR noise
- The HIM paper demonstrates a large performance advantage over RMA

Cons:
- High implementation complexity (SwAV, Sinkhorn-Knopp, prototype management)
- Requires 2-phase optimization (HIO + PPO)
- A major change to the existing pipeline

#### Option D: Keep the current approach + tune parameters (recommendation: ★☆☆)

Keep adaptive entropy + linear DR curriculum, adjust only the parameters.

Pros: minimal code change
Cons: no success cases for this combination in the literature, and it may not be a fundamental solution

---

## References

1. OpenAI. "Solving Rubik's Cube with a Robot Hand." 2019.
   https://openai.com/index/solving-rubiks-cube/
2. Tiboni et al. "DORAEMON: Domain Randomization via Entropy Maximization." ICLR 2024.
   https://arxiv.org/abs/2311.01885
3. Mehta et al. "Active Domain Randomization." CoRL 2019.
   https://arxiv.org/abs/1904.04762
4. "Proximal Policy Optimization with Adaptive Exploration (axPPO)." 2024.
   https://arxiv.org/abs/2405.04664
5. Haarnoja et al. "Meta-SAC: Auto-tune Entropy Temperature." 2020.
   https://arxiv.org/abs/2007.01932
6. Kumar et al. "RMA: Rapid Motor Adaptation for Legged Robots." RSS 2021.
   https://ar5iv.labs.arxiv.org/html/2107.04034
7. Long et al. "HIM: Hybrid Internal Model for Agile Legged Locomotion." ICLR 2024.
   https://arxiv.org/abs/2312.11460
8. Cheng et al. "Extreme Parkour with Legged Robots." ICRA 2024.
   https://ar5iv.labs.arxiv.org/html/2309.14341
9. Isaac Lab Discussion #2813: Tips for Domain Randomization.
   https://github.com/isaac-sim/IsaacLab/discussions/2813
10. "Entropy-Controlled Intrinsic Motivation for Quadruped." 2024.
    https://arxiv.org/html/2512.06486
