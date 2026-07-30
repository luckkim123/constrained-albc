---
title: "Stonefish base-hull effective hydro MEASURED (2026-07-27): damping is the gap axis (yaw ~45-100x, pitch-linear ~10x, translational 3-8x under nominal); effective added inertia already matches; nominals recentered on marinelab exp/hydro-recenter"
tags: ["stonefish", "hydrodynamics", "system-id", "damping", "added-mass", "sim-to-real", "domain-randomization", "decay-test", "engine-bug", "hydrorc"]
created: 2026-07-27T08:42:33.953196
updated: 2026-07-30T02:29:55.535066
sources: ["vault:krit/simulator/docs/stonefish-hydro-measurement-2026-07-27.md", "marinelab:exp/hydro-recenter@016d1b1", "stonefish_dev:/tmp/hydro", "hull-addedmass-correction-20260730", "stonefish-reply-20260730", "code-verify-20260730"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
blocked-on: "RETRACTED 2026-07-30: these nominals are engine artifacts and must NOT be applied; the live item moved to hydrorc_016d1b1_recentered_nine_hull_hydro_numbers_onto_a_broken"
---

# Stonefish base-hull effective hydro MEASURED (2026-07-27): damping is the gap axis (yaw ~45-100x, pitch-linear ~10x, translational 3-8x under nominal); effective added inertia already matches; nominals recentered on marinelab exp/hydro-recenter

Base-only system-ID rig in stonefish_dev (deployment hull geometry: cylinder r=0.09 h=0.3105 + gripper stand-off, neutral mass trim 7.886 kg, cg z=+0.05 kept, 60 m depth, freshwater 998). Thruster-step terminal velocity (absolute drag, ThrusterState reported thrust = applied force, no thrust-model assumption) + release decay (effective mass) + static-tilt restoring k + free-decay oscillation (pitch I+A, c1, c2) + spin-down (yaw ratios). Purity via empirically-solved combos (onset-accel B matrix); heave up/down symmetric; fits trim-robust (rotor spin-down tail excluded: means shift <1%).

MEASURED vs ALBCHydrodynamicsCfg nominal (base body):
- yaw: c1 0.0012-0.0026 / c2 0.0094-0.0116 vs nominal 0.15 / 0.5 -> ~45-100x under. c2/I=0.224 consistent over 4 amplitudes.
- pitch: c1 ~0-0.06 (=~0) / c2 1.0-1.2 vs 0.3 / 1.0; measured k 3.06-3.62 N.m/rad (analytic W*BG 4.27, -15~28% seam unresolved).
- surge/sway: c2 ~7.6-11.5 / 4.9-7.4 vs 39 (3-8x under); absolute scale banded on A_surge theory (slender-body 8.25 outside validity at L/D 1.7 -> band [4,10]).
- heave: c1 1.61 / c2 22.7 vs 1.5 / 15 (comparable); A = 15.0+-0.3 kg vs nominal 1.0.
- ADDED-INERTIA KEY CORRECTION: added_mass_stability_factor 0.5 ATTENUATES the applied added-mass force (hydrodynamics.py:361), so Isaac EFFECTIVE inertia = I_rigid + 0.5*A_nominal. Effective-vs-effective: pitch 0.133-0.148 (SF) vs 0.144 (Isaac), yaw 0.042-0.052 vs 0.055, surge band 11.9-17.9 vs 13.2 -> NO gap on rotational/translational added inertia; only heave gaps (22.9 vs 9.68).

APPLIED (marinelab exp/hydro-recenter 016d1b1, stacked on B0c f45d612; DR relative ranges untouched):
linear_damping (2,2,1.5,0.3,0.3,0.15)->(0.5,0.5,1.6,0.03,0.03,0.002); quadratic_damping (39,39,15,1,1,0.5)->(8.0,8.0,22.7,1.2,1.2,0.011); added_mass heave 1.0->8.0 (measured 15.0, hard cap M_a<body_mass 9.18 binds, surge-precedent ratio 0.87). Rotational added mass KEPT (effective match). volume/cg/cob unchanged (engine displaced volume 7901.3 cm3 = cfg 0.00790 exactly).

CAVEATS: (a) recentered yaw band [0.4,1.7]x0.011 excludes the old analytical 0.5 entirely - this is an explicit Stonefish-transfer choice, Stonefish is NOT ground truth (see stonefish_yaw_gap page caveat); real-vehicle anchoring stays the band strategy (sim_hydro page). (b) buoy (link2/ABPC) hydro NOT measured (base-only rig) - the buoy added-mass ~10x-under lead stays open. (c) thruster reported-thrust sign convention seam (m2/m5 negative at +pwm) and odom-frame ambiguity documented in the vault doc. (d) Stonefish long-run degradation: physics stall after ~170 s continuous headless run - restart per family (133-175 s runs clean).

---

## Update (2026-07-30T02:17:19.388898)

[CORRECTION 2026-07-30] The "heave added mass ~15 kg, 15x above Isaac nominal" line in this
measurement is an ENGINE ARTIFACT and is retired. The damping conclusions and the rotational
added-inertia conclusion are untouched -- the correction is confined to translational added mass.
Consequence: `added_mass` heave 1.0 -> 8.0 should be DROPPED from HydroRC, not batched.

WHERE IT CAME FROM. The buoy work (P-C, 2026-07-29) found that SolidEntity::ComputeCylindrical-
Approx() computes the axial added-mass term as m1 = rho*pi*r^2 -- dimensionally kg/m used as kg --
and that getAugmentedMass() then collapses the (m2, m2, m1) vector to its isotropic arithmetic
mean. That was recorded as a buoy finding. It is not: it is a generic SolidEntity method, so it
applies to EVERY cylinder solid. The ALBC hull is one of them --
albc.scn declares <external_part name="Base" type="cylinder" radius="0.09" height="0.3105">.

  term                                value [kg]   note
  m2 = rho*pi*r^2*L  (broadside)           7.885   dimensionally sound
  m1 = rho*pi*r^2    (axial)              25.396   missing length factor; disc geometry
                                                   (8/3)*rho*r^3 = 1.940, so 13.1x above physics
  isotropic mean, getAugmentedMass()      13.722   (7.885 + 7.885 + 25.396)/3
  Base rigid mass                          9.180   albc.scn <mass value="9.18"/>
  PREDICTED effective mass                22.900   plus a little from Gripper (0.30 kg, cylinder)

This page reports a MEASURED effective mass of 22.6-23.3 kg, consistent over four decay runs. The
prediction lands inside the measured band. Exactly as with the buoy, the source explains the
measurement -- which is how we know the measurement is faithfully reporting the bug.

TWO CONSEQUENCES.

(1) 22.6-23.3 IS NOT A HEAVE NUMBER. It is the isotropic mean, so it carries no axis information.
Setting it beside Isaac's per-axis heave nominal of 1.0 and calling the ratio "15x" was a category
error stacked on the dimensional bug. Stonefish structurally cannot supply a per-axis translational
added mass: getAugmentedMass() averages the three axes, whereas getAugmentedInertia() does not, so
the isotropic collapse hits translation only.

(2) ON GEOMETRY, THE ISAAC NOMINAL IS ALREADY DEFENSIBLE. The hull cylinder axis is body z, so
heave is axial and surge/sway are broadside:

  axis         geometric [kg]                             Isaac nominal   verdict
  surge/sway   7.885 (5.5-7.9 with finite-length corr)         8.0        agrees, at most 1.4x high
  heave        1.940 (disc limit)                              1.0        1.9x low

So the recentering line `added_mass`: heave 1.0 -> 8.0 must be RETIRED. Applying it puts heave 4x
ABOVE geometry -- it moves the plant away from physics, in the same way and for the same reason
that recentering the buoy onto the Stonefish measurement would.

STATE OF THAT CHANGE, verified rather than assumed. It has NOT reached the mainline: marinelab @
f45d612 (exp/max-thrust-dr) still reads added_mass = (8.0, 8.0, 1.0, 0.09, 0.09, 0.035). It IS on
exp/hydro-recenter @ 016d1b1, and that branch was the delta of the 2026-07-28 half-recenter run
that FAILed the Isaac paired gate. This is NOT a claim that it explains the roll/yaw regressions --
wrong axis, and the run data was not re-examined. The narrower claim is that the run carried a hull
heave nominal we now know originated in an engine artifact, so it was not the clean single-variable
test of damping recentering it was designed to be. Drop that line when HydroRC-v2 is rebuilt.

This also removes the last exception from the earlier reduction of this page's added-mass finding
("no gap except heave"). There is no base translational added-mass gap at all.

GUARD SCOPE NARROWS TO THE BUOY. The hull needs no guard decision: generalized inertia 9.18 puts
the per-reset cap at 0.95 * 9.18 = 8.72 and the geometric maximum is 7.9, so there is headroom.
Only the buoy binds (geometric ~2.0 against a 0.8835 cap).

A CAVEAT ON THE DAMPING SIDE TOO. The same function ends with a hardcoded Vector3 Cd(0.5, 0.5, 1.0)
applied to every cylinder regardless of L/D. So the axial:broadside quadratic-damping ratio of 2.09x
measured on the buoy rig is NOT geometry-derived -- it is that constant (2x) times the frontal-area
ratio (1.13x). Geometry alone gives 1.13x. On a slender cylinder the same constant would make
Stonefish wrong in the opposite direction. Isaac's anisotropy ORDERING is still wrong and still
worth fixing from the frontal-area argument, but the MAGNITUDE target must come from geometry or
literature, not from the Stonefish measurement. Same trap as the added mass: Stonefish is a good
detector of the other simulator's errors and a bad source of its values.

FOR AN UPSTREAM BUG REPORT: state the inflation against physics, not against a dimensionally fixed
version of itself. m1 is 3*pi/(8*r) above the disc limit -- 13.9x for the buoy (r=0.085) and 13.1x
for the hull (r=0.09). "1/L" (8.47x, 3.22x) is only the missing length factor. Note also that
getAugmentedMass() then averages the broken axis into the other two, so the error propagates to all
three translational axes of every cylinder solid.

Full result: vault docs/stonefish-hydro-measurement-2026-07-27.md, section "정정 (2026-07-30)".
[SOURCE: hull-addedmass-correction-20260730] [CONFIDENCE: HIGH]

---

## Update (2026-07-30T02:29:55.535066)

CORRECTION 2026-07-30 -- THESE MEASUREMENTS REPORT THE ENGINE, NOT THE HULL. Do not reuse any number
on this page as a hull property without re-deriving it from geometry first.

The Stonefish side traced its ComputeCylindricalApprox dimensional bug to the ALBC base hull, which
albc.scn declares as a cylinder external_part r=0.09 h=0.3105. The axial added-mass term is computed
as rho*pi*r^2 (a mass per unit length used as a mass), giving 25.396 kg against the disc-limit physics
value of 1.940 kg, i.e. 13.09x above physics. getAugmentedMass then averages that broken axis into the
other two, producing an isotropic 13.722 kg; plus the rigid 9.18 kg this predicts an effective mass of
22.902 kg. This page reports a measured effective mass of 22.6-23.3 kg. The source explains the
measurement exactly, which is how we know the measurement is reporting the bug.

Two consequences for this page. (1) The effective mass here is an ISOTROPIC AVERAGE and carries no
axis information at all, so the derived heave added mass A=15.0 is not a heave quantity; Stonefish
structurally cannot supply a per-axis translational added mass. Rotational is different --
getAugmentedInertia does not average -- so the pitch and yaw effective-inertia agreements this page
records are unaffected. (2) The damping numbers inherit the same class of defect from a different
mechanism: the same engine function ends with a hardcoded Cd(0.5, 0.5, 1.0) applied to every cylinder
regardless of L/D, which alone is 2.34x below the analytical Cd_cross of 1.17, and the single-cylinder
approximation omits appendage, thruster and gripper drag entirely. The damage is concentrated on yaw
(linear 75x, quadratic 45x), the one axis that is rotation about the cylinder's axis of revolution;
roll and pitch quadratic barely move. See the full audit and prescription in wiki
hydrorc_016d1b1_recentered_nine_hull_hydro_numbers_onto_a_broken.

The caveat already on this page -- "recentered yaw band excludes the old analytical 0.5 entirely, this
is an explicit Stonefish-transfer choice, Stonefish is NOT ground truth" -- was the right instinct and
is now upgraded from a caution to a measured defect. The exp/hydro-recenter nominals derived here must
not be reinstalled as-is.

[EVIDENCE: Stonefish reply 2026-07-30 with hull cylinder declaration and Cd constant; arithmetic
re-derived 2026-07-30 code-exec at rho=998 matching their 7.885 / 25.396 / 1.940 / 13.722 / 22.900 to
three decimals; git show 016d1b1 damping delta by axis] [CONFIDENCE: HIGH on added mass; HIGH on the
Cd constant arithmetic; MEDIUM on the yaw-specific mechanism pending the rotational-drag question]

