---
title: "Episode return over the extension is non-monotone and net-negative: `Train/mean_"
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

# Episode return over the extension is non-monotone and net-negative: `Train/mean_

Episode return over the extension is non-monotone and net-negative: `Train/mean_reward` rose to 250.9 at iter 7500 (curriculum still tractable) then DECLINED to 213.7 by iter 14998 — below baseline's 229.6 — as DORAEMON widened the DR faster than the policy could follow.

[EVIDENCE: TB Train/mean_reward e3 @7500=250.9 → @10000=228.7 → @12500=218.7 → @14998=213.7; baseline @4999=229.6]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
