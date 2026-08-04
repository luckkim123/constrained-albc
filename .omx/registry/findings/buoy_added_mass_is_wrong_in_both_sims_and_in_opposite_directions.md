---
title: "Buoy added mass is wrong in BOTH sims and in opposite directions: Isaac 3.8-8.2x below the geometric value, Stonefish 3.5-5.7x above it via an isotropic average of a dimensionally broken axial term; recentering Isaac onto Stonefish moves it further from reality"
tags: ["sim-to-real", "stonefish", "buoy", "added-mass", "hydrodynamics", "domain-randomization", "hydrorc", "cross-sim-measurement", "guard-structure", "compound-body", "batch", "plant", "upstream-bug", "title-drift"]
created: 2026-07-29T09:01:06.191774
updated: 2026-08-04T16:24:13.137955
sources: ["buoy-hydro-rig-20260729", "buoy-probe-design-20260729", "stonefish-reply-20260729", "isaac-side-verify-20260729"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
blocked-on: "Isaac-side guard-structure decision, NOT a further Stonefish measurement (the probe route is closed: no link3, buoy welded into the link2 compound, no external-wrench service, and the standalone rig already ran). Decide among: raise the 0.95 cap, drop/retune added_mass_stability_factor, or move added mass out of the explicit external-wrench path into the mass matrix as Stonefish does. Target is the GEOMETRIC value (broadside ~2.0, axial ~1.6 kg), never the Stonefish measurement"
---

# Buoy added mass is wrong in BOTH sims and in opposite directions: Isaac 3.8-8.2x below the geometric value, Stonefish 3.5-5.7x above it via an isotropic average of a dimensionally broken axial term; recentering Isaac onto Stonefish moves it further from reality

[MEASURED 2026-07-29] The buoy's added mass is wrong in BOTH simulators, in OPPOSITE directions, and
the geometric answer is a value neither of them uses. Any plan that recenters Isaac's buoy hydro onto
Stonefish's measured value moves the policy FURTHER from the real object, not closer.

METHOD. Stonefish welds the buoy into the link2 compound alongside Arm2, so it cannot be isolated in
place; Isaac models it as its own link (link3) with its own ALBCBuoyHydrodynamicsCfg, so the
like-for-like object is a standalone cylinder. Built a measurement-only rig: buoy geometry verbatim
from albc.scn (r=0.085, h=0.118, V=0.0026786 m3), material Neutral so it is neutrally trimmed
(engine-reported mass 2.678 kg, volume 2678.4 cm3), driven by two Push actuators (+x broadside,
+z axial). Push applies ApplyCentralForce only -- no rotor, no propeller -- and the ROS2 interface
feeds the setpoint array straight into setForce(), so commands are NEWTONS. Four force levels
(2/5/10/20 N), each an 8 s hold to terminal velocity followed by a 10 s free decay. Terminal velocity
gives the damping with NO added-mass dependence; the decay then yields the effective mass.

GOTCHA worth recording: ThrustersCallback DROPS the entire message when its length differs from the
robot's actuator count. A 6-wide array copied from the 6-thruster vehicle produced zero motion for a
whole run, with the reason logged as "Wrong number of thruster setpoints".

DAMPING (terminal velocity, LSQ residual 0.066 N on x and 0.016 N on z):
  coefficient           Stonefish   Isaac
  linear, broadside        0.599     0.8
  quadratic, broadside     6.670    10.0
  linear, axial            1.186     0.6
  quadratic, axial        13.917     8.0
Same order of magnitude, but the ANISOTROPY IS INVERTED. This buoy is a squat disc (D=0.17 > h=0.118,
L/D=0.69), so its axial frontal area (0.0227 m2) EXCEEDS its broadside area (0.0201 m2) and axial
drag should be the larger one. Stonefish has that ordering; Isaac's (10, 10, 8) does not. Isaac's
values look like the intuition for a slender cylinder (L/D > 1), which this is not.

ADDED MASS. Fixing the damping coefficients and taking M = drag/(dv/dt) pointwise over the decays
gives M = 12.2-12.5 kg on ALL four force levels and BOTH axes (IQR width 0.2-0.6). Subtracting the
2.678 kg rigid mass leaves ~9.8 kg, ISOTROPIC.

The source explains both the magnitude and the isotropy. SolidEntity::ComputeCylindricalApprox():
    Scalar m1 = rho*M_PI*r*r;        // "Parallel to axis"  -> 22.65 kg here
    Scalar m2 = rho*M_PI*r*r*L;      // "Perpendicular"     ->  2.673 kg here
    aMass = T_CG2H.getBasis() * Vector3(m2, m2, m1);
m1 IS MISSING A LENGTH FACTOR -- it is dimensionally kg/m used as kg, which is why the axial term
comes out 8.5x the broadside term when for a squat disc it should be SMALLER. Then
getAugmentedMass() collapses the vector: `mass + (aMass.x + aMass.y + aMass.z)/3` = 2.678 + 9.33 =
12.01 kg, isotropic -- matching the measured 12.2-12.5 to within 2-4%. Note getAugmentedInertia()
does NOT average (it returns Ipri + aI per axis), so the isotropic collapse hits translation only.

AGAINST THE GEOMETRIC REFERENCE:
  axis        geometric [kg]                      Isaac   SF effective   Isaac err   SF err
  broadside   2.67 (2-D strip rho*pi*r^2*L)        0.7        9.33       3.8x low   3.5x high
  axial       1.64 (disc, (8/3)*rho*r^3)           0.2        9.33       8.2x low   5.7x high

This CONFIRMS the "buoy added-mass ~10x under" item on the yaw-gap page in both direction and
magnitude (13.3x and 46.6x below Stonefish). What it does NOT confirm is that page's implicit
premise that the Stonefish value is the target.

CONSEQUENCE FOR HYDRORC. HydroRC-v2 was designed as "recenter Isaac nominal onto Stonefish
measurement". For the buoy that is wrong: Stonefish's 9.33 kg is the product of a dimensional error
plus an isotropic average. The correct target is the geometric value (~2 kg broadside, ~1.6 kg
axial), and Isaac already supports a per-axis added_mass 6-tuple so no isotropic collapse is needed.
BUT the existing cap applies: added mass is clamped per axis to 0.95 * (DR-randomized rigid inertia)
and nominal already sits near that ceiling on this small vehicle. Raising broadside 0.7 -> ~2.0 will
hit that guard, so this is a GUARD-STRUCTURE decision, not a coefficient swap -- exactly the caveat
the probe plan flagged in advance.
It also re-frames the 2026-07-28 half-recenter FAIL: that run recentered base only and left the buoy
on analytic nominal, and the nominal it left in place is 4-8x below the geometric value.

NOT DONE: rotational added inertia (Isaac uses 0.002 on all three; Stonefish's formula is
I2 = (1/12)*pi*rho*L^2*r^3, I1 = 0). The same rig can excite it by offsetting the Push attachment.

Full result: vault docs/buoy-hydro-measurement-2026-07-29.md. Rig, runner, analyzer and raw CSVs at
tools/buoy_hydro/. [SOURCE: buoy-hydro-rig-20260729] [CONFIDENCE: HIGH]

---

## Update (2026-07-29T10:13:55.607781)

[SOURCE-VERIFIED 2026-07-29] The buoy MEASUREMENT ROUTE IS CLOSED, and that closes this item: the
standalone rig was the only like-for-like object and it already ran. What remains is an Isaac-side
guard-structure decision. Also: the "~10x under" figure is retired here in favour of a
total-effective-inertia table, and the reference implementation supplies direct evidence on the
guard question.

Q1 -- CAN link3 / THE BUOY BE EXCITED INDEPENDENTLY IN STONEFISH? Not in place. There is no link3:
albc.scn welds the buoy in as an external_part ("Buoy") of the link2 COMPOUND alongside Arm2, with no
joint between them, so nothing can move one relative to the other. Actuators CAN bind to any link --
ScenarioParser.cpp:2495 calls Robot::AddLinkActuator(act, robotName+"/"+linkName, origin) with an
arbitrary link name -- so a Push on link2 is legal, but it excites the Arm2+Buoy compound, which is
not the object Isaac's link3 models. Stonefish exposes no external-wrench service; the only force
injection path is an scn-declared actuator fed through thrusterSetpoints_. A STANDALONE rig is the
only like-for-like route, and that is exactly what buoy_rig.scn (P-C, same day) is. So this lead
converts from "needs a measurement" to "measured; awaiting an Isaac-side decision".

Q2 -- IS ADDING A FORCE PATH CHEAP? On a RIG, yes: one scn block, no Stonefish core change.
Push::Update is already an ApplyCentralForce path and the ROS2 layer feeds setpoints straight into
setForce(). On the DEPLOYED ROBOT, NEVER. Push and Thruster share the SINGLE thrusterSetpoints_
array indexed by declaration order (ROS2SimulationManager.cpp:379-407), and ThrustersCallback DROPS
THE WHOLE MESSAGE on a width mismatch (:913-917). Adding a 7th actuator to albc silently kills all
six thrusters for a bridge that keeps sending 6-wide arrays.

Q3 -- DOES THE BUOY CARRY A SEPARATE ADDED-MASS TERM, OR IS IT LUMPED? Both, and the distinction is
the whole answer.
  - PART LEVEL: it has its own term. The Buoy is a Cylinder, so ComputeCylindricalApprox() runs on
    its own r=0.085/h=0.118 and yields aMass = (2.673, 2.673, 22.65) kg. The <mass value="0.93"/>
    override does NOT rescale it: ScalePhysicalPropertiesToArbitraryMass (SolidEntity.cpp:124-135)
    touches only mass and Ipri. Added mass stays geometry-derived.
  - LINK LEVEL: it is collapsed. Compound::RecalculatePhysicalProperties() folds each external part
    in through a SCALAR -- compoundAugmentedMass += part->getAugmentedMass(), and
    SolidEntity::getAugmentedMass() returns mass + (aMass.x+y+z)/3, the isotropic average. The
    compound then re-broadcasts that as isotropic (Compound.cpp:266-268).
  - ROTATION takes a different path: the compound inertia sum uses the part's per-axis
    getAugmentedInertia() (Ipri + aI) AND the part's AUGMENTED mass as the point mass in the
    parallel-axis term (Compound.cpp:211,219), so the buoy's added mass survives as rotational added
    inertia about joint1 through its 0.233 m moment arm.
So the comparable quantity is the PART-LEVEL SCALAR, which is measured (9.33 kg predicted, 12.2-12.5
kg total effective measured). What is malformed as posed is anything AXIS-RESOLVED: Stonefish
collapses translation to one isotropic number at both part and link level, so Isaac's per-axis
6-tuple has no counterpart to be arbitrated against.

RETIRING "~10x under". The correction is accepted: my table compared added-mass COEFFICIENTS while
the dynamics are governed by TOTAL EFFECTIVE INERTIA (rigid + added). Restated on that basis, with
the deployed buoy rigid mass 0.93 kg and Fossen short-cylinder geometry:

  axis        geometric total     Isaac total (after 0.4 stability factor)   Stonefish total
  broadside   0.93+2.01 = 2.94    0.93+0.28 = 1.21   -> 2.4x LOW             0.93+9.33 = 10.26 -> 3.5x HIGH
  axial       0.93+1.64 = 2.57    0.93+0.08 = 1.01   -> 2.5x LOW             0.93+9.33 = 10.26 -> 4.0x HIGH

The old "~10x" was stated against Stonefish's value as if it were the target, and that premise died
with the P-C measurement. This table replaces the yaw-gap page's buoy line.

REFERENCE-IMPLEMENTATION EVIDENCE FOR THE GUARD DECISION. Stonefish runs this buoy at M_a/m ~= 10.0
(9.33 added against 0.93 rigid; ~9x at the link2 compound level) with NO cap at all, and it is
stable -- the P-C measurements matched theory to within 2-4%. Isaac's construction-time guard raises
at M_a/I_rigid >= 1.0, i.e. Stonefish stably runs an order of magnitude past the ratio Isaac refuses
to construct. The reason is the integration path: Stonefish never adds added mass as an external
force. It sets the multibody link's MASS AND INERTIA to the augmented values at construction --
FeatherstoneEntity.cpp:37-38, 470-471, 506-507, 541-542 all pass getAugmentedMass() /
getAugmentedInertia() as the link constructor arguments. Added mass lives in the MASS MATRIX, so a
large ratio does not destabilise it. Answering the third branch of the guard question directly: no,
added-mass force does NOT belong in an explicit-integration external-wrench path, and the 0.95 cap
is not a physical law but a stabilisation convention forced by using that path. Changing the path is
a real alternative to shaving coefficients down to fit the cap.

Full result: vault docs/buoy-hydro-measurement-2026-07-29.md, appendix B. Rig and raw data at
tools/buoy_hydro/. [SOURCE: buoy-probe-design-20260729] [CONFIDENCE: HIGH]

---

## Update (2026-07-29T11:47:19.746521)

[BATCHED 2026-07-29, user decision] This item is NO LONGER an independently actionable guard decision. It is candidate 1 of four in plant_change_batch_v2_four_isaac_plant_corrections_are_now_pendi, all of which force a teacher retrain and are therefore decided as a unit behind one sizing gate. Do not act on this page alone; read the batch page first. [CONFIDENCE: HIGH -- user decision]

THREE ISAAC-SIDE VERIFICATIONS OF THIS PAGE, done 2026-07-29 against source.
1. The dimensional bug is CONFIRMED by unit analysis and its scope is WIDER than this page states. m1 = rho*pi*r*r evaluates to 22.65 with units kg/m used as kg; the missing length factor inflates the axial term by exactly 1/L = 8.47x here. Because ComputeCylindricalApprox is a generic SolidEntity method, this affects EVERY cylinder solid in Stonefish, not only this buoy -- it is an upstream engine bug worth reporting, not a scenario-file quirk.
2. The damping-anisotropy criticism of Isaac is CORRECT and is now tracked as its own batch candidate. Frontal areas computed from the deployed geometry: axial disc pi*r*r = 0.02270 m2 against broadside 2*r*h = 0.02006 m2, so axial exceeds broadside by 1.13x and axial drag should dominate. Isaac quadratic_damping (10, 10, 8) has the ordering inverted; the Stonefish rig measurement 6.670 broadside against 13.917 axial agrees with geometry. Unlike the added-mass item this hits no guard.
3. The mass-matrix argument stands, but NOT on the number it was argued with. Moving added mass onto the left-hand side is unconditionally stable where an explicit forward-Euler external wrench is not, and that is exactly why the 0.95 cap exists -- the architectural case is sound. However the supporting claim that Stonefish stably runs M_a/m about 10 leans on the very axial term this page shows is 8.47x inflated. At the GEOMETRIC target (2.0 broadside, 1.6 axial on a 0.93 kg body) the ratio is about 2.2 and 1.8, still above the Isaac cap but an order of magnitude below 10. Argue the path, not the ratio.

TITLE-BODY DRIFT, flagged not fixed. The title still carries the retired coefficient comparison (3.8-8.2x low, 3.5-5.7x high) while the 10:13 update replaced it with a total-effective-inertia table (2.4-2.5x low, 3.5-4.0x high). Both are internally correct -- they compare different quantities -- but the backlog and query results render the TITLE, so a later session reading only the listing will pick up the retired framing. Retitling requires a gc round, so it is recorded here rather than patched.

---

## Update (2026-08-04T16:24:13.137955)

## VERDICT 2026-08-05 -- RESOLVED, and NOT the way this program expected (backlog-closeout)

Measured rather than argued. Three points of effective buoy added mass were evaluated on the
E-int teacher (model_4999.pt) against its own baseline eval static_260804_203719, same GPU,
same branch, same DORAEMON anchor. Pairing verified: 24/24 dr+fault keys elementwise identical
at all four DR levels, so the paired decision floors legitimately apply.

The geometric target cannot be set directly. hydrodynamics.py:215 raises at construction when
added_mass / body_mass >= 1.0 and the buoy's body mass is 0.93 kg, while events.py:273 silently
clamps the DR-scaled coefficient at 0.95 * body_mass on EVERY reset -- including at the none DR
level, so a naive coefficient raise would have been a silent no-op. The applied wrench is
M_a * acc * added_mass_stability_factor (hydrodynamics.py:361) and the factor carries no guard,
so the target was reached by splitting it between coefficient and factor. Rotational terms were
held byte-equal throughout (effective 0.0008 at every point), so only translational added mass
moved. Each override was confirmed in the hydra-resolved config, not assumed.

| point | effective surge/sway | ratio to body mass | result |
|:--|:--|:--|:--|
| current | 0.28 kg | 0.30 | reference |
| x2 | 0.56 kg | 0.60 | ZERO REAL flags on any field, axis or DR level |
| ceiling | 0.88 kg | 0.95 | survival -18.75 to -31.25 pp, REAL at all four levels |
| geometric | 2.00 kg | 2.15 | 0/64 alive before step 1000; the run crashed on an all-NaN metric |

**This is a numerical stability cliff, not a control-sensitivity curve, and reading it the other
way would be the error.** The ceiling point also shows ss_error +0.19 to +0.35 deg and
ss_error_std +0.86 to +1.46 deg flagged REAL -- but those numbers come from a run in which a
fifth to a third of the environments died, so the surviving population is a biased subset and
the accuracy deltas are survivorship-contaminated. They must NOT be quoted as "the policy
degrades by 0.35 deg under corrected added mass". The primary result at that point is the
survival collapse, and its mechanism is the same one that kills every env at the geometric
value: explicit external-wrench integration of a force proportional to acceleration is
unconditionally unstable as the added mass approaches the body's own inertia. The death rate is
monotone in that ratio (0 percent at 0.60, 19-31 percent at 0.95, 100 percent at 2.15).

**Consequence: the correct geometric added mass is UNREACHABLE by any coefficient or factor
setting in the current formulation.** This lead offered three options -- raise the 0.95 cap,
drop or retune added_mass_stability_factor, or move added mass out of the explicit
external-wrench path into the mass matrix as Stonefish does. The first two are now measured to
be dead ends: they do not fail because the cap is too conservative, they fail because the
underlying integration scheme cannot carry the value. Option (c) is the only route, and it is a
**gen-2 engine item**, not a coefficient fix.

**What gen-1 ships with, stated precisely.** Within the numerically representable range the
policy is insensitive to buoy added mass -- zero REAL flags anywhere at 2x. That is why the
known model error is accepted for gen-1. But the honest form of that statement is "insensitive
across a range that does not reach the true value", which is weaker than "the error does not
matter". Nothing here measures behaviour at the real vehicle's added mass, because nothing can.
This belongs in the DGX handoff as a quantified, bounded sim-to-real gap rather than a resolved
one.

**Engine defect found while running this, recorded and deliberately NOT fixed.** The stability
guard validates the RAW coefficient (`ratio = added_mass[i] / gen_inertia[i]`,
hydrodynamics.py:215) while the applied wrench is coefficient * added_mass_stability_factor. So
the guard under-protects whenever the factor exceeds 1 and over-protects whenever it is below 1.
Concretely: the geometric configuration had a raw ratio of 0.54 and passed validation silently,
then destroyed the simulation; and with the shipped factor of 0.4 the guard is 2.5x conservative
on the buoy. The correct test is `added_mass[i] * added_mass_stability_factor / gen_inertia[i]`.
This is a one-line change and it is NOT being made now: altering a plant-engine guard during an
active experiment program is exactly what voids a baseline mid-campaign. Queued as a gen-2
engine item alongside option (c), which touches the same code.

