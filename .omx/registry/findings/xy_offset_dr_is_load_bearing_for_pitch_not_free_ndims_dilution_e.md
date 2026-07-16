---
title: "xy-offset DR is load-bearing for pitch, not free NDIMS dilution (e4 xyprune)"
tags: ["dr", "doraemon", "heavy-tail", "pitch", "roll", "xyprune", "p7_tail", "privileged-obs"]
created: 2026-07-14T05:10:47.487506
updated: 2026-07-16T06:53:56.907691
sources: ["trpo_e4_xyprune_260714_090201", "diagnose-20260714-135623"]
links: ["doraemon_over_widens_then_oscillates_when_a_converged_teacher_is.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md", "buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy.md", "cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
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

---

## Update (2026-07-16T06:53:56.907691)

## Update (2026-07-16): USER DECISION — e4 FULLY REJECTED; the whole xy-prune DIRECTION is closed, including the `_y`-only refinement

[DECISION] User (2026-07-16): "e4는 완전 기각하는걸로 하자. 굳이 이 dr 파라미터를 지울 이유가 없다."
This is STRONGER than the 2026-07-14 discard, which rejected only the *blanket 4-dim* prune and left a
`_y`-only refinement queued. The direction itself is now CLOSED: do not prune cog/cob xy-offset DR dims,
in any subset, blanket or refined.
[CONFIDENCE: HIGH — user domain judgment, the same authority that opened the buoy volume/mass
decorrelation gate on 2026-07-08]

RATIONALE (user): the manufacturing tolerance these dims model is PHYSICALLY REAL on the hardware, so
removing them makes the sim less like the robot. NDIMS economy is not a reason to stop modelling a real
disturbance. This is the mirror image of the 2026-07-08 buoy volume/mass decision (a real, physically
independent tolerance JUSTIFIED adding dims) — the same principle, applied in the removal direction.

REINFORCING EVIDENCE (surfaced 2026-07-16, already recorded in
[[buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy]]): the 4 pruned dims are
BODY-SHARED — `randomize_hydrodynamics` calls `_randomize_hydro_model` for BOTH `env._hydro` (main,
body="base") and `env._buoy_hydro` (body="link3", the arm-tip float) with the SAME `sampled` dict; only
`volume_key` is parameterized (events.py:293-295). So pruning them pins the lateral centers of the
ARM-TIP BUOY too, not just the hull. Because link3 sits at the end of the manipulator, its lateral
center offset is modulated by arm pose — i.e. the prune deleted an arm-pose-dependent disturbance, which
is a further reason the pitch trim was load-bearing (this campaign's H2). It also makes the prune a
LARGER intervention than its "remove 4 hull-tolerance dims" framing suggested.

## What this retires

- RETIRED: this page's own NEXT-PROBE hint ("prune only the roll-coupled `cob/cog_offset_y`, keep the
  pitch-coupled `_x`"). Do NOT re-propose it. Any future proposal to prune these dims should be rejected
  at design time citing this decision.
- RETIRED: teacher_baseline_opt README 교훈 2 ("`_y`만 정밀 prune") and §5 재설계 대기
  ("e4-refined `_y`-only prune") — same lead, same retirement.
- RETIRED as an e4-motivated probe: the common-exam re-eval of the e4 checkpoint proposed in
  [[cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov]]. With the prune direction closed,
  re-grading e4 on a shared DR has no decision value — it could only inform a prune we will not do.

## What SURVIVES the rejection

- The OBSERVATION stands: the roll heavy-tail is responsive to DR-dimension shaping (hard 23.2x->10.5x,
  none 5.7x->1.8x, on a wider/harder exam). e4 remains this campaign's only demonstrated tail lever.
  What is dead is the LEVER (prune), not the FINDING (roll tail is shapeable). A future tail probe must
  reach that responsiveness by some means other than deleting a physically-real DR dim.
- The over-widen mechanism stands: removing DR dims let DORAEMON over-widen the survivors past the alpha
  feasibility floor (mode=-2, success 0.36 < 0.429) — same family as e3, reached by dim-count rather than
  budget. See [[doraemon_over_widens_then_oscillates_when_a_converged_teacher_is]].
- The common-exam METHODOLOGY (frozen reference DR + `--doraemon-dr-from`) is independent of e4 and
  remains an open lead on its own merits.

