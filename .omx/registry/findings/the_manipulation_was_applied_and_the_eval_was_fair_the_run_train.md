---
title: "The manipulation was applied and the eval was fair: the run trained with a per-e"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T10:30:03.859588
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The manipulation was applied and the eval was fair: the run trained with a per-e

The manipulation was applied and the eval was fair: the run trained with a per-env max_thrust ceiling band of (0.85, 1.15) x 50 N = 42.5-57.5 N, the config default is OFF, and the eval's `none` level collapses the band to nominal 1.0. - run `params/env.yaml:482` -> `max_thrust_scale: (0.85, 1.15)`; the anchor's env.yaml has no such key (grep) - code default OFF: `envs/main/config.py:250` `max_thrust_scale = (1.0, 1.0)` - applied at reset: `albc_env.py:1580,1693` -> `ThrusterModel.randomize_parameters(max_thrust_scale=...)`; ceiling clamp at `marinelab/core/thruster.py:203-207` - eval-side registration: `constrained_albc/analysis/dr_config.py:94` (tuple field) + `:136` (true nominal 1.0 -> none-collapse) - identity guard: `tests/test_max_thrust_identity.py` (committed with the proposal revision)

[EVIDENCE: params/env.yaml:482 vs anchor env.yaml; config.py:250; albc_env.py:1580,1693; analysis/dr_config.py:94,136; tests/test_max_thrust_identity.py]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

The manipulation was applied and the eval was fair: the run trained with a per-env max_thrust ceiling band of (0.85, 1.15) x 50 N = 42.5-57.5 N, the config default is OFF, and the eval's `none` level collapses the band to nominal 1.0. - run `params/env.yaml:482` -> `max_thrust_scale: (0.85, 1.15)`; the anchor's env.yaml has no such key (grep) - code default OFF: `envs/main/config.py:250` `max_thrust_scale = (1.0, 1.0)` - applied at reset: `albc_env.py:1580,1693` -> `ThrusterModel.randomize_parameters(max_thrust_scale=...)`; ceiling clamp at `marinelab/core/thruster.py:203-207` - eval-side registration: `constrained_albc/analysis/dr_config.py:94` (tuple field) + `:136` (true nominal 1.0 -> none-collapse) - identity guard: `tests/test_max_thrust_identity.py` (committed with the proposal revision)

[EVIDENCE: params/env.yaml:482 vs anchor env.yaml; config.py:250; albc_env.py:1580,1693; analysis/dr_config.py:94,136; tests/test_max_thrust_identity.py]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
