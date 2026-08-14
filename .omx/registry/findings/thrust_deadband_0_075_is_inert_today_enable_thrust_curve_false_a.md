---
title: "thrust_deadband 0.075 is inert today (enable_thrust_curve false) and wrong for the day it is not: the board measures 0.16 half-span, asymmetric"
tags: ["albc", "thruster", "deadband", "esc", "plant", "retrain", "sim2real", "mixer", "conditional-gate"]
created: 2026-08-14T05:33:06.787041
updated: 2026-08-14T07:51:11.190550
sources: ["trpo_iterbudget_s30_260805_012813", "wiki-curation-2026-08-14", "wiki-backlog-20260814"]
links: ["esc_deadband_and_the_six_channel_pwm_unification_that_removed_it.md", "esc_deadband_is_1450_1545_us_on_this_uuv_the_vertical_channels_p.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-apply-before-retrain
blocked-on: "conditional: fires only if enable_thrust_curve is turned on. Verified still False 2026-08-14, so the no-op condition currently HOLDS and nothing is invalidated today"
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

---

## Update (2026-08-14T06:48:12.231927)

LINK REPAIR 2026-08-14. This page's ESC-deadband reference pointed at the slug
`esc_deadband_and_the_six_channel_pwm_unification_that_removed_it`, which no longer exists. That page
was hand-written with an invalid `category: sim2real` AND a filename that did not match its own title,
so the 2026-08-14 curation re-created it through the CLI at its correct title-derived slug:

[[esc_deadband_is_1450_1545_us_on_this_uuv_the_vertical_channels_p]]

Content is unchanged and the 2026-08-13 STOP/CORRECTION header is preserved. The stale link above
cannot be removed (the `links` field unions on merge and is never rewritten), so this note is the
repair -- follow the slug in this block, not the one in the earlier body.

STATUS UNCHANGED: still needs-apply-before-retrain. Nothing in this repair touches the underlying
finding, which is that the sim deadband constant and the board's measured half-span disagree.

---

## Update (2026-08-14T07:51:11.190550)

PRECONDITION RE-VERIFIED 2026-08-14. This page's no-op condition still holds, confirmed in code rather
than assumed:
- `marinelab/assets/uuv_cfg.py:143` -- `enable_thrust_curve: bool = False`
- `marinelab/assets/uuv_cfg.py:148` -- `thrust_deadband: float = 0.075`
- `marinelab/core/thruster.py:178` -- `if not getattr(self.cfg, "enable_thrust_curve", False): return`
  the state unchanged, so neither the deadband nor the signed-square curve is applied.

So as of today nothing is invalidated: the trained plant is still linear through zero, the deployment
mixer's `undeadband(D=0.15)` compensation is still CORRECT rather than double-counting, and the
instruction in the body -- do NOT "fix" 0.075 to 0.16 while the curve is off -- is still the right
action, which is to say: no action.

THE GATE QUESTION THIS RAISES, for the owner and deliberately not decided here. This lead holds
`needs-apply-before-retrain`, which makes `queue-launch` REFUSE every launch until it is resolved or
acked. But the finding is CONDITIONAL: it invalidates a run only if someone enables the thrust curve
without also setting the deadband from the measurement. Today the condition is false. The skill's own
rule for the blocking value is "facts that INVALIDATE dependent runs", with the warning that inflating
it "teaches the next session to ack past the gate, which costs more than the empty roster ever did".
A permanently-blocking flag on a currently-inert fact is exactly that shape.

Two defensible resolutions, both the owner's call:
- KEEP BLOCKING -- the trap is real and severe (training against 0.075 while the robot has 0.16 would
  reproduce the gap the mixer papers over, one layer deeper and harder to see), and the ack is one
  flag on the rare launch that touches the thruster model.
- DOWNGRADE to no status, and instead attach the requirement to the thrust-curve switch itself, so it
  fires when the condition becomes true rather than standing on every launch.

Status left UNCHANGED pending that decision -- changing it would be taking the call, and a silent
downgrade of a blocking gate is worse than an inflated one.

WHAT IS NOT CONDITIONAL, and does not depend on the above: the config value 0.075 is WRONG on its own
terms. It traces to an assumed "+-25 us out of +-400 us half-span"; the board measures +-48 us out of
+-300 us, so both numerator and denominator were wrong, and the real deadband is ~0.16 and ASYMMETRIC
(-0.167 / +0.150) where the knob is a single scalar. Whoever turns the curve on inherits all three
problems at once.

