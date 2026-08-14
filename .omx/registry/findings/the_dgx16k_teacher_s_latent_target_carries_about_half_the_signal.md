---
title: "The dgx16k teacher's latent target carries about half the signal-to-noise of E-int's, which is a candidate mechanism for C3 non-transfer measurable without any student"
tags: ["latent", "distillation", "c3", "teacher-lineage", "non-transfer", "target-difficulty", "snr", "retraction", "provenance", "census"]
created: 2026-08-14T07:53:20.321999
updated: 2026-08-14T08:37:14.001617
sources: ["wiki-backlog-20260814", "diagnose-20260814-172325"]
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

---

## Update (2026-08-14T08:37:14.001617)

## WITHDRAWN 2026-08-14: the dgx16k column has no measured teacher behind it

The dgx16k column of the table above comes entirely from static_260810_011725, an eval whose
subject is unrecoverable: the run it sits under never trained (zero "Learning iteration" lines, no
log directory, empty config/, no wandb run; full chain on
[[the_c3_recipe_does_not_transfer_across_teachers_on_a_same_width_]] and in analysis
diagnose-20260814-172325). The 0.58x spread and 0.53x SNR figures are therefore WITHDRAWN, and
with them caveat 1's "n=1 for dgx16k" framing -- the correct count is n=0.

Confidence is dropped from medium to low: the E-int column survives, the comparison does not.

## What the census this page proposed actually found

This page proposed the cheap probe: measure l_true_envvar and SNR at none on every teacher and
check whether it orders the teachers as their students' control verdicts do. That census was run
2026-08-14 over 26 evals / 15 arms / 4 lineages. Three lineages had valid data; dgx16k had none.

l_true_envvar at none, clean post-fix evals, per teacher:
- buoyfix       0.020847-0.022419, mean 0.021422, SNR mean 9.95
- obs76         0.013049-0.015238, mean 0.013850, SNR mean 10.19
- E-int         0.007656-0.009617, mean 0.008951, SNR mean 6.61
- dgx16k        VOID, never trained

THREE RESULTS, in descending order of how much they constrain:

1. THE STATISTIC INVERTS ACROSS DR LEVELS, which by itself kills the proposed action. In the one
   fully paired pair (E-int C3 static_260804_144932 vs obs76 C3 static_260804_145821, 27/27
   identical dr keys at ALL four levels, so soft/medium/hard are legitimately comparable here) the
   obs76/E-int SNR ratio runs none 1.58x, soft 0.73x, medium 0.72x, hard 0.89x, and the
   l_true_envvar ratio runs 1.81x, 1.36x, 0.86x, 0.85x. none is the ONLY level at which obs76
   leads on either statistic -- and none is the level this page reads. A selection statistic whose
   sign depends on which level you read it at cannot select teachers.

2. NO MONOTONE RELATION across the three valid lineages. Latent-signal ranking is
   buoyfix > obs76 > E-int; student control ranking is E-int approximately equal to obs76, both
   far ahead of buoyfix (roll ss_error 0.415 / 0.372-0.441 / 0.522-0.613 deg; n_gt20 0.333 /
   2.33-3.33 / 13.00-21.33 envs of 64). The teacher with the WEAKEST latent target has the
   joint-best student. buoyfix is recipe-confounded (TCN/DAgger, not C3-GRU) and unpaired, so it
   constrains rather than proves.

3. l_true IS NOT A PURE TEACHER PROPERTY, which is the premise this page rests on. l_true =
   f_teacher(s_t) and s_t comes from the student's own rollout. Measured directly on the C1-latsens
   sweep -- same teacher, same student WEIGHTS, only the latent handed to the frozen actor
   perturbed -- l_true_envvar at none moves from 0.009078 to 0.007787, i.e. -14.2%. Across ten
   distinct students on the E-int teacher the span is 1.26x. Teacher separation still clears that
   band (1.55x E-int to obs76, 2.39x E-int to buoyfix) but by only about 1.2-1.9x, which is
   thinner than a teacher-only reading implies.

## Correction to this page's own noise bound

Caveat 1 bounds E-int repeat noise at "~18% on l_true_envvar at none (0.008949 vs 0.007315)".
Those two evals are static_260729_194845 and static_260804_144932, which straddle the per-level
reseed introduced by commit 9eac3a8. That is a PROTOCOL CHANGE, not repeat noise, and it bounds
nothing. Use instead the two bounds measured above: 1.26x across ten students on one teacher
(rollout + arm variation), and -14.2% under pure latent perturbation (rollout alone).

Separately: five of the six a0g_gru evals are the C1-latsens perturbation sweep, not repeats
(roll ss_jitter 0.126 / 0.149 / 0.197 / 0.298 / 0.538 when sorted, launched in three concurrent
pairs 18:08-18:28 on 2026-07-29, 34 minutes before commit a8ae34a added the injector). Treating
them as repeat measurements inflates any noise bound roughly fourfold.

