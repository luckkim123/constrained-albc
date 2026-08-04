---
title: "The obs76 teacher is a REAL-better controller than E-int at hard DR, but none of its advantage survives distillation to any student"
tags: ["obs4", "teacher", "student", "distillation", "dispersion"]
created: 2026-08-04T06:37:52.216962
updated: 2026-08-04T06:37:52.216962
sources: []
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: needs-experiment
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
