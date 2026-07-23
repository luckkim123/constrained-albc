---
title: "Eval metric units and decision floors: os_env_mean is percent-of-step (roll steps 30 deg), ss_error is degrees; paired screening floors and the machine-isolation rule"
tags: ["units", "os_env_mean", "ss_error", "decision-floor", "machine-isolation", "paired-seed", "methodology", "audit"]
created: 2026-07-23T07:08:05.945326
updated: 2026-07-23T08:41:31.063757
sources: ["diagnose-20260723-134359", "teacher-campaign-plan.md#11"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Eval metric units and decision floors: os_env_mean is percent-of-step (roll steps 30 deg), ss_error is degrees; paired screening floors and the machine-isolation rule

FROM the 2026-07-23 experiment-validity audit (SSOT: docs/reference/teacher-campaign-plan.md section 11).

UNITS (read from code, HIGH):
- ss_error / ss_jitter are DEGREES (analysis/_analyze/recompute_metrics.py:167, |actual_deg - target_deg|).
- os_env_mean / os_env_median / us_env_mean are PERCENT OF STEP MAGNITUDE (recompute_metrics.py:109, (peak-target)/step_mag*100). NOT degrees, despite report tables that print "os_env_mean (deg)" (the mislabel originated in diagnose-20260723-134359 and propagated into planning docs).
- n_gt20 = envs whose overshoot exceeds 20 PERCENT of the step (recompute_metrics.py:121), not 20 deg.
- The static eval steps roll by exactly 30 deg per attitude segment (pitch 30 or 60), so roll os in degrees = pp x 0.30, exact. Anchor roll os 15.86 pp = 4.76 deg; the buoyancy plant fix moved roll os by -3.93 pp = -1.18 deg (NOT -3.93 deg).

DECISION FLOORS (roll, none level; eval itself is deterministic - biasema evaluated twice independently gave identical metrics, so ALL run-to-run variance is training-side):
- UNPAIRED cross-seed p2p: 74.8% old plant / 56.0% corrected plant (0.24 / 0.22 deg ss_error).
- Same-machine PAIRED scatter bound (one-lever 5k arms vs biasema, n=3): max 16.8% = 0.036 deg ss_error; transient scatter is much larger (unrelated levers moved os by +7.7..+9.3 pp).
- CROSS-MACHINE, same config + same seed (dgxseed30 vs biasema, config diff = usd_path + wandb project only): +109% ss_error (+0.235 deg), +6.4 pp os, +31.3 envs n_gt20. One pair, but decisive in size.

RULES:
1. MACHINE ISOLATION: never compare runs trained on different machines; any machine hosting training needs its own anchor.
2. Pre-register bands in ABSOLUTE units (deg / pp+deg); percent-only bands are how the +/-5% band broke.
3. Screening = 1 paired same-seed same-machine run; REAL only if |d ss_error| >= 0.10 deg or |d os| >= 10 pp (3.0 deg) or |d n_gt20| >= 15 envs; below floors say NULL/INCONCLUSIVE, never "worse"/"better".
4. Adoption = 3 paired seeds vs the 3 anchor seeds, 3/3 sign-consistent, mean clears half the screening floor.
5. Paper number = full 3-seed distribution, pre-declared median-seed rule.
UNSETTLED: the true same-machine paired repeatability floor; measured directly by one exact config+seed repeat of trpo_buoyanchor_s30 (~5 h, human-gated, proposed in SSOT 11.7).

---

## Update (2026-07-23T08:41:31.063757)

UPDATE 2026-07-23: the audit SSOT document moved to constrained-albc/.omx/programs/teacher-final-closeout/PLAN.md (omx v0.9.0 program layer); section 11 content unchanged. Redirect stub remains at docs/reference/teacher-campaign-plan.md.
