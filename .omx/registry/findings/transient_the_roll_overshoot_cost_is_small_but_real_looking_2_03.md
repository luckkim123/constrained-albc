---
title: "Transient: the roll overshoot cost is small but real-looking (+2.03 pp = +0.61 d"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T10:30:03.859588
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Transient: the roll overshoot cost is small but real-looking (+2.03 pp = +0.61 d

Transient: the roll overshoot cost is small but real-looking (+2.03 pp = +0.61 deg on the 30-deg roll step at `none` — above the ~0.33 pp E1 eval-noise floor recorded in PLAN.md section 7, far below the 10 pp screening floor); the yaw transient IMPROVES at 3 of 4 levels; roll jitter is flat (no oscillation trade). | level | roll d os (pp) | pitch d os (pp) | yaw d os (pp) | roll d ss_jitter (deg) | |---|---|---|---|---| | none | +2.03 | +0.24 | -0.71 | -0.057 | | soft | +1.24 | +0.46 | -1.44 | -0.023 | | medium | +0.16 | +0.34 | -1.99 | +0.011 | | hard | +1.08 | +0.59 | +0.32 | +0.036 |

[EVIDENCE: compare.py paired delta os_env_mean and ss_jitter; roll step magnitude 30 deg so deg = pp x 0.30]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

Transient: the roll overshoot cost is small but real-looking (+2.03 pp = +0.61 deg on the 30-deg roll step at `none` — above the ~0.33 pp E1 eval-noise floor recorded in PLAN.md section 7, far below the 10 pp screening floor); the yaw transient IMPROVES at 3 of 4 levels; roll jitter is flat (no oscillation trade). | level | roll d os (pp) | pitch d os (pp) | yaw d os (pp) | roll d ss_jitter (deg) | |---|---|---|---|---| | none | +2.03 | +0.24 | -0.71 | -0.057 | | soft | +1.24 | +0.46 | -1.44 | -0.023 | | medium | +0.16 | +0.34 | -1.99 | +0.011 | | hard | +1.08 | +0.59 | +0.32 | +0.036 |

[EVIDENCE: compare.py paired delta os_env_mean and ss_jitter; roll step magnitude 30 deg so deg = pp x 0.30]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
