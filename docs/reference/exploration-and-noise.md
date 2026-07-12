# Exploration and Action Noise (`envs/main`)

> Verified against commit c5a8a08.

> **Scope**: The exploration mechanism of the default task
> `Isaac-ConstrainedALBC-TRPO-v0` (`constrained_albc/envs/main/`) — the policy's
> action-noise parameterization (`log_std`), how it becomes the sampling
> distribution, the post-update std clamp, the entropy bonus, and *why* entropy
> collapses under ConstraintTRPO despite the KL trust region.
>
> This is a code-level reference verified against disk. It consolidates the
> exploration/entropy material that `main-network-architecture.md` (§4, §8) and
> `action-pipeline.md` (§3.1) previously referenced or linked out to; those docs
> now point **here** for the noise/std/entropy detail. This document owns the
> exploration story end-to-end.
>
> **Not covered:** the network layer shapes (see `main-network-architecture.md`)
> and the action→physics path (see `action-pipeline.md`). This doc starts at the
> `log_std` parameter and ends at the logged noise metrics.

---

## 1. Overview

Exploration is a **single global Gaussian noise** on the 8D action. The policy
carries one learnable log-std vector `log_std` of dim 8; the sampling std is
`exp(log_std)`, state-independent and broadcast across the batch. There is no
state-dependent std head and no tanh-squashing. Three forces act on `log_std`
every update:

```
init:  log_std = log(0.7)      # init_noise_std = 0.7, all 8 dims

sample: a ~ Normal(action_mean, exp(log_std))          # act() -- exploration noise

update (ConstraintTRPO.update):
  surrogate = reward_surr + IPO_barrier + entropy_bonus     # 3 terms
     |            |            |             |
     |            |            |             +-- pushes std UP  (per-dim coef)
     |            |            +-- pushes std DOWN (avoid risky samples)
     |            +-- pushes std DOWN (concentrate on high-adv actions)
     +-- natural-gradient TRPO step under KL trust region (bounds STEP SIZE)
  clamp: log_std <- [log(min_std_per_dim), log(max_std)]    # hard floor/ceiling
  log:   Policy/entropy, Noise/std_mean, Noise/std_min
```

**Two independent "noise" concepts — do not conflate.** This document covers only
**action noise** (`log_std`, the trained exploration std the policy *emits*), never
the fixed **observation noise model** (`_OBS_NOISE_STD` in `config.py`, corrupts
`o_t`). Full side-by-side comparison: §7.

---

## 2. The `log_std` parameter

A single `nn.Parameter` of shape `(num_actions,) = (8,)`, initialized in
`PolicyBase._init_base` (`_core/encoder/_policy_base.py:96`):

```python
self.log_std = nn.Parameter(torch.log(init_noise_std * torch.ones(num_actions)))
```

With `init_noise_std = 0.7` (`rsl_rl_ppo_cfg.py:142`), every dim starts at
`log(0.7) ≈ -0.357`, i.e. std 0.7. It is **global / state-independent** — the same
8-vector for every observation in the batch. The sampling distribution is built in
`_update_distribution` (`_core/encoder/_policy_base.py:128–130`):

```python
def _update_distribution(self, mean: torch.Tensor) -> None:
    std = torch.exp(self.log_std).expand_as(mean)
    self.distribution = Normal(mean, std)
```

`act()` then returns `distribution.sample()` (the noisy training action);
`act_inference()` returns the mean (deterministic eval). The action-side handling
of the sample — clamps, split, physics — is in `action-pipeline.md`; the standing
of the *choice* (global vs state-dependent) is in `main-network-architecture.md` §8
(**standard** for on-policy PPO/TRPO).

`log_std` is a *live wire*: it is a trained parameter, and where it lives in the
optimizer split (§5) is what lets the KL trust region damp its collapse.

---

## 3. Std clamp — asymmetric, in log space, after the step

After the TRPO step, `ConstraintTRPO.update` clamps `log_std` in place
(`_core/algorithms/constraint_trpo.py:505–511`):

```python
with torch.no_grad():
    log_max = math.log(self.max_std)
    if self._log_min_std is not None:               # per-dim floor path
        self.policy.log_std.data.clamp_(max=log_max)
        self.policy.log_std.data = torch.max(self.policy.log_std.data, self._log_min_std)
    else:                                            # scalar fallback
        self.policy.log_std.data.clamp_(min=math.log(self.min_std), max=log_max)
```

Three things worth noting, each a common misread:

1. **It clamps `log_std`, not `std`.** The bounds are `log(min_std)` and
   `log(max_std)`; the linear std is `exp` of the clamped value.
2. **The ceiling and floor are different operations.** The ceiling is `clamp_(max=…)`;
   the per-dim floor is a separate `torch.max(log_std, _log_min_std)`. Only the
   scalar-fallback branch does both in one `clamp_`.
3. **It is a hard projection after the gradient step**, not a term in the loss. The
   TRPO step can drive `log_std` anywhere; the clamp then snaps it back into
   `[floor, ceiling]`. It cannot, on its own, *raise* a std the optimizer wants low
   — it only prevents overshoot past the floor (see §6: the entropy bonus is what
   actually keeps std up).

### 3.1 The bounds (per-dim floor)

From `RslRlConstraintTRPOAlgorithmCfg` (`rsl_rl_ppo_cfg.py:242–246`):

| Bound | Value | Note |
|---|---|---|
| `max_std` | 2.0 | scalar ceiling, all dims |
| `min_std` | 0.05 | scalar floor (fallback only, when per-dim empty) |
| `min_std_per_dim` | (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05) | **arm dims = 0.10, thruster dims = 0.05** |

The per-dim floor is the live one (it is non-empty, so it overrides the scalar
`min_std`). The arm dims get a **higher floor (0.10 vs 0.05)** because they collapse
faster — the cfg comment records that arm dims hit the scalar floor by **iter 1404**
while thruster dims stay above 0.14. `min_std_per_dim` is **project-custom** (not in
rsl_rl upstream); the standing of a std floor at all is discussed in
`main-network-architecture.md` §8.

---

## 4. Entropy bonus — per-dim, alongside the IPO barrier

Entropy enters the surrogate as a third additive term
(`_core/algorithms/constraint_trpo.py:486–500`):

```python
mean_entropy = self.policy.entropy.mean()
self._last_mean_entropy = mean_entropy.item()
if self._entropy_coef_per_dim is not None:
    per_dim_ent = self.policy.distribution.entropy()             # [batch, action_dim]
    entropy_bonus = -(self._entropy_coef_per_dim * per_dim_ent).sum(dim=-1).mean()
else:
    entropy_bonus = -self._entropy_coef * mean_entropy
return reward_surr + barrier + entropy_bonus
```

The surrogate that TRPO differentiates is `reward_surr + barrier + entropy_bonus`.
Because it is *minimized*, `-coef·H` maximizes entropy `H` — the gradient on
`log_std_i` is `+entropy_coef_i`, a constant upward push on noise (per the code
comment). Per-dim is the live path (`entropy_coef_per_dim` is non-empty), so each
action dim gets its own coefficient.

### 4.1 The coefficients

| cfg | Value | Location |
|---|---|---|
| `entropy_coef` (scalar) | 0.003 | `rsl_rl_ppo_cfg.py:233` (fallback when per-dim empty) |
| `entropy_coef_per_dim` | (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001) | `rsl_rl_ppo_cfg.py:239` — **arm = 0.01, thruster = 0.001** |

Arm dims get a **10× stronger entropy push** than thruster dims, mirroring the
higher arm std floor (§3.1) — both target the same measured problem (arm noise
collapses first). **Adaptive entropy is disabled**: there is no `target_entropy` /
entropy scheduler; the coefficients are fixed. (An earlier adaptive-entropy attempt
failed — see the `adaptive-entropy-failed` project memory / network doc.)

The measured effect, from the cfg comment: `entropy_coef=0.003` recovered noise
0.36→0.55 (04-09 run); `entropy_coef=0` let noise collapse to 0.12 (04-10 run).

---

## 5. Why `log_std` is in the TRPO group (not Adam)

ConstraintTRPO splits parameters into two optimizer groups by name prefix
(`_core/algorithms/constraint_trpo.py:156–175`):

```python
# 1. Policy (actor + encoder + log_std): TRPO natural gradient (no optimizer)
#    log_std included in TRPO so KL trust region protects against entropy collapse.
# 2. Value (critic + cost_critic): Adam
value_prefixes = ("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")
for name, param in self.policy.named_parameters():
    if any(name.startswith(p) for p in value_prefixes):
        value_params.append(param)          # -> Adam (value_lr)
    else:
        self._policy_params.append(param)   # -> TRPO natural gradient (actor, encoder, log_std)
```

`log_std` is deliberately in the **TRPO natural-gradient group**, not the Adam value
group. The reason (cfg comment): keeping it under the KL trust region means the
Fisher curvature *sees* the std, so a step that would slam entropy down is bounded
in KL. The offset of the sigma slice is tracked (`_sigma_param_offset`,
`_core/algorithms/constraint_trpo.py:176–178`) for logging the sigma component of the flat step.

**FVP includes `log_std`.** The Fisher-vector product
(`_fisher_vector_product`, `_core/algorithms/constraint_trpo.py:368–379`) is a pure KL Hessian on
`Normal(action_mean, action_std)`, differentiated over `self._policy_params` —
which contains `log_std`. Since `action_std = exp(log_std)`, `log_std` genuinely
contributes to the Fisher curvature and to the surrogate KL; it is **not**
logging-only. (Same finding as `main-network-architecture.md` §4.)

The same split note also records that the **encoder** is kept in the policy group:
decoupling it (run 2026-03-30) dropped encoder gradients ~85% (`:157`) because the
actor→z path alone is too weak. That is an encoder fact, cross-referenced in the network
doc §4; here the point is only that `log_std` shares that group.

---

## 6. Why entropy collapses despite the KL trust region

A common misconception is that TRPO's KL trust region *prevents* entropy collapse.
It does not — the trust region bounds the **size** of each step, not its
**direction**. If the objective gradient points toward smaller std at every step,
each step stays small but the policy walks steadily toward zero entropy; the trust
region only slows the descent. Two pressures push std down, one lifts it:

1. **Surrogate / advantage (down).** Policy gradient raises the probability of
   high-advantage actions; for a Gaussian, concentrating probability on a chosen
   action *is* shrinking std. This is the structural PPO/TRPO-common pressure the
   trust region cannot block.
2. **IPO log-barrier (down, project-specific).** A large std occasionally samples
   constraint-violating actions, shrinking the constraint margin `d_k - hat{J}_{C_k}`
   and lowering `log(margin)`. The barrier therefore adds pressure to reduce std so
   the policy stops sampling risky actions — constraints make the policy "cautious".
3. **Entropy bonus (up).** The `-coef·H` term pushes `log_std` up by a constant
   per-dim gradient (§4), the only counter-pressure.

Because pure TRPO has only pressure 1 while this algorithm has 1 + 2, entropy
collapses *faster* than vanilla TRPO — which is exactly why the (project-custom)
entropy bonus and per-dim floor exist. The collapse-and-recovery is measured
(§4.1). Pressure 2 (IPO barrier) is a mechanism inference plus general
constrained-RL literature support (constraints suppress exploration: ESB-CPO
arXiv:2302.14339; safe-RL review arXiv:2508.09128); it is **not** isolated by a
controlled experiment — the deferred test is in
`docs/plans/2026-06-30-entropy-collapse-ipo-barrier-experiment.md`. The literature
standing of "TRPO + entropy bonus" (**non-standard**, an EnTRPO novelty) is in
`main-network-architecture.md` §8.

---

## 7. Action noise vs. observation noise (do not conflate)

Both are called "noise" and both are Gaussian, but they are different objects with
different roles:

| | Action noise | Observation noise |
|---|---|---|
| What | policy exploration std | sensor-simulation corruption |
| Object | `log_std` (`_core/encoder/_policy_base.py:96`) | `_OBS_NOISE_STD` (`config.py:259`) |
| Learned? | **yes** — trained parameter, clamped each update | **no** — fixed cfg constant |
| Applied to | the action *before* env | the observation `o_t` *before* the policy |
| Purpose | drive exploration | sim-to-real robustness |
| This doc | **covered** | out of scope (see the obs/DR docs) |

`_OBS_NOISE_STD` is the per-dim Gaussian added to the 69D `o_t` (plus a uniform
additive bias); notably its first 3 dims (the command `ang_cmd`) and all action-history
dims are 0.0 — those are our own quantities, not sensed. That obs-noise model belongs
to the observation pipeline, not here. This document's entire subject is `log_std`.

---

## 8. What to watch (logged metrics)

`ConstraintEncoderRunner._log_constraint_metrics` logs the noise/entropy state each
iteration (`_core/runners/constraint_encoder_runner.py:311, 349–350`):

| Metric | Meaning | Read it for |
|---|---|---|
| `Policy/entropy` | `_last_mean_entropy` (mean over batch) | overall exploration level; a monotone drop toward 0 is collapse |
| `Noise/std_mean` | `log_std.exp().mean()` over 8 dims | the 0.36↔0.55 band the entropy tuning targets |
| `Noise/std_min` | `log_std.exp().min()` | which dim is pinned at its floor (arm dims first) |
| `Grad/sigma_step` / `Grad/sigma_dir` | sigma component of the natural-gradient step (norm / signed mean) | is the step pushing noise up or down this iteration |

A run where `Noise/std_min` sits exactly at 0.05 (or 0.10 for an arm dim) means the
floor is binding — the entropy bonus lost to pressures 1+2 and the clamp is holding
the line. That is the signal that motivated the per-dim tuning.

---

## 9. Knob map

All in `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` unless noted.

| Knob | Value | Location |
|---|---|---|
| `init_noise_std` | 0.7 | `:142` |
| `entropy_coef` (scalar fallback) | 0.003 | `:233` |
| `entropy_coef_per_dim` | (0.01, 0.01, 0.001×6) | `:239` |
| `min_std` / `max_std` (scalar) | 0.05 / 2.0 | `:242` / `:243` |
| `min_std_per_dim` | (0.10, 0.10, 0.05×6) | `:246` |
| std clamp application (log space) | — | `_core/algorithms/constraint_trpo.py:505–511` |
| entropy bonus in surrogate | — | `_core/algorithms/constraint_trpo.py:486–500` |
| param-group split (log_std → TRPO) | — | `_core/algorithms/constraint_trpo.py:156–175` |
| FVP includes log_std | — | `_core/algorithms/constraint_trpo.py:368–379` |
| log_std parameter | — | `_core/encoder/_policy_base.py:96` |
| `_update_distribution` (std = exp) | — | `_core/encoder/_policy_base.py:128–130` |
| entropy/noise log keys | Policy/entropy, Noise/std_mean, Noise/std_min | `_core/runners/constraint_encoder_runner.py:311, 349–350` |

---

## 10. Notes and limitations

- **The clamp cannot raise std the optimizer wants low.** It is a floor/ceiling
  projection, not a spring. Keeping noise up is the entropy bonus's job; the clamp
  only stops undershoot past the floor and blow-up past the ceiling.
- **`min_std_per_dim` and `entropy_coef_per_dim` are two knobs on the same
  problem** (arm dims collapse first). They are tuned together; changing one without
  the other re-opens the confound the per-dim split was introduced to close.
- **The IPO-barrier → entropy pressure (pressure 2) is inferred, not isolated.**
  It rests on the barrier mechanism plus constrained-RL literature; the controlled
  experiment that would separate it from pressure 1 is deferred (§6).
- This is a static code-structure reference. Whether entropy is *actually*
  collapsing on a given run is a runtime-diagnostic question — read the §8 metrics,
  do not assume from the config.

---

## 11. Action bounding: is the clamp justified + unverified experiment room

> **Verdict (2026-07-02 review, literature + code cross-checked).** The current
> raw Gaussian + `[-1,1]` hard clamp is **justified and standard**. Switching to
> tanh-squashing is not an improvement — it moves the problem. Below is the evidence,
> plus the unverified experiment room that does *not* touch the clamp.

### 11.1 Why the clamp is justified

The action sample is a raw Gaussian with no clamp (`_core/encoder/actor_critic_encoder.py:275–280`
`distribution.sample()`, "no action clamping"). The clamp happens only in the env
buffer (`albc_env.py:452` `self._actions = actions.clone().clamp(-1.0, 1.0)`). The
vecenv `clip_actions` (Clamp#0) is unset → isaaclab default `None` → **no-op**; the
only active clamp is this single env buffer.

log-prob is computed on the **pre-clamp raw sample** (`_core/algorithms/constraint_trpo.py:473`) and
the clamp applies only to env dynamics. So "policy density" and "executed action" are
each internally consistent — the **standard on-policy PPO/TRPO convention** of
treating the clamp as part of the environment, not the policy (SB3 PPO =
`DiagGaussianDistribution` + clip, no tanh; the PPO/TRPO papers use plain Gaussians).

### 11.2 Why NOT to switch to tanh (moving the problem, not improving)

1. **This task's optimal action is at the *center* of the action space.** The arm is
   a delta integrator (`albc_env.py:567-578` `q_des += 0.10·a`) so idle (a≈0) is
   optimal with no boundary attractor; the thrusters are hover so a small-command
   equilibrium (near 0) is optimal. So tanh saturation ($1-\tanh^2(u)\to0$ at the
   boundary) killing the gradient **barely applies** here. (The old EE-position
   absolute mode had the optimum at the workspace *boundary*, where tanh/clamp caused
   gradient freeze — `project_delta_ee_decision.md`. That failure mechanism is absent
   in the current joint-space mode, so applying "tanh = arm freeze" to the present
   task is wrong.)
2. **on-policy TRPO + tanh is not a validated combination.** tanh-squashing is a
   defining element of the SAC family (off-policy, reparameterization,
   entropy-in-objective), where the Jacobian correction
   $-\sum_i\log(1-\tanh^2(u_i))$ is natural to that objective (Haarnoja 2018,
   arXiv:1801.01290 App.C). TRPO's KL trust region is computed over the policy
   distribution; adding tanh changes the geometry of "policy" and "KL" — no literature
   validates squashed-Gaussian TRPO (**no source found**). That is a full
   ConstraintTRPO+IPO+FVP redesign (§5) with no upside per §11.2-1.
3. **Omitting the correction breaks the entropy math.** Adding tanh but dropping the
   Jacobian correction makes log-prob use the wrong density, so the entropy bonus is
   systematically wrong near the boundary → the collapse-defense math of §4/§6 breaks.

### 11.3 The clamp's one unmeasured value + experiment room (docs only, no code change; check this before launching)

Justified does not mean "harmless." The known defect of clipping is not vanishing
gradient but **log-prob bias for out-of-bound samples** (Fujita & Maeda 2018,
arXiv:1802.07564, CAPG), which grows the more often actions saturate the boundary.
Per §11.2-1, with the optimum at center and small std (floor 0.05~0.10), saturation is
*presumed* rare so the bias is likely small in practice — but **this is not measured.**
That gap is the basis of the remaining experiments:

| # | Experiment | Rationale | Nature |
|---|---|---|---|
| 1 | **Add `clip_fraction` logging** (`|a|≥1` rate) | Not logged today (code-confirmed). Must measure saturation frequency to judge whether the §11.3 bias is a real problem. Literature also recommends "measure this before changing the pipeline" | **Code change** (a few log lines, algorithm unchanged, no training gate). Top priority |
| 2 | Revisit `max_std=2.0` / `init_noise_std=0.7` | Other knobs (entropy_coef 0.003, per-dim coef, arm floor) have empirical backing; only these two have zero justification comments = inertia | Comparison training run (training gate). Depends on experiment 1 |
| 3 | Isolate the IPO barrier→entropy causality (`entropy_coef_per_dim=0` vs current) | §6 admits this is "inferred, not isolated"; the referenced plan file is also absent | Comparison training run (training gate). tanh-independent |

**Discarded**: tanh vs raw+clamp comparison run — ruled out in §11.2.

> **Literature sources.** Haarnoja et al. 2018 (SAC, arXiv:1801.01290) — tanh Jacobian
> correction. Fujita & Maeda 2018 (Clipped Action Policy Gradient, ICML,
> arXiv:1802.07564) — clip-bias theory. Schulman 2015 (TRPO, arXiv:1502.05477) / 2017
> (PPO, arXiv:1707.06347) — plain-Gaussian convention. Chou et al. 2017 (ICML, Beta
> policy) — both clip and squash have boundary artifacts. "No literature validating
> squashed TRPO" and "no paper directly comparing tanh vs clip at boundary optima" are
> flagged as no-source-found (not fabricated — the gap is stated).

---

## Source files

- `constrained_albc/envs/_core/encoder/_policy_base.py` — `log_std` parameter (`:96`), `_update_distribution` (`:128`)
- `constrained_albc/envs/_core/algorithms/constraint_trpo.py` — std clamp (`:505`), entropy bonus (`:486`), param-group split (`:156`), FVP (`:368`)
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `init_noise_std`, `entropy_coef(_per_dim)`, `min/max_std`, `min_std_per_dim`
- `constrained_albc/envs/_core/runners/constraint_encoder_runner.py` — `Policy/entropy`, `Noise/std_*` logging
- `constrained_albc/envs/main/config.py` — `_OBS_NOISE_STD` (the *observation* noise, contrasted in §7)
