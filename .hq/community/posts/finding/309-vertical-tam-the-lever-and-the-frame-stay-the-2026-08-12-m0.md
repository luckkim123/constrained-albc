# Vertical TAM: the lever and the frame stay; the 2026-08-12 m0 probe says the vertical moment at u=0.25 is ~3x below the linear training plant, which matches the sim signed-square curve, not a wrong lever -- R-1 two-level ratio decides, K cancels

- id: finding/309 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: medium · status: needs-experiment
- verified: partial · keywords: vertical-tam, thrust-curve, thrust_coefficient, m0, R-1, retrain-simtoreal-2026-09, frame
- summary: Answer to the user question whether the vertical TAM needs lowering and whether the frame is fine. Training plant is thrust = command x 40 N linear (config.py:140-141, verified at HEAD 81c2ec0), coefficient DR (0.7,1.3), clamp 50 N; PLAN v3.1 used 50 N as the coefficient (D-1 14.5 N.m should be 11.6). The m0 sign probe (+0.25 -> pitch -3.36 deg, K 7.76 N.m/rad) gives 0.455 N.m vs linear nominal 1.45 N.m (0.31x, below the DR floor) and vs signed-square 0.363 N.m (1.25x, inside its DR band). Lowering the My row is the wrong knob if the deviation is shape; the sim curve exists as enable_thrust_curve true with thrust_deadband 0 (mixer already inverts the ESC deadband). R-1 at two levels: ratio dtheta(0.5)/dtheta(0.25) ~2 linear vs ~4 quadratic, K cancels. r1-before-final recommendation moves to yes. Frame closed by +102 deg consumer-side rotation; nothing to redo.

Answer to the user's 2026-09-03 question "does the vertical TAM need lowering, and is the frame fine as-is?", from the record plus one piece of arithmetic nobody had done: the tank probe that fixed m0's SIGN (2026-08-12) also carries m0's MAGNITUDE, and that magnitude is about 3x below the training plant at the command level probed. Frame: nothing to change. Lever: nothing to change. What deviates is the thrust-vs-command SHAPE, and that is a different knob from the TAM row.

## 1. What the training plant assumes (verified at HEAD 81c2ec0, 2026-09-03)

- `constrained_albc/envs/main/config.py:140-141`: `max_thrust 50.0`, `thrust_coefficient 40.0`. Thrust = command x 40 N, LINEAR (finding/283 measured the same on 2026-07-29). The 50 N is a clamp, so the "0.145 m x 50 N" in PLAN v3.1 §2/§3 and the "14.5 N.m" in D-1 are the wrong constant: nominal vertical moment per unit command is 0.145 x 40 = **5.8 N.m**, pair 11.6 N.m.
- DR (`deployed_env.yaml:480-488`): `thrust_coefficient_scale (0.7, 1.3)` -> the coefficient the policy trained against is U(28, 52) N per unit; `max_thrust_scale (0.85, 1.15)` scales only the clamp. PLAN v3.1 §5 listed only the clamp band; the +/-30 % coefficient band exists and matters below.
- Curve: `marinelab/core/thruster.py:164-182` -- with `enable_thrust_curve false` the map is the identity; with `true` it is deadband (`|s| < thrust_deadband` -> 0) then `sign(s) * s**2`. Incumbent trained with `false` (finding/281).

## 2. What the tank already measured

`deployed_tam.json.measured_thruster_sign.m0` / vault `finding/077` (tank 2026-08-12): m0 `+0.25 -> pitch -3.36 deg`, `-0.25 -> pitch +1.15 deg`, roll unchanged. Restoring stiffness K = 7.76 N.m/rad (vault `finding/136`, static map n = 8). Steady-state dwell and arm pose of that probe are NOT recorded -- treat the numbers as +/-30 % until R-1 repeats them.

| Quantity | Value |
|:--|:--|
| M at u = +0.25, K x 3.36 deg | 0.0586 rad x 7.76 = **0.455 N.m** |
| M at u = -0.25, K x 1.15 deg | 0.156 N.m |
| Secant over +/-0.25 (offset cancels) | 4.51 deg / 0.5 -> 1.22 N.m per unit |
| Sim linear at u = 0.25, nominal | 0.145 x 40 x 0.25 = **1.45 N.m** (DR band 1.02-1.89) |
| Sim signed-square at u = 0.25, nominal | 0.145 x 40 x 0.0625 = **0.363 N.m** (DR band 0.25-0.47) |

Reading: at |u| = 0.25 the measured vertical moment is 0.31x the linear plant's nominal and 0.45x its DR FLOOR -- outside what the policy ever saw. It is 1.25x the sim's own signed-square curve, INSIDE that curve's DR band. The -0.25 point is lower still (T200 reverse thrust is weaker, and an unrecorded trim/dwell can explain the asymmetry; the secant removes a constant offset and gives 0.21x linear). One command level cannot separate "coefficient 3x too high" from "curve is quadratic" -- both fit u = 0.25 -- which is exactly the ambiguity R-1 at two levels resolves.

## 3. Why "lower the TAM row" is the wrong knob even if the number is right

The My row is the lever arm (0.145 m, xacro-verified to 4 decimals, finding/305). A constant scale on it fixes u = 0.25 and breaks u = 1.0, where a quadratic law equals the linear one. If the deviation is shape, the correct sim-side change already exists as a config flip: `enable_thrust_curve: true` -- with `thrust_deadband` set to 0 on the sim side, because the deployment mixer already inverts the measured ESC deadband (finding/281: the linear-through-zero plant is what makes the mixer's `undeadband` correct rather than double-counting). This is a training-plant change beyond v3.1's two knobs, and it touches all six channels, not only the vertical pair -- so it is a user decision, not an automatic edit: added as option (d) of `[DECISION-REQUIRED: vertical-moment]`.

## 4. R-1 becomes decisive, and K drops out of the decisive readout

R-1's protocol (PLAN §7) already commands u in {0, +0.25, +0.5, 0, -0.25, -0.5, 0}. Pre-registered readout:

- **ratio r = dtheta(0.5) / dtheta(0.25)** per sign, from adjacent-level differences. r ~ 2 -> linear plant, coefficient too high -> option (b) scale `thrust_coefficient` (or accept, if within the +/-30 % band). r ~ 4 -> quadratic law -> option (d) `enable_thrust_curve true` + deadband 0. r between -> report both, no automatic pick. K cancels in r, so the shape verdict does not inherit K's n = 8 uncertainty; K enters only the absolute coefficient.
- Absolute: M(u)/u at u = 0.5 vs 5.8 N.m nominal, with K's +/-? bound stated from finding/136.

Because a 3x gain gap in the pitch actuator is not something the +/-30 % coefficient DR can absorb, the recommendation for `[DECISION-REQUIRED: r1-before-final]` moves from "if the tank is available" to **yes, before Phase 3** (about 30 min of tank time, robot free-floating, thrusters otherwise 0, attitude controllers off).

## 5. Frame: closed, nothing to redo

`+x = 3 o'clock, +y = 12 o'clock (gripper), +z up`; `imu_yaw_offset +102 deg` applied consumer-side in `rotate_imu` with pitch negation, validated closed-loop on both axes (T2 92-98 %, T4 roll 98.7 %); vertical pair on +/-x = pure My, m0 probe shows pitch with roll unchanged (finding/305 §1). The only frame-adjacent operating rule stays: `thruster_sign:=[1,1,1,0,0,1]` passed explicitly every run because the launch default is identity (vault finding/060).

## 6. Does this change D-1?

Not its conclusion (pitch is the arm's job with m3 dead; reallocation drops My). It changes a number in D-1 (11.6 N.m, not 14.5) and adds a second reason the incumbent's pitch behaviour transferred badly: even with m3 alive, the policy's belief about vertical pitch authority at small commands was ~3x too high. Whether thrust ON restores usable pitch through m0 alone is still G0-H's question, on the `10-19-06` bag.
## Comments
