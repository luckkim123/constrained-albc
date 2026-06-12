---
title: "state_dependent_std: robustness-vs-nominal trade-off, NOT difficulty-adaptive (Phase-2 falsification)"
tags: ["state_dependent_std", "action_std", "falsification", "ood", "exploration"]
created: 2026-06-08T21:56:24.254183
updated: 2026-06-08T21:56:24.254183
sources: ["diagnose-20260609-064938"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# state_dependent_std: robustness-vs-nominal trade-off, NOT difficulty-adaptive (Phase-2 falsification)

state_dependent_std (per-state log_std head, 16D actor) vs global log_std baseline on attitude_only (run trpo_state_std_260609_011906 vs trpo_baseline_260608_172710). VERDICT: NOT a clean null -- a robustness-vs-nominal TRADE-OFF. Eval att_norm ss_error (summary.json): none +348% (0.968 vs 0.216 deg, WORSE) monotone -> ood -34.5% (0.750 vs 1.146, BETTER). CV lower at hard/ood (hard 137 vs 223%, ood 142 vs 234%); yaw heavy-tail CV collapses (hard 52 vs 350%). Training reward parity at convergence (+5.1% iter4999; early -12% was LAG not intrinsic, baseline late-regressed). MECHANISM (adaptivity probe, model_4999 actor head on 512 obs): per-state std IS state-varying (cross-state CV 45.6%) but does NOT track difficulty (corr +0.04) -- so the theoretical payoff (wide noise on hard states) did NOT emerge; OOD win is a byproduct of a globally-TIGHTER converged std (0.167 vs 0.175) helping where baseline's larger noise hurts. thruster_util binds harder (J_C/d_k 0.903 vs 0.807 = authority starvation). NOT worth adopting: +348% nominal regression disqualifying; OOD gain not from intended mechanism -- a global-std schedule / lower late min_std could reproduce it cheaper. FVP integration (allow_unused for the unused global log_std) verified correct: line_search 100%, KL bounded. (analysis diagnose-20260609-064938)
