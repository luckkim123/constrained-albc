---
title: "eval npz fault block contract: fault_injection flag, fault_ keys absent-by-design on healthy evals"
tags: []
created: 2026-07-27T04:45:27.038653
updated: 2026-07-27T04:45:27.038653
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# eval npz fault block contract: fault_injection flag, fault_ keys absent-by-design on healthy evals

Since 2026-07-27 (commit after fault-DR A/B analysis): every eval data_<level>.npz carries a 0-d bool 'fault_injection' scalar -- True iff per-env fault_ keys (fault_thruster_0..5, fault_sensor_noise, fault_joint) were captured. Healthy (--fault-less) evals still OMIT the fault_ keys entirely (absent-by-design, npz stays fault-free), so consumers must branch on bool(npz['fault_injection']) rather than KeyError-probing fault_thruster_*. Evals recorded BEFORE this date have neither the flag nor the keys: treat a missing 'fault_injection' as fault_injection=False. compare.py paired's bite-check already tolerates a baseline without the key.
