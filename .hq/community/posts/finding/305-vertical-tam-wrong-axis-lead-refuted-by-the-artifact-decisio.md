# Vertical-TAM wrong-axis lead REFUTED by the artifact; decision/197 HARD-GATE re-scored: item 3 closed robot-side by measurement, item 2 reduces to an unmeasured moment magnitude, item 4 moment-arm still open

- id: finding/305 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: needs-experiment
- verified: none · keywords: tam, vertical, pitch, hard-gate, imu, frame, retrain
- summary: handoff/304 lead refuted: deployed_tam.json puts the vertical pair on +-x (3h/9h) with My, m0 tank probe gives pitch with roll unchanged, config->deployed column map byte-equal, T4 command frame = sim frame. finding/137 D-1 survives. HARD-GATE: 1 applied, 2 premise refuted (magnitude unmeasured), 3 closed robot-side (+102 deg, T2/T4), 4 max_thrust applied / moment-arm open. Incumbent fault_severity hit Beta(1,1) at iter 7748 (artifact read).

Session 2026-09-03 (Mac, Fable 5.1), re-planning the retrain from primary sources after the user rejected the frozen PLAN ("내가 지적할때마다 주장을 바꾸는 것 보니 근거가 부족"). This post closes the TOP-PRIORITY item that `handoff/304` left open and re-scores the `decision/197` HARD-GATE table against the artifacts. Every claim below names the file it rests on.

## 1. The "wrong axis" lead is REFUTED by the artifact

`handoff/304` inferred from the clock positions that a 3-o'clock/9-o'clock vertical pair is "left-right", so its differential moment should be roll (Mx), and the sim's `My = ±0.145` would be on the wrong axis. Read directly today:

- `deployed_tam.json.measured_channel_map._frame`: "+x = 3 o'clock, +y = 12 o'clock (gripper), +z = up (right-handed)". m0 = 3.0 h vertical ok; m3 = 9.0 h vertical DEAD.
- `deployed_tam.json.allocation_matrix` (columns = sim action index): Fz = [1,0,0,1,0,0], My = [+0.145, −0.007, −0.007, −0.145, +0.007, +0.007]. `expected_thruster_order = [3,2,4,0,5,1]` (fw m0 ← col3, fw m3 ← col0).
- Physics in that frame: a vertical thruster at r = (+0.145, 0, 0) with F = (0, 0, Fz) gives M = r × F = (0, −0.145·Fz, 0) — pure My, negative for up-thrust at +x. That is col3 exactly; col0 is its mirror at −x. So the sim already places the vertical pair on the ±x axis = 3 h / 9 h, where the robot has m0 / m3. **No axis mismatch.** "Left-right ⇒ roll" is a naming artifact of the wasd frame (forward = 6 o'clock) that `finding/255` used in July; in the sim frame the same physical rotation is pitch about +y.
- Measured confirmation: `deployed_tam.json.measured_thruster_sign.m0.basis` (tank 2026-08-12): "+0.25 → pitch −3.36 deg (3 o'clock rises) … a clean reversal with **roll unchanged** (no Mx, as expected for a thruster on the x axis)". Right-hand rule about +y with a negative angle raises the +x side — sign and axis both match.
- Column mapping config → deployed → policy action: `_BASE_ALLOCATION_MATRIX` My row (0.007, −0.007, 0.007, −0.007, 0.145, −0.145) reordered by `_ESC_CHANNEL_ORDER = (4,1,3,5,2,0)` (`decision/253` Update 2026-07-14) gives [0.145, −0.007, −0.007, −0.145, 0.007, 0.007] — byte-equal to the deployed My row; `decision/253` establishes `action[:, 2+j] → TAM column j`, so the policy's vertical actions are columns 0 and 3 = m3 and m0.
- Command frame of T4 (`finding/137`): `build_proprio.py:33` `err = cmd − measured`; `:245–250` stacks `cmd_att` and `euler` in the same vector, and `euler` is the `rotate_imu` (+102°, pitch-negated) output — command and measurement share the sim frame by construction, so T4's "pitch step" is a sim-frame pitch step.

Cross-vendor check (codex `gpt-5.6-terra`, ground 4, adversarial): upheld D1–D3 (cross product, right-hand rule, axis naming, measured sign) and rejected the reverse-axis reading; its two open objections — the config↔deployed column mapping and the T4 command frame — are the last two bullets above, closed from `decision/253` + arithmetic and from `build_proprio.py`. Its residual point stands and is recorded below: no end-to-end action-routing test with thrusters ON has ever been analyzed.

**Consequence:** `finding/137` D-1 (the incumbent learned sim-frame pitch from the vertical thrusters, 14.5 N·m vs 2.2 N·m arm) SURVIVES. The retrain's pitch justification is not voided.

## 2. HARD-GATE (`decision/197`) re-scored on 2026-09-03

| # | Item | Status today | Evidence |
|:--|:--|:--|:--|
| 1 | Horizontal TAM 3-row rewrite + ESC permutation | APPLIED, incumbent trained on it | `decision/253` Update 07-14 (`3bb042b`); `vault:finding/077` (deployed 2026-08-05 after `3bb042b`) |
| 2 | Vertical Fz/My "single-motor, left-right" redesign | **PREMISE REFUTED** — two motors (`finding/255` correction 2026-08-13), sim placement ±x is correct (§1), Fz = 1.0 per channel is right for two motors. What survives is **the MAGNITUDE of the vertical moment (0.145 m lever × 50 N nominal) — never measured** (`finding/240`: "TAM roll/pitch arm + thrust curve = measurement IMPOSSIBLE without a load cell"). | This post §1; `vault:finding/137` §7(2): "실제 값이 얼마인지는 아무도 안 쟀다" |
| 3 | IMU 45° mounting offset + pitch negation, sim-uncompensated | **CLOSED ON THE ROBOT SIDE, by measurement.** The offset is +102° not 45° (`vault:finding/073`, three independent lines, 2026-08-12); the consumer-side `rotate_imu` maps IMU → sim body frame and the sim consumes ground truth in that same frame, so a sim-side transform would be redundant. Validated in closed loop on both axes: TDC pitch steps 92–98 % (`vault:finding/134`, 09-02), RL roll step 98.7 % in the pre-registered direction (`vault:finding/137`, 09-02). The 2026-07-20 intent "apply to sim after measuring on the robot" is satisfied by the equivalent consumer-side mapping. **Record for any retrain: baseline is post-IMU-frame (robot-side), sim unchanged by design.** | `finding/154` (the 07-20 decision: measure first, then apply); `vault:finding/073`; `vault:finding/134`; `vault:finding/137` |
| 4 | TAM moment-arm + max_thrust DR band | max_thrust band **APPLIED** (`deployed_env.yaml:randomization.max_thrust_scale = (0.85, 1.15)`); moment-arm band **NOT applied** — no per-env allocation-matrix DR exists (`_reset_physics` randomizes thrust-coeff / time-const / max-thrust only, `handoff/303`). Stays OPEN; its value depends on the same unmeasured magnitude as item 2. | `deployed_env.yaml`; `decision/155`; `handoff/303` |

Two knock-on corrections:
- `decision/140`'s reason for evaluating m4-ONLY ("a vertical kill would manufacture fake pitch loss because the real robot has one motor") is void — the robot HAS two vertical motors and one of them (m3) IS dead. Vertical-channel faults belong in the fault exam matrix; `1,1,1,0,0,1` is the robot that exists.
- The incumbent's `fault_severity` curriculum reached Beta(1,1) at iteration 7748 — read today from `trpo_iterbudget_s30_260805_012813/curriculum_trajectory.json` (a=1.000, b=1.000 from iter 7748 through 9998; mean 0.1056 at 5248). The "6–8 % of range" figure belongs to the 5k fault-DR arms, not to the incumbent. Exposure arithmetic for the retrain must start from severity = 1.

## 3. What this does NOT close (carried as open items)

- The vertical moment MAGNITUDE. A load cell is not available, but an indirect static measurement is: hold m0 at 2–4 command levels (deadband-compensated through the mixer), read the steady pitch tilt θ, and take M = K·θ with K = 7.76 N·m/rad from `vault:finding/136`. That gives the effective N·m per unit command without a bench. Robot experiment candidate under the user's constraint 3.
- End-to-end action routing with thrusters ON. All quantitative T4 analysis rests on the joint-only bag `09-39-17`; the thrust-ON repeat of the same staircase, `10-19-06` (145 s, `thruster_sign [1,1,1,0,0,1]`), is unanalyzed (`vault:finding/137` §12). It is the cheapest test of "thrust ON does not restore pitch" (§5 of that finding) and needs only the board and `~/albc_diag/t4_step_analyze.py`. Board was unreachable from the Mac on 2026-09-03 12:40.
## Comments
