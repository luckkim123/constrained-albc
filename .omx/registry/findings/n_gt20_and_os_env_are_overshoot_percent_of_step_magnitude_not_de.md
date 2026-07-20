---
title: "n_gt20 and os_env_* are OVERSHOOT PERCENT of step magnitude, NOT degrees -- several posttam reports mislabel it as 'peak>20deg'"
tags: ["n_gt20", "os_env_mean", "overshoot", "metric-definition", "recompute_metrics", "rule03", "label-vs-implementation", "posttam", "report-defect"]
created: 2026-07-20T07:08:09.576984
updated: 2026-07-20T07:08:09.576984
sources: ["constrained_albc/analysis/_analyze/recompute_metrics.py:105-123", "trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md"]
links: ["april_2026_entropy_collapse_campaign_machinery_bug_solved_conver.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# n_gt20 and os_env_* are OVERSHOOT PERCENT of step magnitude, NOT degrees -- several posttam reports mislabel it as 'peak>20deg'

`n_gt20` counts envs whose transient OVERSHOOT exceeds **20 PERCENT of the target step
magnitude** -- it is NOT a count of envs whose peak exceeded 20 DEGREES. Several
`teacher_baseline_posttam` reports label it as degrees and are wrong. Any conclusion phrased as
"N envs had >20 deg excursions" from this field is a misstatement of what was measured.

## Code (verified 2026-07-20, `constrained_albc/analysis/_analyze/recompute_metrics.py:105-123`)

    sign     = 1.0 if cur_tgt > prev_tgt else -1.0
    peak_env = nanmax/nanmin of the alive window
    os_signed = sign * (peak_env - cur_tgt) / step_mag * 100.0   # PERCENT of step
    os_clip   = clip(os_signed, 0, None)
    "n_gt20": int(np.sum(os_clip > 20.0))                        # > 20 PERCENT
    "n_gt40": int(np.sum(os_clip > 40.0))

The whole `os_env_*` family (`os_env_mean` / `_std` / `_median` / `_q90`) is on the same percent
scale, as is `n_us_lt_minus20` (undershoot). `step_mag` is the commanded step size, so the metric
is scale-free by construction -- which is exactly why it cannot be an angle.

Two secondary properties that also get misread:

- The reported value is **fractional** (e.g. 4.333, 61.3) because the per-target-step integer
  count is AVERAGED over the eval's target steps. A non-integer `n_gt20` is not a bug.
- It is a THRESHOLD view of the same distribution as `os_env_mean`, so it CORROBORATES that
  mean, it is not independent evidence. Do not present both as two findings.

## Where the mislabel appears

- `trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md`: tracking table
  header reads `n_gt20 (peak>20deg envs)` -- WRONG.
- `trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md`: same degree framing.
- CORRECT (code-verified, with the metric definition stated inline):
  `trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-124259/report.md`, which
  explicitly notes "counts envs whose overshoot exceeds 20 %, NOT a 20 deg peak".

The mislabel is consequential, not cosmetic: a "20 degree excursion" reads as a near-loss-of-
control event, whereas 20% overshoot on a small commanded step can be a fraction of a degree. It
inflates the perceived severity of every transient finding it appears in.

## Related metric-vs-name traps in the same family

This is the same class of defect as the `min_std` mislabel corrected on 2026-07-20 (a config
field named in a report without checking which code branch actually reads it) -- see
[[april_2026_entropy_collapse_campaign_machinery_bug_solved_conver]]. Workspace rule 03 already
requires reading the implementation rather than trusting the name; these two are the concrete
instances in this campaign.

Separately, the steady-state tail (`ss_error` CV) and the transient tail (`os_env_*` / `n_gt20`)
are DIFFERENT failure modes and must not be merged into one "heavy-tail" claim.

