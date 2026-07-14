---
title: "xy-offset DR is load-bearing for pitch, not free NDIMS dilution (e4 xyprune)"
tags: ["dr", "doraemon", "heavy-tail", "pitch", "roll", "xyprune", "p7_tail", "privileged-obs"]
created: 2026-07-14T05:10:47.487506
updated: 2026-07-14T05:10:47.487506
sources: ["trpo_e4_xyprune_260714_090201", "diagnose-20260714-135623"]
links: ["doraemon_over_widens_then_oscillates_when_a_converged_teacher_is.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# xy-offset DR is load-bearing for pitch, not free NDIMS dilution (e4 xyprune)

Probe e4 (proposal next-20260713-143610) pruned the 4 xy body-offset DR dims (cog_offset_x/y, cob_offset_x/y) from _PARAM_DEFS (NDIMS 20->16) and trimmed privileged obs p_t 28->24D, vs baseline trpo_baseline_260713_031325. Discriminator: NDIMS-dilution (H1) vs load-bearing-offsets (H2).

OUTCOME = SPLIT BY AXIS (reviewer-approved, all numbers recomputed exact):
- H1 confirmed for ROLL: the roll heavy-tail genuinely shrank -- hard per-env median |error_roll| max/median 23.2x->10.5x, top-6/64 48.7%->29.4%, and at the FAIR none level 5.7x->1.8x (max 1.031->0.329 deg). This is REAL, not a milder-exam artifact: e4's end-of-training DR is WIDER than baseline (every surviving DR dim wider in data_hard.npz; DORAEMON/std/inertia_scale 0.352 vs 0.268), so the shrink is achieved on a HARDER exam and is understated.
- H2 confirmed for PITCH: at the fair none level pitch ss_error regressed 2.61x (0.208->0.543 deg) as a pure DC-bias (none pitch ss_jitter unchanged 0.081->0.085), dragging att_norm none to 1.34x worse. Removing the xy body-offset DR removed the disturbance the pitch trim was learned against.

So the xy-offset DR is NOT free budget dilution -- it is load-bearing for pitch trim, while the roll tail IS responsive to DR-dimension shaping (a reusable lever). A blanket 4-dim xy prune trades roll tail for pitch mean.

Training-health cost: removing 4 DR dims let DORAEMON over-widen the survivors past the alpha feasibility floor -> mode=-2 (infeasible), doraemon_success_rate 0.36 < baseline 0.429, Reward/total 6.87 < 7.81. Same over-widen family as e3 (budget extension), reached here by dim-count reduction. See [[doraemon_over_widens_then_oscillates_when_a_converged_teacher_is]].

DECISION: recommend DISCARD (do not merge exp/dr-xy-prune; keep main at 28D, 8a9d8df) -- the whole-policy effect at the fair level is a regression plus infeasible curriculum, and the roll win does not offset it. Branch merge/discard is the user's call per comparison-experiment-isolation.

NEXT-PROBE hint for exp-design: do NOT re-propose a blanket xy-offset prune. A sharper one-variable follow-up: prune only the roll-coupled offsets (cob/cog_offset_y, which create roll moments) while KEEPING the pitch-coupled _x dims that the pitch trim needs. Weigh against e2's bias-observation family (which gave a large absolute tracking gain without a pitch cost). Cross-run tail comparisons must anchor to the none level per [[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]].

