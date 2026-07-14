---
title: "e3 shows no genuine robustness gain: because the only fair cross-run point (`non"
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

# e3 shows no genuine robustness gain: because the only fair cross-run point (`non

e3 shows no genuine robustness gain: because the only fair cross-run point (`none`) regressed 4.4x and the hard-level "narrowing" is an exam-difficulty artifact (§1), there is no level at which e3 generalizes better than baseline. A shared-distribution re-eval (`--doraemon-dr-from baseline`) could quantify the hard-exam tail exactly, but is not needed for the verdict: the fair `none` regression + violated H1 mean band already settle it. (OOD level not evaluated for e3; the standard 4-level sweep was run.)

[EVIDENCE: §1 att_norm none 4.42x + §0 confound; H1 mean band att_norm hard ≤0.80° violated at 0.999°]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
