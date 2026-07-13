---
title: "DORAEMON alpha is a feasibility FLOOR, not a DR-expansion lever (E5 dr-harder)"
tags: ["doraemon", "alpha", "curriculum", "kl_ub", "dr-harder"]
created: 2026-06-07T02:50:59.890630
updated: 2026-07-13T05:40:13.709549
sources: ["diagnose-20260607-114548"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# DORAEMON alpha is a feasibility FLOOR, not a DR-expansion lever (E5 dr-harder)

E5 (trpo_260606_225859) raised DORAEMON alpha 0.50->0.75; all other knobs at teacher baseline (kl_ub=0.06). Result = near-null intervention, alpha was never binding. EVIDENCE (tb_final + same-iter stride, analysis diagnose-20260607-114548 sect.7): success_rate sat 0.96-0.99 the whole run >> both alpha values, so the feasibility floor never gated a curriculum step (DORAEMON mode=0 throughout). The binding constraint is the per-update trust-region KL: DORAEMON/kl_step pinned at kl_ub=0.06 (identical to teacher); only E1 which raised kl_ub to 0.12 moved the cap. E5 expanded DR LESS than teacher: ocean_current mean 0.1014 vs teacher 0.1175 (0.86x), ocean std 0.0916 vs 0.1044 (0.88x); noise_std ratio E5/teacher=0.988 (no policy-stochasticity change = no-expansion signature). Reward/total +0.2%, Train/mean_reward -0.2% vs teacher. Eval: only real delta = attitude gain (roll none -37%, pitch hard -32%, lower attitude CV) bought against weak-DR translation overfit (vz none +213%, soft +173%; vy none +104%). CONCLUSION: to widen robustness you must move the binding KL trust region (kl_ub) or DR variance directly, NOT the success floor (alpha). Cross-ref E1 kl_ub-0.12 (expanded 3.6x but overfit attitude) + E2 ocean-center-shift (collapsed entropy). Re-visit: report.md sect.7 + BLUF.

---

## Update (2026-07-13T05:40:13.709549)

RECURRING QUESTION SETTLED (2026-07-13, user asked on trpo_baseline_260713_031325): 'success_rate only peaks ~0.6 then declines — should it not reach ~0.9 before declining? adjust performance_lb/kl_ub?' ANSWER: the observed shape IS the designed alpha=0.5 closed-loop equilibrium, not a defect. Measured on baseline TB: success 0.003(it500) -> 0.627 PEAK(it3258) -> 0.429(it4999), while DORAEMON/entropy_before stays flat (-45.9) until success crosses alpha~0.5 at it~2000-2500 and THEN rises monotonically (-44.5 -> -30.1) — i.e. the controller starts widening exactly when success clears the floor, and the widening pulls success back down toward alpha. Success parking at 0.9 under alpha=0.5 would be the DEFECT (unused headroom, the E5 pattern above). The 'should reach 0.9' intuition belongs to alpha~0.9 configs (binary-success DORAEMON setups); this project gates on return>=performance_lb=250 (mean return 232.6, so the gate sits near the return median) with alpha=0.5 (env.yaml:508-510). Knob evidence: kl_ub-up rejected (dr_harder E1, speed kills attitude); alpha-up tried (E5, this page: floor not lever); performance_lb has no evidence of miscalibration (eval healthy: sub-degree means, 100% survival). The only open question is BUDGET (curriculum still expanding at it5000) — probed by proposal next-20260713-142604 (resume +5000 iters, zero config delta). Do NOT reflexively retrain baseline+in-flight runs over this curve shape.
