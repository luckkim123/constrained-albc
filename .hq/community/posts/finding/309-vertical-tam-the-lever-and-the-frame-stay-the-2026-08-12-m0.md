# Vertical TAM: the lever and the frame stay; the "3x gap" is RETRACTED (unit error -- the m0 probe was RAW, effective u=0.1176, ratio 0.67x at the DR floor), and R-1 (2026-09-03) found neither pre-registered law but a shifted origin -- the absolute coefficient now hinges on net buoyancy B, which is the next probe

- id: finding/309 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: medium · status: needs-experiment
- verified: partial · keywords: vertical-tam, thrust-curve, thrust_coefficient, m0, R-1, retrain-simtoreal-2026-09, frame
- summary: CORRECTED 2026-09-03 (twice). (a) The 3x/0.31x vertical-moment gap is RETRACTED as a unit error: the 08-12 m0 probe used b1_channel_probe.py, which publishes RAW commands with the mixer bypassed, so raw 0.25 is effective u=0.1176 (undeadband D=0.15) -- the measured 0.455 N.m is 0.67x the linear nominal 0.682 N.m, at the coefficient-DR floor (0.7,1.3), and 5.7x the signed-square curve, not the other way round. (b) R-1 ran 2026-09-03 (vault finding/144): the PLAN section 7 settled-tilt protocol is UNEXECUTABLE on this robot -- m3 dead means m0 is the only vertical channel, reallocate() turns every command into net heave, and both + steps clamped at 0.205 m and both - steps at 0.890 m with doubling the thrust changing neither. Replacement readout (terminal descent rate, 9/9 steps, R2 0.988-0.996, free rise 0.0230 m/s pins B=c*v_rise^2 so drag cancels): the law fits NEITHER pre-registered option -- not curvature but a shifted origin, T ~ (u-delta) with delta ~ 0.11-0.14 linear above it (T=15.5*u^1.0 N). That residual deadband undercuts option (d) premise (finding/281 assumed the mixer fully inverts the ESC deadband). Absolute coefficient is undecided and thruster levels are no longer the lever: B=0.53 (free-rise fit) gives 0.39x, vault finding/136 B=1.07 gives 0.78-0.86x INSIDE the DR band -- a FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly) is now the deciding probe. Also identified: (m+m_a)=52.0 kg (added mass 41.7 on 10.3 dry), c=1000 N.s2/m2. Also retracted: rev1 +20.2 deg/s yaw was wall reaction. Frame, lever 0.145 m, 40 N constant, D-1 conclusion all stand.
Answer to the user's 2026-09-03 question "does the vertical TAM need lowering, and is the frame fine as-is?". Frame: nothing to change. Lever: nothing to change. The magnitude claim this post originally made has been **corrected twice on 2026-09-03** — once for a unit error found at the desk, once by R-1 actually running. Both corrections are in §0; the rest of the post is the surviving record.

## 0. Two corrections to this post (2026-09-03, tank session)

### 0a. RETRACTED — the "0.31× / ~3× gap" was a unit error, not a measurement

The 2026-08-12 m0 probe ran through `b1_channel_probe.py`, which publishes **raw ESC
commands with the mixer bypassed** (`deployed_tam.json._what`; vault PLAN §2b-0). A raw
command is not a policy command. The mixer's `undeadband` maps a policy command `u` to
`raw = sign(u)·(D + (1−D)|u|)` with `D = 0.15` (vault `finding/077`), so:

    raw 0.25  <=>  u_eff = (0.25 − 0.15) / 0.85 = 0.1176

This post compared a raw-0.25 measurement against the sim's nominal **at u = 0.25**. That
is a factor of 2.1 in the command axis, and it is the whole of the "3× gap".

| | old (wrong) | corrected |
|:--|--:|--:|
| command the probe actually applied | u = 0.25 | **u = 0.1176** |
| sim linear nominal there | 1.45 N·m | **0.682 N·m** |
| measured 0.455 N·m → ratio | 0.31× | **0.67×** |
| secant over ±raw 0.25 (Δu_eff = 0.235) | 0.21× | **0.45×** (2.60 N·m/unit) |

0.67× sits **at the coefficient-DR floor** (`thrust_coefficient_scale (0.7, 1.3)`), not 3×
below it. Every downstream sentence that read "outside the DR band, so Phase 3 would train
on a channel the record says is wrong" loses its arithmetic. The R-1 *recommendation*
survives — see §0b, which is a stronger reason than the one it replaces.

### 0b. R-1 ran (2026-09-03). The §7 protocol was unexecutable; the readout was replaced

Full record: vault `finding/144` (+ its comment carrying the identification).

**The settled-tilt protocol cannot run on this robot.** With m3 dead, m0 is the only
vertical channel, so `reallocate()` turns every vertical command into net **heave** — the
robot leaves the depth band before tilt settles. Measured: both `+` steps clamped at depth
0.205 m and both `−` steps at ~0.890 m, and **doubling the thrust changed neither**. The
first run's `r(+) = 0.98` was a boundary reaction, not a plant property. This is structural,
not a dwell-tuning problem: §7's "discard a level if depth changes > 0.3 m" discards every
level.

**Replacement readout: terminal descent rate, down-only.** 3 levels × 3 repeats, 9/9 steps
accepted, per-step linear fit R² 0.988–0.996:

| u | v_descent (m/s) |
|--:|--:|
| 0.251 | 0.0495 |
| 0.375 | 0.0766 |
| 0.500 | 0.0877 |
| free rise (no thrust) | 0.0230 ± 0.0040 |

Measuring the free rise is what makes this decisive: it pins `B = c·v_rise²`, so the drag
coefficient **cancels in every ratio** and the shape verdict does not inherit a drag
estimate.

**Shape: neither pre-registered option.** Adjacent ratios 2.147 / 2.756 / 1.283 against
linear 1.494 / 1.992 / 1.333 and quadratic 2.232 / 3.968 / 1.778 — no single power law fits.
The joint identification says the deviation is not curvature but a **shifted origin**:
`T ∝ (u − δ)` with **δ ≈ 0.11–0.14**, above which the law is linear (`T = 15.5·u^1.0` N,
rms depth residual 0.0134 m against ~0.010 m quantisation). Only the lowest level misses
(+17 %); the upper two are within 3–5 %.

> **This weakens option (d)'s premise.** (d) sets the sim's `thrust_deadband` to 0 *because*
> the deployment mixer already inverts the ESC deadband (`finding/281`). A residual
> δ ≈ 0.12 on top of the mixer's `D = 0.15` says that inversion is incomplete. (d) should
> not be selected until δ is either explained or compensated.

**Absolute coefficient: undecided, and thruster levels are no longer the lever.**
`T = 15.5 N/unit` → My/unit = 0.145 × 15.5 = **2.25 N·m** = **0.39×** the sim's 5.8, outside
the DR band. But that rests entirely on `B`: the fit pins `B = 0.53 N` from the free rise,
while vault `finding/136` measured net buoyancy **1.07 N** — exactly 2×. With B = 1.07 the
scale becomes **0.78–0.86×** (joint transient fit vs terminal balance), **inside** the
(0.7, 1.3) band, and no coefficient change is warranted at all.

    B = 0.53  ->  0.39x        (outside DR)
    B = 1.07  ->  0.78-0.86x   (inside DR)

So `[DECISION-REQUIRED: vertical-moment]` **cannot be read from R-1**. The deciding probe is
a **FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly)**, not more thruster levels. Note the 08-12 probe's corrected
0.45–0.67× (§0a) brackets both candidates and separates neither.

**By-product identification** (9 dives, 1071 depth samples): `(m + m_a) = 52.0 kg` → added
mass **41.7 kg** on a 10.3 kg dry body (plausible for a wide open frame in heave); drag
`c = 1000 N·s²/m²` at B = 0.53.

**Also retracted:** the first run reported "the vertical thruster produces large yaw
(+20.2 °/s)". The rev2 runs show −0.4 to −4.9 °/s. The rev1 yaw was most likely wall
reaction — the run was stopped because the robot was contacting a wall.

### 0c. What did NOT change

The frame (§5), the lever 0.145 m, the `40 N` sim constant, D-1's conclusion, and the
11.6 N·m pair figure all stand. §1 below is verified source reading and is untouched.

### 0d. Correction (2026-09-03 21:40): B was never measured directly

The operator pointed out that a submerged weighing *was* done. It was -- but only of half
the assembly, and that changes what the open probe is.

| quantity | value | how |
|:--|--:|:--|
| hull (buoy excluded), in air | 101.37 N | weighed |
| hull, submerged | **15.55 N** | **weighed submerged -- a direct measurement** |
| buoy net buoyancy | 16.62 N | **NOT weighed** -- cylinder approximation (65x20 + 200x65 mm) minus 0.410 kg |
| assembly B | **+1.07 N** | the **difference** of the two above |

So B is a difference of two ~16 N numbers. A **3.2 % (0.54 N) error in the buoy term alone
turns 1.07 into 0.53** -- which means R-1's free-rise fit of 0.53 N is **not a refutation of
1.07, it is inside the error bar**. Vault `finding/136` flags the weakness itself: "the volume
is a cylinder approximation ... remeasure by displacement if precision is needed."

Therefore the open item is not a *re*-measurement, it is the **first direct one**. And it does
not have to be a hanging weigh: the robot is slightly positively buoyant, so hanging it
requires adding lead (operator, 2026-09-03). Two cheaper routes:

- **(A) bottom-tethered scale** -- anchor a line from the tank floor to the robot through a
  0-500 gf scale; it reads the upward force, i.e. **B directly**. No lifting, no lead.
- **(B) known weight + two rise rates** -- attach one weight of known mass and repeat the
  free rise. `B / (B - dW) = (v1/v2)^2` separates B from drag with **no scale at all**, and
  reuses R-1 rev2's exact procedure and tooling.

Either way the decision-9 fork (0.39x outside DR vs 0.86x inside) closes on one measurement.

---

*(Original body follows, with the §2 ratio column superseded by §0a and the §4 readout
superseded by §0b.)*

## 1. What the training plant assumes (verified at HEAD 81c2ec0, 2026-09-03)

- `constrained_albc/envs/main/config.py:140-141`: `max_thrust 50.0`, `thrust_coefficient 40.0`. Thrust = command x 40 N, LINEAR (finding/283 measured the same on 2026-07-29). The 50 N is a clamp, so the "0.145 m x 50 N" in PLAN v3.1 §2/§3 and the "14.5 N.m" in D-1 are the wrong constant: nominal vertical moment per unit command is 0.145 x 40 = **5.8 N.m**, pair 11.6 N.m.
- DR (`deployed_env.yaml:480-488`): `thrust_coefficient_scale (0.7, 1.3)` -> the coefficient the policy trained against is U(28, 52) N per unit; `max_thrust_scale (0.85, 1.15)` scales only the clamp. PLAN v3.1 §5 listed only the clamp band; the +/-30 % coefficient band exists and matters below.
- Curve: `marinelab/core/thruster.py:164-182` -- with `enable_thrust_curve false` the map is the identity; with `true` it is deadband (`|s| < thrust_deadband` -> 0) then `sign(s) * s**2`. Incumbent trained with `false` (finding/281).

## 2. What the tank already measured

`deployed_tam.json.measured_thruster_sign.m0` / vault `finding/077` (tank 2026-08-12): m0 `+0.25 -> pitch -3.36 deg`, `-0.25 -> pitch +1.15 deg`, roll unchanged. Restoring stiffness K = 7.76 N.m/rad (vault `finding/136`, static map n = 8). Steady-state dwell and arm pose of that probe are NOT recorded -- treat the numbers as +/-30 % until repeated.

⚠️ **The command column below is RAW, not effective — see §0a.**

| Quantity | Value |
|:--|:--|
| M at raw = +0.25, K x 3.36 deg | 0.0586 rad x 7.76 = **0.455 N.m** |
| M at raw = -0.25, K x 1.15 deg | 0.156 N.m |
| Secant over +/-raw 0.25 (offset cancels), per **effective** unit | 4.51 deg over du_eff 0.235 -> **2.60 N.m/unit** |
| Sim linear at u_eff = 0.1176, nominal | **0.682 N.m** (DR band 0.48-0.89) |
| Sim signed-square at u_eff = 0.1176, nominal | **0.080 N.m** |

Reading (corrected): at the command the probe actually applied, the measured vertical moment
is **0.67x the linear plant's nominal** -- at the DR floor -- and **5.7x the sim's
signed-square curve**, far outside that curve's band. The original reading had these the
other way round, which is what made "the law is quadratic" look like the leading hypothesis.
R-1 (§0b) then found the law is linear above a residual deadband, consistent with this
corrected direction.

## 3. Why "lower the TAM row" is the wrong knob even if the number is right

The My row is the lever arm (0.145 m, xacro-verified to 4 decimals, finding/305). A constant scale on it fixes one command level and breaks another. If the deviation is shape, the correct sim-side change already exists as a config flip: `enable_thrust_curve: true` -- with `thrust_deadband` set to 0 on the sim side, because the deployment mixer already inverts the measured ESC deadband (finding/281). This is a training-plant change beyond v3.1's two knobs, and it touches all six channels, not only the vertical pair -- so it is a user decision, not an automatic edit: added as option (d) of `[DECISION-REQUIRED: vertical-moment]`. **See §0b: R-1 found a residual deadband delta ~ 0.12 that undercuts this option's premise.**

## 4. R-1: what it was for, and what it actually delivered

⚠️ **The protocol below did not survive contact with the robot -- see §0b.** Kept for the
record because the *identifiability* reasoning (K cancels in a ratio) is what made the
replacement readout correct too: the free-rise measurement makes the drag coefficient cancel
the same way.

R-1's protocol (PLAN §7) commanded u in {0, +0.25, +0.5, 0, -0.25, -0.5, 0}. Pre-registered readout:

- **ratio r = dtheta(0.5) / dtheta(0.25)** per sign. r ~ 2 -> linear plant, coefficient too high -> option (b). r ~ 4 -> quadratic law -> option (d). K cancels in r.
- Absolute: M(u)/u at u = 0.5 vs 5.8 N.m nominal.

**Outcome: neither branch fired.** The tilt never settles (heave boundary), and when the
readout was moved to descent rate the ratios matched no single power law. The decision moved
to a different probe entirely (net buoyancy).

The recommendation for `[DECISION-REQUIRED: r1-before-final]` **stays yes**, but on the
corrected ground: not "a 3x gap outside the DR band" (retracted, §0a) but "the vertical
channel's absolute coefficient is unresolved between 0.39x and 0.86x and the deciding
measurement has not been made."

## 5. Frame: closed, nothing to redo

`+x = 3 o'clock, +y = 12 o'clock (gripper), +z up`; `imu_yaw_offset +102 deg` applied consumer-side in `rotate_imu` with pitch negation, validated closed-loop on both axes (T2 92-98 %, T4 roll 98.7 %); vertical pair on +/-x = pure My, m0 probe shows pitch with roll unchanged (finding/305 §1). The only frame-adjacent operating rule stays: `thruster_sign:=[1,1,1,0,0,1]` passed explicitly every run because the launch default is identity (vault finding/060).

## 6. Does this change D-1?

Not its conclusion (pitch is the arm's job with m3 dead; reallocation drops My). It changes a number in D-1 (11.6 N.m, not 14.5). The second reason it once added -- "the policy's belief about vertical pitch authority at small commands was ~3x too high" -- is **retracted** (§0a); the honest version is that the belief is off by somewhere between 1.0x and 2.6x, and B decides which. Whether thrust ON restores usable pitch through m0 alone was G0-H's question, and G0-H closed on 2026-09-03 (vault `finding/143`): realized My is pinned at `-0.145 x Fz` in all 7 segments, so m0 cannot serve pitch independently of heave at all -- which is also why R-1's settled-tilt protocol was unexecutable.

## Comments
- (2026-09-03, session-mac) 정정: two corrections on 2026-09-03: (a) the 0.31x/3x gap was a unit error -- the 08-12 m0 probe published RAW 0.25 with the mixer bypassed, which is effective u=0.1176, so the ratio is 0.67x at the DR floor, not 0.31x; (b) R-1 ran and its settled-tilt protocol proved unexecutable (m3 dead -> every vertical command is net heave -> depth boundary before settling), so the readout was replaced by descent rate: law is linear above a residual deadband delta~0.12, and the absolute coefficient is 0.39x or 0.78-0.86x depending on net buoyancy B, which is now the deciding probe
