# Experiments Archive

> ARCHIVE — historical narrative, not maintained as reference. Current experiment results
> live in the experiments/ tree (exp-analyze reports); durable findings live in the omx
> wiki (`omx wiki query`).

Consolidated record of the full ALBC experiment campaign (2026-04-04 ~ 04-18) plus
the two root-cause investigations that preceded it. Raw per-round files were compressed
into this single lookup table; the machine-readable run index lives in
[`experiments-index.json`](experiments-index.json). Per-run eval/training PNG plots
survive in the gitignored `experiment-plots/` directory (repo root) — see its
[`README.md`](../../experiment-plots/README.md) for layout. Raw checkpoints and
TensorBoard/wandb logs were deleted (2026-05-25) as their runtime environment no
longer exists post repo-3split; only `r13_A`/`r13_B` `model_4999.pt` are kept under
`experiment-plots/_final_models/`.

> **Currency caveat.** "BEST POLICY" / "first simultaneous SS+OS improvement" below are
> *historical training-metric claims*. Per current project ground truth, **no successful
> training run exists** — these labels describe relative progress within the campaign,
> not a deployable policy.

## Two cross-cutting threads

- **Settling-constraint dead end** (Round 3 → 5): the binary-gate `(err<thr)·|dv|`
  incentive is structurally untunable. Failed 3 times, then permanently abandoned.
- **Integral-observation lineage** (Round 5 audit → R7 3D → R8 6D error-gated): the
  single biggest surviving design element. The current 87D obs carries the 6D
  error-gated integral directly from Round 8.

---

## Pre-round infrastructure (04-04 ~ 04-13)

- **Change:** Stabilize the stack before experiments — DORAEMON optimizer
  (trust-constr → SLSQP, log-space Beta, `kl_ub` 1.5→0.04, `perf_lb` 200→90, 15D
  physics-only); build `eval_dr_fulldof` (fix DR-anchor bug capping eval at ~40% range);
  settle 3-term exp+quad reward (att k=9.0 / lin 4.0 / yaw 3.5, sigma 0.10) + 10
  constraints; diagnose entropy collapse.
- **Result:** DORAEMON stable; corrected eval → att SS 1.9-2.3°, 100% survival.
  Entropy-collapse root cause: `entropy_coef` is the sole upward pressure
  (coef=0.003 recovers noise 0.36→0.55; coef=0 collapses to 0.12).
- **Verdict:** merged — defines the Round-1 baseline. Adaptive entropy, ERC-TRPO,
  HardDR expansion all rejected here.
- **Carried forward:** DORAEMON (`kl_ub=0.04`, `perf_lb=90`), eval methodology,
  exp+quad reward, 10-constraint system, `entropy_coef=0.003` + per-dim `min_std`.

## Round 1 — Per-dim entropy coef (04-14)

- **Change:** Per-dim `entropy_coef` (arm=0.01, thr=0.001) vs uniform 0.003; also
  `max_std` cap 2.0→1.0. (1024 envs, 2500 iters.)
- **Result:** PerDimEnt best — reward +5.6%, att_rp 5.03° (+9.1%), smoothness 2.2× better.
  MaxStd1 negligible (dim never hit cap), worst reward.
- **Verdict:** merged — PerDimEnt clearly superior; `max_std` cap kept as secondary aid only.
- **Carried forward:** PerDimEnt (arm=0.01, thr=0.001) — permanent entropy config thereafter.

## Round 2 — PerDimEnt validation under harder DR (04-14 ~ 04-15)

- **Change:** Attribute PerDimEnt gain to arm-boost vs thr-reduction; PerDimEnt vs
  ArmOnly (thr=0.003) vs uniform at `kl_ub=0.06` (2048 envs, 5000 iters).
- **Result:** PerDimEnt best (reward 151.3, DORAEMON success 0.811). ArmOnly *worse*
  than baseline — arm boost propagates to thrusters and diverges (thr 1.36).
  Low entropy (−0.26) not a problem.
- **Verdict:** merged — thr entropy reduction identified as the key ingredient.
- **Carried forward:** PerDimEnt locked; `perdiment_kl06` run becomes control baseline for R3-6.

## Round 3 — L1 penalty + settling constraint (04-16)

- **Change:** exp+quad reward has `dr/de=0` at `e=0` (dead zone). Add (a) L1 linear
  penalty (lin_vel/yaw, ratio=0.15); (b) lin_vel/yaw settling constraints.
- **Result:** L1 improved SS (vx −15…−21%, yaw −10…−21%) but degraded OS (att +25…60%,
  vx +49…86%). Settling = catastrophic: yaw SS 0.012→0.27-0.34 (+20×), reward −31%.
- **Verdict:** L1 inconclusive (SS/OS tradeoff, can't win both); settling = dead-end
  (binary-gate perverse incentive, untunable). [strike 1]
- **Carried forward:** nothing direct. Dead-zone diagnosis motivates Round 4.

## Round 4 — Saturating penalty Tanh/Arctan (04-16)

- **Change:** Replace L1 with `coef·eps·tanh(|e|/eps)` / arctan (coef=1.0, eps=0.10)
  on lin_vel + yaw.
- **Result:** Per-env OS metric overturned the "Arctan wins" framing — Arctan roll OS
  17.1% (worst), yaw +26%; saturating penalty eroded lin_vel reward ~40% with no SS gain.
  No run improved all axes — **TAM coupling dominates** (independent thruster vz improves;
  shared-thruster vx/vy/yaw mixed).
- **Verdict:** rejected at coef=1.0 (gradient 6.7× L1, erodes reward).
- **Carried forward:** Per-env OS metric (methodology) survives and reshapes later analysis.
  Key conclusion: SS root cause is **observation structure (no integral obs)**, not reward
  shape. Recalibration target coef=0.3 → Round 6.

## Round 5 — Constraint budget tuning (04-17)

- **Change:** Tighten `rp_vel_settling` budget 0.20→0.08; reactivate lin_vel/yaw
  settling with relaxed threshold 0.04→0.10.
- **Result:** rp_vel tightening over-damped — roll SS 1.68→1.90° (+13%), rise time +29%.
  Settling reproduced catastrophe: yaw SS 0.025→0.308 (+1117%), reward −30%.
- **Verdict:** rejected (rp_vel over-damps) / dead-end (settling fails 3rd time →
  declared structural dead end). [strike 3]
- **Carried forward:** Settling-constraint family permanently abandoned. Per-env
  sigma-ratio confirmed as robust-vs-regression discriminator. Obs-structure audit
  (26D proprio has no error/integral term) sets up Round 7.

## Round 6 — Axis-specific shape calibration, coef=0.3 (04-17)

- **Change:** Per-axis winning shapes from R4: Arctan on attitude (coef=0.3) vs Tanh
  on velocity (coef=0.3).
- **Result:** AttArctan backfired — pitch SS +62%, pitch OS 9.4→18.8° (direct attitude
  penalty causes overcorrection-oscillation). **VelTanh = first run to pass 4/4 none-DR
  targets** (roll 1.05, pitch 0.69, vy 0.037, yaw 0.011); roll fails at medium DR.
- **Verdict:** VelTanh merged (new baseline); AttArctan rejected (attitude direct-penalty
  structurally counterproductive).
- **Carried forward:** VelTanh (velocity-only saturating penalty, coef=0.3) → R7 baseline.

## Round 7 — Integral observation (04-17 ~ 04-18)

- **Change:** From VelTanh: (a) EpsSmooth (tanh_eps 0.10→0.20); (b) Integral — add 3D
  leaky integrator [roll_err, pitch_err, vy_err] to obs (81D→84D, leak=0.99, clamp±2.0),
  per Hwangbo 2017.
- **Result:** EpsSmooth failed (blunt: pitch SS +90%, yaw 3× worse). **Integral
  succeeded:** att SS −64% (none) / −59% (hard), vy SS −56%, reward +54%; but yaw SS +94%
  worse (integral not applied to yaw). OS rose (pitch +80%) — diagnosed as learned
  "slow-start + integral push," not windup (`|I|↔OS` r=−0.37).
- **Verdict:** Integral merged (structural win transcending reward-shape tuning);
  EpsSmooth rejected.
- **Carried forward:** Integral observation → current 6D error-gated integral obs.
  R7's 3D limit + yaw regression motivate the R8 6D expansion.

## Round 8 — Error-gated 6D integration (04-18) — "BEST POLICY"

- **Change:** Expand to 6D integral (→ 87D obs); fix R7's OS rise via error-gating
  (`accumulate only when |err| < reward_sigma`). Compare vs ungated and FastLeak (leak 0.95).
- **Result:** **First run to improve SS and OS simultaneously** — aggregate SS 0.131 /
  OS 13.1%; vs R7 att SS −15%/OS −48%, vel SS −53%/OS −52%, yaw SS 0.021→0.001 (−95%, 6D
  fix). 36/48 metrics significantly better than R7. FastLeak worst. Remaining weakness:
  yaw OS 34.4%; roll SS high per-env variance (CV=1.19).
- **Verdict:** merged. ⚠ "BEST POLICY" is a historical training-metric label only —
  open items (yaw OS, roll variance, universal entropy collapse) remained unresolved and
  no successful training run was confirmed.
- **Carried forward:** **6D error-gated integral obs (87D) = the current design.**

---

## Root-cause investigations (pre-campaign)

### Encoder ablation — why online encoder co-training destabilizes (03-27 ~ 03-30)

- **Setup:** 20+ single-variable experiments isolating why an online encoder crashes
  PPO/TRPO in 2-DOF ALBC (Fisher amplification, z-saturation, normalization, LR, freeze,
  critic asymmetry, log_std vs scalar, `act()` clamp).
- **Result:** Root cause = `sample().clamp(-1,1)` in `ActorCriticEncoder.act()` piling
  actions at boundaries → KL spikes 100× → LR crash. Secondary = env-clamp + unclamped-
  action buffer positive-feedback loop (noise_std→148). History-only PPO (no encoder)
  works fine. 11/12 hypotheses disproved.
- **Verdict:** Online encoder co-training = dead-end in 2D action space → resolved via
  offline encoder pipeline.
- **Carried forward:** Diagnostic lesson (action-clamp = KL poison) survives. ⚠ This is
  2-DOF / HORA-aligned work; the online/reconstruction encoder path is NOT current
  (current = asymmetric encoder elu+LayerNorm+softsign, latent=9). Mostly historical.

### Arm freeze analysis — absolute-EE action traps arm at boundary (03-26)

- **Setup:** Diagnose policy freezing the arm at max extension within 100 iters
  (roll 40° / pitch 20° plateau).
- **Result:** H1 confirmed — tanh saturation + absolute-EE action whose physical optimum
  sits at the boundary creates a flat reward landscape (EE range 0.022m of 0.922m,
  advantage = noise). Smoothness penalty −0.5 accelerates the trap.
- **Verdict:** root-cause confirmed → switch absolute-EE → delta-EE (optimum recentered
  at 0), reduce smoothness_weight −0.5→−0.05.
- **Carried forward:** Delta-EE decision survives in spirit (current arm action is
  delta / joint-PD, not absolute/EE-position which is deprecated).
