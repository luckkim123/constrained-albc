---
title: "e3 extend10k REGRESSED the policy — training budget is NOT the p7_tail tail lever; keep 5000 iters"
tags: ["p7_tail", "budget", "extend10k", "doraemon", "heavy-tail", "regression", "verdict", "e3"]
created: 2026-07-13T23:52:42.715919
updated: 2026-07-13T23:52:42.715919
sources: ["diagnose-20260714-084409"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# e3 extend10k REGRESSED the policy — training budget is NOT the p7_tail tail lever; keep 5000 iters

Proposal next-20260713-142604 (resume baseline to iter ~15000, +10000, zero config delta) resolves to H2 (structural), decisively — and beyond H2 the extension was NET-HARMFUL. Judged vs the proposal bands: H1 needed hard roll max/median<=15x AND top-6/64<=40% AND att_norm hard ss_error<=0.80deg; e3 posted 41.6x / 53% / 0.999deg (ALL three violated). H2 needed max/median>=18x AND top-6>=45%; e3 posted 41.6x / 53% (both met). CRUCIAL: the only FAIR cross-run exam (none, fixed nominal physics) is not neutral but REGRESSED — att_norm ss_error 0.532->2.350deg (4.42x), per-env median |roll| 0.180->2.797deg (15.5x, and max/median collapses to 1.2x = uniform DC-bias across all 64 envs, not a tail). hard/soft/medium are NON-COMPARABLE (eval.py --doraemon-dr default True: e3 graded on its OWN wider learned DR; see eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr). Per-step reward fell 7.74->6.69 and Train/mean_reward 229.6(bl)->213.7(e3). DECISION: campaign KEEPS the 5000-iter run budget; e1/e2 tail verdicts carry NO under-training discount (extending makes them worse, not better); all tail-shrink work routes to STRUCTURAL probes (e4 xyprune DR-shaping, e2 bias-obs family). Evidence: analysis diagnose-20260714-084409 report.md sections 1,2,9 + verdict; run trpo_e3_extend10k_260713_224822 eval static_260714_082219.
