---
title: "DORAEMON alpha is a feasibility FLOOR, not a DR-expansion lever (E5 dr-harder)"
tags: ["doraemon", "alpha", "curriculum", "kl_ub", "dr-harder"]
created: 2026-06-07T02:50:59.890630
updated: 2026-06-07T02:50:59.890630
sources: ["diagnose-20260607-114548"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# DORAEMON alpha is a feasibility FLOOR, not a DR-expansion lever (E5 dr-harder)

E5 (trpo_260606_225859) raised DORAEMON alpha 0.50->0.75; all other knobs at teacher baseline (kl_ub=0.06). Result = near-null intervention, alpha was never binding. EVIDENCE (tb_final + same-iter stride, analysis diagnose-20260607-114548 sect.7): success_rate sat 0.96-0.99 the whole run >> both alpha values, so the feasibility floor never gated a curriculum step (DORAEMON mode=0 throughout). The binding constraint is the per-update trust-region KL: DORAEMON/kl_step pinned at kl_ub=0.06 (identical to teacher); only E1 which raised kl_ub to 0.12 moved the cap. E5 expanded DR LESS than teacher: ocean_current mean 0.1014 vs teacher 0.1175 (0.86x), ocean std 0.0916 vs 0.1044 (0.88x); noise_std ratio E5/teacher=0.988 (no policy-stochasticity change = no-expansion signature). Reward/total +0.2%, Train/mean_reward -0.2% vs teacher. Eval: only real delta = attitude gain (roll none -37%, pitch hard -32%, lower attitude CV) bought against weak-DR translation overfit (vz none +213%, soft +173%; vy none +104%). CONCLUSION: to widen robustness you must move the binding KL trust region (kl_ub) or DR variance directly, NOT the success floor (alpha). Cross-ref E1 kl_ub-0.12 (expanded 3.6x but overfit attitude) + E2 ocean-center-shift (collapsed entropy). Re-visit: report.md sect.7 + BLUF.
