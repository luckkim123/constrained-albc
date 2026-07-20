---
title: "TAM plant-correctness fix collapses the void hard-DR roll heavy-tail (into a raised floor)"
tags: ["heavy-tail", "roll", "TAM", "plant", "teacher-baseline", "doraemon"]
created: 2026-07-14T16:38:59.611547
updated: 2026-07-20T06:24:42.684595
sources: ["diagnose-20260715-011113"]
links: ["ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# TAM plant-correctness fix collapses the void hard-DR roll heavy-tail (into a raised floor)

DECISION/FINDING: the corrected-TAM teacher baseline (trpo_baseline_260714_192020) does NOT inherit the void baseline's (trpo_baseline_260713_031325) hard-DR roll steady-state heavy-tail — the plant fix collapses it, trading the catastrophic tail for a higher, tighter roll-error floor.

EVIDENCE (per-env roll ss = last-20%-window mean |error_roll|, code-exec on data_*.npz; eval ids cited):
- MATCHED +-15 box (static_260715_003649) vs void +-15 (static_260713_075722):
  - hard: max/median 25.3x -> 7.49x; top-6/64 share 49.1% -> 32.8%; peak_max 16.4deg -> 10.1deg.
  - ood:  max/median 28.3x -> 6.37x; top-6 share 51.9% -> 22.5%; peak_max 7.3deg -> 6.0deg.
  - Corroborated at the ONLY strictly-fair cross-run level (none, zero DR): 7.05x -> 4.26x, top-6 30% -> 18%.
- COST: the typical-env body ROSE (per-env roll: hard median 0.199 -> 0.440deg +121%, hard mean 0.389 -> 0.568deg +46%, none mean 0.229 -> 0.534deg +133%). So this is robustness-for-accuracy, not a free win.

CAVEAT (must honor): DORAEMON grades each run's hard/ood on its OWN learned DR (wiki eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr), so cross-run hard/ood ratios are NOT like-for-like; the verdict is qualitative (a >10x tail with ~half its mass in 6 envs -> a <8x tail with ~a third) and is corroborated at the fair none level. Do not present 25.3x -> 7.5x as a like-for-like delta.

GOTCHA: summary.json ss_error uses a DIFFERENT steady-state window than the per-env engine method; they are NOT interchangeable (hard roll rise +8% summary vs +46% per-env; ood disagrees in SIGN, -22% vs +6%). Use the per-env engine method for tail analysis; use summary.json only for the mean/CV cross-run view.

DUAL-BOX: widening the command box +-15 -> +-30 (same checkpoint, static_260715_004654) does NOT re-open a tail (hard roll max/median 7.49x -> 6.07x, top-6 33% -> 30%); pitch is the most box-sensitive axis (hard-pitch ss_error +80%: 0.295 -> 0.532deg). Re-visit analysis diagnose-20260715-011113 KEY QUESTION + generalization sections.

---

## Update (2026-07-20T06:24:42.684595)

## CORRECTION (2026-07-20): "robustness-for-accuracy" overstates the cost -- it is ~20:1 in the fix's favour

The "robustness-for-accuracy, not a free win" framing above (and the same wording in the
`teacher_baseline_posttam` campaign README) is a percentage-on-a-small-base artifact. Restated in
absolute degrees, on the same numbers already in this page:

| | change | absolute |
|---|---|---|
| GIVEN UP (typical env, hard per-env median) | 0.199 -> 0.440 deg | **+0.24 deg** |
| GIVEN UP (none mean) | 0.229 -> 0.534 deg | +0.31 deg |
| GAINED (worst transient) | 16.4 -> 10.1 deg | **-6.3 deg** |

Every absolute reference scale that exists in this repo puts the +0.24 deg well below significance
and the -6.3 deg well above it:

- actor's own attitude OBSERVATION noise: `_OBS_NOISE_STD` euler = 0.02 rad = **1.15 deg**
  (`envs/main/config.py:275`). The forfeited 0.24 deg is 21% of one sigma of the noise the policy
  is trained to see.
- attitude observation BIAS band the policy must tolerate: +-0.02 rad = **+-1.15 deg**
  (`config.py:292`).
- the only degree-valued threshold in the codebase: `rp_vel_settling` gate at 0.087 rad = **5 deg**
  (`docs/reference/constraints.md:157`). Note this is a constraint-cost ACTIVATION gate, not an
  accuracy spec.

There is NO project-wide accuracy specification and NO IMU (3DM-GX5) datasheet-derived noise floor
anywhere in `constrained_albc/`, `marinelab/`, `docs/`, or `.omx/` -- searched 2026-07-20, negative
result. The three scales above are proxies, not requirements. If a real hardware requirement of
~0.1 deg were ever established, this verdict would flip; until then it does not.

REVISED VERDICT: the TAM plant fix is close to a straight win on the error distribution. Prefer
"traded 0.24 deg of typical-case error for 6.3 deg of worst-case error" over "traded robustness for
accuracy". Do NOT open a next-experiment lead aimed at "recovering the lost accuracy" on the basis of
the +121% figure alone.

## CORRECTION 2 (2026-07-20): the two runs were graded on statistically indistinguishable DR draws

The CAVEAT above ("cross-run hard/ood ratios are NOT like-for-like ... do not present 25.3x -> 7.5x
as a like-for-like delta") is correct as a general rule but is MEASURABLY over-cautious for THIS
pair. The realized per-env DR draws in the two evals were compared directly, all 23 `dr_*` keys,
n=64 envs, `static_260713_075722` (VOID) vs `static_260715_003649` (POSTTAM MATCHED):

- median std ratio (posttam / void) at `hard` = **1.048**; same 1.048 median at soft / medium / ood.
- expected relative SE of a sample std at n=64 is ~1/sqrt(2*63) = **8.9%**, so a 5% median gap is
  inside sampling noise. Largest single-parameter gaps (`dr_cob_y` 1.234, `dr_cob_x` 1.189) are
  within ~2 SE and several parameters are clamped/non-Gaussian, which inflates finite-sample spread.
- code cross-check: ZERO commits touch any `DomainRandomizationCfg` range field between the two eval
  dates (last touches `7dcb0dd` 07-08 and `3e1f81f` 07-07; every commit in the 07-08..07-16 window
  verified to change TAM / bias-ema / latency / constraint-budget fields only).
- `data_none.npz`: all 23 params std=0 with identical means in both runs -- `none` confirmed
  genuinely DR-free and fair.

So the heavy-tail collapse IS effectively like-for-like for this pair, and the qualitative hedge can
be dropped for it. The general rule still stands for OTHER pairs and must not be discarded.

RESIDUAL GAP (do not overstate the above): only the STD (width) of the DR draws was compared at
`hard`. The MEANS were not. A center shift with unchanged width also changes difficulty -- that is
exactly the E2 dr-harder failure mode
([[ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder]]). Accurate statement: **widths match
within sampling noise; centers unverified.** Comparing hard-level per-parameter means is a zero-GPU
follow-up on the same npz files.

