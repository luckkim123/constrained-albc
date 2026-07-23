---
title: "At `none` the tracking moved well outside the pre-registered +/-5% band on every"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-23T02:21:27.244561
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# At `none` the tracking moved well outside the pre-registered +/-5% band on every

At `none` the tracking moved well outside the pre-registered +/-5% band on every attitude axis -- roll worse, pitch and yaw better -- so the strict NULL clause is NOT satisfied at single-seed resolution. | axis  | A5 ss_error | anchor ss_error | delta%  | A5 os_env_mean | anchor os | os delta% | |-------|-------------|-----------------|---------|----------------|-----------|-----------| | roll  | 0.2509      | 0.2149          | +16.8%  | 26.35          | 17.02     | +54.8%    | | pitch | 0.1724      | 0.1946          | -11.4%  | 11.96          | 13.39     | -10.7%    | | yaw   | 0.0023      | 0.0052          | -56.0%  | 17.14          | 3.59      | +376.9%   |

[EVIDENCE: A5 vs anchor summary.json, `none` level]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

At `none` the tracking moved well outside the pre-registered +/-5% band on every attitude axis -- roll worse, pitch and yaw better -- so the strict NULL clause is NOT satisfied at single-seed resolution. | axis  | A5 ss_error | anchor ss_error | delta%  | A5 os_env_mean | anchor os | os delta% | |-------|-------------|-----------------|---------|----------------|-----------|-----------| | roll  | 0.2509      | 0.2149          | +16.8%  | 26.35          | 17.02     | +54.8%    | | pitch | 0.1724      | 0.1946          | -11.4%  | 11.96          | 13.39     | -10.7%    | | yaw   | 0.0023      | 0.0052          | -56.0%  | 17.14          | 3.59      | +376.9%   |

[EVIDENCE: A5 vs anchor summary.json, `none` level]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
