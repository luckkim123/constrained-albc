---
title: "uniform-only DR full roster (9 params, DORAEMON-bypassing) + payload XY-radius vs Z curriculum split"
tags: ["payload", "doraemon", "dr", "ndims", "merge", "main"]
created: 2026-07-07T06:52:51.038810
updated: 2026-07-07T18:53:11.982150
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
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

---

## Update (2026-07-07T18:41:10.477183)

## UPDATE (2026-07-08): XY-radius DORAEMON promotion is now IMPLEMENTED (not pending) + NDIMS is branch-dependent

The "pending-experiment" design above was **executed** by a separate SDD session. Status correction:

- **Implemented** on worktree/branch `worktree-payload-radius-doraemon` (tip `eb47f0e`, 6 commits
  `115fc2c..eb47f0e`), baseline tag `baseline-260707-payload-radius-dr`. New DORAEMON dim
  `payload_cog_offset_xy_u` registered in `_PARAM_DEFS` (nominal 0 via `_NOMINAL_OVERRIDES`), events
  applies `radius = r_max * sqrt(u)` with `u` sourced from DORAEMON. angle stays uniform. opus
  whole-branch review = READY TO MERGE (Critical/Important 0). 18 albc + 6 marinelab tests pass.
- **NOT merged to main** — held for GPU baseline comparison (comparison-experiment rule: adopt/discard
  only after baseline-vs-change eval). A later branch-consolidation attempted `git rebase main` but
  ABORTED on a STRUCTURAL conflict (main `3e1f81f` merged base+Hard DomainRandomizationCfg into ONE
  class; the promotion branch still sits on the OLD two-class structure). User decision: leave un-rebased,
  do the structural integration WITH A HUMAN after the GPU verdict. So as of 2026-07-08 the promotion
  lives only on its worktree; main is unchanged.

### NDIMS is BRANCH-DEPENDENT — never state it without naming the branch

This card's "NDIMS=16" is the **main / pre-promotion** value. On `worktree-payload-radius-doraemon`
NDIMS=**17** (the xy_u dim added). The same `doraemon.py` therefore has different `len(_PARAM_DEFS)`
on different branches/worktrees. A session repeatedly gave wrong answers (16 -> "actually 17" -> ...)
by reading whichever `doraemon.py` a delegated agent happened to open (the worktree copy) and treating
it as the origin. RULE: answer code facts as "main=16, promotion worktree=17", run `git worktree list`
before asserting, and when delegating a read, name the branch/path. This is the branch-awareness
extension of the handle-directly-overuse lesson.

### promotion's own latent caveat (reviewer Minor)
`_sample_stashed_cog_offset` (the mid-episode PICK/carry re-sample path, albc_env.py) does NOT apply the
curriculum — but `payload_toggle_steps=0` default means that path never runs in the default task, so it
is inert for now.

---

## Update (2026-07-07T18:53:11.982150)

## UPDATE (2026-07-08, later same day): XY-radius promotion MERGED TO MAIN — supersedes the "held for GPU verdict" note above

The immediately-preceding UPDATE said "NOT merged to main / held for GPU verdict / main is
unchanged / do the structural integration with a human later". **That is now stale.** Same day the
user reversed the hold decision and adopted the promotion into main.

- **MERGED to main**: constrained-albc main tip `b830043` (`merge --no-ff`). The 6 promotion commits
  were REBASED onto the merged single-class `DomainRandomizationCfg` (main `3e1f81f`), resolving the
  structural conflict, then merged. rebase also carried the promotion branch's own wiki commit `a790772`.
- **Conflict resolution (what a human/agent must know for future edits here)**: merge-base was the OLD
  two-class layout; main deleted the base class and kept a single class, the promotion branch added the
  field to the (now-gone) base class. git could not auto-resolve "one side deleted the lines the other
  edited". Real conflicts were only 3 files: `config.py` x2 (structure) + `analysis/dr_config.py` (both
  sides added different keys to `_TRUE_NOMINAL_PHYSICS`). doraemon.py / events.py / tests applied cleanly
  (main never touched them). Resolution kept main's single-class structure and ADDED the payload field /
  dict entries on top. `payload_cog_offset_xy_radius` stays main's **0.08** (u_range is a normalized
  quantile, independent of the physical r_max, so the 0.08-vs-0.10 question is moot).
- **NDIMS on main is now 17** (was 16). The "NDIMS is branch-dependent, main=16" rule in the section
  above is superseded: after this merge, main itself has NDIMS=17. The `_PARAM_DEFS` roster on main now
  includes `payload_cog_offset_xy_u`, so payload XY-radius is no longer in the uniform-only-DR roster —
  it is DORAEMON-managed. The uniform-only roster shrinks from 9 to 8 params on main.
- **Verification**: `tests/test_doraemon.py test_dr_config.py test_priv_obs_bounds.py` = 44 passed / 2
  skipped on the merged main tree (the NDIMS-17 assertion passes, confirming `len(_PARAM_DEFS)==17`).
  A broader sweep showed 3 `tests/deploy/` failures, but those are PRE-EXISTING (reproduced on pre-merge
  main `bc3878f` via a throwaway worktree) — the promotion did not introduce them.
- **HONEST TRADEOFF (recorded in the merge commit)**: merged WITHOUT the GPU baseline-comparison verdict
  that comparison-experiment isolation normally requires — the user consciously overrode that rule and
  invariant #3. Mitigation: the curriculum dim starts at nominal u=0 (no XY offset), so the training
  default behavior is unchanged until DORAEMON widens it. The GPU baseline verdict was NOT performed.
- **Tree state**: constrained-albc is now a single main tree (payload-radius worktree/branch removed);
  main is UNPUSHED (push is user-gated). marinelab side of unrelated actuation-noise stays un-consolidated.

