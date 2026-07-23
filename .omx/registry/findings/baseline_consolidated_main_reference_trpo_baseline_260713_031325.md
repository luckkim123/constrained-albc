---
title: "baseline (consolidated main) reference: trpo_baseline_260713_031325"
tags: ["baseline", "attitude", "heavy-tail", "reference", "P7"]
created: 2026-07-12T23:46:26.844974
updated: 2026-07-23T07:42:44.097202
sources: ["diagnose-20260713-081707", "session-260713-p7tail-design"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# baseline (consolidated main) reference: trpo_baseline_260713_031325

New P7 reference run (from-scratch teacher on consolidated main commit 7ac39c8; delta = thruster-dt 4x fix, 28D union p_t, M1 encoder-in-value-optimizer, clip_fraction logging, thruster-curve OFF). Healthy baseline: training converged ~iter 490 then plateau (DR-hardening not stall), line_search 100%, Loss/kl 0.005, all 10 Constraint/margin/* >0, encoder z_std 0.387 non-collapsed. Eval static (64 env, none/soft/medium/hard+ood): sub-degree mean ss_error every axis every level (att_norm 0.53 deg none -> 0.72 deg hard; yaw ~0.005), survival 100% at ALL levels incl ood. THE weakness = hard-DR steady-state heavy-tail on roll(worst)>pitch: per-env median |error_roll| max/median 5.7x(none)->23.2x(hard)->29.2x(ood), top-6/64 share 27%->49%->51% (data_*.npz); jitter small (not oscillation), sample-env hugs mean (no axis-decorrelation). Next-experiment target = shrink the hard-DR tail not the mean (P7 obs-noise-DR / latency-DR leads). Full report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:33:17.361855)

## Update (2026-07-13): obs-noise DR was LIVE in this baseline (P7 lead retired) + p7_tail campaign launched

Correction to the next-experiment framing above: `obs_noise_scale` was a live DORAEMON dim during
this run (NDIMS=18; env.yaml `obs_noise_scale_range=(0.0,1.0)`), so "obs-noise DR ON" is NOT a
pending experiment — it is consumed. Realized exposure stayed near-nominal: TB
`DORAEMON/mean/obs_noise_scale` 0.010 -> 0.054 and std 0.010 -> 0.051 over 5000 iters — the
curriculum barely widened this dim, matching the obs-noise design doc's NDIMS-dilution
reservation (KL budget spread over 18 dims + performance_lb gating). Also note the baseline
group DESIGN.md originally recorded this toggle as OFF; corrected 2026-07-13.

Follow-up campaign `p7_tail` (2026-07-13, both proposals reviewer-approved): e1_latdr =
control_delay_steps (0,0)->(0,3) (proposal next-20260713-122215); e2_biasobs = expose _bias_ema
as 3D obs channel, o_t 69->72D, theory-review R1 (proposal next-20260713-122216). One variable
each vs trpo_baseline_260713_031325. Campaign DESIGN.md:
experiments/rsl_rl/albc_trpo_teacher/p7_tail/DESIGN.md.

---

## Update (2026-07-23T07:42:44.097202)

2026-07-23 curation: PRE-TAM-FIX CAVEAT -- this run (diagnose-20260713-081707, teacher_baseline_opt) trained on a TAM plant known-wrong per the incident post-mortem. Do not treat as the current baseline. Live post-TAM-fix reference: teacher_baseline_posttam (see tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_.md).
