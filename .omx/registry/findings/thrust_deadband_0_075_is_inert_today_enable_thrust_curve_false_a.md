---
title: "thrust_deadband 0.075 is inert today (enable_thrust_curve false) and wrong for the day it is not: the board measures 0.16 half-span, asymmetric"
tags: ["albc", "thruster", "deadband", "esc", "plant", "retrain", "sim2real", "mixer", "conditional-gate", "gate-downgrade", "precedent", "conditional-blocker", "broken-ref-correction"]
created: 2026-08-14T05:33:06.787041
updated: 2026-08-14T10:27:25.841981
sources: ["trpo_iterbudget_s30_260805_012813", "wiki-curation-2026-08-14", "wiki-backlog-20260814", "diagnose-20260814-172325"]
links: ["esc_deadband_is_1450_1545_us_on_this_uuv_the_vertical_channels_p.md", "esc_deadband_is_1450_1545_us_on_this_uuv_the_vertical_channels_p.md", "plant_change_batch_v2_four_isaac_plant_corrections_are_now_pendi.md", "buoy_added_mass_is_wrong_in_both_sims_and_in_opposite_directions.md", "buoy_added_mass_is_wrong_in_both_sims_and_in_opposite_directions.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "RESOLVED = off this queue, NOT applied in code. The requirement moved to plant_change_batch_v2 item 3 and to a comment above enable_thrust_curve in marinelab/assets/uuv_cfg.py. It fires when the curve is switched on; it no longer stands on every launch."
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

---

## Update (2026-08-14T10:25:13.827552)

## GATE DOWNGRADED 2026-08-14 (user-approved): blocking status released, requirement relocated

The facts on this page are unchanged and still correct. What changes is where the requirement is
enforced.

WHY THE BLOCKING STATUS WAS WRONG FOR THIS ITEM. `needs-apply-before-retrain` refuses EVERY
launch, including the many that never touch the thruster model. This fact invalidates a run only
under one condition -- somebody enables the thrust curve without also fixing the deadband -- and
that condition is currently false and cannot be made true casually.

THE CONDITION IS ALREADY GUARDED BY A STRONGER GATE. Enabling `enable_thrust_curve` is not a free
edit: it IS item 3 of [[plant_change_batch_v2_four_isaac_plant_corrections_are_now_pendi]], whose
own text says "The thruster nonlinear-curve lead is the same measurement as the item 3 gate, not a
separate item". That batch carries a standing user decision from 2026-07-29 that the four
corrections are NOT decided one at a time and that nothing is applied until the batch is decided as
a unit, and it is blocked on a T200 bench session that has no booked date (the 2026-08-05 user
decision skipped the hardware-measurement items). So reaching the trap requires bypassing a user
decision, and a wiki status is not what stops that.

PRECEDENT, and this is what settled it. Of 291 pages on this root only TWO carried a blocking
status; the established pattern for a conditional or parked item is `resolved` with the reason in
`blocked-on` (81 pages). Decisively, the SIBLING item in this very batch --
[[buoy_added_mass_is_wrong_in_both_sims_and_in_opposite_d]], item 1, same conditional structure,
same gate -- already carries `resolved`. This page carrying a blocking status while its sibling did
not was an inconsistency, not a stricter standard.

THE COST OF GETTING THIS WRONG IN THE OTHER DIRECTION is what the omx skill warns about: inflating
the blocking status teaches the next session to ack past the gate, which costs more than an empty
roster ever did. With only two blocking pages, each one has to be genuinely unconditional. The
control-delay page is (any retrain trains on the wrong distribution). This one is not.

WHERE THE REQUIREMENT LIVES NOW -- two attachments, both at the point of change:
1. `plant_change_batch_v2` item 3: the deadband must be re-derived from the bench curve in the
   SAME edit that applies item 3.
2. `marinelab/marinelab/assets/uuv_cfg.py`, a comment block immediately above
   `enable_thrust_curve`: "BEFORE FLIPPING THIS TO True: re-derive thrust_deadband below in the
   SAME edit", with the board numbers inline.

Attachment 2 is the load-bearing one. It sits on the exact line a person must edit to create the
condition, so it cannot be missed by anyone who is in a position to cause the failure.

---

## Update (2026-08-14T10:27:25.841981)

## Link correction 2026-08-14

The sibling-precedent reference in the section above points at a truncated slug. The correct
target is [[buoy_added_mass_is_wrong_in_both_sims_and_in_opposite_directions]] -- item 1 of
plant_change_batch_v2, which carries `status: resolved` under the same conditional structure and
is the precedent this downgrade follows.

The truncated entry `buoy_added_mass_is_wrong_in_both_sims_and_in_opposite_d` remains in this
page's frontmatter `links` union and resolves to nothing. `omx wiki add` unions links and never
removes them, so a bad entry is permanent short of a gc round; it is recorded here rather than
silently left to mislead. Cause: the slug was copied from a shell listing truncated at 55
characters, not from the registry.

