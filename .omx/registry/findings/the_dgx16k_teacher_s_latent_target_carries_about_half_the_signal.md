---
title: "The dgx16k teacher's latent target carries about half the signal-to-noise of E-int's, which is a candidate mechanism for C3 non-transfer measurable without any student"
tags: ["latent", "distillation", "c3", "teacher-lineage", "non-transfer", "target-difficulty", "snr"]
created: 2026-08-14T07:53:20.321999
updated: 2026-08-14T07:53:20.321999
sources: ["wiki-backlog-20260814"]
links: ["the_c3_recipe_does_not_transfer_across_teachers_on_a_same_width.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: pattern
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The dgx16k teacher's latent target carries about half the signal-to-noise of E-int's, which is a candidate mechanism for C3 non-transfer measurable without any student

The two teachers whose C3 students disagree also differ in how much SIGNAL their latent target carries,
and that difference is a property of the TEACHER alone -- it needs no student to measure and is
therefore a candidate mechanism for the non-transfer that
[[the_c3_recipe_does_not_transfer_across_teachers_on_a_same_width_]] records as unidentified.

MEASURED from `summary_latent.json` on each arm's eval (`l_true_*` is the teacher's own latent; the
student never enters these two columns):

| level | E-int `l_true_envvar` | dgx16k `l_true_envvar` | ratio | E-int SNR | dgx16k SNR | ratio |
|:--|--:|--:|--:|--:|--:|--:|
| **none** | **0.008949** | **0.005159** | **0.58x** | **7.70** | **4.09** | **0.53x** |
| soft   | 0.011607 | 0.008217 | 0.71x | 13.96 | 6.22 | 0.45x |
| medium | 0.043012 | 0.029966 | 0.70x | 31.03 | 20.37 | 0.66x |
| hard   | 0.067635 | 0.047247 | 0.70x | 28.49 | 15.30 | 0.54x |

SNR here is `l_true_envvar_mean / l_true_tvar_mean` -- across-env spread (the thing a distillation
target exists to convey, since z is the reset-fixed DR vector) divided by within-episode wobble (which
for a reset-fixed target is pure estimation noise). `l_true_tvar` is comparable or slightly higher on
dgx16k at every level, so the SNR gap is driven by the numerator: **there is simply less across-env
signal in the dgx16k teacher's latent.**

READ THE `none` ROW, NOT THE HEADLINE AVERAGE. DR is OFF at `none`, so both arms sit on the identical
plant there and the comparison is anchor-fair. The other three levels are graded under each teacher's
OWN learned DR via `--doraemon-dr-from`, so their boxes differ by construction -- the standing rule
that only `none` is cross-run fair applies here exactly as it does to attitude
([[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]]). At the fair level the dgx16k
target carries 58% of the spread and 53% of the SNR.

COUNTERINTUITIVE AND WORTH NOTING: dgx16k SATURATED its curriculum (all 21 dims at Beta(1,1) from
iteration 7250) while a 5000-iteration buoyfix teacher stops at roughly 65% of its box. The teacher
with the WIDER trained box has the WEAKER latent spread. Whatever produces this, it is not "wider DR
gives more z spread".

CONFIDENCE MEDIUM, and here is exactly why. Three limits, none of them fatal but all of them real:
1. **n=1 for dgx16k.** Only one eval exists (`static_260810_011725`) and it saved no npz, only the
   summary. The E-int arm has four evals, three byte-identical and one variant, which bounds
   repeat noise at ~18% on `l_true_envvar` at `none` (0.008949 vs 0.007315) and ~10% at hard. The
   between-teacher gap at `none` is 42%, so it clears its own repeat noise by roughly 2.3x -- clearly
   but not overwhelmingly.
2. **Correlational.** A weaker target is CONSISTENT with worse distillation; it does not prove the
   causal path. The dgx16k student's `overall_mse` is indeed worse at every level (0.0360/0.0327/
   0.0377/0.0435 against 0.0236/0.0163/0.0337/0.0606), but note that at HARD the E-int arm's MSE is
   the WORSE of the two -- so absolute MSE does not track the control verdict either, which is the
   third instance of that pattern on this line.
3. **Two teachers is not a trend.** This is a paired observation, not a dose-response.

WHY IT IS STILL WORTH HAVING: it is the first quantity anyone has found that separates these two
teachers WITHOUT running a student, which is what a mechanism for a teacher-lineage effect has to look
like. It also suggests the cheap next probe: measure `l_true_envvar` and SNR at `none` on every teacher
this line has, and check whether it orders the teachers the same way their students' control verdicts
do. That needs no training -- only the latent block of an eval each.

