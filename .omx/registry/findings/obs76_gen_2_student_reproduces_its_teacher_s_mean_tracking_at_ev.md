---
title: "obs76 gen-2 student reproduces its teacher's mean tracking at every DR level but triples roll dispersion at hard; in-loop latent R2 stays negative, so the observability intervention did not close covariate shift"
tags: []
created: 2026-08-04T04:32:23.492837
updated: 2026-08-04T06:38:37.750117
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
---

# obs76 gen-2 student reproduces its teacher's mean tracking at every DR level but triples roll dispersion at hard; in-loop latent R2 stays negative, so the observability intervention did not close covariate shift

Phase E of program obs4-deployable-obs. Run `trpo_sdobs76_c3_gruselect_s30_260804_124951`
(campaign `student_distill_obs76`), C3 recipe (GRU 128 + head 64, dagger_mix=select, beta 0.5 fixed,
lambda_latent 1.0, lr 5e-4, 2048 envs, seed 30, 1000 iters), distilled from the Phase-D teacher
`trpo_obs76fault_s30_260804_043926`. Gen-2 interface: the 4 deployable channels live INSIDE policy_obs
(76D), so extra_obs_dim = 0. Eval static_260804_130704. Report: analysis diagnose-20260804-132500.

DELIBERATELY NOT COMPARED TO C3. The student reconstructs THIS teacher's latent, so C3's R2 and every
bar in student_distill_eint refer to E-int's z and do not carry over. Judged against its own teacher.

WHAT IT ACHIEVES
- Mean steady-state attitude tracking is statistically indistinguishable from the teacher at all four
  DR levels: max |delta|/SE = 1.43 over twelve level x axis cells.
- Transients preserved: roll overshoot median moves at most 1.24 pp, q90 at most 1.72 pp, n_gt40
  identical at every level.
- Pitch and yaw carry none of the effect. Survival 100% at none/soft/medium.
- Training converged cleanly: loss_latent 0.04820 -> 0.00400 (12.1x), dagger_teacher_frac 0.4964 ->
  0.5002 against a fixed beta 0.5, so dagger_mix=select behaved as configured.

WHAT IT COSTS, and it is a tail cost not a mean cost
- Roll steady-state dispersion at hard is 3.06x the teacher's (std 0.6928 -> 2.1218 deg), CV
  130% -> 303%; att_norm CV 110% -> 255%.
- 2 of 64 envs terminate at hard (t = 13.3 s and 22.3 s); the teacher loses none.
- The student/teacher roll CV ratio is monotone in DR strength from soft onward: 0.79, 1.50, 2.33.

WHY THE INTERVENTION DID NOT DO WHAT IT WAS PROPOSED TO DO
In-loop aggregate latent R2 is NEGATIVE at every level -- worse than a constant-mean predictor of the
teacher latent: -1.581 (none), -0.904 (soft), -0.131 (medium), -0.078 (hard). Only the hard number is
decision-grade; the `none` denominator collapses (per-dim Var_total spans 2.99e-5 to 6.47e-2, a 2163x
spread) exactly as this campaign already flagged for that level, while at hard the same quantity spans
only 3.8x. Positive-R2 dim counts rise with DR: 0/9, 1/9, 4/9, 6/9.

The train-to-in-loop latent MSE gap is 10-19x (training per-element MSE 0.00400 vs in-loop 0.0414 at
none and 0.0779 at hard). Training runs at beta 0.5; the eval is full closed loop. That gap IS the
covariate shift, measured rather than inferred, and folding the deployable channels into policy_obs
plus retraining the teacher on them did not shrink it.

More training is not the lever: loss_latent has plateaued (iters 600-800 mean 0.00442 vs 800-1000
mean 0.00417, slope -1.25e-6/iter), so even a LINEAR extrapolation -- a lower bound on an asymptoting
curve -- needs ~1600 further iterations to halve a quantity whose in-loop counterpart is an order of
magnitude larger.

TWO CONSTRAINTS ON READING THIS
- Per-dim latent indices are NOT comparable across teachers. The Phase-D encoder was trained from
  scratch; nothing pins latent dimension ordering or semantics, so d_k denotes different directions in
  the two teachers' latent spaces. Only aggregate and count statements survive a teacher swap.
- The teacher-vs-student tracking comparison is UNPAIRED (see the decision-floors page): the floors
  called two hard regressions REAL that are 0.51 and 0.59 SE from zero.

OPEN, and the limiting factor on reading any future student arm: the campaign registers no floor for
ss_error_std or CV, so a 3.06x dispersion change and a 2-env fatality land in the same
"cannot adjudicate at n=1" bucket as genuine noise. The only decision-grade cost this run carries is
invisible to the metric the protocol adjudicates.

---

## Update (2026-08-04T06:38:37.750117)

CLOSED 2026-08-04 by X1-tailsplit. Both halves of this pages finding now have attributed causes, and they are DIFFERENT causes.

(a) The negative in-loop latent R2 was the DELIVERY PATH, not the teacher: the tail-split re-distill from the same obs76 teacher recovered hard aggregate R2 from -0.1044 to +0.0645 (delta +0.169 vs a pre-registered 0.107 threshold). Fixable, and fixed.

(b) The tripled roll dispersion at hard was NOT fixed by that recovery - X1 sits at 3.130 deg absolute vs Phase Es 2.880 and C3s 2.526, so the delivery fix did not touch it. Dispersion tracks neither the teachers own dispersion (obs76 teacher: 1.072) nor the latent quality. See the teacher-advantage-does-not-distill page; the open problem moved from "observability" to "the distillation gap itself".

The env deaths follow the teacher, not the delivery: under paired draws the obs76 teacher, C3 and X1 all lose exactly 1 env of 64 at hard, while Phase E lost 2 (a 1.562 pp difference, below the registered 1.6 pp floor either way).
