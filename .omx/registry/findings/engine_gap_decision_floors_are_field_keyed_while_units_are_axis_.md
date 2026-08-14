---
title: "engine-gap: decision floors are field-keyed while units are axis-keyed, so steady-state error is unadjudicated on 4 of 7 axes"
tags: ["engine-gap", "decision-floor", "eval", "units", "yaw", "lin-vel", "screening", "albc"]
created: 2026-08-14T06:22:54.831015
updated: 2026-08-14T06:22:54.831015
sources: ["diagnose-20260729-172500", "wiki-curation-2026-08-14"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: decision floors are field-keyed while units are axis-keyed, so steady-state error is unadjudicated on 4 of 7 axes

[ENGINE-GAP] The pre-registered decision floors are keyed by FIELD while the metric units are keyed by
AXIS, so the only registered steady-state floors (deg) can screen the three attitude axes and nothing
else -- yaw and the three linear-velocity axes come back NO-FLOOR and their deltas are never adjudicated.

[WHERE] constrained_albc/analysis/_analyze/recompute_metrics.py -- DECISION_FLOORS (line 89) and
floor_verdict (line 96).

[SPEC] Register per-axis-unit floors so every axis is screenable. Concretely: give ss_error and
ss_error_std a rad/s floor for yaw and an m/s floor for vx/vy/vz, derived the same way the deg floors
were (cross-seed peak-to-peak on the corrected-plant standard evals), and key DECISION_FLOORS by
(field, unit) instead of field alone. Until that exists, floor_verdict returning NO-FLOOR on those
axes must be read as "not measurable at this protocol", never as "no regression".

[EVIDENCE] Verified in code 2026-08-14, not inferred:
- AXIS_UNITS = roll/pitch/att_norm deg, vx/vy/vz m/s, yaw rad/s (recompute_metrics.py:44).
- DECISION_FLOORS = {ss_error 0.10, os_env_mean 10.0, n_gt20 15.0, ss_error_std 0.60,
  survival_pct 1.6} -- the two axis-scoped entries are both in deg (recompute_metrics.py:89).
- floor_verdict guards them correctly: `if field in ("ss_error","ss_error_std") and axis is not None
  and AXIS_UNITS.get(axis) != "deg": return "NO-FLOOR"` (recompute_metrics.py:107). The guard has been
  in place since 7b4fb5c (2026-07-27), and the one production call site passes the real axis
  (paired.py:132), so this is a MISSING FLOOR, not a mis-applied one.
- Scale of the blind spot, measured on B1b (analysis diagnose-20260729-172500): yaw ss_error values
  are 0.0049-0.0082 rad/s. No registered floor stands between those and any delta.
- The axis-independent floors (os_env_mean in pp-of-step, n_gt20 and survival_pct in envs) DO apply on
  all seven axes and are unaffected.

[CONSEQUENCE] Four of seven axes are screened for overshoot and survival but not for steady-state
accuracy or its dispersion. A campaign that reports "no regression" on yaw or lin_vel from the floor
machinery is reporting the absence of an instrument. Say NO-FLOOR explicitly in the report rather than
letting an unscreened axis read as a passed one.

[STATUS] proposed

RELATED: eval decision floors are the binding standard for student-arm comparisons (0.1 deg / 15 envs);
eval metric units and decision floors (os_env_mean is percent-of-step).

