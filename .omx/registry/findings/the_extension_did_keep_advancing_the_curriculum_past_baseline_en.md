---
title: "The extension DID keep advancing the curriculum past baseline (entropy_before −3"
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

# The extension DID keep advancing the curriculum past baseline (entropy_before −3

The extension DID keep advancing the curriculum past baseline (entropy_before −30.1→−18.6 peak, ends −24.4 > baseline −30.1 — H1's "curriculum advances" premise is met), but it OVERSHOT: the widened DR drove doraemon_success_rate below α=0.5, so DORAEMON contracted the distribution again (−18.6→−24.4) in the last 5000 iters. The curriculum oscillated rather than converging, ending at success 0.368 < baseline 0.429.

[EVIDENCE: TB DORAEMON/entropy_before −30.1→−18.6(i10k)→−24.4(i14998); doraemon_success_rate 0.654(i7.5k)→0.368(i14998) vs baseline 0.429; DORAEMON/ess_ratio 1.00, DORAEMON/kl_step settled; engine TIER2 DORAEMON mode=−3]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
