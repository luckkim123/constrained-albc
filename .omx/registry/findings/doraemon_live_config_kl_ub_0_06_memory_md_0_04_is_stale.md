---
title: "DORAEMON live config: kl_ub=0.06 (MEMORY.md 0.04 is stale)"
tags: ["doraemon", "kl_ub", "config", "stale-fact"]
created: 2026-06-02T10:24:06.110807
updated: 2026-06-02T10:24:06.110807
sources: ["20260602-192051-diagnose"]
links: []
category: reference
confidence: high
schemaVersion: 1
---

# DORAEMON live config: kl_ub=0.06 (MEMORY.md 0.04 is stale)

Live DORAEMON config on run 260525_232805_trpo_main_teacher: kl_ub=0.06, performance_lb=90.0, step_interval=250 (constrained_albc/envs/main/config.py:396 DoraemonCfg(...)). MEMORY.md states kl_ub=0.04 — that is STALE; the actual value is 0.06. Verified two ways: (1) grep config.py:396; (2) every fired DORAEMON/kl_step value in TB == 0.0600 (the cap was hit on all 19 updates), analysis 20260602-192051-diagnose Axis 2. alpha=0.5 and min_ess_ratio=0.01 live in the marinelab engine (marinelab/algorithms/doraemon.py:40,46), NOT the constrained-albc re-export shim.
