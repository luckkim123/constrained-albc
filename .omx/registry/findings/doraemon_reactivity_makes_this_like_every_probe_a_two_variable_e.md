---
title: "DORAEMON reactivity makes this (like every probe) a two-variable experiment: wit"
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

# DORAEMON reactivity makes this (like every probe) a two-variable experiment: wit

DORAEMON reactivity makes this (like every probe) a two-variable experiment: with the uniform band on, doraemon_success_rate ends lower (0.81 -> 0.73), cumulative difficulty entropy ends lower (DORAEMON/entropy_before -22.77 -> -24.68, final-10-iteration window), and the driven curriculum dims reach LESS of their range (ocean_current 14.3% -> 10.2%, obs_noise 13.9% -> 11.4%, payload_cog_xy 13.0% -> 8.9%; DORAEMON/ess_ratio 0.78 -> 0.77) — so part of the tiny eval deltas is curriculum-mediated, not purely the band.

[EVIDENCE: engine TIER 2 DORAEMON per-param table, both runs; tb_final.py window=10 for DORAEMON/entropy_before and DORAEMON/kl_step (0.0 both, final window); wiki doraemon_reactivity_makes_every_single_variable_probe_two_variab]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

DORAEMON reactivity makes this (like every probe) a two-variable experiment: with the uniform band on, doraemon_success_rate ends lower (0.81 -> 0.73), cumulative difficulty entropy ends lower (DORAEMON/entropy_before -22.77 -> -24.68, final-10-iteration window), and the driven curriculum dims reach LESS of their range (ocean_current 14.3% -> 10.2%, obs_noise 13.9% -> 11.4%, payload_cog_xy 13.0% -> 8.9%; DORAEMON/ess_ratio 0.78 -> 0.77) — so part of the tiny eval deltas is curriculum-mediated, not purely the band.

[EVIDENCE: engine TIER 2 DORAEMON per-param table, both runs; tb_final.py window=10 for DORAEMON/entropy_before and DORAEMON/kl_step (0.0 both, final window); wiki doraemon_reactivity_makes_every_single_variable_probe_two_variab]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
