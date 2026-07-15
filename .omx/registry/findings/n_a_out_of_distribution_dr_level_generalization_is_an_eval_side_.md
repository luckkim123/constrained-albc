---
title: "N/A: out-of-distribution / DR-level generalization is an EVAL-side property (sid"
tags: ["auto-captured", "trpo_perflb200_260715_023744"]
created: 2026-07-15T04:54:53.987453
updated: 2026-07-15T04:54:53.987453
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# N/A: out-of-distribution / DR-level generalization is an EVAL-side property (sid

N/A: out-of-distribution / DR-level generalization is an EVAL-side property (side-by-side DR boxes via `eval.py --ood`), not a training-log property; no eval exists for the perflb run and exp-analyze does not launch eval (D4/B8).

[EVIDENCE: engine TIER3 DR shows perflb reached a WIDER box than baseline (ocean current 0.03->0.07, payload 1.36->1.48) because its curriculum did not re-stall; whether the policy GENERALIZES there needs a gated `eval.py --ood`; no `summary.json`/`*.npz` under the perflb run tree]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md
