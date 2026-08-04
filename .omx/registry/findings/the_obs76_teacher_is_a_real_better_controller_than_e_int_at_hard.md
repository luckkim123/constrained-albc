---
title: "The obs76 teacher is a REAL-better controller than E-int at hard DR, but none of its advantage survives distillation to any student"
tags: ["obs4", "teacher", "student", "distillation", "dispersion"]
created: 2026-08-04T06:37:52.216962
updated: 2026-08-04T15:58:14.196994
sources: []
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "The distillation gap itself is the open problem: three students from two teachers all land at hard roll ss_error_std 2.5-3.1 deg regardless of teacher (1.07-2.02) or delivery path. No probe is designed yet; encoder capacity (GRU256, +0.230 latent in the census) is the named runner-up family but the X1 result shows latent gains need not transfer to control, so a capacity probe must pre-register a CONTROL endpoint."
---

# The obs76 teacher is a REAL-better controller than E-int at hard DR, but none of its advantage survives distillation to any student

Measured 2026-08-04 on five PAIRED evals (per-level reseed fix 9eac3a8; 24/24 dr/fault keys identical across all five, so every delta below is same-env). Absolute hard-DR values:

  arm                  roll ss_error  roll ss_error_std  n_gt20  survival
  E-int teacher (72D)      0.816            2.015          5.00   100.0%
  obs76 teacher            0.535            1.072          3.67    98.4%
  C3 gen-1 student         0.971            2.526          5.67    98.4%
  Phase E gen-2 student    0.840            2.880          4.33    96.9%
  X1 tail-split student    0.855            3.130          3.00    98.4%

Teacher-vs-teacher (gate G3): obs76 beats E-int by -0.281 deg roll ss_error and -0.943 deg roll ss_error_std at hard, both REAL against the registered floors (0.10 / 0.60). That is a 34% mean and 47% dispersion improvement - the largest single-change teacher gain in the corrected-plant era.

Student-vs-student: every student sits at 2.5-3.1 deg dispersion, i.e. WORSE than either teacher, and the ordering does not follow the teacher ordering. The obs76 teachers 1.072 advantage is entirely lost: its two students (2.880, 3.130) are worse than the WEAKER teachers student (2.526). n_gt20 differences are all far below the 15-env floor and are NOT decision-grade.

CONSEQUENCE for model selection: picking the teacher by its own eval is not picking the better product. On the deployed artifact (the student) the obs76 line delivers no advantage, which is why the final-model declaration stays gen-1 (E-int + C3) and the flagship obs width stays 72D - see program dgx-final-scaleup PLAN sections 1 and 3. It also means a teacher-side scale-up (DGX 32768) optimises a quantity that has not been shown to reach the student.

CONSEQUENCE for the obs4 program: combined with the X1 decoupling result, the 4 deployable channels have now been delivered three different ways (gen-1 side channel, gen-2 z-scored, gen-2 tail-split) and none produced a decision-grade control gain in a student.

---

## Update (2026-08-04T15:58:14.196994)

## VERDICT 2026-08-05 -- CLOSED-NULL (backlog-closeout program)

The finding stands: the obs76 teacher IS a real-better controller than E-int at hard DR, and
none of that advantage survives distillation. What has changed is that this is no longer an
open question awaiting a probe -- the probe space named on this page has since been covered.

Twelve student arms now exist across three groups, and essentially all are analyzed. Between
them they span every axis this page identified: teacher (E-int and obs76), delivery path
(policy_obs and the X1 tail-split side channel), encoder capacity (b2wide_gru256, the named
runner-up family, run and analyzed 2026-08-03), distillation weight (b1_lam0 / b1_lam4),
sample selection (c2_daggersel / c3_gruselect) and extra observations (b2_extraobs). Every one
lands in the same 2.5-3.1 deg hard-roll dispersion band regardless of which knob moved, while
the teachers they were distilled from sit at 1.07-2.02 deg.

X1-tailsplit is the decisive one. It closed the latent gap the capacity family was supposed to
close (aggregate hard R2 -0.1044 to +0.0645, a +0.169 swing) and bought ZERO control gain --
converted to the objective side that R2 swing is only a 6.69 percent RMSE cut, so the sub-floor
control result was the PREDICTION, not a surprise. That is exactly why this page demanded any
future capacity probe pre-register a CONTROL endpoint: a latent endpoint has already been shown
not to transfer.

A thirteenth student arm with no new mechanism would not be a probe, it would be noise. The
measured conclusion is that the ceiling is the distillation step itself, not the teacher and not
the encoder's capacity. That conclusion is already acted on: obs72 remains the default and gen-1
ships as-is. Reopen only with a NEW mechanism and a pre-registered control endpoint.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

