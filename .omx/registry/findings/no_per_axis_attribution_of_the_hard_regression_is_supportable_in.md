---
title: "No per-axis attribution of the hard regression is supportable in this arm: the l"
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# No per-axis attribution of the hard regression is supportable in this arm: the l

No per-axis attribution of the hard regression is supportable in this arm: the largest per-axis move is roll `os_env_mean` +0.99 against a floor of 10.0, and the largest heavy-tail move is pitch `n_gt20` +1.50 against a floor of 15.0, so all of them are sub-floor.

[EVIDENCE: the per-axis table above against `summary.json decision_floors` (`os_env_mean` 10.0, `n_gt20` 15.0); this differs from B2, whose roll `n_gt20` move was cited in Phase C, and the difference is that B2's att_norm delta had a per-axis carrier while WIDE's does not]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
