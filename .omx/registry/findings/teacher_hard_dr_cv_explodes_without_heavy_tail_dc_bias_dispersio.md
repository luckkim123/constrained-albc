---
title: "teacher hard-DR: CV explodes without heavy-tail (DC-bias dispersion)"
tags: ["roll", "heavy-tail", "CV", "hard-DR", "env-variance", "auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-06-05T10:09:40.828564
updated: 2026-07-23T07:32:14.143051
sources: ["20260605-190606-diagnose", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: ["heavy_tail_vs_sample_mean_divergence_are_independent.md"]
category: pattern
confidence: high
schemaVersion: 1
---

# teacher hard-DR: CV explodes without heavy-tail (DC-bias dispersion)

Under hard DR the teacher's env-to-env CV (ss_error_std/ss_error) explodes while NO heavy-tail forms and mean stays low. CV roll 0.84(none)->2.65(hard), yaw 0.008->3.05, vz 0.00->2.35, att_norm 0.85->2.38 (omx reduce summarize --cv-field ss_error on summary.json). BUT pct_peak_gt_thresh=0% on all att/lin-vel axes (eval_adapter heavy-tail; roll peak_max hard=11.36deg < 20deg). So the spread is per-env DC-bias dispersion, NOT a few catastrophic envs. Mechanism to move for hard-DR robustness = per-env CV, not mean. See analysis 20260605-190606-diagnose teacher 260525_232805. Confirms wiki [[heavy_tail_vs_sample_mean_divergence_are_independent]].

---

## Merged from across_the_full_dr_ladder_the_per_env_spread_widens_sharply_with.md (2026-07-23T07:32:14.143051)

# Across the full DR ladder the per-env spread widens sharply with DR, the familia

Across the full DR ladder the per-env spread widens sharply with DR, the familiar heavy-tail-at-hard pattern -- consistent with the anchor family, not introduced by this intervention. | level  | roll ss | roll CV | pitch ss | pitch CV | |--------|---------|---------|----------|----------| | none   | 0.2509  | 13%     | 0.1724   | 6%       | | soft   | 0.2749  | 41%     | 0.1936   | 17%      | | medium | 0.4146  | 101%    | 0.2389   | 54%      | | hard   | 1.1419  | 257%    | 0.5699   | 280%     |

[EVIDENCE: A5 summary.json, roll/pitch ss_error and CV=std/mean per level]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

Across the full DR ladder the per-env spread widens sharply with DR, the familiar heavy-tail-at-hard pattern -- consistent with the anchor family, not introduced by this intervention. | level  | roll ss | roll CV | pitch ss | pitch CV | |--------|---------|---------|----------|----------| | none   | 0.2509  | 13%     | 0.1724   | 6%       | | soft   | 0.2749  | 41%     | 0.1936   | 17%      | | medium | 0.4146  | 101%    | 0.2389   | 54%      | | hard   | 1.1419  | 257%    | 0.5699   | 280%     |

[EVIDENCE: A5 summary.json, roll/pitch ss_error and CV=std/mean per level]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md


---

## Merged from the_hard_level_heavy_tail_roll_cv_257_pitch_280_is_the_dominant_.md (2026-07-23T07:32:14.143051)

# The hard-level heavy tail (roll CV 257%, pitch 280%) is the dominant per-env fai

The hard-level heavy tail (roll CV 257%, pitch 280%) is the dominant per-env failure mode and is a property of the teacher-policy family under high DR, not introduced by the budget relaxation -- the anchor shows the same heavy-tail-at-hard structure.

[EVIDENCE: A5 summary.json hard roll/pitch CV=std/mean; consistent with the teacher heavy-tail wiki family]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

The hard-level heavy tail (roll CV 257%, pitch 280%) is the dominant per-env failure mode and is a property of the teacher-policy family under high DR, not introduced by the budget relaxation -- the anchor shows the same heavy-tail-at-hard structure.

[EVIDENCE: A5 summary.json hard roll/pitch CV=std/mean; consistent with the teacher heavy-tail wiki family]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
