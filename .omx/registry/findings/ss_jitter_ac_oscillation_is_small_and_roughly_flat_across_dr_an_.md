---
title: "ss_jitter (AC oscillation) is small and roughly flat across DR, an order below t"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# ss_jitter (AC oscillation) is small and roughly flat across DR, an order below t

ss_jitter (AC oscillation) is small and roughly flat across DR, an order below the DC-bias spread — so the §8.1 CV blow-up is env-level steady-state bias, not policy oscillation (rules/03: independent failure modes; only the DC one is present).

[EVIDENCE: summary.json ss_jitter — roll <=0.22°, pitch <=0.10° at all levels vs §8.1 ss_error_std up to 1.54° at hard]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

ss_jitter (AC oscillation) is small and roughly flat across DR, an order below the DC-bias spread — so the §8.1 CV blow-up is env-level steady-state bias, not policy oscillation (rules/03: independent failure modes; only the DC one is present).

[EVIDENCE: summary.json ss_jitter — roll <=0.22°, pitch <=0.10° at all levels vs §8.1 ss_error_std up to 1.54° at hard]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
