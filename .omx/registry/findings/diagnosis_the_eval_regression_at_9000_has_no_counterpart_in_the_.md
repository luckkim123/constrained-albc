---
title: "DIAGNOSIS — the eval regression at 9000 has no counterpart in the reward signal."
tags: ["auto-captured"]
created: 2026-08-14T08:13:07.299190
updated: 2026-08-14T08:13:07.299190
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# DIAGNOSIS — the eval regression at 9000 has no counterpart in the reward signal.

DIAGNOSIS — the eval regression at 9000 has no counterpart in the reward signal. Across windows spanning a 34% degradation in `none` steady-state error, every reward term and the episode return move by less than 1%, and `Reward/att_rp` — the term the exam measures — is flat to three digits.

[EVIDENCE: table above, `~/groups.py` over the run's single event file, 138 scalar tags]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
