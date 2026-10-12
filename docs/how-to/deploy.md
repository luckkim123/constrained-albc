# Deploy — The Controller on the Vehicle

What runs on the vehicle, and the observation contract the board must honor. How to build a
pack is in [deploy-pack-export.md](deploy-pack-export.md).

## What is deployed

- The **student** (GRU encoder) runs on the vehicle at **50 Hz** together with the teacher's
  actor, with the simulation weights unchanged. The student predicts the 9D latent `z` from
  the 72D observation history, so no privileged input is needed at inference.
- Two additions act outside the network:
  - a guard in the joint driver halts the arm at the two-turn cable limit of joint 1;
  - a damping term feeds the body angular rate back to the joint targets.
- The board-side inference code (numpy runtime `npforward.py`, loaded under Python 2.7) lives
  in the separate `agent-jetson` repository.

The paper's pack is `pack_rr_ft_ftp7200_s30_gru_260927_193819`: teacher `model_7200.pt`
(run `trpo_rr_FTP_s30_260927_182609`) and student `student_999.pt`
(run `trpo_sd_rr_ft_ftp7200_s30_260927_192341`); obs 72, action 8, latent 9, GRU hidden 128.

## Yaw observation contract

The yaw command is a world-frame **heading target in rad**, not a body yaw rate. The board's
proprio builder must feed a heading setpoint `yaw_cmd` (rad) and compute the tracking error as
the shortest-path wrapped difference

```
yaw_err = atan2(sin(yaw_cmd - yaw), cos(yaw_cmd - yaw))     # in (-pi, pi], rad
```

using the same measured `yaw` it feeds into the euler slots. A plain subtraction takes the
long way round: from `-3.0` rad toward `+3.0` rad the correct error is `-0.283` rad, not
`+6.0` rad. No shape error or crash reveals a wrong quantity here.

| Obs index | Slot | Quantity |
|:---|:---|:---|
| `2` | `ang_cmd[2]` — the yaw command | heading target, rad (world frame) |
| `26`, `36`, `46` | `ang_err[2]` in each of the 3 history steps | `wrap(yaw_cmd - yaw)`, rad |
| `68` | integral error, yaw channel | leaky integral of the wrapped heading error |
| `71` | bias-EMA, yaw channel (72D layout) | EMA of the wrapped heading error |

The history block `20..49` is step-major: three consecutive 10-float steps, each
`[joint_pos_err(2), joint_vel(2), ang_err(3), euler(3)]`, so the yaw error sits at offset 6 in
each step. The bias-EMA triple (`use_bias_ema_obs`, on by default) occupies `69..71`.

**Setpoint plumbing.** Feed the heading target itself; do not wrap the policy in an outer
heading P-loop. A "hold heading" command latches the vehicle's *current* yaw as the target
when it is issued and holds that value — `yaw_cmd = 0` means "point at world heading 0", and
re-reading the live heading every step makes the error zero and removes all yaw authority.

**Rate limiting.** Slew is bounded by the `yaw_rate` constraint (`soft_threshold = 0.55` rad/s),
so a pi turn takes at least 5.7 s, and `yaw_settling` damps `|w_z|` once `|yaw_err| <= 0.087`
rad. The board does not rate-limit the setpoint. Tether wrap is not a trained constraint
(`cumul_yaw` is diagnostic only), so any tether guard is board-side.

**Check after a board change.** Command a heading step of about +0.5 rad and confirm the
`yaw_err` slot crosses zero once and settles; a target of `+3.0` rad from a heading near
`-3.0` rad must give a small negative error.

## Dims and architecture

[observation-space.md](../reference/observation-space.md),
[main-network-architecture.md](../reference/main-network-architecture.md). Sim-to-real gap
analysis: [sim-to-real.md](sim-to-real.md).
