---
title: "HydroRC IS half-recentered (buoy/link3 nominals untouched) -- but the '10x under added mass' framing dies to the effective-vs-effective correction (~2.4x); the lead survives on a different mechanism: HydroRC drops hull yaw damping 45x, so unmeasured analytical buoy damping becomes 1.8x hull's and DOMINATES the retrained plant"
tags: ["stonefish", "hydrodynamics", "buoy", "link3", "added-mass", "domain-randomization", "sim-to-real", "hydro-recenter", "yaw", "system-id", "envs-main", "guard-policy", "handoff"]
created: 2026-07-27T11:28:30.027308
updated: 2026-08-04T16:49:24.840526
sources: ["marinelab:exp/hydro-recenter@016d1b1", "marinelab@f45d612", "next-20260727-174905", "code-review-20260727", "diagnose-20260728-081953", "code-verify-20260729", "handoff-stonefish-servo-pc-20260729"]
links: ["stonefish_yaw_gap_claim_review_main_body_hydro_yaw_torque_struct.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy.md", "stonefish_base_hull_effective_hydro_measured_2026_07_27_damping.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
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

---

## Update (2026-07-27T23:24:47.066924)

UPDATE 2026-07-28: the half-recenter shipped and FAILED the Isaac paired gate (HydroRC probe,
trpo_hydrorc_s30_260728_013136 -- roll n_gt20 0 -> 18.67 envs, yaw ss +18.8%, hard-corner collapse).
Consistent with this page's mechanism: with hull yaw damping cut 45x while the analytical buoy hydro
stays untouched, the unmeasured buoy damping dominates the retrained plant -- and the retrained policy
regresses on transients across all DR levels. The gate FAIL adds evidence that a partial/guarded
recenter (or a measured buoy correction) is required before the plant can move toward the Stonefish
values. Probe design for buoy/link3 measurement remains undecided (unchanged).
[EVIDENCE: report diagnose-20260728-081953 under trpo_hydrorc_s30_260728_013136/analysis]

---

## Update (2026-07-29T08:50:56.367055)

RE-VERIFIED 2026-07-29 AGAINST envs/main, AND THE SCOPE IS WIDER THAN THIS PAGE STATED. Every code citation on this page pointed at envs/full_dof paths, which invites the reading that the lead is legacy-only. It is not: the CURRENT teacher task envs/main wires the buoy identically. env._buoy_hydro is built at envs/main/albc_env.py:269, its wrench is applied every step, and envs/main/mdp/events.py:295 randomizes it through the same _randomize_hydro_model call as the hull, with the same post-sampling re-clamp at threshold = 0.95 (events.py:273). So rebuttal 2 binds on the plant the final teacher actually runs on. [CONFIDENCE: HIGH]

ONE MORE ARGUMENT FOR REBUTTAL 2, FROM THE CONFIG ITSELF. The cap is not a subtle consequence to be discovered by arithmetic -- ALBCBuoyHydrodynamicsCfg already documents it in the comment above added_mass: "Capped for stability: M_a[i] < I_rigid[i]" and "surge/sway=0.7 (theory 2.67, capped)". The installed value is a KNOWN, DECLARED simplification, not an unexamined default. Numerically the DR cap is 0.95 * 0.93 = 0.8835 kg while theory sits at 2.01 kg (Ca 0.75, this pages rebuttal) to 2.67 kg (Ca 1.0, the config comment), i.e. 2.28x to 3.02x above the cap. No measured buoy added mass in that range is installable, which is exactly why the deliverable is a guard-structure decision and not a coefficient. [CONFIDENCE: HIGH]

UNRESOLVED MINOR. The config comment and this pages rebuttal disagree on the theory number (2.67 vs 2.01 kg) because they use Ca 1.0 vs the Ca 0.75 short-cylinder value the same docstring cites. The conclusion is unaffected at either value; settle it only if the theory number is ever needed on its own.

DISPATCHED 2026-07-29. A handoff to the Stonefish session asks the three questions that actually gate the measurement route -- can link3/ABPC be excited independently at all, is adding a force-application path cheap, and does the Stonefish buoy model even carry a separate added-mass term -- rather than commissioning a measurement. A no on the first two CLOSES the measurement route and converts this lead into an Isaac-side guard decision. Handoff at /workspace/.sp/plans/2026-07-29-handoff-stonefish-servo-pc.md (scratch, gitignored). It is bundled with the servo-gain fix because the servo chatter contaminates any arm-involving Stonefish measurement, and decay/oscillation measurement is exactly the class a high-frequency limit cycle corrupts.

---

## Update (2026-08-04T16:49:24.840526)

## VERDICT 2026-08-05 -- RESOLVED (backlog-closeout program)

This lead survived its own correction on a specific mechanism: HydroRC drops hull yaw damping
45x, so the unmeasured analytical buoy damping would become about 1.8x the hull's and would
DOMINATE the retrained plant. That mechanism is now answered on two independent grounds.

**It is conditional on a plant we are not building.** The 45x drop comes from 016d1b1, which is
not on marinelab main and is retired rather than rebuilt (see the hydrorc_016d1b1 page, resolved
the same day). Without that commit the hull keeps its analytical yaw damping and the buoy never
becomes dominant.

**And the dominance would not matter even if it happened.** A hull-yaw-damping bracket directly
perturbs the hull-versus-buoy balance this lead is about, and it was swept 100x -- more than
twice the 45x the mechanism invokes -- in both directions.

The bracket, run 2026-08-05 on the E-int teacher (model_4999.pt) against its own baseline eval
static_260804_203719 -- same GPU, same branch, same DORAEMON anchor:

| point | hull yaw damping | result |
|:--|:--|:--|
| baseline | linear 0.15, quadratic 0.5 | reference |
| low | linear 0.015, quadratic 0.05 | ZERO REAL flags; survival unchanged at all four levels |
| high | linear 1.5, quadratic 5.0 | ZERO REAL flags; survival unchanged at all four levels |

Across a **100x span** nothing clears a decision floor on any field, axis or DR level. The
largest movement anywhere is ss_error_std +0.169 deg at hard against a 0.60 deg floor, and the
hard-level ss_error actually improves slightly (-0.058 deg) with more damping. Both ends are
sub-floor.

The intervention is verified to have bitten rather than assumed to have: `dr_lin_damp_5` records
0.1597 at baseline and 0.01597 in the low arm, exactly the intended 10x, and the tool's own
BITE-CHECK passes on all four levels. It is also verified to be surgical: 23 of the 24 dr+fault
keys are elementwise identical between conditions, and the single differing key is the one that
was supposed to differ. This matters here because a previous eval-side injector in this project
ran happily and changed nothing, and the silent no-op was caught only by a byte-identical
comparison.

**Verdict**: RESOLVED. The lead's probe-design blocker also dissolved independently -- it was
waiting on a Stonefish-side route (no link3, no external-wrench service), and Stonefish was
dropped entirely by user decision on 2026-08-05. The buoy half of this page's concern is
handled on the buoy_added_mass page, which was resolved by measurement the same day and found
a numerical stability cliff rather than a coefficient error. Deliberately not duplicated here
so that question keeps one home.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

