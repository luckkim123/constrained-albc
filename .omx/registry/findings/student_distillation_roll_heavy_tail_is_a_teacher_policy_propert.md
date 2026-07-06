---
title: "Student distillation roll heavy-tail is a teacher-policy property (TCN==GRU), not a distillation artifact"
tags: ["student", "distillation", "TCN", "GRU", "roll", "heavy-tail", "teacher", "differential-diagnosis"]
created: 2026-07-06T02:12:29.071910
updated: 2026-07-06T02:12:29.071910
sources: ["overnight_260526"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Student distillation roll heavy-tail is a teacher-policy property (TCN==GRU), not a distillation artifact

Student distillation (2026-05-26 overnight run) fidelity finding: the roll-axis heavy-tail at hard DR is a TEACHER-POLICY property faithfully reproduced by both student architectures, NOT a distillation artifact. To improve roll, fix teacher training (roll DOF / arm-action coupling into roll), not the students.

DIFFERENTIAL DIAGNOSIS (rule 03): TCN and GRU — two independent architectures — show near-identical roll heavy-tail on the DR-switching eval (%env peak>5 deg at hard DR):
| axis | TCN | GRU |
|---|---|---|
| roll | ~70% | ~68% |
| pitch | ~17% | ~18% |
| yaw | ~5% | ~6% |
Two independent nets reproducing the SAME roll weakness => the weakness lives in the teacher policy they both imitate, not in either distillation head.

GRU command-tracking ss_error by axis (none->hard): roll 0.50->2.03 deg, vx 0.002->0.007, vy 0.003->0.009, vz 0.021->0.099, yaw 0.001->0.003 m/s. Roll is the dominant weak axis; lin-vel and yaw stay tight even at hard. (Consistent with the teacher's own att-dominated reward and the later dr_harder finding that roll is a DC-bias axis.)

Teacher static eval context (per-env SS, last 20% of 155s, 64 envs): survival 100% at all 4 DR levels; att SS 0.04/0.19/0.40/0.64 deg (none/soft/medium/hard); att CV% 1/51/133/215 (env-to-env variance climbs steeply with DR — the expected DR-difficulty trend, NOT called heavy-tail without analyze.py per rule 03).

THREE SCRIPT BUGS found in the overnight pipeline (reported, and the pipeline has since moved to the omx eval-adapter / experiments tree — recorded here as the historical root causes, in case a similar shell-driven eval loop is rebuilt):
1. `run_student_evals.sh` early-exit under `set -e`: `run()` ended with `[ $rc -ne 0 ] && {...}`. When stage1 succeeds (rc=0) the test is false, making the compound statement exit-status 1, which `set -e` treats as the function failing -> whole script aborts after stage1. Only TCN-switching ran; GRU stages were run manually. FIX: `if [ $rc -ne 0 ]; then ...; exit $rc; fi`.
2. enhanced_summary path mismatch: teacher static eval's enhanced-summary step looked for `eval/eval_dr/summary.json` (old layout) while actual output is in `eval/static_<ts>/`. Non-fatal (raw .npz + PNGs fine); this is the same class of bug the eval-output-naming unification later fixed.
3. `TEACHER` must be an ABSOLUTE path for `run_student_evals.sh` (it `cd`s into isaaclab; a `constrained-albc/experiments/...` relative path is not found there). First student-eval attempt failed FileNotFoundError before correction.

VERIFIED: overnight run 2026-05-26 (teacher model_4999, TCN/GRU student_999, num_envs=4096, ConstraintTRPO+IPO+asym encoder). Pre-schema results doc (student runs had no experiments-tree report at the time). Related: `teacher_dr_harder_yaw_is_the_only_heavy_tail_*`, `teacher_dr_harder_doraemon_curriculum_froze_*`.

