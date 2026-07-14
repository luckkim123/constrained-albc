---
title: "This is the precise mechanism by which more budget REGRESSED the policy rather t"
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

# This is the precise mechanism by which more budget REGRESSED the policy rather t

This is the precise mechanism by which more budget REGRESSED the policy rather than shrinking the tail: baseline α=0.5 is a feasibility floor the policy could not sustain under the wider DR, so the extra iterations trained the policy against a non-stationary, over-hard target — worsening nominal tracking (§1) without buying tail robustness (§2).

[EVIDENCE: §1 none regression + §2 tail unchanged/worse + this section's oscillation; wiki `doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
