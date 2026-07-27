---
title: "HydroRC IS half-recentered (buoy/link3 nominals untouched) -- but the '10x under added mass' framing dies to the effective-vs-effective correction (~2.4x); the lead survives on a different mechanism: HydroRC drops hull yaw damping 45x, so unmeasured analytical buoy damping becomes 1.8x hull's and DOMINATES the retrained plant"
tags: ["stonefish", "hydrodynamics", "buoy", "link3", "added-mass", "domain-randomization", "sim-to-real", "hydro-recenter", "yaw", "system-id"]
created: 2026-07-27T11:28:30.027308
updated: 2026-07-27T11:28:30.027308
sources: ["marinelab:exp/hydro-recenter@016d1b1", "marinelab@f45d612", "next-20260727-174905", "code-review-20260727"]
links: ["stonefish_yaw_gap_claim_review_main_body_hydro_yaw_torque_struct.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy.md", "stonefish_base_hull_effective_hydro_measured_2026_07_27_damping.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "probe design undecided (link3 has no thruster, Stonefish has no external-wrench service); and per rebuttal 2 the deliverable may be a guard-structure decision rather than a measured coefficient"
---

# HydroRC IS half-recentered (buoy/link3 nominals untouched) -- but the '10x under added mass' framing dies to the effective-vs-effective correction (~2.4x); the lead survives on a different mechanism: HydroRC drops hull yaw damping 45x, so unmeasured analytical buoy damping becomes 1.8x hull's and DOMINATES the retrained plant

Reviewed (2026-07-27, code-verified, NO measurement and NO training run) the claim "HydroRC is a
half-recentering: Isaac runs two hydro bodies (base + buoy/link3), Task 2 measured base only, and
HydroRC moves base nominals only, so the buoy band still sits on analytical values." VERDICT: the
factual premise is CONFIRMED, but the ORIGINAL SIZING ARGUMENT ("buoy added mass ~10x under") is
LARGELY WRONG once the effective-vs-effective correction is applied. The lead survives on a
DIFFERENT and stronger mechanism than the one it was filed under: HydroRC itself changed the
relative weight of the buoy channel.

CONFIRMED PREMISE (re-verified against disk, not copied from the brief):
- Two hydro cfgs exist: ALBCHydrodynamicsCfg body_name="base" and ALBCBuoyHydrodynamicsCfg
  body_name="link3" (marinelab/marinelab/assets/albc/albc.py, classes at :37 and :100).
- Buoy carries its own added_mass (0.7,0.7,0.2,0.002,0.002,0.002), linear_damping
  (0.8,0.8,0.6,0.02,0.02,0.01), quadratic_damping (10,10,8,0.05,0.05,0.02), body_mass 0.93,
  rigid_body_inertia (0.00278,0.00278,0.00336), added_mass_stability_factor 0.4.
- Buoy hydro is wired into the training env and applied every step: _init_hydrodynamics builds
  _buoy_hydro (envs/full_dof/albc_env.py:205-213, sharing the hull's OceanCurrent object), and
  the buoy wrench is pushed through permanent_wrench_composer at :809-819.
- DR randomizes BOTH bodies through the SAME sampler: randomize_hydrodynamics calls
  _randomize_hydro_model(env._hydro, ...) AND (env._buoy_hydro, ...) (envs/full_dof/mdp/events.py
  :281-283, docstring "for main body and buoy").
- DR scales are RELATIVE multipliers on nominal (events.py:196-210: base.added_mass * am_scales,
  base.linear_damping * ld_scales, base.quadratic_damping * qd_scales), so moving a nominal drags
  its whole band; leaving a nominal leaves its band.
- HydroRC scope confirmed by diff, not by assumption: git diff f45d612..exp/hydro-recenter@016d1b1
  touches ONLY albc.py, 20+/10-, entirely inside ALBCHydrodynamicsCfg. Zero lines mention Buoy.
  Buoy nominals are untouched.

REBUTTAL 1 (effective-vs-effective on the buoy) -- KILLS THE ORIGINAL SIZING. added_mass_stability_
factor is a force attenuator, not a cap threshold (core/hydrodynamics.py:361: added_mass_force =
self._compute_added_mass(...) * self._am_stability_factor), so Isaac's effective buoy inertia is
I_rigid + 0.4*A_nominal. Surge/sway: Isaac effective 0.93 + 0.4*0.7 = 1.21 kg vs Fossen short-
cylinder theory 0.93 + 2.01 = 2.94 kg (rho*V*Ca, V = pi*0.085^2*0.118 = 0.00268 m^3 matching cfg
volume exactly, Ca=0.75 per the cfg docstring) = 2.4x under, NOT 10x. Rotational is ~1.4x under on
a crude A_trans*(L^2/12) estimate. The "~10x" in the existing stonefish_yaw_gap card is a
nominal-vs-theory number computed before the base measurement forced the effective-vs-effective
correction; it should be read as superseded. This is the same reversal that turned base "added
mass 15x gap" into "no gap except heave."

REBUTTAL 2 (is there room to put a measured value?) -- SURVIVES, AND CHANGES THE PRESCRIPTION.
Two independent guards bind. (a) Construction-time _validate_added_mass_stability raises
ValueError at M_a/I_rigid >= 1.0 and warns above 0.8 (hydrodynamics.py:189-225); the buoy already
sits at surge/sway 0.753, roll/pitch 0.719, yaw 0.595. (b) A guard the brief did not know about:
DR itself re-clamps per env at threshold 0.95 AFTER sampling (events.py:265-271). Consequence with
the current band added_mass_scale=(0.5,1.5): the surge/sway high tail 0.7*1.5 = 1.05 exceeds the
clamp 0.95*0.93 = 0.883 and IS clamped; roll/pitch 0.003 exceeds 0.95*0.00278 = 0.0026 and IS
clamped; only yaw passes. So the buoy's upper DR tail is ALREADY truncated today, and even the
2.4x-under theory value (2.01 kg) cannot be installed as a nominal -- it is 2.2x the hard cap. The
actionable item is therefore NOT "measure and swap the coefficient"; it is a decision about the
guard structure (cap policy / stability factor / whether added-mass force belongs in an explicit-
integration external-wrench path at all). Precedent: base heave measured 15.0 was installed as 8.0
because the cap bound.

REBUTTAL 3 (is the buoy second-order next to the base gap?) -- REVERSES, STRENGTHENING THE LEAD.
Pre-HydroRC the answer was yes. Post-HydroRC it is no, and precisely BECAUSE of HydroRC. The buoy
yaw disturbance channel is translational drag at the lever arm, not the buoy's own yaw damping:
(0.8*0.5 + 10*0.5^2) N * 0.47 m = 1.36 N.m, reproducing the ~1.4 N.m figure the existing yaw card
derived. HydroRC drops hull yaw quadratic damping 0.5 -> 0.011 (45x). The disturbance is unchanged
while the hull's resistance to it fell 45x, so the buoy channel's share of the yaw budget rises by
that factor in the retrained plant. "Fix base first, buoy later" was sound arithmetic before
HydroRC and is not after it.

REBUTTAL 4 (does yaw_damping_scale reach the buoy?) -- CONFIRMED, and it compounds rebuttal 3.
events.py:213-215 overrides index 5 unconditionally inside _randomize_hydro_model, which both
bodies call, so the buoy's yaw quadratic damping is banded 0.02*(0.5,1.5) = 0.010..0.030. Against
hull yaw the buoy used to be 0.02/0.5 = 4% of hull damping; post-HydroRC it is 0.02/0.011 = 1.8x
hull damping. An unmeasured analytical coefficient that was a rounding error is about to become
the dominant yaw damping term in the retrained plant. This is the sharpest single argument in the
lead and it was not in the original claim.

NET VERDICT: HydroRC remains defensible to run as-is -- it is a strict improvement on the axis it
measured, and the buoy question is not a blocker (nothing here says the retrain is invalid). But
"buoy is second-order" is no longer a valid reason to defer, and the deferral should be recorded
as a deliberate scope choice with a known consequence, not as a sizing judgement. Concretely: after
HydroRC retrains, buoy analytical damping becomes the dominant yaw damping term and buoy
translational drag at lever arm becomes a larger share of the yaw disturbance budget.

PROBE DESIGN (open, not decided). The base rig cannot be copied: link3 has no thruster and
Stonefish exposes no external-wrench service (established during the base measurement). Candidates:
(a) attach a temporary thruster to the buoy body in a MEASUREMENT-ONLY scn -- the rig is a jig,
not the deployment model, so this is legitimate and reuses the base protocol verbatim (step
terminal velocity + release free-decay); currently the strongest candidate. (b) free-ascent
terminal velocity driven by net buoyancy +17.1 N -- yields heave drag only, no rotation, and is
corrupted if the buoy tumbles. (c) spin-down from an initial angular velocity -- requires first
verifying the scn/engine supports setting initial angular velocity. Undecided.

OPEN QUESTIONS: (1) Which probe design, given no thruster on link3. (2) Given rebuttal 2, is the
deliverable a measured coefficient at all, or a guard-structure decision? (3) Should the buoy's own
lever-arm-induced yaw moment be treated as a separate disturbance channel from its damping
coefficient in the DR space? (4) Sequencing: measure before the HydroRC retrain (delays it) or
after (the retrain then bakes in analytical buoy values)? This is a scope call, not a technical one.

CORRECTION TO AN EXISTING PAGE: stonefish_yaw_gap_claim_review_... claim 4 states "buoy added mass
is effectively ~10x UNDER." Per rebuttal 1 that number is nominal-vs-theory; the effective-vs-
effective figure is ~2.4x (translational) / ~1.4x (rotational). The direction stands, the magnitude
does not. That page is otherwise untouched here -- its P1 half stays open and is a separate lead.

[EVIDENCE: marinelab@f45d612 + exp/hydro-recenter@016d1b1 albc.py:37-151; core/hydrodynamics.py:
189-225,350-398; constrained-albc envs/full_dof/albc_env.py:189-213,805-819; envs/full_dof/mdp/
events.py:185-215,255-283; envs/main/config.py:178-206,485; git diff f45d612..016d1b1 --stat;
arithmetic re-derived 2026-07-27 code-exec] [CONFIDENCE: HIGH on the code facts and on rebuttals
2/3/4; MEDIUM on rebuttal 1's theory value, which uses the cfg's own Fossen Ca=0.75 rather than an
independent hydrodynamic derivation]

Cross-links: [[stonefish_yaw_gap_claim_review_main_body_hydro_yaw_torque_struct]],
[[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]],
[[buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy]],
[[stonefish_base_hull_effective_hydro_measured_2026_07_27_damping_]]

