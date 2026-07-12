---
title: "yaw command is rate not angle: inherited design, defensible only if heading is a free DOF (yaw-angle A/B idea)"
tags: ["yaw", "command", "attitude-control", "experiment-idea", "station-keeping"]
created: 2026-07-08T23:20:11.777465
updated: 2026-07-08T23:20:11.777465
sources: []
links: ["teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia.md", "command_is_not_domain_randomization_command_range_scale_is_inert.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# yaw command is rate not angle: inherited design, defensible only if heading is a free DOF (yaw-angle A/B idea)

Multi-source review (control adversarial check + marine-control literature + git-history audit, 2026-07-09) of whether the default `envs/main` task should command yaw as a RATE (current) or as an ABSOLUTE ANGLE. Command layout: `_ang_cmd = [roll_att, pitch_att, yaw_rate]` (roll/pitch = attitude ±30°, yaw = rate ±0.5 rad/s). Full doc rationale now in `docs/reference/command-and-task.md` §8.5.

## Verified findings

- **Yaw-as-rate is INHERITED, not a deliberate design decision.** Before `git 11dcad6` (2026-04-01) all 3 axes were angular-velocity (rate) commands. That commit promoted ONLY roll/pitch to absolute attitude; yaw was left as a rate (semantics renamed velocity->yaw-rate). Yaw was NEVER an absolute-angle command in repo history. So "yaw is a rate" = residue of not touching yaw, not a documented choice. `full_dof` handles yaw identically (only adds lin-vel cmd).
- **Physical asymmetry is real (verified) but does not alone justify rate.** roll/pitch have metacentric restoring torque (CoB above CoG) -> a physical zero (level) -> absolute-attitude target natural. yaw about vertical axis is energetically neutral -> no restoring torque -> no privileged heading zero. Matches project's own `references/iros_2026/notes/02_problem.md` ("Yaw: 없음"). BUT absence of restoring force is the classic argument FOR an active absolute-heading loop; the policy already observes absolute yaw (`euler[3:6]`, observations.py:54). So the asymmetry justifies "treat yaw differently," NOT "command the rate."
- **The genuinely sound reason (found by adversarial review, NOT in the original code/docs):** task objective has no heading requirement (reward = roll/pitch attitude + yaw-RATE; no yaw-angle term). When heading is don't-care, an absolute yaw datum would force the policy to fight ocean-current yaw torque to hold an ARBITRARY heading, burning thruster_util and disturbing the arm task, for no reward benefit. Rate command lets heading float. `cumulative_yaw_cost` (limit 8π ~ 4 revolutions) is then purely a tether-wrapping safety envelope (its docstring; non-binding/inert in practice), NOT a heading objective.
- **Standard-practice caveat.** Marine station-keeping/DP (Fossen cascaded autopilots; ArduSub/BlueROV2 "hold current heading") closes the OUTER loop on absolute HEADING ANGLE, rate only inner-loop -- does NOT free-drift at rate=0. So "yaw-angle is cleaner" aligns with the station-keeping convention. The quadrotor yaw-as-rate precedent (yaw = only free rotational DOF since translation consumes roll/pitch) does NOT transfer to an independent-thruster UUV.

## Prior analysis error (self-approval lesson)

An earlier handle-directly answer claimed "yaw-rate is physically/academically correct" on 4 grounds; adversarial review found 2 WRONG (non-sequiturs) and 2 WEAK: (1) "no restoring force -> rate natural" WEAK (non-sequitur); (2) "strong TAM yaw authority -> good for rate" WRONG (strong authority helps ANGLE equally); (3) "hover -> rate=0 suffices" WRONG (rate=0 lets heading drift unbounded; the 8π cumul_yaw guard proves drift is a known/tolerated failure); (4) "angle needs wrapping/arbitrary-zero/regresses" WEAK (cost/inertia argument, wrapping already implemented). The correct framing is task-dependent, not "physically correct."

## Experiment idea (NOT yet run; user gate)

A/B: yaw-angle command vs current yaw-rate command, for station-keeping. This is a BROAD change (command def + reward yaw_vel_tracking->yaw-angle tracking + cumulative_yaw_cost/yaw_rate_cost semantics + obs integral channel + wrap error), so a clean one-variable A/B is hard -- design via exp-design (differential) before any code prompt. STRONG precondition: first audit whether the arm/manipulation objective implicitly needs a stable heading (directional sensor, world-frame reach) -- code-only, no GPU; if yes it tips toward yaw-angle and changes the hypothesis. Then hypothesis: "does floating heading (rate) cost anything vs pinned heading (angle) under ocean-current yaw torque?"

## Open / unverified

(a) Whether yaw-angle would regress the tuned baseline is UNTESTED (needs the A/B). (b) Marine-autopilot convention rests on secondary sources (Fossen Handbook Ch.7 primary not read). (c) arm-task implicit heading dependence not audited. Related: [[teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia]], [[command_is_not_domain_randomization_command_range_scale_is_inert]].

