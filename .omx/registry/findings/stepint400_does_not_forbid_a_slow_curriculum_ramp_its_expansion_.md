---
title: "stepint400 does not forbid a slow curriculum ramp: its expansion budget was 2.40 KL against the 3.12 needed to saturate, so it tested under-saturation rather than the knob"
tags: ["doraemon", "curriculum", "step_interval", "kl_ub", "budget", "citation-correction", "methodology"]
created: 2026-08-09T07:16:06.097980
updated: 2026-08-09T07:16:06.097980
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# stepint400 does not forbid a slow curriculum ramp: its expansion budget was 2.40 KL against the 3.12 needed to saturate, so it tested under-saturation rather than the knob

`trpo_stepint400_260720_180208` is cited across this campaign as the measurement that forbids slowing
the DORAEMON curriculum ("the worst of three arms at the fair `none` level"). It does not support that
reading, because it never reached the box ceiling.

THE ARITHMETIC, from the run's own recorded config (`max_iterations: 8000`, `step_interval: 400`,
`kl_ub: 0.12`):

    expansion budget = (max_iterations / step_interval) x kl_ub = (8000/400) x 0.12 = 2.40 KL

Saturation on that same posttam plant needs **3.12** (extend8k: 26 boundaries x 0.12, box at Beta(1,1)
by iter 7000). So stepint400 was 23% short of the budget required to saturate and stopped on a
partially-opened box. Its poor `none` score is confounded with under-saturation — exactly the failure
the curriculum recalibration protocol names: "widen the box at a fixed budget and the run stops short
of the new bound: the same exam as before, arrived at later."

WHAT IS THEREFORE STILL UNTESTED: a slowed ramp WITH the budget to finish it. The two ways to slow it
are equivalent in rate — `kl_ub`/`step_interval` is the expansion rate per iteration, and 0.06/250 =
0.12/500 = 2.4e-4 — but they are not equally grounded. `kl_ub` = 0.06 is the value the lineage ran
before E1 and that the E1/E2 factorial identifies as attitude-preserving; `step_interval` = 500 has no
anchor, since its only prior test is the budget-starved run above.

GENERAL RULE. Before citing any curriculum-knob run as evidence, compute its expansion budget and
compare it to the saturation distance measured on that plant (currently 3.5209 KL / 30 boundaries on
the 21-dim plant, from `trpo_iterbudget_s30_260805_012813`). A run that could not saturate did not
test the knob; it tested "the same exam, arrived at later". The budget is not in `summary.json` — it
is three numbers in the config.

SOURCE: `experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/config/*.yaml`
read 2026-08-09; extend8k saturation figure from
`curriculum_recalibration_protocol_widening_the_dr_box_requires_r`; Run A saturation distance from
`teacher_iter_budget/README.md`.

