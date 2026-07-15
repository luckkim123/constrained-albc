---
title: "performance_lb (DORAEMON gate) is causally independent of the actor exploration collapse"
tags: ["doraemon", "exploration", "entropy", "noise_std", "performance_lb"]
created: 2026-07-15T04:54:06.615107
updated: 2026-07-15T04:54:06.615107
sources: ["diagnose-20260715-133249"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# performance_lb (DORAEMON gate) is causally independent of the actor exploration collapse

Probe trpo_perflb200_260715_023744 vs baseline trpo_baseline_260714_192020 (single variable DORAEMON performance_lb 250->200, seed 30, verified via git show d3789a7 = one-line config diff + git log = no other envs/main|_core commit between launches).

RESULT: lowering performance_lb UN-STALLS the curriculum but does NOT touch exploration.
- DORAEMON channel MOVED: mode -2.00->0.00 (baseline re-stalls at -2 late; perflb holds 0), success_rate 0.407->0.712, ess_ratio 0.414->0.754, DR widened (ocean_current 0.03->0.07, payload 1.36->1.48). [TB DORAEMON/*, analysis diagnose-20260715-133249 report.md central table]
- Exploration UNTOUCHED: Policy/entropy -7.758->-7.796, Policy/mean_noise_std 0.0995->0.0985; trajectories near-identical across all 5000 iters (max abs dev 0.18 entropy ~1% of collapse range, 0.003 noise_std) = two orders below the DORAEMON-side divergence. [TB Policy/entropy, Policy/mean_noise_std strided trajectory]

CONCLUSION: the actor entropy/noise_std collapse (noise_std pinned near min_std=0.05 floor, entropy ~-7.8) is causally INDEPENDENT of the DORAEMON feasibility gate. Engine [DIAGNOSIS] 'exploration dead: check min_std floor and entropy_coef' is IDENTICAL in both runs. The mode=-2 stall was a co-symptom, not the cause.

DECISION: adopt performance_lb=200 as the standing curriculum setting (stabilizes mode at 0 vs baseline's late re-stall). The next exploration lever must target the actor noise/entropy machinery (min_std, entropy_coef=0.003, or the noise parameterization / entropy schedule) — NOT the curriculum. Re-testing performance_lb / DORAEMON knobs for the exploration collapse is refuted; do not re-run that lever for exploration.
