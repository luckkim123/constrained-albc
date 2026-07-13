---
title: "eval.py static --doraemon-dr grades each run on its OWN learned DR — cross-run hard/ood is non-comparable, only none is fair"
tags: ["eval", "doraemon-dr", "cross-run", "comparability", "confound", "none-level", "static", "heavy-tail", "e1"]
created: 2026-07-13T10:08:05.594876
updated: 2026-07-13T10:08:05.594876
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md", "eval.py", "dr_config.py"]
links: ["an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_.md", "cross_run_reference_values_must_be_re_extracted_fresh.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# eval.py static --doraemon-dr grades each run on its OWN learned DR — cross-run hard/ood is non-comparable, only none is fair

`constrained_albc/analysis/eval.py static` defaults `--doraemon-dr` to True
(eval.py:93-97, BooleanOptionalAction default=True). When set, each run's eval loads THAT
run's OWN final learned DORAEMON distribution (eval.py:1074-1078 -> load_doraemon_dr(run_dir);
constrained_albc/analysis/dr_config.py:206 "hard range = learned mean +/- 2*std from the run's
TB/curriculum trajectory"). So the soft/medium/hard/ood exam is RUN-RELATIVE: two runs' "hard"
are DIFFERENT physical distributions, each scaled to that run's own learned curriculum width.

Consequence for cross-run comparison: if run A's curriculum widened (inertia_scale Beta-std
0.268) and run B's stalled narrow (0.111, 2.4x narrower), then B's "hard" is a much MILDER exam
than A's "hard". Comparing their hard/ood metrics directly is apples-to-oranges -- a
narrower-curriculum run can post BETTER hard/ood tracking purely because it was graded on an
easier distribution, not because it generalizes better.

Only the `none` level (nominal physics, no DR) is a FAIR cross-run comparison -- it is the same
fixed distribution for every run. Every other level entangles the intervention effect with the
two runs' different learned curricula.

Concrete instance (e1 latency probe vs baseline, 2026-07-13): e1's apparent hard/ood heavy-tail
"win" (roll max/median 23.2x->5.5x, top-6/64 49%->26%) was an eval-difficulty ARTIFACT -- e1's
curriculum stalled (see [[an off-DORAEMON channel that costs return stalls the curriculum below
the alpha floor]]), so e1 was graded on a narrower distribution. At the matched `none` level e1
was 3.6x WORSE (att_norm ss_error 1.903 vs 0.532) -- the true direction.

Rule when comparing runs whose curricula may differ: anchor the cross-run claim to `none`, OR
re-eval BOTH runs under a SHARED fixed distribution (`--no-doraemon-dr`, or `--doraemon-dr-from
<one run>` so both take the same exam). Never read a cross-run hard/ood delta as a
generalization result without first checking the two runs' end-of-curriculum widths are
comparable. Related sibling gotcha: [[cross-run reference values must be RE-EXTRACTED fresh]].
