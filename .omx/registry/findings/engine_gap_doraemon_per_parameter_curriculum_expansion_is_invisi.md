---
title: "engine-gap: DORAEMON per-parameter curriculum expansion is invisible in the text diagnosis (TIER 2 prints only success/ess/mode)"
tags: ["engine-gap", "analyze_training", "doraemon", "curriculum", "omx"]
created: 2026-07-27T04:26:02.980659
updated: 2026-07-27T04:38:04.407694
sources: ["diagnose-fault-dr-260727"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# engine-gap: DORAEMON per-parameter curriculum expansion is invisible in the text diagnosis (TIER 2 prints only success/ess/mode)

[ENGINE-GAP] analyze_training.py [TIER 2] DORAEMON prints only success / ess_ratio / mode. There is NO per-parameter line telling whether each DR dim expanded, saturated, stalled, or contracted -- so the single most load-bearing result of the fault-DR A/B had to be hand-derived (load curriculum_trajectory.json, index param_names, convert per-dim Beta(a,b) to mean/std against param_bounds by hand). That hand computation is what revealed fault_severity reached only mean 0.077 (Arm A) / 0.096 (Arm B) of its [0,1] range and was STILL RISING at iter 4750 -- under-expanded, not stalled. A numbers-first report misses this entirely; the engine's 05_doraemon_curriculum.png plots the bands but no text line states it. [WHERE] .omx/profile/analyze_training.py TIER 2 DORAEMON block; reuse the auto-discovery already used by the deep-plot at ~line 1701 (globs DORAEMON/mean/<param>) so new DR dims appear for free. [SPEC] emit a per-param table (param | mean_final | frac_of_range | std | trend | verdict) with verdict in {SATURATED, EXPANDING, STALLED, CONTRACTED} derived from the trajectory shape, preferring TB tags DORAEMON/mean/* + DORAEMON/std/* (21 dims present on the fault-DR runs) over parsing curriculum_trajectory.json; surface EXPANDING/STALLED calls into the [DIAGNOSIS] list. [EVIDENCE] fault-DR runs 2026-07-27: engine TIER2 said only 'success=0.58 ess_ratio=0.77 mode=0.00' (Arm A) / 'success=0.73' (Arm B) while the hand-computed fault_severity trajectory showed monotone expansion 0.010 -> 0.077/0.096 across iters 0..4750. [STATUS] proposed. Full prompt: /workspace/.sp/plans/2026-07-27-analysis-engine-upgrades.md (G3).

---

## Update (2026-07-27T04:38:04.407694)

RESOLVED (2026-07-27, commit 8f9bfbc): [TIER 2] DORAEMON now renders a per-dim curriculum table (mean(final), frac-of-range, std, trend/1k, verdict SATURATED|EXPANDING|STALLED|CONTRACTED), auto-discovered from DORAEMON/mean|std/<param> TB tags; bounds come from the run's curriculum_trajectory.json (TB has no bounds tags). [DIAGNOSIS] aggregates the calls: one-sided mean-channel dims named with their frac (e.g. 'fault_severity at 8% of range'), centered std-widening dims counted. Verified against the fault-DR Arm A hand-derivation (0.077 / 7.7% EXPANDING). Verdict thresholds are fixed heuristics (flat <1% of range moved over last quarter, at-bound 2%, saturated width 90% of uniform std) -- see _doraemon_param_verdicts in analyze_training.py.
