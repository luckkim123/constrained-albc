---
title: "Fault robustness collapses by an order of magnitude on the recentered plant: the"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Fault robustness collapses by an order of magnitude on the recentered plant: the

Fault robustness collapses by an order of magnitude on the recentered plant: the m4-dead att_norm ss_error fault delta (m4dead minus healthy, same run) is +1.74/+1.88/+1.51/+2.39 deg at none/soft/medium/hard vs E-int +0.10/+0.14/+0.22/+0.17 deg — 17x/14x/7x/14x larger degradation, despite the fault-DR config being identical and the fault_severity curriculum reaching further (10.83% vs 7.70%). Survival stays 100% at all levels under the fault for both runs.

[EVIDENCE: att_norm ss_error of experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075433/summary.json minus static_260728_075343, and experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260728_000754 minus static_260727_235736, all levels; fault_thruster_4 = 0 for all envs verified in data_none.npz; DORAEMON/mean/fault_severity finals 0.1083 vs 0.0770]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

Fault robustness collapses by an order of magnitude on the recentered plant: the m4-dead att_norm ss_error fault delta (m4dead minus healthy, same run) is +1.74/+1.88/+1.51/+2.39 deg at none/soft/medium/hard vs E-int +0.10/+0.14/+0.22/+0.17 deg — 17x/14x/7x/14x larger degradation, despite the fault-DR config being identical and the fault_severity curriculum reaching further (10.83% vs 7.70%). Survival stays 100% at all levels under the fault for both runs.

[EVIDENCE: att_norm ss_error of experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075433/summary.json minus static_260728_075343, and experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260728_000754 minus static_260727_235736, all levels; fault_thruster_4 = 0 for all envs verified in data_none.npz; DORAEMON/mean/fault_severity finals 0.1083 vs 0.0770]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

Fault robustness collapses by an order of magnitude on the recentered plant: the m4-dead att_norm ss_error fault delta (m4dead minus healthy, same run) is +1.74/+1.88/+1.51/+2.39 deg at none/soft/medium/hard vs E-int +0.10/+0.14/+0.22/+0.17 deg — 17x/14x/7x/14x larger degradation, despite the fault-DR config being identical and the fault_severity curriculum reaching further (10.83% vs 7.70%). Survival stays 100% at all levels under the fault for both runs.

[EVIDENCE: att_norm ss_error of experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/eval/static_260728_075433/summary.json minus static_260728_075343, and experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260728_000754 minus static_260727_235736, all levels; fault_thruster_4 = 0 for all envs verified in data_none.npz; DORAEMON/mean/fault_severity finals 0.1083 vs 0.0770]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
