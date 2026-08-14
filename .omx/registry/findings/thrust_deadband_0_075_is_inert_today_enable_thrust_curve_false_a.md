---
title: "thrust_deadband 0.075 is inert today (enable_thrust_curve false) and wrong for the day it is not: the board measures 0.16 half-span, asymmetric"
tags: ["albc", "thruster", "deadband", "esc", "plant", "retrain", "sim2real", "mixer"]
created: 2026-08-14T05:33:06.787041
updated: 2026-08-14T05:33:06.787041
sources: ["trpo_iterbudget_s30_260805_012813"]
links: ["esc_deadband_and_the_six_channel_pwm_unification_that_removed_it.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-apply-before-retrain
---

# thrust_deadband 0.075 is inert today (enable_thrust_curve false) and wrong for the day it is not: the board measures 0.16 half-span, asymmetric

[FIELD-MEASURED 2026-08-12] The training config's `thrust_deadband: 0.075` is inert today and
WRONG for the day it stops being inert. The board-measured deadband is 0.16 of half-span, more
than twice the configured value.

WHY IT IS INERT NOW. The deployed teacher's `params/env.yaml` sets `thrust_deadband: 0.075` AND
`enable_thrust_curve: false`, and `marinelab/core/thruster.py:177` returns `self._state`
unchanged when the curve is off. So neither the deadband nor the signed-square curve was applied
during training -- the trained plant is linear through zero. This matters in the other direction
too: it is what makes the deployment mixer's `undeadband(D=0.15)` compensation CORRECT rather
than double-counting. A session reading only the config concluded the opposite ("the policy
learned a deadbanded plant, so the mixer over-compensates") and was wrong.

WHAT THE HARDWARE ACTUALLY DOES. ESC deadband measured on the board 2026-08-12: 1450..1545 us
against a 1500 us neutral, i.e. -0.167 / +0.150 of half-span, so about 0.16 -- and ASYMMETRIC.
The config's 0.075 traces to a comment assuming "+-25 us out of +-400 us half-span"; the measured
numbers are +-48 us out of +-300 us. Both the numerator and the denominator were wrong.

WHAT TO DO BEFORE THE NEXT RETRAIN. If `enable_thrust_curve` is turned on -- and turning it on is
the natural way to close the deployment mixer's compensation loop inside training instead of
outside it -- then `thrust_deadband` must be set from the measurement, not left at 0.075.
Training against a 0.075 deadband while the robot has 0.16 would reproduce the gap the mixer is
currently papering over, one layer deeper and harder to see. The asymmetry (-0.167 vs +0.150) has
no representation in the current scalar knob; the deployment mixer carries the same limitation
and leaves magnitudes under 0.02 dead in the negative direction (1.7 percent of span), recorded
there as a calibration-knob item.

IF THE CURVE STAYS OFF, this page is a no-op and should be left alone -- do not "fix" 0.075 to
0.16 while `enable_thrust_curve: false`, because that changes nothing and creates the false
impression that the plant now models the deadband.

SOURCE: vault `notes/2026-08-12-coordinate-frame-reconciliation-plan.md` section 9e (false-alarm
avoidance) and the board deadband measurement in
`.omx/programs/simtoreal-thrusters-live/PLAN.md` section 0g / 0i-5c.
Related: [[esc_deadband_and_the_six_channel_pwm_unification_that_removed_it]]
[CONFIDENCE: HIGH -- both the config values and the board measurement were read directly]

