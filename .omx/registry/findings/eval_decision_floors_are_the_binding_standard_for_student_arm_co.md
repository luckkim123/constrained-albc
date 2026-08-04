---
title: "Eval decision floors are the binding standard for student-arm comparisons (0.1 deg / 15 envs)"
tags: ["eval", "decision-floor", "screening", "student", "distillation", "albc", "methodology"]
created: 2026-07-29T07:25:58.151005
updated: 2026-08-04T04:35:03.203619
sources: ["diagnose-20260729-161459"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Eval decision floors are the binding standard for student-arm comparisons (0.1 deg / 15 envs)

Every static eval summary.json carries `decision_floors` = {ss_error: 0.1, os_env_mean: 10.0, n_gt20: 15.0} with `decision_floors_protocol` = 'screening n=1 paired same-machine; |delta| below floor = noise'. Apply it BEFORE reading any inter-arm delta as an effect.

Measured consequence in campaign student_distill_eint (analysis diagnose-20260729-161459 on trpo_sdeint_b4b_beta05_s30_260729_153436, section 'tracking'):
- B4b vs A0 att_norm ss_error deltas = 0.0245 / 0.0316 / 0.0570 / 0.0776 deg (none/soft/medium/hard). ALL below the 0.1 deg floor -> the arm is a null result at eval level, despite a 10.5% relative 'win' at hard.
- A0g vs A0 deltas = 0.1384 / 0.1233 / 0.0929 / 0.0916 deg. Only none and soft clear the floor, so the recorded 'GRU better at all four levels' is decision-grade at TWO of four.
- roll n_gt20 spans 0.00-7.00 envs across all four runs against a 15-env floor. At 64 envs this metric detects catastrophe only, never degradation, so the recorded A0g 'tail regression' (7.00 vs A0's 5.67) is sub-floor and must not be cited as a real cost.

Practical rule: a relative percentage on a sub-0.1-deg absolute difference is not evidence. Convert to the axis unit and compare against the floor first (repo rule: sign consistency is not magnitude). No floor is declared for ss_error_std / CV, so dispersion differences cannot be adjudicated at n=1 under the current protocol -- that gap is itself worth closing.

---

## Update (2026-08-04T04:32:23.386929)

## LIMIT discovered 2026-08-04: the floors are PAIRED-only, and teacher-vs-student evals are NOT paired

The floors carry `decision_floors_protocol` = "screening n=1 paired same-machine". The word that
matters is PAIRED. Phase E (analysis diagnose-20260804-132500) found that a teacher eval and a
student eval do NOT share their DR draws at any level except `none`:

| level | dr_*/fault* keys differing (of 24) |
|:--|--:|
| none | 0 (DR off -- identity is trivial) |
| soft | 23 |
| medium | 23 |
| hard | 23 |

Consequence, measured on the Phase E pair (teacher static_260804_092723 vs student
static_260804_130704): the 0.10 deg ss_error floor called TWO regressions REAL at hard
(att_norm +0.1503, roll +0.1659 deg). Both are noise. The actual sampling standard error of those
deltas, SE = sqrt((std_t^2 + std_s^2)/64), is 0.2976 and 0.2790 deg -- roughly 3x the floor -- so the
two "REAL" rows sit 0.51 and 0.59 standard errors from zero. Across all twelve level x axis cells the
largest |delta|/SE is 1.43. Not one mean attitude delta is distinguishable from env-draw noise.

THE RULE THIS ADDS: the floors adjudicate a delta only when the two evals share their `dr_*` draws.
Student-vs-student arms in one campaign normally do; teacher-vs-student never does except at `none`.
Before applying a floor across run TYPES, either verify draw identity or switch to the dispersion-aware
test (compare |delta| against sqrt((std_a^2 + std_b^2)/n_env)), and say which one you used.

WHAT THIS DOES NOT CHANGE: within-campaign student-arm comparisons, which is what this page was
written for. The A0/A0g/B4b numbers above stand. What it invalidates is any teacher-vs-student floor
verdict, which should be re-read wherever one was recorded.

This is the sixth member of the campaign's denominator/draw family, after the B1b ratio-target
reversal, the B2 R2-delta decomposition, the WIDE mirror case, 38d979e, and the
d2-smallest-denominator ranking. Same shape every time: the metric was believed rather than decomposed.

---

## Update (2026-08-04T04:35:03.203619)

## Re-check of the affected prior verdicts (2026-08-04): Phase D SURVIVES

The LIMIT above says every teacher-vs-teacher / teacher-vs-student floor verdict must be re-read.
Done for the one that carries a recorded conclusion, rather than left as a standing doubt.

Phase D pair (E-int `trpo_eint_s30_rs2350_260727_195102` static_260729_133417 vs the obs76 teacher
`trpo_obs76fault_s30_260804_043926` static_260804_092723) is ALSO unpaired: 0 of 24 dr_*/fault* keys
differ at none, 23 of 24 at soft, medium and hard. Same defect. But its conclusions hold under the
dispersion-aware test, |delta| vs SE = sqrt((std_a^2+std_b^2)/64):

| level | axis | delta (deg) | SE | \|d\|/SE | verdict |
|:--|:--|--:|--:|--:|:--|
| soft | pitch | +0.1336 | 0.0419 | 3.19 | REAL, survives |
| medium | pitch | +0.1204 | 0.0286 | 4.21 | REAL, survives |
| none | pitch | +0.0612 | 0.0307 | 1.99 | borderline, under 2 |
| hard | att_norm | +0.0108 | 0.1888 | 0.06 | null -- H1's clause passes by a wider margin than the floor showed |
| hard | roll | -0.0651 | 0.1720 | 0.38 | null |

So the recorded Phase D result -- obs76 buys the hard-DR corner at the cost of a REAL pitch
regression at soft/medium outside H1's clauses, and H1 PASSES -- needs no correction. The pitch
regression is real by both tests, and the H1 hard clause is 0.06 SE from zero, i.e. an even cleaner
pass than the floor comparison suggested.

The Phase E student pair is where the two tests DISAGREE (floor says two REAL rows at hard, noise
says 0.51 and 0.59 SE), because that pair's hard dispersion is 3x larger. General shape: the floor
and the noise test agree when dispersion is ordinary and diverge exactly where a heavy tail makes the
floor over-sensitive. Run both; when they disagree, the arithmetic wins.

