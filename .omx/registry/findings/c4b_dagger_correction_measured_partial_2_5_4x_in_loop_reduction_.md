---
title: "C4b DAgger correction measured: partial (2.5-4x in-loop reduction at low-mod DR, under-dispersion floor persists at hard)"
tags: ["dagger", "student", "distillation", "covariate-shift", "albc", "observability", "dgx"]
created: 2026-07-30T06:06:14.644675
updated: 2026-07-30T06:06:14.644675
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: needs-experiment
blocked-on: "the residual cross-env under-dispersion (l_hat/l_true ratio ~0.12-0.16, worst at hard DR) needs the observability angle -- longer history window and/or an explicit velocity channel; that arm (E1) is itself blocked on an observation-interface implementation"
---

# C4b DAgger correction measured: partial (2.5-4x in-loop reduction at low-mod DR, under-dispersion floor persists at hard)



C4b on-policy DAgger correction RAN on the DGX 2026-07-24 at constrained-albc be42a2f (branch exp/dagger-correction, single commit off main 88e0849). Training: TCN student, anchor teacher trpo_buoyanchor_s30_260722_134743/model_4999.pt, 4096 envs, 1000 iters, dagger_beta 1.0->0.0 linear over 600 then held, --enable_cudnn (DGX cuDNN healthy), seed 42. Runtime 19.4 min (~1.16 s/iter). beta anneal VERIFIED from tfevents: iter0=1.0, 100=0.833, 300=0.5, 500=0.167, 600=0.0, held after -- args took, STOP condition passed. Final open-loop loss_latent=0.00518 (teacher-only was 0.00493; higher as beta drops = expected self-distribution, not a regression). time_collect ~0.72-0.84 s (cuDNN on, far below the ~17 s cuDNN-off penalty). New student: logs/rsl_rl/albc_trpo_student/trpo_buoyfix_dagger_s30_tcn_260724_133040/models/student_999.pt.

STEP-4 IN-LOOP READOUT (eval.py static, 64 envs, 4 DR levels; base open-loop residual 0.002145) vs the E4 teacher-only student baseline (trpo_buoyfix_s30_tcn_260722_184632):
- none    DAgger overall_mse=0.03833 (17.9x base) vs E4 0.15584 (72.7x) -> 4.07x reduction;  l_true_envvar=0.01935  l_hat_envvar=0.00312 (ratio 0.16)
- soft    DAgger overall_mse=0.04419 (20.6x base) vs E4 0.16190 (75.5x) -> 3.66x reduction;  l_true_envvar=0.02623  l_hat_envvar=0.00321 (ratio 0.12)
- medium  DAgger overall_mse=0.06798 (31.7x base) vs E4 0.16829 (78.5x) -> 2.48x reduction;  l_true_envvar=0.04429  l_hat_envvar=0.00615 (ratio 0.14)
- hard    DAgger overall_mse=0.14794 (69.0x base) vs E4 0.17613 (82.1x) -> 1.19x reduction;  l_true_envvar=0.09473  l_hat_envvar=0.01189 (ratio 0.13)

VERDICT: INTERMEDIATE / PARTIAL (mixed cause: covariate shift is real AND DAgger-addressable, but an under-dispersion floor persists that DAgger does NOT fix).
- H1 (covariate shift, DAgger fully works) NOT met by the pre-registered signature: overall_mse is NOT below l_true_envvar at ANY level (0.038>0.019 at none, gap widens with DR), and l_hat_envvar did NOT rise toward l_true_envvar -- the l_hat/l_true ratio stayed ~0.12-0.16, essentially unchanged from E4's ~0.14-0.18. The student STILL under-disperses across envs by 6-8x.
- H2 (pure observability floor, DAgger no help) also NOT clean: at none/soft DAgger cut in-loop error 4.07x/3.66x, far more than H2's "<=2x improvement" clause. So covariate shift WAS a substantial real component -- closing the train/deploy distribution gap materially reduced closed-loop error (72.7x base -> 17.9x base at none).
- Net: the improvement is large but DR-dependent -- 4x at none, collapsing to 1.19x at hard -- and the under-dispersion failure mode (l_hat_envvar collapse) is untouched at every level. overall_mse still exceeds l_true_envvar everywhere. This is a mixed cause: partly covariate shift (DAgger helped, keep it) and partly an observability/capacity floor that worsens with DR (DAgger cannot fix it; worst at hard).

CONSEQUENCE: partial adoption. On-policy DAgger distillation is worth keeping (it demonstrably cuts closed-loop latent error 2.5-4x at low-moderate DR), but it is NOT sufficient alone for deployment: the residual cross-env under-dispersion, worst at hard DR, needs the observability angle (longer history window and/or an explicit velocity channel) as a complementary fix. No blanket deployment claim. per_dim_mse (hard: dims 5/7/3 dominate 0.286/0.254/0.182) is EXPLORATORY only per the z_sweep caveat, not a criterion.


