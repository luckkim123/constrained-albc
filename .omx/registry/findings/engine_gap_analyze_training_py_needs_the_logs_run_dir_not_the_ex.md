---
title: "engine-gap: analyze_training.py needs the logs/ run dir, not the experiments/ run dir (events under train symlink)"
tags: ["engine-gap", "analyze_training", "omx", "debugging"]
created: 2026-06-08T21:56:40.651093
updated: 2026-06-08T21:56:40.651093
sources: ["diagnose-20260609-064938"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: analyze_training.py needs the logs/ run dir, not the experiments/ run dir (events under train symlink)

[ENGINE-GAP] analyze_training.py load_events() does EventAccumulator(str(run_path)) directly, so passing the experiments-tree run dir (experiments/.../trpo_state_std_260609_011906, which holds config/eval/train/manifest but NOT events.out.tfevents at top level) returns 'No metrics found' (exit 1) for BOTH runs. [WHERE] .omx/profile/analyze_training.py load_events (line 306-308) + the run_path resolution (line 1768-1782). [SPEC] when run_path lacks events.out.tfevents.* at its top level, fall back to run_path/train/ (the symlink to logs/) or glob for events under it -- mirror the rule03 train-symlink convention the eval harness already uses. Workaround used this analysis: point the engine at the logs/ run dir directly (logs/rsl_rl/albc_trpo_teacher/attitude_only_campaign/<run_id>), which has the events file. [EVIDENCE] Phase-2 state_std analysis: engine reported 'No metrics found' on the experiments path, worked on the logs path. [STATUS] proposed
