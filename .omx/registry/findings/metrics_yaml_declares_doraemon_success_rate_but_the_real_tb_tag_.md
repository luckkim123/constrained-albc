---
title: "metrics.yaml declares doraemon_success_rate but the real TB tag is DORAEMON/success_rate -- a coverage check that trusts the declared token reports the group as unlogged"
tags: []
created: 2026-08-03T19:54:01.563410
updated: 2026-08-04T06:11:42.098428
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "One-line fix to .omx/profile/metrics.yaml (doraemon group): replace doraemon_success_rate with DORAEMON/success_rate. Not applied yet because editing the profile mid-campaign changes the coverage contract for reports already written against it; apply it together with the next profile revision."
---

# metrics.yaml declares doraemon_success_rate but the real TB tag is DORAEMON/success_rate -- a coverage check that trusts the declared token reports the group as unlogged

## Evidence

Both teacher runs log 138 scalar tags. A by-name check over `trpo_eint_s30_rs2350_260727_195102`
and `trpo_obs76_s30_260803_233239`:

- `doraemon_success_rate` -- ABSENT from both event files.
- `DORAEMON/success_rate` -- present in both, final-50 means 0.81044 and 0.91889.

The other three declared tokens in the group (`DORAEMON/entropy_before`, `DORAEMON/kl_step`,
`DORAEMON/ess_ratio`) all exist and are correctly named, so only this one entry is wrong.

## Why it matters

This is the exact "engine-gap" trap exp-analyze warns about: an empty cell is a hypothesis about
tag naming, not a fact about data. A report that trusted the declared token would have written
"the run did not log a DORAEMON success rate" while the data was there under a different name.
The by-name dump of the scalar tag set is what settles it.

## Related caution

`DORAEMON/kl_step` is logged only on curriculum update steps and reads 0 between them, in BOTH
runs. A final-window mean of 0 is therefore NOT evidence that the curriculum stalled -- E-int
reads 0.0000 at steps 2350/3012/3675/4337/4735/4947 and 0.12 only at 4999. Any stall claim needs
the update-step trajectory, not a trailing mean.

---

## Update (2026-08-04T06:11:42.098428)

RESOLVED 2026-08-04 (gate G4, dgx-final-scaleup program, commit 72351a4): the full profile audit found 10 drifted tokens, not just this one - doraemon_success_rate -> DORAEMON/success_rate plus entropy/noise_std/line_search_success/kl/barrier_penalty/reward_total/att_roll_err_deg/att_pitch_err_deg/yaw_rate_err, all fixed in the metric list AND groups (trpo/constraint/doraemon). Verified 59/59 declared tokens exist in the E-int event file. The mid-campaign coverage-contract concern was accepted because the profile revision rode a program boundary (dgx-final-scaleup), not an open campaign report.
