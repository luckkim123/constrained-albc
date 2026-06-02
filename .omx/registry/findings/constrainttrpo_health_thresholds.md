---
title: "ConstraintTRPO health thresholds"
tags: ["thresholds", "anomaly", "diagnosis"]
created: 2026-06-02T08:08:21.693225
updated: 2026-06-02T08:08:21.693225
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# ConstraintTRPO health thresholds

Anomaly thresholds the engine flags (analyze_training.py ANOMALY rules): entropy<0 COLLAPSED; noise_std<0.25 LOW / >=0.95 CEILING; z_min<-0.95 or z_max>0.95 SAT; z_std<0.1 LOW; grad_norm<1e-4 DEAD; line_search_success<0.5 FAIL (barrier_t too low / too many active constraints); barrier_penalty>0.1 SPIKE; roll_deg>20 HIGH; pitch_deg>25 HIGH; thruster_util_max>0.95 saturation. Evidence: encoded as the engine's anomaly table; matches 03-analysis-quality.md rule (CV=std/mean mandatory, all 4 DR levels). Conclusion: these are the reusable pass/fail bars for any albc training run, not just one run.
