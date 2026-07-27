---
title: "The per-step reward decomposition is essentially unchanged — the band does not r"
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

# The per-step reward decomposition is essentially unchanged — the band does not r

The per-step reward decomposition is essentially unchanged — the band does not redistribute reward across channels; the episode return gap is -2.5% with identical episode length. | term | anchor | B0c | |---|---|---| | Reward/att_rp | 6.69 | 6.73 | | Reward/yaw_vel | 2.12 | 2.06 | | Reward/bias | -0.01 | -0.01 | | Reward/smoothness | -0.02 | -0.02 | | Reward/thruster | -0.02 | -0.02 | | Reward/torque | -0.07 | -0.06 | | per-step total | 8.69 | 8.68 | | Train/mean_reward (episode) | 265.98 | 259.20 | | ep_len | 1424 | 1424 |

[EVIDENCE: engine TIER 3 Rewards and TIER 1 rows, b0c_engine.txt and anchor_engine.txt]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

The per-step reward decomposition is essentially unchanged — the band does not redistribute reward across channels; the episode return gap is -2.5% with identical episode length. | term | anchor | B0c | |---|---|---| | Reward/att_rp | 6.69 | 6.73 | | Reward/yaw_vel | 2.12 | 2.06 | | Reward/bias | -0.01 | -0.01 | | Reward/smoothness | -0.02 | -0.02 | | Reward/thruster | -0.02 | -0.02 | | Reward/torque | -0.07 | -0.06 | | per-step total | 8.69 | 8.68 | | Train/mean_reward (episode) | 265.98 | 259.20 | | ep_len | 1424 | 1424 |

[EVIDENCE: engine TIER 3 Rewards and TIER 1 rows, b0c_engine.txt and anchor_engine.txt]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
