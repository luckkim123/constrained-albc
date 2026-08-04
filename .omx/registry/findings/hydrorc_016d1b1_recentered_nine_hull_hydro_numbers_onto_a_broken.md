---
title: "HydroRC 016d1b1 recentered nine hull hydro numbers onto a broken engine approximation, and the damage concentrates on yaw -- the axis where the 2026-07-28 paired gate failed; retire the commit rather than rebuild it minus one line"
tags: ["stonefish", "hydrodynamics", "added-mass", "damping", "hydro-recenter", "yaw", "cylinder-approximation", "system-id", "sim-to-real", "plant-change", "envs-main", "marinelab"]
created: 2026-07-30T02:28:59.725325
updated: 2026-08-04T16:49:24.714620
sources: ["marinelab:exp/hydro-recenter@016d1b1", "marinelab@f45d612", "stonefish-reply-20260730", "code-verify-20260730", "handoff-stonefish-servo-pc-20260729", "diagnose-20260728-081953"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
blocked-on: "each 016d1b1 damping axis needs re-derivation from geometry or literature before HydroRC-v2 is proposed; and the rotational-drag question to the Stonefish side decides whether yaw 0.011 is structurally near-zero"
---

# HydroRC 016d1b1 recentered nine hull hydro numbers onto a broken engine approximation, and the damage concentrates on yaw -- the axis where the 2026-07-28 paired gate failed; retire the commit rather than rebuild it minus one line

The Stonefish session traced its own ComputeCylindricalApprox dimensional bug (2026-07-30) onto the
ALBC base hull and showed that the 2026-07-27 effective-mass measurement is the bug's OUTPUT, not a
hull property. Their prescription was to drop ONE line (hull heave added mass) when HydroRC is
rebuilt. That prescription is too narrow. Commit 016d1b1 recentered NINE hull hydro numbers off the
same rig on the same day, and their own hardcoded-Cd caveat reaches the axis they explicitly
disclaimed as out of scope.

ACCEPTED, AND INDEPENDENTLY RE-DERIVED (not taken on their report). At freshwater rho=998 their
arithmetic is exact: broadside m2 = rho*pi*r^2*L = 7.885 kg, axial m1 = rho*pi*r^2 = 25.396 kg
(missing length factor), disc limit (8/3)*rho*r^3 = 1.940 kg, so m1 sits 13.09x above physics
(= 3*pi/(8*r) at r=0.09); isotropic getAugmentedMass average = 13.722 kg; plus rigid 9.18 predicts
effective 22.902 kg against the measured band 22.6-23.3. The measured number is therefore the
engine's own broken axial term averaged into the other two axes. Consequence: hull heave added mass
1.0 -> 8.0 is RETIRED, not batched. Applying it would put heave 8.0/1.940 = 4.12x ABOVE geometry.
Verified on disk: 016d1b1 does set added_mass = (8.0, 8.0, 8.0, 0.09, 0.09, 0.035), and
git merge-base --is-ancestor 016d1b1 exp/max-thrust-dr returns false, so it never reached mainline.

OUR ANALYTICAL NOMINAL WAS ALREADY RIGHT ON THE AXIS THEY VINDICATE. Isaac surge/sway 8.0 against
geometric 7.885 is 1.015, i.e. 1.5 percent high. Isaac heave 1.0 against the disc limit 1.940 is
1.9x LOW -- the only genuine base translational added-mass gap, and it points the opposite way from
the recentering. The nominal tuple (8.0, 8.0, 1.0, ...) already encodes the cylinder axis as body z
(broadside much greater than axial), independently confirming their axis statement from our own
config. The analytical derivation was sound; the recentering replaced a sound value with an artifact.

WHAT THEY MISSED -- THE AXIS SIGNATURE. Tabulating the full 016d1b1 delta by axis (old analytical ->
recentered, as a reduction factor):

  axis         linear                quadratic
  surge/sway   2.0   -> 0.5    4.0x   39.0 -> 8.0     4.9x
  heave        1.5   -> 1.6    0.9x   15.0 -> 22.7    0.7x  (up)
  roll/pitch   0.3   -> 0.03  10.0x    1.0 -> 1.2     0.8x  (up)
  yaw          0.15  -> 0.002 75.0x    0.5 -> 0.011  45.5x

Yaw is the ONLY axis that collapses in both damping terms. Yaw is also rotation about the cylinder's
axis of revolution. Roll and pitch are broadside tumble, where the cylinder approximation still has a
real cross-section, and their quadratic term barely moves (it rises 20 percent). That asymmetry is
the signature of a geometric approximation losing all information on exactly one axis, not of a
measurement finding a smooth hull.

THE HARDCODED Cd EXPLAINS ONLY HALF THE TRANSLATIONAL GAP. Stonefish applies Vector3 Cd(0.5, 0.5, 1.0)
to every cylinder regardless of L/D (their own statement, given as a caveat against reusing their
buoy anisotropy magnitude). Against the analytical Cd_cross = 1.17 that is 2.34x. The observed
surge/sway quadratic gap is 39.0/8.0 = 4.88x. The residual 2.08x is the appendage, thruster and
gripper drag that a single-cylinder approximation omits. So the translational damping recentering is
low for two independent reasons, both of them engine artifacts, and neither of them a hull property.

WHY THIS IS THE RIGHT AXIS, UNLIKE THE HEAVE ITEM. The Stonefish side correctly noted heave is the
wrong axis to explain the 2026-07-28 roll/yaw regressions. But the wiki lead
hydrorc_is_half_recentered_buoy_link3_nominals_untouched_but_the had already named hull yaw
quadratic damping 0.5 -> 0.011 as the mechanism, PREDICTED the failure from it, and the paired gate
then failed exactly there (roll n_gt20 0 -> 18.67 envs, yaw ss +18.8 percent, hard-corner collapse).
Their Cd finding supplies the missing provenance for that same number. The heave item is a category
error with no behavioural consequence; the yaw damping item is an artifact WITH one, already observed.

PRESCRIPTION. Do not rebuild HydroRC-v2 as 016d1b1 minus the heave line. Every number on that commit
needs the geometry-versus-engine audit that was just applied to added mass, and on present evidence
most of them fail it. The defensible salvage is narrow: rotational added mass was KEPT unchanged by
016d1b1 (a no-op) and is the one quantity Stonefish reports per-axis, since getAugmentedInertia does
not average where getAugmentedMass does. Treat the damping recentering as unsourced until each axis
is re-derived from geometry or literature, using Stonefish only as a detector of ordering errors and
never as a source of magnitudes.

OPEN QUESTION FOR THE STONEFISH SIDE (decides whether yaw 0.011 is structurally near-zero). Does
Stonefish derive rotational drag from a distributed integral over the approximated geometry, or from
a separate rotational term? If it is the former, a body of revolution rotating about its own axis has
near-zero yaw drag by construction, the residual 0.011 comes from the offset Gripper cylinder, and
the 45x is fully explained as an approximation artifact. If there is a separate rotational term, the
number may carry real information and the audit conclusion softens for that axis only.

WHAT SURVIVES THEIR POINT (i), AND WHY. Their repeated measurement showed the 50 Hz HF fraction is
run-dependent (HF percent dq1 came out 0.1 and 14.8 on two identical runs) and that track_max
scatters 1.76x at fixed gains, so both statistics are unusable. This does NOT void the
stationary-arm cleanliness conclusion, because that conclusion never used an HF fraction. It rests on
rms dq1 = 2e-6 rad/s while holding (a direct kinematic quantity, measured at odom 100 Hz) and on
cross-gain INVARIANCE of rms base yaw rate: 0.034326, 0.034283, 0.034408 across three gain settings
whose chatter differs by roughly 50x, a 0.2 percent spread. An invariance argument is immune to a
common-mode sampling bias, which is precisely why this survives while their absolute HF and peak
figures did not. Past base-only measurements remain clean of servo contamination. They are NOT clean
of engine geometry, which is a second and newly opened contamination axis.

RETRACTED NUMBERS TO STOP QUOTING (their own corrections, accepted): the 12.5x peak joint-torque
reduction becomes 7x on rms (1.032-1.069 -> 0.147-0.156, reproducing to 3 percent); track_max is
unusable at every gain setting and rate; the claim that 0.1/0.1 improves tracking over 1.0/1.0
survives only on track_rms (0.0041-0.0044 across four runs and both rates, against Isaac 0.0072, so
Stonefish tracks tighter); the M_a/m = 10 stability datum is withdrawn in favour of the analytic
argument that M + M_a is positive definite for any M_a greater than zero, so implicit treatment is
unconditionally stable regardless of ratio; the upstream bug report should carry 13.1x (hull) and
13.9x (buoy) distance-from-physics rather than the 8.47x missing-length-factor figure.

GUARD SCOPE NARROWS TO THE BUOY ALONE. Recomputed: the hull per-reset cap is 0.95*9.18 = 8.721 kg
against a geometric maximum of 7.885 kg, so there is headroom and the hull needs no guard decision.
The buoy still binds (geometric broadside 2.674 kg, axial disc 1.634 kg, against a cap of
0.95*0.93 = 0.8835 kg). The guard-structure question raised in the half-recenter lead is therefore
the buoy's alone.

[EVIDENCE: git show 016d1b1 -- marinelab/assets/albc/albc.py (full diff, nine changed hydro values);
git merge-base --is-ancestor 016d1b1 exp/max-thrust-dr -> false; marinelab/assets/albc/albc.py:52
current added_mass (8.0, 8.0, 1.0, 0.09, 0.09, 0.035) and :85 body_mass 9.18; arithmetic re-derived
2026-07-30 code-exec at rho=998; Stonefish reply 2026-07-30 (vault
docs/stonefish-hydro-measurement-2026-07-27.md correction section and
docs/servo-gain-deployed-fix-2026-07-29.md); prior mechanism and gate result in wiki
hydrorc_is_half_recentered_buoy_link3_nominals_untouched_but_the and
hydrorc_recenter_gate_result_2026_07_28_isaac_paired_gate_fail_r; stationary-arm evidence in wiki
stonefish_yaw_gap_claim_review_main_body_hydro_yaw_torque_struct update 2026-07-29T10:13]
[CONFIDENCE: HIGH on the arithmetic, the axis signature, the branch facts and the heave retirement;
HIGH on the Cd constant being 2.34x below the analytical Cd_cross given their stated constant;
MEDIUM on the specific yaw mechanism (cylinder of revolution has no axial-rotation drag), which is a
deduction from their premises and not from Stonefish source this session read -- the open question
above is what would settle it]

---

## Update (2026-08-04T16:49:24.714620)

## VERDICT 2026-08-05 -- RESOLVED (backlog-closeout program)

Two things settle this without the per-axis re-derivation the lead was waiting on.

**First, the damage never landed.** Commit 016d1b1 is not on marinelab main -- it exists only
on branch `exp/hydro-recenter`, and `git merge-base --is-ancestor 016d1b1 HEAD` is false. The
shipped plant still carries the pre-recenter analytical values (albc.py:56/60: linear yaw 0.15,
quadratic yaw 0.5). The yaw 0.011 that this page identifies as the concentrated damage exists
only inside the rejected commit. This page's own recommendation was to retire that commit
rather than rebuild it minus one line; retiring it is already the de-facto state, and it stays
that way.

**Second, the remaining question is now measured.** The open item was whether every 016d1b1
damping axis must be re-derived from geometry or literature before a HydroRC-v2 could be
proposed. That is only worth doing if hull damping is a lever the policy can feel.

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

**Verdict**: the plant is insensitive to hull yaw damping across two orders of magnitude, so a
per-axis re-derivation is not justified by any control benefit that could follow from it. No
HydroRC-v2 is proposed. The other half of this page's blocker -- the rotational-drag question
to the Stonefish side, which was to decide whether yaw 0.011 is structurally near-zero -- died
with the 2026-08-05 user decision to drop Stonefish entirely, and it is moot regardless now
that the axis is measured not to matter.

**Scope, stated honestly**: this measures how much a TRAINED policy's control performance
depends on hull yaw damping at eval time. It does not measure whether training on a different
damping would produce a different policy. That is a weaker claim than 'hull yaw damping is
irrelevant', and it is the claim being made. It is however exactly the claim the open item
needed, because the item was about whether to spend effort re-deriving coefficients.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

