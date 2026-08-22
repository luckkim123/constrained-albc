---
title: "ESC deadband is 1450..1545 us on this UUV: the vertical channels parked inside it, and thruster_order was wrong for three horizontals"
tags: ["sim2real", "thruster", "firmware", "agent-jetson", "esc", "deadband"]
created: 2026-08-14T06:46:47.752350
updated: 2026-08-14T06:46:47.752350
sources: ["vault 0_Project/in_progress/albc/.omx/programs/simtoreal-thrusters-live/PLAN.md", "agent-jetson commit 1673058"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# ESC deadband is 1450..1545 us on this UUV: the vertical channels parked inside it, and thruster_order was wrong for three horizontals

> # STOP -- CORRECTION 2026-08-13. "Defect 2" below is INVERTED.
>
> **`thruster_order = [3, 2, 4, 0, 5, 1]` is CORRECT. The `[3, 5, 4, 0, 1, 2]` that
> Defect 2 asserts is WRONG.** Read the correction section at the bottom of this page
> before using any number from Defect 2. Everything else here still stands: the deadband
> measurement, Defect 1 and its firmware fix, and the physical clock map.
>
> The premise Defect 2 rests on -- "`_ESC_CHANNEL_ORDER` is `(4,0,1,5,2,3)`, unchanged
> since `238932c`" -- is false. `3bb042b` (2026-07-14) changed it, BEFORE the 2026-08-05
> teacher. The old tuple was read from a stale container copy (`marinegym-isaaclab`);
> the SSOT is `marinelab-isaaclab`.


# ESC deadband 1450..1545 us, and the three defects it exposed

## The measurement

An ESC on this vehicle does not turn until the pulse leaves **1450..1545 us** (half-width about
48 us). The number is pinned because **two channels with different span AND bias broke away at
exactly 1545 us**: m2 (horizontal, span 300, bias 0) at `a=+0.15`, and m0 (vertical, span 150,
bias 30) at `a=+0.50`. `pwm = 1500 - bias + a*span`.

[EVIDENCE: dry channel sweeps, `b1_channel_probe.py _channel:=N _level:=L`, operator watching
for sustained rotation rather than twitching]
[CONFIDENCE: HIGH]

## Defect 1 -- the vertical channels parked INSIDE the deadband

`DEPTH_BIAS=30` put the RL path's zero command at **1470 us**, only 20 us from the lower edge.
Publishing **all-zero** thrust still made m0 twitch continuously -- so the policy's "zero
thrust" was not zero on the real vehicle. That is a plant bias absent from training.
It also cost half the positive authority (`a>=0.50` to break away, vs `a<=-0.13` negative).

Fix (`agent.ino`, flashed): **all six channels now use span 300, ESC_MIN/MAX, bias 0.** The sim
gives all six thrusters the same `max_thrust=50.0`, so the firmware must too; the narrow
vertical span was a debt the code's own comment had flagged. The classic depth PID
(`pid.cpp:77-81`) still uses `DEPTH_BIAS` and was not touched.

Verified in both directions after flashing: all-zero -> m0 **completely still**; m0 at `+0.20`
-> **spins cleanly** (it needed 0.50 before). Opposite-direction predictions, both confirmed.

## Defect 2 -- `thruster_order` was wrong for three horizontals

Correct value: **`[3, 5, 4, 0, 1, 2]`** (`order[j]` = sim index feeding fw channel j).
The 2026-08-11 value `[3, 2, 4, 0, 5, 1]` came from mis-remembering `_ESC_CHANNEL_ORDER` as
`(4,1,3,5,2,0)`; the repo value is `(4,0,1,5,2,3)`, unchanged since `238932c` (2026-07-03),
so it is what the 2026-08-05 teacher trained on. **Established from git log, not the working
tree** -- a working tree cannot tell you what a checkpoint was trained with.

Physical map (gripper at 12 o'clock): m0=3h vert, m1=1:30, m2=4:30, m3=9h vert (**DEAD**),
m4=7:30, m5=10:30. Sim columns from `actuators.xacro` with `+x=3h`: col0=T4 9h, col1=T0 7:30,
col2=T1 10:30, col3=T5 3h, col4=T2 4:30, col5=T3 1:30.

**Why nothing caught it:** `Mz = +0.144` for **all four** horizontals, so any permutation of
them yaws identically -- a yaw observation cannot detect the error even in principle. The
startup axis assertion only guards the vertical/horizontal split, which the wrong order
respected. And `thruster_scale` defaults to 0.0, so every recorded field-test bag carries
`thruster_pwm == 0`. Three safety layers, all blind to this one fault. Only `Fx`/`Fy`
(translation) separate the horizontals.

## Defect 3 -- m3 is genuinely dead, re-confirmed under valid conditions

The original "m3 dead" call was made while the 1470-us creep was contaminating observations,
and under a firmware where m3 needed `a>=0.50` to break away at all. Re-tested after the flash
(threshold now 0.15) at `+0.30`, `-0.30`, `+0.70`: no response. Hardware failure confirmed.

Heave authority vs the sim's two-thruster assumption: was about **1/6** (half span, 30 %
deadband, one motor), now about **1/2** (structural, one motor gone). The deployed teacher
trained with `fault: enable: true`, `thruster_fail_prob=0.1`,
`thruster_health_range=(0.0, 0.5)`, so a dead thruster is inside the training distribution.

## Compensation lives in the mixer, not the firmware

`thruster_mixer.py` gained `~thruster_deadband` (default 0.15) applying
`out = sign(a) * (D + (1-D)*|a|)`, so `a=0` stays exactly neutral and `a=+-1` keeps full
authority. Kept in Python so it is tunable without a reflash. It **presupposes** the
2026-08-12 firmware; on older firmware the verticals are asymmetric and one scalar cannot
express them -- run with `~thruster_deadband:=0.0` until reflashed.

## Bonus: this firmware build IS reproducible

`BUILD_AND_FLASH.md` claimed byte-identical rebuilds were impossible. False: the same commit
built on 2026-07-03 and 2026-08-12 gave **identical md5** (`5f20e09b...`, 38124 flash bytes).
So verify with a **control build** of the pre-change commit, and confirm what is on the chip
with `avrdude -U flash:v:<control>.hex:i` (read-only). That check passed, ruling out the
"chip ahead of git" failure mode that broke teleop conventions in July.
Count flash bytes from the data records, not the hex file's text size.

---

## CORRECTION 2026-08-13 -- Defect 2 above is INVERTED. Do not use its number.

**`thruster_order = [3, 2, 4, 0, 5, 1]` is correct. `[3, 5, 4, 0, 1, 2]` (asserted above) is WRONG.**
Defect 2 has it exactly backwards and carries an authority phrase ("Established from git log, not
the working tree") that makes it read as settled. It is not.

WHY IT IS WRONG. Its premise -- "`_ESC_CHANNEL_ORDER` is `(4,0,1,5,2,3)`, unchanged since
`238932c` (2026-07-03), so it is what the 2026-08-05 teacher trained on" -- is false.
`3bb042b` (2026-07-14) changed it to `(4,1,3,5,2,0)`, which is BEFORE the 2026-08-05 teacher.
The old tuple came out of a STALE CONTAINER COPY (`marinegym-isaaclab`, a separate checkout that
lags; SSOT is `marinelab-isaaclab`). "I checked git log" is no defence when the checkout is wrong.

HOW THE CORRECT VALUE IS OBTAINED -- never read it from a constant.
`test_deploy_constants.py` recomputes it from `deployed_tam.json`'s `allocation_matrix` via
`M = r x F`, resolves each column's physical clock position (unique on the +-0.102 grid), matches
it against the measured channel map, and asserts three-way agreement between the JSON, the
derivation, and `thruster_mixer.DEFAULT_ORDER`. All three read `[3, 2, 4, 0, 5, 1]`.

ALSO STALE HERE. "`Mz = +0.144` for **all four** horizontals, so any permutation of them yaws
identically" held only for the PRE-`3bb042b` matrix. The deployed matrix splits 2-2
(col1,4 = -0.144 / col2,5 = +0.144), so a wrong horizontal permutation DOES yaw wrong. Yaw is a
usable discriminator now, not a blind spot.

STILL CORRECT: the deadband measurement (1450..1545 us), Defect 1 and the firmware fix
(six channels, span 300, bias 0), and the clock map (m0=3h, m1=1:30, m2=4:30, m3=9h DEAD,
m4=7:30, m5=10:30).

[EVIDENCE: `deployed_tam.json` + `test_deploy_constants.py` three-way assertion;
`albc_rl_fieldtest.launch:69`; `thruster_mixer.py:157`; agent-jetson HEAD 6b962be]
[CONFIDENCE: HIGH]

RECATEGORISED 2026-08-14: this page was originally hand-written with `category: sim2real`, a value omx_core's CATEGORIES rejects, so it had never passed through `omx wiki add`. Re-added through the CLI at the same slug with category=reference. Body preserved verbatim.
