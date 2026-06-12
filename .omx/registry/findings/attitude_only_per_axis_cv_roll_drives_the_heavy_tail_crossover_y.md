---
title: "attitude_only per-axis CV: roll DRIVES the heavy-tail crossover, yaw is the EXTREME tail"
tags: ["heavy-tail", "CV", "roll", "pitch", "yaw", "per-axis", "attitude_only", "rule03"]
created: 2026-06-09T04:02:50.086523
updated: 2026-06-09T04:02:50.086523
sources: ["diagnose-20260609-125556"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# attitude_only per-axis CV: roll DRIVES the heavy-tail crossover, yaw is the EXTREME tail

Pattern from analysis diagnose-20260609-125556 (state_std vs baseline, attitude_only). When comparing a robustness intervention on attitude_only, split CV (ss_error_std/ss_error) PER AXIS x 5 DR levels — att_norm CV alone hides which axis crosses over. Observed: baseline per-axis CV is tight on easy DR (roll 8.8%, yaw 9.5% at none) but RUNS AWAY at hard/ood (roll 249%, yaw 350% at hard); the intervention (here state_std) starts dispersed at none (roll 59%) but stays bounded under stress (roll 146% hard). ROLL carries the largest ABSOLUTE ss_error (~0.7-1.0 deg vs pitch ~0.2), so its CV crossover dominates the att_norm crossover -> roll is the axis to watch. YAW is the EXTREME heavy-tail axis (baseline CV 350% hard / 315% ood) even though its absolute ss_error is tiny (~0.003 rad/s) — a pure tail, collapsed to 52%/81% by the tighter std. CAUTION: pitch per-env peak>20deg = 64/64 both runs is a step-response TRANSIENT, not heavy-tail (steady-state pitch ss ~0.1-0.2 deg) — use steady-state not peak for the rule03 heavy-tail count. Consistent with prior page 'teacher dr_harder: yaw is the ONLY heavy-tail axis, roll is DC-bias'. Re-visit: report diagnose-20260609-125556 sec generalization.
