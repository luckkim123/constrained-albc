---
title: "command is NOT domain randomization; command range scale is inert residue (unwired 2026-04-06, stale comment)"
tags: []
created: 2026-07-07T06:53:21.423097
updated: 2026-07-07T06:53:21.423097
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# command is NOT domain randomization; command range scale is inert residue (unwired 2026-04-06, stale comment)

# command is NOT domain randomization; command range scale is inert residue (unwired 2026-04-06, stale comment)

Two distinct facts about the attitude/yaw-rate command that are easy to get wrong (a prior session did,
by trusting comments over code -- Verify Implementation Not Name).

## 1. command is a task target, NOT domain randomization

The command `_ang_cmd` (roll/pitch attitude target + yaw-rate target), sampled in
`_sample_velocity_command` (albc_env.py:610), is the TRACKING TARGET the policy must follow -- a task
specification, not DR. Distinctions:
- Reward is computed as att_error = cmd - actual (albc_env.py:480); command is the reference, not a hidden
  physics variable.
- Command is IN obs (policy must know its target to track it); most DR params are privileged/absent from obs.
- It IS sampled uniformly (`.uniform_(-1,1)`, albc_env.py:635-636) but "uniform sampling" does NOT make
  something DR. Robot-pose reset (reset_robot_pose_default) and joint-pos reset (randomize_joint_positions)
  are also uniform yet are initial-state, not DR.
- uniform-only DR requires BOTH (a) physics randomization AND (b) outside DORAEMON. Command fails (a) -> it
  is neither uniform-only DR nor DORAEMON DR; it is a third category (task command). The DR docs are already
  correct on this (domain-randomization-and-doraemon.md:33-35; command-and-task.md exemplary).

## 2. command range scale is inert residue -- always 1.0, NOT DORAEMON-managed (despite a stale comment)

Buffers `_cmd_att_scale`/`_cmd_yaw_scale`/`_cmd_lin_scale` (albc_env.py:318-321 main, :303-305 full_dof).
- **Wiring status (write-site grep, all 10 hits): permanently 1.0.** Every hit is either the `torch.ones`
  init or a read (albc_env.py:632-633). ZERO reassignment / += / .fill_ / .copy_ / setattr anywhere. No
  runner/algorithms/doraemon reference. Not in `_PARAM_DEFS`. So command range is ALWAYS full-scale and no
  curriculum drives it.
- **Git classification = deliberately-removed RESIDUE, not unimplemented placeholder:**
  - faddc51 (2026-04-02): WIRED a command-difficulty curriculum -- `self._cmd_att_scale[env_ids] =
    sampled["cmd_att_scale"]` (+lin/yaw) and `ParamSpec("cmd_att_scale", 0.1, 1.2, 0.3)` (18D DORAEMON).
  - f4583fd (2026-04-06): REMOVED it (18D->15D). Commit message rationale: "DORAEMON preferentially shrank
    command scales (cmd_att to 0.16) to boost success_rate -> degenerate solutions where robot barely moves.
    Commands are task difficulty knobs, not physics parameters." Added the correct comment "Command scales
    fixed at 1.0 (not DORAEMON-managed)" at :1368/:1354 but LEFT the init-line comment `# Per-env command
    range scales (DORAEMON-managed, default 1.0 if disabled)` stale -> self-contradiction in the same file.
  - Later refactors (2fb6338/088809f/cbe1408) carried the residue + stale comment into current paths.
- **DO NOT re-wire**: the curriculum was removed on purpose because it produced degenerate policies.
  Restoring it would re-introduce a known failure.

## action taken (2026-07-07)

Stale-comment correction prompt authored (not yet applied, code done in another session):
/root/.claude/jobs/*/tmp/PROMPT_command_scale_stale_comment_fix.md -- fixes 2 confirmed stale comments
(main:318, full_dof:302) + 3 optional (read-site :631, docstrings :615/:581) to match the already-correct
:1368/:1354 comments. Docs need NO change (already accurate). Buffers themselves are harmless (1.0);
deleting the dead buffers is a separate cleanup decision.

