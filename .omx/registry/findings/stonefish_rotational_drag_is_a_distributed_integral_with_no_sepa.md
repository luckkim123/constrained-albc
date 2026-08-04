---
title: "Stonefish rotational drag is a distributed integral with no separate rotational term, so hull yaw pressure drag is exactly zero by construction -- the 45.5x yaw damping gap is an artifact and roll/pitch is corrupted by a force-derived torque correction"
tags: ["stonefish", "hydrodynamics", "damping", "yaw", "rotational-drag", "cylinder-approximation", "added-inertia", "hydro-recenter", "code-verify", "marinelab", "mesh-vs-primitive"]
created: 2026-07-30T03:08:04.356936
updated: 2026-08-04T15:35:29.082528
sources: ["stonefish-v1.3-source", "code-verify-20260730", "rotational-damping-verdict-20260730", "marinelab-reply-20260730"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "HydroRC-v2 must re-derive every 016d1b1 damping axis from geometry or literature; separately, declaring the hull as a mesh routes it to the correct ellipsoid path and is worth evaluating before any coefficient work"
---

# Stonefish rotational drag is a distributed integral with no separate rotational term, so hull yaw pressure drag is exactly zero by construction -- the 45.5x yaw damping gap is an artifact and roll/pitch is corrupted by a force-derived torque correction

ANSWER to the blocked-on clause of the 016d1b1 page: Stonefish derives rotational drag from a
distributed integral over the approximated geometry, with NO separate rotational term. So the hull
yaw number is structurally not a form-drag measurement -- it is not merely "near-zero", the hull's
yaw pressure drag is EXACTLY zero by construction. Hull yaw damping 0.15 -> 0.002 and 0.5 -> 0.011
are RETIRED. Roll/pitch are NOT salvageable either, for a separate reason given below.

VERSION DISCIPLINE FIRST. Installed is 1.3.0 (StonefishConfigVersion.cmake). GitHub master does NOT
match it -- master's CorrectHydrodynamicForces is 8-arg with no linear term, the installed header
SolidEntity.h:126 is 7-arg with _Fdl/_Tdl. Tag v1.3 matches the installed signature exactly. All
citations below are v1.3, cross-checked against installed headers and the deployed albc.scn.

(1) DISTRIBUTED INTEGRAL, NO ROTATIONAL TERM. ComputeHydrodynamicForcesSubmerged
(SolidEntity.cpp:1589-1673) loops over mesh->faces. omega enters at exactly one point:
vc = GetFluidVelocity(fc) - (v + cross(omega, fc-p)); vn = dot(vc,fn1)*fn1; vt = vc - vn;
linear = vn*expf(-0.5*|vn|^2)*A; quadratic = vn*|vn|*A; Tdq += cross(fc-p, quadratic). Torque is the
moment of the same per-face force. No rotational drag coefficient, no omega-quadratic term, no
separate rotational damping anywhere in the file.

(2) EXACTLY ZERO ON THE AXIS OF REVOLUTION. Pressure drag is built from vn ALONE (both terms). For a
body of revolution spinning about its own axis, side-wall facet normals are radial through the axis
while the velocity omega x r is azimuthal -- dot = 0 exactly; end-cap normals are axial against the
same azimuthal velocity -- also exactly 0. A regular prism's facet normals pass through the axis
exactly, so there is not even a tessellation residual. This is the mechanism behind the axis
signature already recorded on the 016d1b1 page, and it explains a detail that page had to leave as
an inference: yaw is the only axis where BOTH damping terms collapse because both are built from the
same vn. Roll/pitch are broadside tumble, so side-wall normals see genuine normal velocity and
pressure drag is real there. One mechanism, exactly one axis, both terms.

(3) THE RESIDUAL 0.011 CLOSES NUMERICALLY WITH HULL FORM DRAG SET TO ZERO. Two things survive in yaw.
Skin friction: vt goes to Fds, which CorrectHydrodynamicForces scales by 0.1*0.5*rho and does NOT
multiply by corFactor. Off-axis parts: Compound::ComputeHydrodynamicForces (Compound.cpp:337-342)
integrates per part under if(parts[i].isExternal), moments taken about the COMPOUND CG. base_link has
exactly two external parts -- Base (r=0.09, L=0.3105, coaxial) and Gripper (r=0.015, L=0.325, offset
y=-0.0881, axis parallel). The six thrusters are <actuator>, no physics mesh, zero contribution to
the drag integral. Reconstruction with the engine's own scaling:
  hull form drag      vn == 0                                             0.00000
  hull skin friction  0.1*0.5*rho*A_side*r^2*r,   A_side = 0.17558 m^2    0.00639
  Gripper cross-flow  0.5*0.5*rho*A_g*d^2*d, A_g = 0.00975, d = 0.0881    0.00166
                                                               SUM       0.00805
  measured 2026-07-27                                                     0.011
Within 1.37x, short by end-cap skin friction and tessellation residual, i.e. the expected direction.
Recentering an Isaac form-drag coefficient onto that number is the same category error as the
added-mass item: not a weak measurement of the right quantity, a measurement of a different quantity.

(4) TWO MORE DEFECTS, REACHING THE ROTATIONAL ADDED MASS THAT 016d1b1 LEFT ALONE. The decision to
leave it alone survives; the premises change. ComputeCylindricalApprox (SolidEntity.cpp:757-769):
  Scalar I1 = Scalar(0);
  Scalar I2 = (1/12)*M_PI*rho * L*L * pow(r,3);
  aI = T_CG2H.getBasis() * Vector3(I2, I2, I1);
(a) I1 IS HARDCODED ZERO -- added inertia about the cylinder axis is written as 0, not computed. So
Stonefish reports zero hull yaw added inertia by construction, and whatever the rig read on that axis
was rigid inertia alone; there is no quantity to compare an Isaac nominal against. Self-consistent
with (2). The compound value is nonzero, but Compound.cpp:204-217 builds it as rotated per-part
getAugmentedInertia PLUS a parallel-axis term using the part's AUGMENTED mass -- so it is entirely
off-axis parts' parallel-axis contribution multiplied by the isotropically-averaged, dimensionally
broken mass. The translational bug propagates into rotation through that door.
(b) I2 HAS L AND r EXPONENTS SWAPPED. Strip theory gives rho*pi*r^2*L^3/12 (a slice dz carries added
mass rho*pi*r^2*dz contributing z^2*rho*pi*r^2*dz); the source computes rho*pi*L^2*r^3/12. Both are
kg*m^2, which is presumably why this survived where m1 did not. Ratio SF/physics = r/L: hull 0.290
(3.45x LOW), buoy 0.720 (1.39x low). The diagnostic that settles it -- the formula diverges from truth
as the body gets MORE slender, i.e. exactly where strip theory becomes exact. An approximation cannot
get worse in the limit where its own basis gets better.

(5) THE TORQUE CORRECTION FACTOR IS DERIVED FROM THE FORCE DIRECTION. CorrectHydrodynamicForces
(SolidEntity.cpp:1218-1253): Fdqn = (T_CG2H.getBasis().inverse() * _Fdq).safeNormalize() is the
normalized FORCE; corFactor = Cd.dot(Fdqn) with Cd(0.5,0.5,1.0); then _Tdq *= fabs(corFactor)*0.5*rho.
The scalar correcting the torque carries no rotational information. For a symmetric body in near-pure
rotation _Fdq -> 0, at which point Bullet safeNormalize (btVector3.h:286-299, read from the installed
header) returns setValue(1,0,0) on a sub-epsilon vector, so corFactor silently becomes Cd.x = 0.5.
In mixed motion it tracks whatever direction the translational drag force happened to point that step.
Bounded in [0.5,1.0] so at most 2x in magnitude, but it means the roll/pitch quadratic "rises 20
percent" observation is a distributed integral times a scalar keyed off translation. Not information.

(6) NET -- FOUR DEFECTS IN TWO FUNCTIONS, and every damping or added-mass number on 016d1b1 traces to
one of them: m1 = rho*pi*r^2 missing the length factor (13.1x hull / 13.9x buoy above disc geometry,
then isotropically averaged into all three translational axes); Cd(0.5,0.5,1.0) hardcoded regardless
of L/D (2.34x below analytical Cd_cross); pressure drag exactly zero about any axis of revolution plus
I1 = 0; I2 exponents swapped and corFactor derived from force applied to torque. The last two are new
on 2026-07-30. HydroRC-v2 is not 016d1b1 minus one line, and not minus two either.

ATTRIBUTION CORRECTION to the translational residual on the 016d1b1 page, magnitude unchanged. That
page assigns the 2.08x residual to "appendage, thruster and gripper drag a single-cylinder
approximation omits". The Gripper is NOT omitted -- it is an external part with its own face integral
and its own Cd correction. What IS omitted is all six thrusters (<actuator>, no physics mesh), plus
cables and frame. The 2.34x / 4.88x / 2.08x arithmetic stands; only the attribution moves.

WHAT SURVIVES from the 2026-07-27 measurement, unqualified: pitch linear damping ~10x short, and
volume 7901.3 cm^3 against cfg 0.00790 m^3. That is what is left of nine numbers.

OPERATING RULE, generalised from the added-mass item and now confirmed across the whole commit: the
Stonefish rig is a DETECTOR of the other simulator's errors (ordering, sign, order of magnitude) and
never a SOURCE of its values.

Full result: vault docs/stonefish-rotational-damping-verdict-2026-07-30.md.
[SOURCE: rotational-damping-verdict-20260730] [CONFIDENCE: HIGH]

---

## Update (2026-07-30T03:11:23.475047)

ANSWER to the blocked-on clause of the 016d1b1 page: Stonefish derives rotational drag from a
distributed integral over the approximated geometry, with NO separate rotational term. So the hull
yaw number is structurally not a form-drag measurement -- it is not merely "near-zero", the hull's
yaw pressure drag is EXACTLY zero by construction. Hull yaw damping 0.15 -> 0.002 and 0.5 -> 0.011
are RETIRED. Roll/pitch are NOT salvageable either, for a separate reason given below.

VERSION DISCIPLINE FIRST. Installed is 1.3.0 (StonefishConfigVersion.cmake). GitHub master does NOT
match it -- master's CorrectHydrodynamicForces is 8-arg with no linear term, the installed header
SolidEntity.h:126 is 7-arg with _Fdl/_Tdl. Tag v1.3 matches the installed signature exactly. All
citations below are v1.3, cross-checked against installed headers and the deployed albc.scn.

(1) DISTRIBUTED INTEGRAL, NO ROTATIONAL TERM. ComputeHydrodynamicForcesSubmerged
(SolidEntity.cpp:1589-1673) loops over mesh->faces. omega enters at exactly one point:
vc = GetFluidVelocity(fc) - (v + cross(omega, fc-p)); vn = dot(vc,fn1)*fn1; vt = vc - vn;
linear = vn*expf(-0.5*|vn|^2)*A; quadratic = vn*|vn|*A; Tdq += cross(fc-p, quadratic). Torque is the
moment of the same per-face force. No rotational drag coefficient, no omega-quadratic term, no
separate rotational damping anywhere in the file.

(2) EXACTLY ZERO ON THE AXIS OF REVOLUTION. Pressure drag is built from vn ALONE (both terms). For a
body of revolution spinning about its own axis, side-wall facet normals are radial through the axis
while the velocity omega x r is azimuthal -- dot = 0 exactly; end-cap normals are axial against the
same azimuthal velocity -- also exactly 0. A regular prism's facet normals pass through the axis
exactly, so there is not even a tessellation residual. This is the mechanism behind the axis
signature already recorded on the 016d1b1 page, and it explains a detail that page had to leave as
an inference: yaw is the only axis where BOTH damping terms collapse because both are built from the
same vn. Roll/pitch are broadside tumble, so side-wall normals see genuine normal velocity and
pressure drag is real there. One mechanism, exactly one axis, both terms.

(3) THE RESIDUAL 0.011 CLOSES NUMERICALLY WITH HULL FORM DRAG SET TO ZERO. Two things survive in yaw.
Skin friction: vt goes to Fds, which CorrectHydrodynamicForces scales by 0.1*0.5*rho and does NOT
multiply by corFactor. Off-axis parts: Compound::ComputeHydrodynamicForces (Compound.cpp:337-342)
integrates per part under if(parts[i].isExternal), moments taken about the COMPOUND CG. base_link has
exactly two external parts -- Base (r=0.09, L=0.3105, coaxial) and Gripper (r=0.015, L=0.325, offset
y=-0.0881, axis parallel). The six thrusters are <actuator>, no physics mesh, zero contribution to
the drag integral. Reconstruction with the engine's own scaling:
  hull form drag        vn == 0                                              0.00000
  hull side skin        0.05*rho*A_side*r^3,  A_side = 2*pi*r*L = 0.17558    0.00639
  hull end-cap skin     0.05*rho*(4*pi*r^5/5), both caps                     0.00074
  Gripper cross-flow    0.5*0.5*rho*(2/3)*A_g*d^3, A_g = 2rL, d = 0.0881     0.00111
                                                                 SUM        0.00824
  measured 2026-07-27, range over runs                             0.0094 - 0.0116
Within 1.14-1.41x. The 2/3 on the Gripper term is the engine's own face-integral for a cylinder in
uniform flow -- the loop applies vn|vn|A only on the windward half, so integral cos^3 yields two
thirds of the frontal area (using frontal area directly overstates by 1.5x). The residual shortfall
is the Gripper's own skin friction plus the fit width. The point is not the ratio: the measurement
reconstructs with hull form drag set to EXACTLY ZERO. Recentering an Isaac form-drag coefficient onto
that number is the same category error as the added-mass item: not a weak measurement of the right
quantity, a measurement of a different quantity.

(4) TWO MORE DEFECTS, REACHING THE ROTATIONAL ADDED MASS THAT 016d1b1 LEFT ALONE. The decision to
leave it alone survives; the premises change. ComputeCylindricalApprox (SolidEntity.cpp:757-769):
  Scalar I1 = Scalar(0);
  Scalar I2 = (1/12)*M_PI*rho * L*L * pow(r,3);
  aI = T_CG2H.getBasis() * Vector3(I2, I2, I1);
(a) I1 IS HARDCODED ZERO -- added inertia about the cylinder axis is written as 0, not computed. So
Stonefish reports zero hull yaw added inertia by construction, and whatever the rig read on that axis
was rigid inertia alone; there is no quantity to compare an Isaac nominal against. Self-consistent
with (2). The compound value is nonzero, but Compound.cpp:204-217 builds it as rotated per-part
getAugmentedInertia PLUS a parallel-axis term using the part's AUGMENTED mass -- so it is entirely
off-axis parts' parallel-axis contribution multiplied by the isotropically-averaged, dimensionally
broken mass. The translational bug propagates into rotation through that door.
(b) I2 HAS L AND r EXPONENTS SWAPPED. Strip theory gives rho*pi*r^2*L^3/12 (a slice dz carries added
mass rho*pi*r^2*dz contributing z^2*rho*pi*r^2*dz); the source computes rho*pi*L^2*r^3/12. Both are
kg*m^2, which is presumably why this survived where m1 did not. Ratio SF/physics = r/L: hull 0.290
(3.45x LOW), buoy 0.720 (1.39x low). The diagnostic that settles it -- the formula diverges from truth
as the body gets MORE slender, i.e. exactly where strip theory becomes exact. An approximation cannot
get worse in the limit where its own basis gets better.

(5) THE TORQUE CORRECTION FACTOR IS DERIVED FROM THE FORCE DIRECTION. CorrectHydrodynamicForces
(SolidEntity.cpp:1218-1253): Fdqn = (T_CG2H.getBasis().inverse() * _Fdq).safeNormalize() is the
normalized FORCE; corFactor = Cd.dot(Fdqn) with Cd(0.5,0.5,1.0); then _Tdq *= fabs(corFactor)*0.5*rho.
The scalar correcting the torque carries no rotational information. For a symmetric body in near-pure
rotation _Fdq -> 0, at which point Bullet safeNormalize (btVector3.h:286-299, read from the installed
header) returns setValue(1,0,0) on a sub-epsilon vector, so corFactor silently becomes Cd.x = 0.5.
In mixed motion it tracks whatever direction the translational drag force happened to point that step.
Bounded in [0.5,1.0] so at most 2x in magnitude, but it means the roll/pitch quadratic "rises 20
percent" observation is a distributed integral times a scalar keyed off translation. Not information.

(6) NET -- FOUR DEFECTS IN TWO FUNCTIONS, and every damping or added-mass number on 016d1b1 traces to
one of them: m1 = rho*pi*r^2 missing the length factor (13.1x hull / 13.9x buoy above disc geometry,
then isotropically averaged into all three translational axes); Cd(0.5,0.5,1.0) hardcoded regardless
of L/D (2.34x below analytical Cd_cross); pressure drag exactly zero about any axis of revolution plus
I1 = 0; I2 exponents swapped and corFactor derived from force applied to torque. The last two are new
on 2026-07-30. HydroRC-v2 is not 016d1b1 minus one line, and not minus two either.

ATTRIBUTION CORRECTION to the translational residual on the 016d1b1 page, magnitude unchanged. That
page assigns the 2.08x residual to "appendage, thruster and gripper drag a single-cylinder
approximation omits". The Gripper is NOT omitted -- it is an external part with its own face integral
and its own Cd correction. What IS omitted is all six thrusters (<actuator>, no physics mesh), plus
cables and frame. The 2.34x / 4.88x / 2.08x arithmetic stands; only the attribution moves.

WHAT SURVIVES from the 2026-07-27 measurement, unqualified: pitch linear damping ~10x short, and
volume 7901.3 cm^3 against cfg 0.00790 m^3. That is what is left of nine numbers.

OPERATING RULE, generalised from the added-mass item and now confirmed across the whole commit: the
Stonefish rig is a DETECTOR of the other simulator's errors (ordering, sign, order of magnitude) and
never a SOURCE of its values.

Full result: vault docs/stonefish-rotational-damping-verdict-2026-07-30.md.
[SOURCE: rotational-damping-verdict-20260730] [CONFIDENCE: HIGH]

---

## Update (2026-07-30T03:25:10.976134)

ANSWER to the blocked-on clause of the 016d1b1 page: Stonefish derives rotational drag from a
distributed integral over the approximated geometry, with NO separate rotational term. So the hull
yaw number is structurally not a form-drag measurement -- it is not merely "near-zero", the hull's
yaw pressure drag is EXACTLY zero by construction. Hull yaw damping 0.15 -> 0.002 and 0.5 -> 0.011
are RETIRED. Roll/pitch are NOT salvageable either, for a separate reason given below.

VERSION DISCIPLINE FIRST. Installed is 1.3.0 (StonefishConfigVersion.cmake). GitHub master does NOT
match it -- master's CorrectHydrodynamicForces is 8-arg with no linear term, the installed header
SolidEntity.h:126 is 7-arg with _Fdl/_Tdl. Tag v1.3 matches the installed signature exactly. All
citations below are v1.3, cross-checked against installed headers and the deployed albc.scn.

(1) DISTRIBUTED INTEGRAL, NO ROTATIONAL TERM. ComputeHydrodynamicForcesSubmerged
(SolidEntity.cpp:1589-1673) loops over mesh->faces. omega enters at exactly one point:
vc = GetFluidVelocity(fc) - (v + cross(omega, fc-p)); vn = dot(vc,fn1)*fn1; vt = vc - vn;
linear = vn*expf(-0.5*|vn|^2)*A; quadratic = vn*|vn|*A; Tdq += cross(fc-p, quadratic). Torque is the
moment of the same per-face force. No rotational drag coefficient, no omega-quadratic term, no
separate rotational damping anywhere in the file.

(2) EXACTLY ZERO ON THE AXIS OF REVOLUTION. Pressure drag is built from vn ALONE (both terms). For a
body of revolution spinning about its own axis, side-wall facet normals are radial through the axis
while the velocity omega x r is azimuthal -- dot = 0 exactly; end-cap normals are axial against the
same azimuthal velocity -- also exactly 0. TESSELLATION RESIDUAL, stated precisely because "it is a
polygon, not a circle" is the obvious objection: the physics mesh is a regular 32-gon prism
(Cylinder.cpp:68, slices = max(ceil(2*pi*r/0.1), 32); the hull hits the floor at 32). At the QUAD
level the cancellation is exact -- facet normal along the bisector, chord midpoint on the same line.
It breaks at the TRIANGLE level: each quad splits into two triangles whose centroids sit
R*sin(pi/N)/3 off the bisector (2.95 mm at N=32 against an 89.9 mm apothem), the engine evaluates
velocity at the triangle centroid, and the pair does NOT cancel because the inflow gate
dot(fn1,vn) < -1e-12 admits only the windward one. The spurious drag scales as sin^4(pi/N):
3.99e-05 at N=8, 4.60e-06 at N=16, 5.63e-07 at N=32 (deployed), 7.01e-08 at N=64 -- i.e. 8.8e-05 of
hull skin friction and 5.1e-05 of the measured 0.011. End caps are exactly zero regardless of the
fan (axial normals). So: zero at the geometric level, triangulation residual four orders below the
terms that matter. The number cannot be rehabilitated by refining the mesh -- the error is a
MODELLING error (bare cylinder standing in for a hull carrying six thrusters, cables and frame), not
a discretisation one. This is the mechanism behind the axis
signature already recorded on the 016d1b1 page, and it explains a detail that page had to leave as
an inference: yaw is the only axis where BOTH damping terms collapse because both are built from the
same vn. Roll/pitch are broadside tumble, so side-wall normals see genuine normal velocity and
pressure drag is real there. One mechanism, exactly one axis, both terms.

(3) THE RESIDUAL 0.011 CLOSES NUMERICALLY WITH HULL FORM DRAG SET TO ZERO. Two things survive in yaw.
Skin friction: vt goes to Fds, which CorrectHydrodynamicForces scales by 0.1*0.5*rho and does NOT
multiply by corFactor. Off-axis parts: Compound::ComputeHydrodynamicForces (Compound.cpp:337-342)
integrates per part under if(parts[i].isExternal), moments taken about the COMPOUND CG. base_link has
exactly two external parts -- Base (r=0.09, L=0.3105, coaxial) and Gripper (r=0.015, L=0.325, offset
y=-0.0881, axis parallel). The six thrusters are <actuator>, no physics mesh, zero contribution to
the drag integral. Reconstruction with the engine's own scaling:
  hull form drag        vn == 0                                              0.00000
  hull side skin        0.05*rho*A_side*r^3,  A_side = 2*pi*r*L = 0.17558    0.00639
  hull end-cap skin     0.05*rho*(4*pi*r^5/5), both caps                     0.00074
  Gripper cross-flow    0.5*0.5*rho*(2/3)*A_g*d^3, A_g = 2rL, d = 0.0881     0.00111
                                                                 SUM        0.00824
  measured 2026-07-27, range over runs                             0.0094 - 0.0116
Within 1.14-1.41x. The 2/3 on the Gripper term is the engine's own face-integral for a cylinder in
uniform flow -- the loop applies vn|vn|A only on the windward half, so integral cos^3 yields two
thirds of the frontal area (using frontal area directly overstates by 1.5x). The residual shortfall
is the Gripper's own skin friction plus the fit width. The point is not the ratio: the measurement
reconstructs with hull form drag set to EXACTLY ZERO. Recentering an Isaac form-drag coefficient onto
that number is the same category error as the added-mass item: not a weak measurement of the right
quantity, a measurement of a different quantity.

(4) TWO MORE DEFECTS, REACHING THE ROTATIONAL ADDED MASS THAT 016d1b1 LEFT ALONE. The decision to
leave it alone survives; the premises change. ComputeCylindricalApprox (SolidEntity.cpp:757-769):
  Scalar I1 = Scalar(0);
  Scalar I2 = (1/12)*M_PI*rho * L*L * pow(r,3);
  aI = T_CG2H.getBasis() * Vector3(I2, I2, I1);
(a) I1 IS HARDCODED ZERO -- added inertia about the cylinder axis is written as 0, not computed. So
Stonefish reports zero hull yaw added inertia by construction, and whatever the rig read on that axis
was rigid inertia alone; there is no quantity to compare an Isaac nominal against. Self-consistent
with (2). The compound value is nonzero, but Compound.cpp:204-217 builds it as rotated per-part
getAugmentedInertia PLUS a parallel-axis term using the part's AUGMENTED mass -- so it is entirely
off-axis parts' parallel-axis contribution multiplied by the isotropically-averaged, dimensionally
broken mass. The translational bug propagates into rotation through that door.
(b) I2 HAS L AND r EXPONENTS SWAPPED. Strip theory gives rho*pi*r^2*L^3/12 (a slice dz carries added
mass rho*pi*r^2*dz contributing z^2*rho*pi*r^2*dz); the source computes rho*pi*L^2*r^3/12. Both are
kg*m^2, which is presumably why this survived where m1 did not. Ratio SF/physics = r/L: hull 0.290
(3.45x LOW), buoy 0.720 (1.39x low). The diagnostic that settles it -- the formula diverges from truth
as the body gets MORE slender, i.e. exactly where strip theory becomes exact. An approximation cannot
get worse in the limit where its own basis gets better.

(5) THE TORQUE CORRECTION FACTOR IS DERIVED FROM THE FORCE DIRECTION. CorrectHydrodynamicForces
(SolidEntity.cpp:1218-1253): Fdqn = (T_CG2H.getBasis().inverse() * _Fdq).safeNormalize() is the
normalized FORCE; corFactor = Cd.dot(Fdqn) with Cd(0.5,0.5,1.0); then _Tdq *= fabs(corFactor)*0.5*rho.
The scalar correcting the torque carries no rotational information. For a symmetric body in near-pure
rotation _Fdq -> 0, at which point Bullet safeNormalize (btVector3.h:286-299, read from the installed
header) returns setValue(1,0,0) on a sub-epsilon vector, so corFactor silently becomes Cd.x = 0.5.
In mixed motion it tracks whatever direction the translational drag force happened to point that step.
Bounded in [0.5,1.0] so at most 2x in magnitude, but it means the roll/pitch quadratic "rises 20
percent" observation is a distributed integral times a scalar keyed off translation. Not information.

(6) NET -- FOUR DEFECTS IN TWO FUNCTIONS, and every damping or added-mass number on 016d1b1 traces to
one of them: m1 = rho*pi*r^2 missing the length factor (13.1x hull / 13.9x buoy above disc geometry,
then isotropically averaged into all three translational axes); Cd(0.5,0.5,1.0) hardcoded regardless
of L/D (2.34x below analytical Cd_cross); pressure drag exactly zero about any axis of revolution plus
I1 = 0; I2 exponents swapped and corFactor derived from force applied to torque. The last two are new
on 2026-07-30. HydroRC-v2 is not 016d1b1 minus one line, and not minus two either.

ATTRIBUTION CORRECTION to the translational residual on the 016d1b1 page, magnitude unchanged. That
page assigns the 2.08x residual to "appendage, thruster and gripper drag a single-cylinder
approximation omits". The Gripper is NOT omitted -- it is an external part with its own face integral
and its own Cd correction. What IS omitted is all six thrusters (<actuator>, no physics mesh), plus
cables and frame. The 2.34x / 4.88x / 2.08x arithmetic stands; only the attribution moves.

WHAT SURVIVES from the 2026-07-27 measurement, unqualified: pitch linear damping ~10x short, and
volume 7901.3 cm^3 against cfg 0.00790 m^3. That is what is left of nine numbers.

OPERATING RULE, generalised from the added-mass item and now confirmed across the whole commit: the
Stonefish rig is a DETECTOR of the other simulator's errors (ordering, sign, order of magnitude) and
never a SOURCE of its values.

Full result: vault docs/stonefish-rotational-damping-verdict-2026-07-30.md.
[SOURCE: rotational-damping-verdict-20260730] [CONFIDENCE: HIGH]

---

## Update (2026-07-30T03:31:36.659471)

ANSWER to the blocked-on clause of the 016d1b1 page: Stonefish derives rotational drag from a
distributed integral over the approximated geometry, with NO separate rotational term. So the hull
yaw number is structurally not a form-drag measurement -- it is not merely "near-zero", the hull's
yaw pressure drag is EXACTLY zero by construction. Hull yaw damping 0.15 -> 0.002 and 0.5 -> 0.011
are RETIRED. Roll/pitch are NOT salvageable either, for a separate reason given below.

VERSION DISCIPLINE FIRST. Installed is 1.3.0 (StonefishConfigVersion.cmake). GitHub master does NOT
match it -- master's CorrectHydrodynamicForces is 8-arg with no linear term, the installed header
SolidEntity.h:126 is 7-arg with _Fdl/_Tdl. Tag v1.3 matches the installed signature exactly. All
citations below are v1.3, cross-checked against installed headers and the deployed albc.scn.

(1) DISTRIBUTED INTEGRAL, NO ROTATIONAL TERM. ComputeHydrodynamicForcesSubmerged
(SolidEntity.cpp:1589-1673) loops over mesh->faces. omega enters at exactly one point:
vc = GetFluidVelocity(fc) - (v + cross(omega, fc-p)); vn = dot(vc,fn1)*fn1; vt = vc - vn;
linear = vn*expf(-0.5*|vn|^2)*A; quadratic = vn*|vn|*A; Tdq += cross(fc-p, quadratic). Torque is the
moment of the same per-face force. No rotational drag coefficient, no omega-quadratic term, no
separate rotational damping anywhere in the file.

(2) EXACTLY ZERO ON THE AXIS OF REVOLUTION. Pressure drag is built from vn ALONE (both terms). For a
body of revolution spinning about its own axis, side-wall facet normals are radial through the axis
while the velocity omega x r is azimuthal -- dot = 0 exactly; end-cap normals are axial against the
same azimuthal velocity -- also exactly 0. TESSELLATION RESIDUAL, stated precisely because "it is a
polygon, not a circle" is the obvious objection: the physics mesh is a regular 32-gon prism
(Cylinder.cpp:68, slices = max(ceil(2*pi*r/0.1), 32); the hull hits the floor at 32). At the QUAD
level the cancellation is exact -- facet normal along the bisector, chord midpoint on the same line.
It breaks at the TRIANGLE level: each quad splits into two triangles whose centroids sit
R*sin(pi/N)/3 off the bisector (2.95 mm at N=32 against an 89.9 mm apothem), the engine evaluates
velocity at the triangle centroid, and the pair does NOT cancel because the inflow gate
dot(fn1,vn) < -1e-12 admits only the windward one. The spurious drag scales as sin^4(pi/N):
3.99e-05 at N=8, 4.60e-06 at N=16, 5.63e-07 at N=32 (deployed), 7.01e-08 at N=64 -- i.e. 8.8e-05 of
hull skin friction and 5.1e-05 of the measured 0.011. End caps are exactly zero regardless of the
fan (axial normals). So: zero at the geometric level, triangulation residual four orders below the
terms that matter. The number cannot be rehabilitated by refining the mesh -- the error is a
MODELLING error (bare cylinder standing in for a hull carrying six thrusters, cables and frame), not
a discretisation one. This is the mechanism behind the axis
signature already recorded on the 016d1b1 page, and it explains a detail that page had to leave as
an inference: yaw is the only axis where BOTH damping terms collapse because both are built from the
same vn. Roll/pitch are broadside tumble, so side-wall normals see genuine normal velocity and
pressure drag is real there. One mechanism, exactly one axis, both terms.

(3) THE RESIDUAL 0.011 CLOSES NUMERICALLY WITH HULL FORM DRAG SET TO ZERO. Two things survive in yaw.
Skin friction: vt goes to Fds, which CorrectHydrodynamicForces scales by 0.1*0.5*rho and does NOT
multiply by corFactor. Off-axis parts: Compound::ComputeHydrodynamicForces (Compound.cpp:337-342)
integrates per part under if(parts[i].isExternal), moments taken about the COMPOUND CG. base_link has
exactly two external parts -- Base (r=0.09, L=0.3105, coaxial) and Gripper (r=0.015, L=0.325, offset
y=-0.0881, axis parallel). The six thrusters are <actuator>, no physics mesh, zero contribution to
the drag integral. Reconstruction with the engine's own scaling:
  hull form drag        vn == 0                                              0.00000
  hull side skin        0.05*rho*A_side*r^3,  A_side = 2*pi*r*L = 0.17558    0.00639
  hull end-cap skin     0.05*rho*(4*pi*r^5/5), both caps                     0.00074
  Gripper cross-flow    0.5*0.5*rho*(2/3)*A_g*d^3, A_g = 2rL, d = 0.0881     0.00111
                                                                 SUM        0.00824
  measured 2026-07-27, range over runs                             0.0094 - 0.0116
Within 1.14-1.41x. The 2/3 on the Gripper term is the engine's own face-integral for a cylinder in
uniform flow -- the loop applies vn|vn|A only on the windward half, so integral cos^3 yields two
thirds of the frontal area (using frontal area directly overstates by 1.5x). The residual shortfall
is the Gripper's own skin friction plus the fit width. The point is not the ratio: the measurement
reconstructs with hull form drag set to EXACTLY ZERO. Recentering an Isaac form-drag coefficient onto
that number is the same category error as the added-mass item: not a weak measurement of the right
quantity, a measurement of a different quantity.

(4) TWO MORE DEFECTS, REACHING THE ROTATIONAL ADDED MASS THAT 016d1b1 LEFT ALONE. The decision to
leave it alone survives; the premises change. ComputeCylindricalApprox (SolidEntity.cpp:757-769):
  Scalar I1 = Scalar(0);
  Scalar I2 = (1/12)*M_PI*rho * L*L * pow(r,3);
  aI = T_CG2H.getBasis() * Vector3(I2, I2, I1);
(a) I1 IS HARDCODED ZERO -- added inertia about the cylinder axis is written as 0, not computed. So
Stonefish reports zero hull yaw added inertia by construction, and whatever the rig read on that axis
was rigid inertia alone; there is no quantity to compare an Isaac nominal against. Self-consistent
with (2). The compound value is nonzero, but Compound.cpp:204-217 builds it as rotated per-part
getAugmentedInertia PLUS a parallel-axis term using the part's AUGMENTED mass -- so it is entirely
off-axis parts' parallel-axis contribution multiplied by the isotropically-averaged, dimensionally
broken mass. The translational bug propagates into rotation through that door.
(b) I2 HAS L AND r EXPONENTS SWAPPED. Strip theory gives rho*pi*r^2*L^3/12 (a slice dz carries added
mass rho*pi*r^2*dz contributing z^2*rho*pi*r^2*dz); the source computes rho*pi*L^2*r^3/12. Both are
kg*m^2, which is presumably why this survived where m1 did not. Ratio SF/physics = r/L: hull 0.290
(3.45x LOW), buoy 0.720 (1.39x low). The diagnostic that settles it -- the formula diverges from truth
as the body gets MORE slender, i.e. exactly where strip theory becomes exact. An approximation cannot
get worse in the limit where its own basis gets better.

(5) THE TORQUE CORRECTION FACTOR IS DERIVED FROM THE FORCE DIRECTION. CorrectHydrodynamicForces
(SolidEntity.cpp:1218-1253): Fdqn = (T_CG2H.getBasis().inverse() * _Fdq).safeNormalize() is the
normalized FORCE; corFactor = Cd.dot(Fdqn) with Cd(0.5,0.5,1.0); then _Tdq *= fabs(corFactor)*0.5*rho.
The scalar correcting the torque carries no rotational information. For a symmetric body in near-pure
rotation _Fdq -> 0, at which point Bullet safeNormalize (btVector3.h:286-299, read from the installed
header) returns setValue(1,0,0) on a sub-epsilon vector, so corFactor silently becomes Cd.x = 0.5.
In mixed motion it tracks whatever direction the translational drag force happened to point that step.
Bounded in [0.5,1.0] so at most 2x in magnitude, but it means the roll/pitch quadratic "rises 20
percent" observation is a distributed integral times a scalar keyed off translation. Not information.

(6) NET -- FOUR DEFECTS IN TWO FUNCTIONS, and every damping or added-mass number on 016d1b1 traces to
one of them: m1 = rho*pi*r^2 missing the length factor (13.1x hull / 13.9x buoy above disc geometry,
then isotropically averaged into all three translational axes); Cd(0.5,0.5,1.0) hardcoded regardless
of L/D (2.34x below analytical Cd_cross); pressure drag exactly zero about any axis of revolution plus
I1 = 0; I2 exponents swapped and corFactor derived from force applied to torque. The last two are new
on 2026-07-30. HydroRC-v2 is not 016d1b1 minus one line, and not minus two either.

ATTRIBUTION CORRECTION to the translational residual on the 016d1b1 page, magnitude unchanged. That
page assigns the 2.08x residual to "appendage, thruster and gripper drag a single-cylinder
approximation omits". The Gripper is NOT omitted -- it is an external part with its own face integral
and its own Cd correction. What IS omitted is all six thrusters (<actuator>, no physics mesh), plus
cables and frame. The 2.34x / 4.88x / 2.08x arithmetic stands; only the attribution moves.

WHAT SURVIVES from the 2026-07-27 measurement, unqualified: pitch linear damping ~10x short, and
volume 7901.3 cm^3 against cfg 0.00790 m^3. That is what is left of nine numbers.

OPERATING RULE, generalised from the added-mass item and now confirmed across the whole commit: the
Stonefish rig is a DETECTOR of the other simulator's errors (ordering, sign, order of magnitude) and
never a SOURCE of its values.

(7) THERE IS AN ESCAPE ROUTE, and it changes what "re-derive from geometry or literature" should mean.
All four defects live in ComputeCylindricalApprox(), which is invoked ONLY for type="cylinder"
primitives (Cylinder.cpp:71). The neighbouring ComputeEllipsoidalApprox() is dimensionally CORRECT --
SolidEntity.cpp:973-977 uses Lamb's k-factor, aMass = (4/3)*pi*rho*a*b^2 in kg, and a transverse
aI with the right exponent structure rho*r^2*L^3. Comparing the two aI lines settles the exponent-swap
diagnosis as a mechanism rather than an inference: they are the SAME expression p1^2 * p0^3, but
ellipsoid stores params = (semi-major, semi-minor, semi-minor) while cylinder stores
params = (radius, length). The formula was copied without swapping for the different convention.
Note also aI.setX(0) carries the upstream author's own comment "//THIS SHOULD BE > 0".

CONSEQUENCE: declaring the hull as a MESH (Polyhedron) instead of a primitive routes it through
approx = AUTO (Polyhedron.h:55,70 default arg) -> ComputeEllipsoidalApprox, which gives (a) Lamb
added mass, (b) Cd derived from the semi-axes instead of the hardcoded (0.5,0.5,1.0), (c) a correct
transverse added-inertia exponent, and (d) a drag integral over real geometry, so modelled thrusters
and appendages generate genuine yaw drag. CAVEAT: ScenarioParser.cpp contains ZERO references to
GeometryApproxType or approx, so the approximation cannot be selected from the .scn -- choosing a
primitive silently locks the broken path, and the only lever is how the geometry is declared.

TWO THINGS REMAIN IMPOSSIBLE EITHER WAY. Axial rotational added inertia is 0 in BOTH branches
(acknowledged upstream), so yaw added inertia is unavailable by any route. And yaw form drag on a
near-axisymmetric hull is physics, not a bug -- a smooth body of revolution genuinely has almost none;
obtaining it requires modelling the appendages as geometry, which is an asset task, not a config one.

Full result: vault docs/stonefish-rotational-damping-verdict-2026-07-30.md.
[SOURCE: rotational-damping-verdict-20260730] [CONFIDENCE: HIGH]

---

## Update (2026-08-04T15:35:29.082528)

## VERDICT 2026-08-05 -- CLOSED-OUT-OF-SCOPE (backlog-closeout program)

This page's content is a finding about how Stonefish computes rotational drag (a distributed
integral with no separate rotational term, making hull yaw pressure drag exactly zero by
construction). It was actionable only as an input to Stonefish-side alignment work, which the
user cancelled on 2026-08-05.

Its one Isaac-side consequence -- whether the 45.5x yaw damping gap was an artifact, and
therefore whether HydroRC's yaw 0.011 is structurally near-zero -- is NOT dropped. It lives on
the hydrorc_016d1b1 page, which is being resolved separately in this same program. Deliberately
not duplicated here so the question has exactly one home.

The finding itself stays on the page as durable reference: if Stonefish is ever revived, the
mesh-versus-ellipsoid routing note is the first thing to re-read.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

