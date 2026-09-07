# Deployment note: the yaw observation slots changed meaning (rate -> position)

**Repo side is done; the board side is not.** `constrained_albc/envs/main` now commands yaw as a
world-frame **heading target in rad** instead of a body yaw **rate in rad/s**. The 69D observation
vector keeps its dimension and its slot ordering — only the *quantity* in four slots changed — so a
board that keeps building the old proprio vector will feed the new policy a rate where it expects an
angle, with no shape error and no crash. The board's proprio builder (`build_proprio.py`,
agent-jetson) must now receive a heading setpoint `yaw_cmd` (rad) instead of a yaw-rate setpoint, and
compute the tracking error as the **shortest-path wrapped difference**

```
yaw_err = atan2(sin(yaw_cmd - yaw), cos(yaw_cmd - yaw))     # in (-pi, pi], rad
```

using the same measured `yaw` (rad) it already feeds into the euler slots. The wrap is what makes the
sign of `yaw_err` the short turn direction: from a heading of `-3.0` rad toward a target of `+3.0`
rad the error is `-0.283` rad (turn the short way), not `+6.0` rad. A plain subtraction gives the
long way round and will drive the vehicle backwards through nearly a full turn.

## Slots whose meaning changed (base 69D layout)

| Obs index | Slot | Was | Is now |
|:---|:---|:---|:---|
| `2` | `ang_cmd[2]` — the yaw command | yaw rate setpoint, rad/s | yaw heading target, rad (world frame) |
| `26`, `36`, `46` | `ang_err[2]` in each of the 3 history steps | `yaw_cmd - w_z`, rad/s | `wrap(yaw_cmd - yaw)`, rad |
| `68` | integral error, yaw channel | leaky integral of the rate error | leaky integral of the wrapped heading error |

Nothing else moves. The history block is **step-major**, not feature-grouped: indices `20..49` are
three consecutive 10-float steps, each laid out `[joint_pos_err(2), joint_vel(2), ang_err(3),
euler(3)]`, so the yaw error sits at offset 6 inside each step. Indices `3..19` (euler, body rates,
arm, thrusters), `50..65` (action history) and `66..67` (roll/pitch integral) are untouched.

If the board runs the 72D variant (`use_bias_ema_obs`, the shipped default), the bias-EMA triple is
appended at `69..71` and its yaw entry at index `71` is likewise now an EMA of the wrapped heading
error rather than of the rate error.

## Setpoint plumbing

Whatever currently produces a yaw-rate command on the board (an operator stick mapped to rad/s, or an
outer heading P-loop whose output was `clip(Kp * yaw_err, +-yaw_rate_sat)`) must be replaced by the
heading target itself. **Delete the outer P-loop rather than re-tune it** — the policy is that loop
now. The same removal was applied repo-side to the segmented eval mode in
`constrained_albc/analysis/eval.py`, where `--kp_yaw` and `--yaw_rate_sat` are now accepted-but-ignored.

A "hold heading" / hover command is **not** `yaw_cmd = 0`. Zero means "point at world heading 0", so a
hover request must latch the vehicle's *current* yaw as the target at the moment the command is
issued, and then hold that latched value. Re-reading the live heading every control step makes the
error identically zero and silently removes all yaw authority.

## Rate limiting still exists, on the constraint side

Slew is bounded by the `yaw_rate` constraint (`soft_threshold = 0.55` rad/s = 31 deg/s), so a pi
turn takes at least 5.7 s. The board does not need to rate-limit the setpoint itself; the trained
policy already respects that budget. The new `yaw_settling` constraint additionally damps `|w_z|`
once `|yaw_err| <= 0.087` rad (5 deg), which is what suppresses hunting about the target.

The `cumul_yaw` constraint was removed from the shipped term list (tether wrap is an operational
concern, not a control constraint). `cumulative_yaw_cost` and the `Episode/cumul_yaw_deg` log remain
as a free diagnostic, so any board-side tether-wrap guard is now the only thing enforcing that limit.

## Verifying the board after the change

Command a heading step of about +0.5 rad and confirm the reported `yaw_err` slot crosses zero once
and settles, and that a target of `+3.0` rad from a heading near `-3.0` rad produces a *small
negative* error rather than a large positive one. That single sign check catches a missing wrap,
which is otherwise invisible until the vehicle takes the long way round.
