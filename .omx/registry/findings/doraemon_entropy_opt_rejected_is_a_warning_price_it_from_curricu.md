---
title: "DORAEMON Entropy opt rejected is a WARNING: price it from curriculum_trajectory.json, not the log (successful expansions are never logged)"
tags: ["albc", "doraemon", "curriculum", "dr", "entropy", "monitoring", "false-alarm", "teacher"]
created: 2026-08-09T09:19:56.885278
updated: 2026-08-09T09:19:56.885278
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# DORAEMON Entropy opt rejected is a WARNING: price it from curriculum_trajectory.json, not the log (successful expansions are never logged)

`[DORAEMON] Entropy opt rejected: Singular matrix E in LSQ subproblem` is a WARNING, not a
crash. The run continues; the curriculum simply does not expand at that one attempt. Price it
before reacting.

## Successful expansions are NOT logged -- only rejections are

Grepping the launch log for DORAEMON gives a one-sided view: in a healthy 2000-iteration stretch
of `trpo_rampw_kl006_s30_260809_161913` the ONLY `DORAEMON` line in the whole log was the single
rejection. Silence is not evidence of a stalled curriculum, and one visible rejection is not
evidence of a broken one.

## The instrument is curriculum_trajectory.json, not the log

`<run>/train/curriculum_trajectory.json` holds `param_names`, `param_bounds`, and a `trajectory`
of `{iter, a, b}` records written once per `step_interval`. Sum the per-dim KL to uniform --
`-scipy.stats.beta.entropy(a, b)` -- and the number is the distance still to travel:
**it decreases toward 0, and 0 with all dims at Beta(1,1) IS saturation.** A rejected attempt
shows up as a record whose delta is exactly `+0.0000`.

Ready-made reader (host bind mount, so it survives container restarts): `/workspace/ctraj2.py`.
Note the file keeps only a rolling window of ~20 records, so an old run shows its tail, not its start.

## Measured cost of one rejection (2026-08-09)

`trpo_rampw_kl006_s30_260809_161913`, `step_interval` 250, `kl_ub` 0.06, 20000 iterations = 80
expansion attempts total. The rejection at iteration 2000 cost exactly one attempt = 250
iterations, against a run that was moving -1.15 KL per successful step with 29.45 KL to go.
Roughly 1.4% of the attempt budget. Benign in isolation; only a recurrence rate high enough to
eat the whole budget matters.

Trajectory around it, for shape: it=0 31.2855 -> it=1250 31.7655 (the box CONTRACTS first, because
`success_rate` is under `performance_lb` 250.0 early) -> it=1500 30.6072 (d -1.1584) -> it=1750
29.4535 (d -1.1537) -> it=2000 29.4535 (d +0.0000, the rejection).

## What saturation actually looks like

Incumbent `trpo_iterbudget_s30_260805_012813` on the same 21-dim plant reached 21/21 saturated at
iteration 7748, approaching it with DECELERATING steps: 6.4337 at 5248, then -1.0899, -1.0161,
-0.9352, -0.8466, -0.7493, -0.6414, -0.5201, -0.3808, -0.2167, -0.0376. Extrapolating a saturation
ETA from the early constant-rate segment therefore reads optimistic -- the last few KL cost several
step_intervals each.

## Watch rule

Do not act on the first rejection. Act if the rejection count grows to where
`(attempts_remaining - rejections) x per_step_progress` no longer covers the remaining KL. Both
numbers are readable from the file above; neither is readable from the log.
