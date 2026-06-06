---
title: "training-log analysis engine (reference adapter)"
tags: ["adapter", "analyze", "engine"]
created: 2026-06-02T08:08:01.570003
updated: 2026-06-02T08:08:01.570003
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# training-log analysis engine (reference adapter)

The TB/wandb training-log diagnostic engine lives at .omx/profile/analyze_training.py (+ tslib.py). Self-contained: numpy/yaml/tensorboard/scipy/ruptures/hmmlearn only, no Isaac Sim. Run: ALBC_LOGS_ROOT=<logs/rsl_rl> python3 .omx/profile/analyze_training.py [run-index|path] [--deep --tier 3 --stride N --focus PAT]. Outputs CONFIG/TIER1/TIER2/DIAGNOSIS + (--deep) PELT changepoints/HMM regime/lead-lag/plateau. Use for 'why stalled/diverged'; use monitor.py plot for quick PNG dashboard. Evidence: verified working from .omx/profile on run trpo_main_teacher_260525_232805 (Jun 2 2026).
