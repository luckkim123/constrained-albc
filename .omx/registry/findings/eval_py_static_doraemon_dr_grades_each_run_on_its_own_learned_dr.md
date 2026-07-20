---
title: "eval.py static --doraemon-dr grades each run on its OWN learned DR — cross-run hard/ood is non-comparable, only none is fair"
tags: ["eval", "doraemon-dr", "cross-run", "comparability", "confound", "none-level", "static", "heavy-tail", "e1", "shared-exam", "replay"]
created: 2026-07-13T10:08:05.594876
updated: 2026-07-16T05:51:09.548030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md", "eval.py", "dr_config.py"]
links: ["an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_.md", "cross_run_reference_values_must_be_re_extracted_fresh_never_carr.md"]
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

---

## Update (2026-07-16T05:51:09.548030)

# Addendum 2026-07-16: the shared-exam remedy shifts soft/medium TOO, not just hard

This page already prescribes the remedy: "re-eval BOTH runs under a SHARED fixed distribution
(`--no-doraemon-dr`, or `--doraemon-dr-from ...`)". Two operational details found while designing the
first probe that actually needs it (P-B1, proposal next-20260716-144615):

[FINDING] `--doraemon-dr-from` does NOT re-anchor only the hard level. It overwrites the shared module
global `_DORAEMON_FULL_DR` (eval.py:1128/1137), and `build_dr_config` interpolates EVERY level from
true nominal toward that same anchor: `lo = nominal + scale*(full - nominal)` (dr_config.py:337-349)
with DR_SCALE = {none 0.0, soft 0.3, medium 0.6, hard 1.0} (common.py:33-36). So re-anchoring moves
soft, medium AND hard together; only `none` (scale 0.0) is anchor-invariant -- which is the same
reason `none` is the only fair cross-run point in the first place. Practical consequence: a
`--doraemon-dr-from` eval's soft/medium panels are NOT comparable against the same run's earlier
self-anchored eval; only against another eval sharing that anchor. The `none` panel should reproduce
the run's existing `none` numbers exactly -- if it does not, the eval did not do what was intended.
[EVIDENCE: eval.py:1117-1143 (inside run_static, def at :955); dr_config.py:337-349; common.py:33-36; verified 2026-07-16]
[CONFIDENCE: HIGH]

[FINDING] Both flags live on the `static` subparser (`--doraemon-dr` BooleanOptionalAction default
**True** at eval.py:117-123; `--doraemon-dr-from` at eval.py:124-131). The default being True is why
every standard static eval is already self-anchored without anyone passing a flag. `--doraemon-dr-from`
was in fact built for this exact use -- its own help string says "Used to evaluate all ablation
variants on the r13_A baseline's learned DR distribution (common test distribution)".
[EVIDENCE: eval.py:117-131, argparse definitions on sp_static]
[CONFIDENCE: HIGH]

[FINDING] A CurriculumReplayer run cannot be self-anchored at all: `load_doraemon_dr` requires TB
scalars `DORAEMON/mean/*` (dr_config.py:232, 251-252), but a replay run's step() emits only
`replay/cur_iter` and `replay/entropy` (doraemon.py:893). With no DORAEMON/mean/* tag the loader
returns None and the eval SILENTLY falls back to the static hard DomainRandomizationCfg
(eval.py:1140-1141). So any future replay-based DR-matched probe MUST pass `--doraemon-dr-from`
explicitly at eval time, or its arms will be graded on a different box than the run it is compared to.
[EVIDENCE: doraemon.py:893 vs dr_config.py:232/251-252; eval.py:1140-1141]
[CONFIDENCE: HIGH]

Status of the remedy itself: proposed twice before (e3 and e4 analyses) and correctly skipped both
times -- their fair-`none` point had already settled the verdict negatively, so the shared-exam
re-eval could not change it. P-B1 is the first case where it is decision-relevant, because P-B1's
fair-`none` point is POSITIVE and the hard level is the only open question.

