---
title: "uniform-only DR full roster (9 params, DORAEMON-bypassing) + payload XY-radius vs Z curriculum split"
tags: []
created: 2026-07-07T06:52:51.038810
updated: 2026-07-07T06:52:51.038810
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# uniform-only DR full roster (9 params, DORAEMON-bypassing) + payload XY-radius vs Z curriculum split

# uniform-only DR full roster (9 params, DORAEMON-bypassing) + payload XY-radius vs Z curriculum split

DR params fall into two classes by whether reset-time sampling consults the DORAEMON `sampled` dict.
Decision rule (verified by full config-field trace 2026-07-07): a param is **uniform-only** (always
full-scale, no Beta curriculum) iff its reset sampler is `dr.get(...)` (=`DRSampler.get`, events.py:134,
ignores `sampled`, calls `_rand_uniform_range` directly) OR a raw `torch.rand` inside the randomize
function. A param is **DORAEMON-managed** iff it routes through `_sample_or_uniform("<key>", sampled, ...)`
AND `<key>` is registered in `_PARAM_DEFS` (doraemon.py:41-62, 16 entries).

## uniform-only roster — exactly 9

| # | param | path | code |
|:--|:---|:---|:---|
| 1 | joint_stiffness_range | dr.get | events.py:465 (randomize_joint_gains) |
| 2 | joint_damping_range | dr.get | events.py:466 |
| 3 | joint_effort_limit_range | dr.get | events.py:504 (randomize_joint_effort_limit) |
| 4 | joint_static_friction_range | dr.get | events.py:567 (randomize_joint_friction) |
| 5 | joint_viscous_friction_range | dr.get | events.py:568 |
| 6 | yaw_damping_scale | dr.get | events.py:214 (_randomize_hydro_model, DOF-5 override) |
| 7 | thrust_coefficient_scale | torch.rand (thruster) | marinelab thruster.py:231 (randomize_parameters) |
| 8 | time_constant_scale | torch.rand (thruster) | marinelab thruster.py:237 (up AND down scaled by SAME factor) |
| 9 | payload_cog_offset_xy_radius | torch.rand disk | events.py:432-433 (r = r_max*sqrt(U)) |

Grouped: arm joint 5 (stiffness/damping/effort_limit/static+viscous_friction) + thruster 2 + yaw_damping 1
+ payload XY-radius 1. These 9 are NOT in `_PARAM_DEFS` -> absent from DORAEMON saturation logging (the
config.py:187 "15 parameters" comment counts only DORAEMON-managed dims; actual NDIMS=16 today, and the
training env additionally sees these 9 uniform channels on top). Consequence: arm-joint + thruster
robustness is exposed at FULL scale from step 1, no curriculum easing.

## payload is per-subfield, NOT monolithic (common confusion)

`randomize_payload` (events.py) splits payload CoG into three subfields on DIFFERENT paths:

| subfield | axis | path | curriculum? | _PARAM_DEFS |
|:---|:---|:---|:---|:---|
| payload_mass | mass | _sample_or_uniform | DORAEMON | line 42 |
| payload_cog_offset_xy_radius | XY | torch.rand disk | uniform-only | absent |
| payload_cog_offset_z | Z | _sample_or_uniform | DORAEMON | line 56 |

So payload contributes exactly ONE param (XY radius) to the uniform-only roster; mass and Z-offset ARE
curriculum-managed.

## why XY vs Z differ (two independent axes)

1. **Sampling FORM**: XY is a 2D disk (angle uniform in [0,2pi], radius = r_max*sqrt(U) for AREA-uniform
   coverage) because horizontal eccentricity is rotationally symmetric (direction doesn't change gravity
   torque m*g*r, only magnitude does). Z is an asymmetric 1D range (-0.05, 0.0) because vertical direction
   is physically decisive (below buoyancy center = restoring/stable; above = unstable).
2. **Curriculum eligibility (the real reason XY is uniform-only)**: NOT physics — it's the DORAEMON engine
   constraint that each param is a **1D Beta** (ParamSpec(name, lo, hi, nominal), doraemon.py:73-75). Z is a
   1D range -> fits -> in _PARAM_DEFS. XY is 2D disk -> a single 1D Beta can't express (angle+radius
   entangled) -> left out -> uniform-only. This is an engine-datastructure side-effect, not a deliberate
   physical judgment. XY radius 0.08 is instead a HUMAN-tuned fixed value (config.py:207-213: r9_tightrates
   outlier analysis dropped 0.15->0.08 to keep payload torque inside roll TAM authority).

## how to put XY radius under DORAEMON (design, pending-experiment)

User proposal (sound): manage only the radius as a 1D Beta, keep angle uniform. Implement as a NORMALIZED
quantile u in [0,1]: register `("payload_cog_offset_xy_u", "payload_cog_offset_xy_radius", 0.0, 1.0)` in
_PARAM_DEFS, `_NOMINAL_OVERRIDES` u=0 (start with no offset), and in events `u = _sample_or_uniform(...)`
then `radius = r_max*sqrt(u)` (sqrt area-correction stays in events; DORAEMON only manages u). eval/DR-off
stays byte-identical (u~U(0,1) reproduces r_max*sqrt(U)). NDIMS 16->17. RESERVATION: radius 0.08 is already
a small human-tuned value so curriculum gain is uncertain, and adding a dim dilutes KL budget across the
other params -- a hypothesis to A/B, not a certain win. Correction prompt authored (not yet applied):
/root/.claude/jobs/*/tmp/PROMPT_payload_radius_doraemon.md.

