---
title: "engine-gap: constraint diagnosis no-ops on real TB tag names (margin//viol/ vs cost_return_)"
tags: ["engine-gap", "analyze_training", "constraint", "tb-tags", "silent-failure"]
created: 2026-06-05T02:19:18.717406
updated: 2026-06-05T02:19:18.717406
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: constraint diagnosis no-ops on real TB tag names (margin//viol/ vs cost_return_)

[ENGINE-GAP] The omx training-log engine (.omx/profile/analyze_training.py) silently no-ops its entire constraint diagnosis on real albc runs because of a TB tag-name mismatch.

[WHERE] analyze_training.py assumes three tag families that DO NOT exist in the actual TB: Constraint/cost_return_{name} (lines 313/323/565/574/914/1534), Constraint/barrier_margin_{name} (lines 384/576/922), Constraint/d_k_{name} (lines 385/575). The real run (260525_232805_trpo_main_teacher) only emits Constraint/margin/{name} and Constraint/viol/{name} (slash-delimited), logged at constraint_encoder_runner.py:279-280. Consequence: _check_cost_divergence, _margin_at_floor, and the constraint plot panels all return empty / False with NO error - the analysis looks like "constraints fine" when it actually never looked at them. Same class as the rule-03 "silent fallback" trap.

[SPEC] (1) Engine: read Constraint/margin/{name} + Constraint/viol/{name} as the primary source; keep the old cost_return_/barrier_margin_/d_k_ names as a fallback (dual-tag support) so older synthetic runs still parse. Add a NEW diagnostic "constraint inert": reconstruct cost = d_k - margin, flag a constraint as inert when cost/d_k stays below a low bar (e.g. < 20 pct) across Q4, and flag it as loose-budget/near-binding when cost/d_k > 80 pct without ever breaching - both mean the constraint is not shaping learning, for opposite reasons. (2) Training: constraint_encoder_runner.py should ALSO log Constraint/d_k_{name} (value = D_k / (1 - cost_gamma)) so future runs are self-describing and the engine needs no albc-config dependency. Past runs lack d_k -> engine must graceful-degrade (skip cost/d_k ratio, still report raw margin/viol) when d_k tag absent.

[STATUS] implemented (2026-06-05)

[IMPL] Engine (.omx/profile/analyze_training.py): added _constraint_names (dual-schema discovery), _constraint_series (reconstructs cost from either cost_return_ OR d_k/-minus-margin/), _cost_ratio_q4, _find_inert_constraints (achieved <20pct / loose >80pct), _cost_trend_late_series. _find_diverging_costs + _margin_at_floor + format_tier2 constraint section rewritten dual-schema. New TIER2 output: per-constraint c/dk ratio + INERT/LOOSE alert + summary "N/M constraints inert". Training (constraint_encoder_runner.py:276): now logs Constraint/d_k/{name} = D_k/(1-cost_gamma). NOTE deviation from SPEC: used slash form Constraint/d_k/{name} (not underscore d_k_{name}) for consistency with the existing margin//viol/ hierarchy; engine fallback still reads the old underscore names for synthetic runs. Verified: teacher run discovers 10 names + graceful no-d_k degrade (raw margin/viol shown); synthetic d_k run classifies cumul_yaw/yaw_rate INERT, thruster_util LOOSE, rp_rate active - all correct.

