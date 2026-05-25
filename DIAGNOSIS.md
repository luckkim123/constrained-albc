# constrained-albc Diagnostic Report

> Written: 2026-05-25. Six areas (env/physics, algorithm, encoder/runners/student, TDC, analysis, structure) were
> diagnosed in parallel by read-only agents, and then **CRITICAL items were re-verified directly against the code**.
> Each item is tagged with a verification status: `[verified]` = confirmed by code/data, `[unverified]` = agent report not directly confirmed,
> `[rejected]` = verification showed it is not true.
>
> **This report contains diagnosis only. Fixes proceed separately after per-item approval.**

---

## 0. Summary — Separating Signal from Noise

The 2 "CRITICAL" items raised by the diagnostic agents were **all rejected as over-classifications upon direct verification**.
This is the pattern that `03-analysis-quality.md` (no baseless claims) and `feedback_no_baseless_claims` warn against,
so the verification status is stated explicitly throughout the report.

| Area | Actual CRITICAL | HIGH | MEDIUM | Notes |
|:---|:---:|:---:|:---:|:---|
| env / physics | 0 | 1 | 4 | 2 agent CRITICALs → rejected/downgraded |
| algorithm | 0 | 1 | 3 | 1 agent CRITICAL → rejected (ignored standardization premise) |
| encoder/runner/student | 0 | 0 | 2 | Structure sound, only duplication exists |
| TDC | 0 | 0 | 2 | Control math correct, 1 C++ candidate |
| analysis | 0 | 1 | 3 | Decomposing the 4041-line eval_dr.py is the biggest opportunity |
| structure | 0 | 2 | 4 | config duplication + absence of tests are the core issues |

**The three highest-ROI items** (details in §7):
1. Decompose `analysis/eval_dr.py` (4041 lines) into modules + extract a shared metric/plotting library
2. Refactor the 9 config classes into base templates (25~40% duplication)
3. Add smoke tests for env/config/runner (currently only 1 test, for TDC)

---

## 1. Rejected / Downgraded Items (cleared up first)

### [rejected] constraints.py:88 — attitude cost `torch.max` is not a bug
The agent classified this as CRITICAL, but `torch.max(a, b)` with **two tensors** as arguments performs an element-wise maximum,
which is standard PyTorch behavior (reduction occurs only with a single tensor). Since two (N,) tensors `(roll.abs(), pitch.abs())` are passed,
the per-env max is computed exactly. It is not "accidentally correct" but **correct by specification**.
→ Actual grade: **LOW (readability)**. Switching to `torch.maximum` would only make the intent clearer; it is a mere nit.

### [rejected] constraint_trpo.py:462 — cost surrogate `1/(1-γ)` scale blows up the margin
The agent claimed "inflated 100× → log(margin) explodes → CRITICAL", but **the premise contradicts the code**.
At `constraint_trpo.py:437-438`, `cost_advantages_flat` is **standardized per-constraint by std before entering the surrogate**
(mean≈0, std≈1). Line 462 multiplies that standardized advantage by the ratio and averages it. Since the on-policy starting ratio≈1,
`cost_surrs ≈ mean(normalized advantage) ≈ 0`. Therefore it is `100 × ≈0 ≈ 0`, not "100×50".
The agent ignored the standardization and assumed the advantage was O(1).
→ **The margin-blowup claim is rejected.** However, whether the `1/(1-γ)` scale exactly matches the NORBC formula requires a paper cross-check, and
since `references/NORBC` contains no Python implementation it **cannot be settled at this time** (tagged separately in §3-A1 below).

---

## 2. env / physics (`albc_env.py`, `mdp/`)

### [unverified·HIGH] quaternion normalization gradient unsafe — `albc_env.py:847`
In `_quat_align_z_to()`, `axis / axis_norm.clamp(min=eps)` evaluates both branches, so when `axis_norm` is small the
gradient can blow up. However, this function is for the payload **visualization marker**, so it must be confirmed whether it is
actually included in the training gradient path. Recommend making it safe via `torch.nn.functional.normalize` or `+eps` in the denominator.
→ Downgrade to LOW if it does not affect training. **Confirming the call path before fixing is mandatory.**

### [unverified·MEDIUM] added-mass stability clamp uses DR'd inertia — `events.py:267`
The post-DR clamp checks `M_a < 0.95*I` against `hydro.rigid_body_inertia` (which already has `inertia_scale` applied).
If the actual PhysX inertia is not randomized by `inertia_scale`, the two diverge, risking forward-Euler divergence.
Linked to memory (`added mass stability: init validation + post-DR per-axis clamp 0.95*I`).
→ **The item with the highest physical inspection value.** Either clamp against the base inertia or scale the PhysX inertia too.

### [verified·MEDIUM] silent obs dimension mismatch — `albc_env.py:883`
Depending on `use_integral_obs`/`integral_dims` the obs changes 87↔84↔81, but there is no runtime assert.
Memory also records past confusion as "docstring 81D vs observation_space=87 authoritative".
→ Add `assert policy_obs.shape[-1] == cfg.observation_space` at the end of `_get_observations()`. Low cost, high benefit.

### [verified·MEDIUM] hot-loop tensor recreation — `albc_env.py:940`
`torch.tensor(sigmas, device=...)` is created every step. Allocating it once in `__init__` would suffice. Small gain at 4096 envs.

### [unverified·MEDIUM] ocean current OU exceeds max_velocity by 5% — `config.py:312`, `albc_env.py:674`
`clamp_bound = max_vel * 1.05` violates the spec (`max_velocity=(0.5,...)`) by 5%. May affect the encoder input distribution.
If intended, annotate it; otherwise clamp exactly.

### [unverified·LOW] in-place accumulation error (`_error_integral.mul_`, `:913`), yaw wrap edge (`:501`), manipulability normalization (`:489`), control decimation undocumented (`:457`), euler cache every step (`:1150`) — all have low correctness impact, batch them in the cleanup phase.

---

## 3. algorithm (`constraint_trpo.py`, `doraemon.py`, `constraints.py`)

### [verified] TRPO/IPO core math — correct
Confirmed by direct reading: gaussian KL (`:329`), Fisher-vector product double backprop (`:354`), CG+damping (`:367`),
step size `sqrt(2δ/sHs)`, line search checks surrogate improvement **AND** KL≤δ simultaneously (`:406`),
IPO adaptive threshold `max(d_k, J+α·d_k)` (`:308`), per-constraint cost adv standardization (`:437`). **Matches the standard implementation.**

### A1. [unverified·HIGH] formula consistency of the cost surrogate `1/(1-γ)` scale — `:462`
The margin blowup was rejected in §1, but **whether this scale matches the NORBC definition** is unsettled.
Generally `1/(1-γ)` is used for (a) the budget→threshold initialization conversion or (b) converting undiscounted cost to discounted.
Here it is multiplied again onto a cost advantage already discounted via GAE, so there is **suspicion of double application**.
However, since the advantage is normalized, the effective result is absorbed as a "scale constant on the barrier gradient" (can be cancelled with barrier_t=100).
→ **Requires paper cross-check or author (user) confirmation.** On its own, the guilty/not-guilty verdict is on hold.

### B. [verified·HIGH] barrier log clamp floor 1e-8 — `:464`
log after `margin.clamp(min=1e-8)`. If the margin drops below zero (constraint violation), log(1e-8)=-18.4 and the gradient blows up
to ~1e8. Rare with the current hyperparameters but can be triggered by a single outlier cost. Recommend raising the floor or a soft-barrier.
(But as seen in §1, the margin is normally stable, so this is HIGH, not CRITICAL.)

### [verified] DORAEMON — correct
Beta KL (`:125`), reverse-KL trust region, IS success-rate estimation + ESS verification (`:516`), entropy maximization + KL≤ε constraint.
Matches the standard implementation.

### [unverified·MEDIUM] cost returns `clamp(min=0)` hides bugs — `:443` / missing detach on monitoring tensor `:466` / hot-path assert (disabled under -O) `:473` / CG damping 0.1 may be too weak
All are robustness/observability improvements. Not fatal to correctness. Recommend adding logging + moving the assert into `__init__`.

---

## 4. encoder / runners / student

### [verified] architecture · gradient flow — correct, 0 aux losses
encoder input (privileged 24D → MLP → LayerNorm → softsign → z9D), actor=[obs87+z9], critic asymmetric,
z gradient flow normal, BPTT truncation normal. **0 grep hits for `reconstruction/contrastive/z_bounds/auxiliary`** —
confirms compliance with the "No Encoder Auxiliary Losses" rule in `03-analysis-quality.md`.

### [verified·MEDIUM] two actor-critic classes 80% duplicated — `actor_critic_encoder.py` vs `actor_critic_asym_constrained.py`
The intent to separate them for ablation is valid, but `act/act_inference/update_normalization/load_state_dict` are nearly identical.
They could be unified by raising the utilization of `PolicyBase` or extracting obs-composition as a strategy. **Low urgency** (both frozen).

### [verified·LOW] runner helper duplication — `constraint_encoder_runner` vs `on_policy_doraemon_runner`
`_should_log/_save_aux_state/_load_aux_state` duplicated. A code comment states it is "intentional duplication to avoid TRPO-specific inheritance".
Could be extracted into a mixin, but since it is intentional the priority is low.

---

## 5. TDC controllers (including C++ candidate)

### [verified] control math — correct
TDC law (one-step delay buffer indexing correct, no off-by-one, first-step PD fallback), Lambda coupling matrix + DLS,
2-link FK/IK/Jacobian, restoring torque sign. The existing test (`test_tdc_controller.py`, 478 lines) covers
Lambda/IK round-trip/reset, etc.

### [verified·C++ HIGH] `tdc.py` compute() hot-path → candidate for C++/CUDA migration
50Hz × num_envs, no autograd needed, pure tensor operations, stable interface. Estimated 5~20×. Matches exactly the
area where **the user permitted C++**. However, kinematics (analytic solution) and thruster_pd have small gains, so keeping them in Python is recommended (decide after profiling).

### [verified·MEDIUM] `compute_M_bb()` unused — `tdc.py:499`
Exported from `__init__.py` but with 0 call sites. Seems reserved for encoder-adaptive M_hat. Document it or remove it.

### [unverified·test gap] TDE delay buffer 1-step accuracy, rate-limit anti-windup, OOD robustness, and `update_gains` are untested.

---

## 6. analysis (the biggest cleanup opportunity)

### [verified·HIGH] `eval_dr.py` 4041-line monolith → decompose into 6 modules
Per subcommand (static/periodic/segmented/sudden), metric computation / plotting / DR config / trajectory / CLI are
all clumped into one file. Proposed structure: `cli.py`, `dr_config.py`, `trajectory.py`, `metrics/`, `plotting/`, `modes/`.
**Preserve the domain logic** and only separate the boundaries — reusable from analyze.py/compare.py/encoder_tools.py.

### [verified·MEDIUM] metric computation 5x duplicated + scattered magic numbers
SS window 0.5, heavy-tail thresholds 5.0°/0.1m, etc. are hardcoded in 3~5 places. Centralize in `common.py` as a `MetricsConfig` dataclass.
matplotlib `use("Agg")` is also repeated in 5 places → `plotting/common.py:setup_matplotlib()`.

### [unverified·MEDIUM] matplotlib figure leak / YAML exception swallowing — `eval_dr.py:2221` etc.
Most plot functions call `plt.close()` but without try/finally. On YAML load failure there is a risk of referencing an undefined `run_agent_dict`.
→ `save_and_close()` helper + initialize `run_agent_dict={}`.

---

## 7. structure / enterprise standards

### [verified·HIGH] 9 config classes 25~40% duplicated — `rsl_rl_ppo_cfg.py` / `ablation_cfgs.py` / `config_noconstraint.py`
`seed=30, num_steps_per_env=64, max_iterations=2500` etc. are 100% duplicated, policy/algo cfg 25~40% duplicated.
6 tasks cross-ref via string paths. → Define `_Base*Cfg` then only inherit/override. **The highest-ROI structural improvement** (§0).

### [verified·HIGH] absence of tests — only 1 in `tests/`, for TDC
env step/reset, config load, constraint evaluation, runner init, encoder forward are all uncovered.
→ Add smoke tests (env+10step, config load, runner+1iter). Also the absence of CI.

### [verified·MEDIUM] print 365 vs logger 54 (7:1)
Many ad-hoc prints in analysis/env code. Recommend standardizing on logging.

### [verified·MEDIUM] no deps version pins — `pyproject.toml`
`["marinelab","gymnasium","torch","numpy"]` have no upper/lower bounds. Reproducibility risk. Pins recommended.

### [unverified·MEDIUM] train.py builtins `__import__` hook / num_constraints auto-sync silent mutation / IPO barrier non-reusable structure — they work but are implicit. Recommend documenting/making them explicit.

---

## 7.5 Promoting general-purpose tools to marinelab (user proposal — verification complete)

> User proposal: "DORAEMON is a general-purpose tool, so move it to marinelab and have constrained-albc import and use it.
> Apply the same approach to other general-purpose algorithms."

### [verified] DORAEMON is eligible for promotion — 0 coupling to research code
The imports in `doraemon.py` are only `numpy/torch/scipy/isaaclab.utils.configclass`. **0 references inside `constrained_albc`**
(confirmed by grep). It does not break the layer dependency direction (isaaclab ← marinelab ← constrained-albc).

**The only research-coupling point = `_PARAM_DEFS` (`doraemon.py:69`)** — the names of 15 DR parameters are hardcoded to ALBC's
`DomainRandomizationCfg` field names. The engine (`DoraemonScheduler`/`BetaDistribution`/`EpisodeBuffer`) is
fully general-purpose. The coupling is only that `build_param_specs(dr_cfg)` reads (lo,hi) via `getattr(dr_cfg, field_name)`.

**Promotion design (engine=marinelab, parameter definitions injected from overlay):**
```
marinelab/marinelab/algorithms/doraemon/   (NEW — general-purpose engine)
  ├── scheduler.py   # DoraemonScheduler, DoraemonCfg
  ├── distribution.py# BetaDistribution
  ├── buffer.py      # EpisodeBuffer
  └── spec.py        # ParamSpec, build_param_specs(dr_cfg, param_defs)  ← param_defs as an argument
constrained-albc/.../constrained_full_albc/
  └── doraemon_params.py  # leave only _PARAM_DEFS (ALBC's 15 parameters) + nominal overrides
                          # from marinelab.algorithms.doraemon import DoraemonScheduler
```
Key change: make `build_param_specs` receive `_PARAM_DEFS` as **an argument** rather than as a module global.
Then the marinelab engine works with the DR cfg of other robots/research such as BlueROV.

### Other promotion candidates (preliminary assessment — unverified; on promotion, verify import boundaries via the same procedure)
| Candidate | Promotion eligibility | Basis |
|:---|:---|:---|
| **DORAEMON** | ✅ eligible (verified) | 0 research-code references, clean interface |
| TDC controller (`controllers/`) | △ conditional | A generic UUV buoyancy-control concept, but specialized to the 2-link arm/buoy. `kinematics.py` is general-purpose, `tdc.py`'s ALBC-specific coupling needs inspection |
| ConstraintTRPO + IPO barrier | △ conditional | General-purpose at the rsl_rl interface, but heavy cost critic/storage coupling. Could be general if only the IPO barrier is detached |
| BetaDistribution standalone | ✅ eligible | Part of DORAEMON, also useful as a standalone util |

→ **Recommendation**: promote DORAEMON first (cleanest, immediately possible). For TDC/TRPO, decide after separately diagnosing the import boundaries.

---

## 8. Recommended execution order (after approval)

```
Phase A (low-risk · no training impact) — immediately possible
  A1. add obs dimension assert (§2)              → verify: raise immediately on wrong obs
  A2. pre-allocate hot-loop sigma tensor (§2)    → verify: identical result + minor speedup
  A3. analysis MetricsConfig + plotting commonization (§6) → verify: reproduces existing plots
  A4. add env/config smoke tests (§7)            → verify: pytest passes

Phase B (structural refactor · behavior-preserving) — verification gate required
  B1. decompose eval_dr.py 4041 lines into 6 modules (§6) → verify: 4-mode output identical before/after
  B2. refactor config base-template (§7)         → verify: 6 task cfg.to_dict() identical
  B3. deps pins + logging standardization (§7)

Phase C (formula · physics — requires user confirmation/paper cross-check)
  C1. cost surrogate 1/(1-γ) consistency (§3-A1) → NORBC paper cross-check or author confirmation
  C2. added-mass clamp inertia basis (§2)        → review training-stability impact
  C3. barrier log clamp floor (§3-B)             → soft-barrier experiment

Phase D (performance — optional)
  D1. port TDC compute() to C++/CUDA (§5)        → verify: numerically identical to Python + speed
```

**Principle**: each item is independently verifiable. Phase C changes training behavior, so per memory and rules it is **not touched
without user approval + before/after data** (`feedback_no_unauthorized_changes`, `feedback_training_control`).

---

## 9. Re-verification supplement (2026-05-25, during marinelab v0.2.0 compatibility work)

This report was written **before** the marinelab API change. As a result of re-reading the code while doing the compatibility work,
a P0 item that DIAGNOSIS did not cover, and Phase A items that were already in place, were identified.

### P0 (not in DIAGNOSIS) — marinelab.core API incompatibility = runtime crash [fix complete]
As marinelab v0.2.0 split the ocean current into an independent `OceanCurrent` component, it removed the
`HydrodynamicsModel._current_velocity` / `._max_current_vel` buffers.
albc read/wrote these buffers in 8+ places, so it died with an immediate **AttributeError at env reset / OU step**.
→ Fixed by switching the paths to `hydro.current.velocity_w` / `.max_velocity` / `.set` + injecting (sharing) main's `OceanCurrent`
into the buoy. OU math unchanged.

### Phase A re-check — some already in place
- **A1 obs assert**: a construction-time assert already exists at `albc_env.py:138-143`
  (config vs computed obs dim). This time only the `_get_observations()` return-tensor runtime assert was added.
- **A2 hot-loop sigma**: already pre-allocated in `__init__` at `albc_env.py:153` (comment "Avoids re-allocating
  ... every step"). It was a no-op.
- **dead code re-judgment**: `randomize_ocean_current` is **live** (albc_env.py:1327,1412, eval_dr.py:601).
  The only unused one is `compute_M_bb` (tdc.py), removed this time.

### Phase C (training behavior change, separate approval required) re-check — still valid
- **added-mass clamp** (`mdp/events.py:258-271`): marinelab core made its own clamp safe via the base-inertia `_clamp_inertia`
  buffer, but **albc events.py's clamp is on a separate path** and is still based on the DR'd
  `rigid_body_inertia`. The forward-Euler divergence risk is unresolved. Highest inspection value.
- barrier log clamp floor 1e-8 (§3-B), cost surrogate 1/(1-γ) (§3-A1), OU 5% exceedance (§2): valid as-is.

> Since these 4 Phase C items change training behavior, **they are not touched without user approval + before/after data.**
