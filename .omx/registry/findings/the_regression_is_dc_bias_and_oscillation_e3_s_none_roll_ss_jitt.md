---
title: "The regression is DC-bias AND oscillation: e3's none roll ss_jitter is 1.19° vs "
tags: ["auto-captured", "trpo_e3_extend10k_260713_224822"]
created: 2026-07-13T23:52:53.410508
updated: 2026-07-13T23:52:53.410508
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The regression is DC-bias AND oscillation: e3's none roll ss_jitter is 1.19° vs 

The regression is DC-bias AND oscillation: e3's none roll ss_jitter is 1.19° vs baseline 0.21° (5.6x), so the policy also oscillates at nominal — over-actuating for disturbances that are absent at `none`.

[EVIDENCE: summary.json none roll ss_jitter 0.2145(bl)→1.1901(e3); att_norm 0.1996→1.1154]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
