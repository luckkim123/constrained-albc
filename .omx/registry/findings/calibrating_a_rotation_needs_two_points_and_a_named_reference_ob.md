---
title: "Calibrating a rotation needs TWO points and a NAMED reference object -- the ALBC J1 zero moved four times in one day for want of both"
tags: ["sim2real", "calibration", "agent-jetson", "arm", "measurement-discipline"]
created: 2026-08-14T06:46:47.666657
updated: 2026-08-14T06:46:47.666657
sources: [".omx/programs/simtoreal-thrusters-live/PLAN.md"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Calibrating a rotation needs TWO points and a NAMED reference object -- the ALBC J1 zero moved four times in one day for want of both

The ALBC arm's J1 Homing Offset was rewritten **four times on 2026-08-12** and landed back
on the value it already had. Every wasted step traces to one of two omissions.

## Final state (three independent observations agree)

`Homing Offset(20) = -1509` for Dynamixel ID 11. With it:

| J1 reading | link1 azimuth observed | residual |
|---|---|---|
| 2287 tick = 201.0 deg | ~8 o'clock (~200 deg) | ~0 deg |
| 509 tick = 44.7 deg | 1:30 (45 deg) | **0.3 deg** |
| 1 tick = 0.1 deg | 3 o'clock (0 deg) | ~0 deg |

`joint1 = 0 => link1 along +x` (agent.urdf) plus link1 observed at 3 o'clock therefore gives
**`+x = 3 o'clock`** with the IMU nowhere in the chain -- a stronger closure of the +-180
question than the morning's IMU-mediated one.

Rotation sense is CCW-positive, matching the URDF `axis (0,0,1)` right-hand rule: J1 +90 deg
moved link1 from 4:30 to 1:30, i.e. +90 deg of azimuth.

[EVIDENCE: `dxl_abs.py 11 0` / `11 1024` with J2 held at pi/2 (1025 tick), torque on, operator
reading the clock face against the gripper at 12 o'clock]
[CONFIDENCE: HIGH]

## Omission 1 -- every earlier check was a SINGLE point

One observation cannot separate a **zero-offset** error from a **direction (sign)** error; both
predict "the arm is not where I expected". Three successive calibrations (-1029, -2908, -1509)
were each derived from one absolute reading, so the ambiguity survived each time and the
confirmations felt real. Two points at 90 deg separate the unknowns: direction comes from the
**difference**, zero from the **common residual**, and the operator's eyeball error cancels out
of the difference entirely.

Worse, the morning's confirmation was a multiple-choice question with ~60-deg-wide bins. A hit
inside a wide bin was read as agreement; the true prediction was later found ~2 clock-hours off.

## Omission 2 -- "the arm direction" named two different objects

The operator and the analysis both said "arm direction" while meaning different things: the
analysis meant **link1** (whose azimuth IS J1, by the URDF), the operator meant the **buoy /
EE** (whose azimuth is set by J1 **and** J2 together). The buoy reading produced a spurious
45-deg correction, an EEPROM write to -2021, and a revert.

The buoy is not a valid proxy for link1: joint2 is an elbow, so link2 swings in the vertical
plane containing link1, and once folded far enough the EE's horizontal projection crosses the
joint1 axis and its azimuth flips by 180 deg. At the bad measurement J2 was at **236.8 deg with
torque OFF** -- hanging where the previous run left it, not the pi/2 deployment pose.

[EVIDENCE: `dxl_read_homing.py` showed `ID 12 present=+2694 tick (+236.78 deg) torque=0` at the
time of the buoy observation; after `dxl_abs.py 12 1024` the link1 reading agreed to 0.3 deg]
[CONFIDENCE: HIGH]

## Also true, and it is why calibration errors kept leaking

Every earlier arm calibration was measured **through the IMU** (raw -> `rotate_imu(theta)` ->
tilt azimuth -> "the arm points there" -> set homing). That chain inherits the IMU's own error,
which was itself wrong by 123 deg until this morning. Repeating a measurement that shares an
instrument does not reduce its systematic error -- it only raises confidence in a wrong number.
Today's decisive measurement removed the IMU from the loop entirely by comparing link1 to the
**gripper**, a mechanical reference.

## Protocol to use next time

1. **Name the reference object in writing** before measuring ("link1", not "the arm").
2. Put every other joint in a **known, torque-held** pose first -- record its encoder value.
3. Measure at **two commanded points 90 deg apart**; report both.
4. Prefer a reference that does **not** share an instrument with the thing being calibrated.
5. Never confirm with a wide multiple-choice bin; ask for the observed value.

RECATEGORISED 2026-08-14: this page was originally hand-written with `category: sim2real`, a value omx_core's CATEGORIES rejects, so it had never passed through `omx wiki add`. Re-added through the CLI at the same slug with category=convention. Body preserved verbatim.
