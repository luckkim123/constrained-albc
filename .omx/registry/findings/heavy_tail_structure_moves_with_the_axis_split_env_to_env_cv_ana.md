---
title: "Heavy-tail structure moves WITH the axis split (env-to-env CV analysis): roll di"
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

# Heavy-tail structure moves WITH the axis split (env-to-env CV analysis): roll di

Heavy-tail structure moves WITH the axis split (env-to-env CV analysis): roll dispersion drops at 3 of 4 levels while pitch dispersion rises at all 4 — the band re-shapes the tails in opposite directions on the two attitude axes rather than shifting means. | level | roll CV anchor -> B0c | pitch CV anchor -> B0c | yaw CV anchor -> B0c | |---|---|---|---| | none | 0.64 -> 0.51 | 0.22 -> 0.36 | 0.09 -> 0.26 | | soft | 0.85 -> 1.29 | 0.36 -> 0.41 | 0.12 -> 0.26 | | medium | 1.06 -> 0.70 | 0.61 -> 0.89 | 0.23 -> 0.27 | | hard | 2.58 -> 1.93 | 0.91 -> 1.89 | 0.37 -> 0.40 |

[EVIDENCE: CV = ss_error_std / ss_error computed from both summary.json (anchor static_260723_091813: e.g. none/roll ss_error 0.497, ss_error_std 0.319; B0c static_260724_073758: 0.470, 0.241)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

Heavy-tail structure moves WITH the axis split (env-to-env CV analysis): roll dispersion drops at 3 of 4 levels while pitch dispersion rises at all 4 — the band re-shapes the tails in opposite directions on the two attitude axes rather than shifting means. | level | roll CV anchor -> B0c | pitch CV anchor -> B0c | yaw CV anchor -> B0c | |---|---|---|---| | none | 0.64 -> 0.51 | 0.22 -> 0.36 | 0.09 -> 0.26 | | soft | 0.85 -> 1.29 | 0.36 -> 0.41 | 0.12 -> 0.26 | | medium | 1.06 -> 0.70 | 0.61 -> 0.89 | 0.23 -> 0.27 | | hard | 2.58 -> 1.93 | 0.91 -> 1.89 | 0.37 -> 0.40 |

[EVIDENCE: CV = ss_error_std / ss_error computed from both summary.json (anchor static_260723_091813: e.g. none/roll ss_error 0.497, ss_error_std 0.319; B0c static_260724_073758: 0.470, 0.241)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
