---
title: "The two arms are protocol-comparable with the anchor pair despite a CLI differen"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The two arms are protocol-comparable with the anchor pair despite a CLI differen

The two arms are protocol-comparable with the anchor pair despite a CLI difference, because passing only the fixed-health vector sets the same enable flag the anchor set explicitly.

[EVIDENCE: eval.py:113-116 sets `env_cfg.fault.enable = True` and pins `thruster_fixed_health` for `--fault_fixed_health`, documented at eval.py:85-86 as "Implies --fault"; anchor ran `--fault --fault_fixed_health 1,1,1,1,0,1` (FTC_M4_README.md), E-int ran `--fault_fixed_health 1,1,1,1,0,1`; both seed 42, num_envs 64, static protocol]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
