---
title: "uniform-only DR full roster (9 params, DORAEMON-bypassing) + payload XY-radius vs Z curriculum split"
tags: ["payload", "doraemon", "dr", "ndims", "merge", "main"]
created: 2026-07-07T06:52:51.038810
updated: 2026-07-23T07:42:44.403170
sources: []
links: ["xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
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

---

## Update (2026-07-16T06:55:59.320356)

## Update (2026-07-16): the PRUNE TRAP — removing a key from `_PARAM_DEFS` alone does NOT pin the param; it silently DEMOTES it to this page's uniform-only class

This page's decision rule ("DORAEMON-managed iff it routes through `_sample_or_uniform(<key>, sampled, ...)`
AND `<key>` is registered in `_PARAM_DEFS`") has a corollary that is easy to get backwards when DESIGNING a
DR-dim prune. Recording it explicitly because a prune proposal is exactly where the rule gets read.

[FINDING] Deleting an entry from `_PARAM_DEFS` while LEAVING its `_sample_or_uniform` call site and its
DR-cfg field intact does not pin the param at nominal. The key vanishes from the `sampled` dict, the
`if sampled and key in sampled` test fails, and control falls to `_rand_uniform_range(shape, range_tuple,
device)` over the **cfg field's full range** — i.e. the param becomes uniform-only per this page's own
roster: always full-scale, no Beta curriculum, at full width from iteration 0. The intent ("stop
randomizing this") produces the opposite ("randomize it maximally, forever, uncurriculumed").
[EVIDENCE: events.py `_sample_or_uniform` else-branch -> `_rand_uniform_range`;
`_apply_xyz_offset_with_doraemon` per-axis else-branch does the same]
[CONFIDENCE: HIGH]

To actually pin a param at nominal you must ALSO remove the cfg field (which forces the call site to
change) or delete the randomize call. e4 xyprune did remove the cfg fields — verified: its
`config/env.yaml` has no `cob_offset_x/y` or `cog_offset_x/y` keys at all, and `state_space: 24` vs the
baseline's 28 — so e4 avoided this trap. It was avoided by construction, not by a guard: nothing in the
code would have flagged the half-prune.

[FINDING] SUB-TRAP — the `default_lo, default_hi` in each `_PARAM_DEFS` tuple are DEAD for training and
must not be read as the live bounds. `build_param_specs` (marinelab/algorithms/doraemon.py:65-83)
destructures `for param_name, field_name, _, _ in param_defs` — discarding both defaults — and takes
`lo, hi = getattr(dr_cfg, field_name)`. Training always goes through this path
(`albc_env.py:495: build_param_specs(self.cfg.randomization, _PARAM_DEFS, _NOMINAL_OVERRIDES)`); the
module-level `PARAM_SPECS`, which DOES use the tuple defaults, is only for "callers without a DR cfg".
So e.g. `("cog_offset_x", "cog_offset_x", -0.01, 0.01)` trains at the CFG range (-0.02, 0.02), not ±0.01.
The in-file comment at the buoy entries already says this ("this is only the module-load default used
when no DR cfg is supplied; the live cfg field default is (0.75, 1.25), see config.py") but it sits on
two entries out of ~20 and reads as buoy-specific when it is universal.
[EVIDENCE: doraemon.py:39 header comment "(doraemon_name, dr_config_field_name, default_lo, default_hi)";
marinelab doraemon.py:79-82; albc_env.py:495; doraemon.py:89 "Default specs (base bounds) for callers
without a DR cfg"]
[CONFIDENCE: HIGH]

CONSEQUENCE for the prune trap: because DORAEMON's live bound and the uniform fallback BOTH read the same
cfg tuple, a half-prune does NOT widen the range — max width is identical. What is lost is the
CURRICULUM: Beta annealing outward from nominal is replaced by full-range uniform from iter 0. Same
ceiling, no ramp.

STALENESS FIX: this page's rule text says "_PARAM_DEFS (doraemon.py:41-62, 16 entries)". As of 2026-07-16
HEAD it is 20 entries (the p_t union merge and the buoy volume/mass decorrelation added dims since this
page was written on 2026-07-07). `NDIMS = len(_PARAM_DEFS)` is dynamic, so no code hardcodes the count —
only this page did.

APPLICABILITY NOTE: the concrete prune this was investigated for (e4 xy-offset) is CLOSED by user
decision 2026-07-16 — see [[xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e]]. The trap
is recorded because it generalizes to any future `_PARAM_DEFS` prune, not because that prune is live.

---

## Update (2026-07-23T07:42:44.403170)

2026-07-23 curation: title says '9 params' but this page's own 2026-07-08 update shrank the uniform-only roster to 8 after payload_cog_offset_xy_u promotion. Treat the title's '9 params' as historical/outdated; current roster is 8 params. (Retitle not applied -- title change would fork the wiki slug via the CLI's slug-of-title merge key.)
