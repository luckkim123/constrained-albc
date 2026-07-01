# Exploration and Action Noise (`envs/main`)

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

**Two independent "noise" concepts — do not conflate.** This document is about
**action noise** (the policy's exploration std, `log_std`, learned at train time).
It is *not* the **observation noise model** (`_OBS_NOISE_STD` in `config.py`, a
fixed sensor-simulation constant applied to `o_t`). Same word, different object:
action noise is what the policy *emits*, observation noise is what the sensors
*corrupt*. §7 draws the line explicitly.

---

## 2. The `log_std` parameter

A single `nn.Parameter` of shape `(num_actions,) = (8,)`, initialized in
`PolicyBase._init_base` (`_policy_base.py:96`):

```python
self.log_std = nn.Parameter(torch.log(init_noise_std * torch.ones(num_actions)))
```

With `init_noise_std = 0.7` (`rsl_rl_ppo_cfg.py:132`), every dim starts at
`log(0.7) ≈ -0.357`, i.e. std 0.7. It is **global / state-independent** — the same
8-vector for every observation in the batch. The sampling distribution is built in
`_update_distribution` (`_policy_base.py:128–130`):

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
(`constraint_trpo.py:484–491`):

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

From `RslRlConstraintTRPOAlgorithmCfg` (`rsl_rl_ppo_cfg.py:232–236`):

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
(`constraint_trpo.py:466–480`):

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
| `entropy_coef` (scalar) | 0.003 | `rsl_rl_ppo_cfg.py:223` (fallback when per-dim empty) |
| `entropy_coef_per_dim` | (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001) | `rsl_rl_ppo_cfg.py:229` — **arm = 0.01, thruster = 0.001** |

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
(`constraint_trpo.py:153–174`):

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
`:175–177`) for logging the sigma component of the flat step.

**FVP includes `log_std`.** The Fisher-vector product
(`_fisher_vector_product`, `constraint_trpo.py:354–365`) is a pure KL Hessian on
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
constrained-RL literature support; it is **not** isolated by a controlled
experiment — the deferred test is in
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
| Object | `log_std` (`_policy_base.py:96`) | `_OBS_NOISE_STD` (`config.py:206`) |
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
iteration (`runners/constraint_encoder_runner.py:324, 337–338`):

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
| `init_noise_std` | 0.7 | `:132` |
| `entropy_coef` (scalar fallback) | 0.003 | `:223` |
| `entropy_coef_per_dim` | (0.01, 0.01, 0.001×6) | `:229` |
| `min_std` / `max_std` (scalar) | 0.05 / 2.0 | `:232` / `:233` |
| `min_std_per_dim` | (0.10, 0.10, 0.05×6) | `:236` |
| std clamp application (log space) | — | `constraint_trpo.py:484–491` |
| entropy bonus in surrogate | — | `constraint_trpo.py:466–480` |
| param-group split (log_std → TRPO) | — | `constraint_trpo.py:153–174` |
| FVP includes log_std | — | `constraint_trpo.py:354–365` |
| log_std parameter | — | `_policy_base.py:96` |
| `_update_distribution` (std = exp) | — | `_policy_base.py:128–130` |
| entropy/noise log keys | Policy/entropy, Noise/std_mean, Noise/std_min | `constraint_encoder_runner.py:324, 337–338` |

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

## Source files

- `constrained_albc/envs/main/encoder/_policy_base.py` — `log_std` parameter (`:96`), `_update_distribution` (`:128`)
- `constrained_albc/envs/main/algorithms/constraint_trpo.py` — std clamp (`:484`), entropy bonus (`:466`), param-group split (`:153`), FVP (`:354`)
- `constrained_albc/envs/main/agents/rsl_rl_ppo_cfg.py` — `init_noise_std`, `entropy_coef(_per_dim)`, `min/max_std`, `min_std_per_dim`
- `constrained_albc/envs/main/runners/constraint_encoder_runner.py` — `Policy/entropy`, `Noise/std_*` logging
- `constrained_albc/envs/main/config.py` — `_OBS_NOISE_STD` (the *observation* noise, contrasted in §7)
