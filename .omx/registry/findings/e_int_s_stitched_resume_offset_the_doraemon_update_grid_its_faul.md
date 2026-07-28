---
title: "E-int's stitched resume offset the DORAEMON update grid: its fault_severity reads 0.0770 iteration-matched (iter 4749) but 0.0901 at actual run end (iter 4999)"
tags: ["doraemon", "curriculum", "fault_severity", "e-int", "resume", "stitched-run", "comparability", "off-by-one-update"]
created: 2026-07-28T09:22:57.309081
updated: 2026-07-28T09:22:57.309081
sources: ["curriculum_trajectory.json", "trpo_eint_s30_rs2350_260727_195102", "trpo_faultdr_agnostic_s30_260725_183121", "trpo_hydrorc_s30_260728_013136"]
links: ["the_mean_preserving_beta_clamp_silently_triples_concentration_fo.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# E-int's stitched resume offset the DORAEMON update grid: its fault_severity reads 0.0770 iteration-matched (iter 4749) but 0.0901 at actual run end (iter 4999)

# Two different correct answers for "how far did E-int's fault curriculum reach"

Checked 2026-07-28 while designing E-ftc1, because the recorded 7.70% did not match the run's own
`curriculum_trajectory.json`. Both numbers are right; they answer different questions, and the
difference is an artifact of the crash-and-resume.

DORAEMON updates on an iteration grid of `step_interval = 250`. A from-scratch 5000-iteration run
gets its grid at 0, 250, ... 4750 — the last update lands at 4750 and nothing further happens before
4999. E-int resumed from `model_2350.pt`, which offset the grid to ... 4499, 4749, **4999**, so the
resumed segment received one EXTRA update, landing exactly on the final iteration.

| run | grid | last update | fault_severity there |
|:--|:--|--:|--:|
| Arm A `trpo_faultdr_agnostic_s30_260725_183121` | 0..4750 | 4750 | 0.0771 |
| HydroRC `trpo_hydrorc_s30_260728_013136` | 0..4750 | 4750 | 0.1083 |
| E-int `trpo_eint_s30_rs2350_260727_195102` | 2499..4999 | 4749 / **4999** | 0.0770 / **0.0901** |

[FINDING] Every comparison already on record is ITERATION-MATCHED and therefore correct as written: PLAN 12.2's "E-int 7.70% vs ArmA 7.71% -> Lane-2 curriculum-tax refuted" compares iter 4749 against iter 4750, and the HydroRC row's "10.83% vs 7.70%" compares iter 4750 against iter 4749. No recorded verdict needs revising.
[EVIDENCE: curriculum_trajectory.json of all three runs, per-dim Beta(a,b) at every logged update converted against param_bounds [0,1]; E-int resumed-segment records run 2499, 2749, ... 4999 (11 records) and the pre-crash segment 0..2250 (10 records), 21 updates total across the stitch]
[CONFIDENCE: HIGH]

[FINDING] But the FINAL TEACHER CHECKPOINT was trained under a curriculum that ended at 0.0901, not 0.0770. `model_4999.pt` is saved after the iter-4999 update, so any statement about the fault exposure the deployed teacher actually experienced must use 0.0901 (P(>=1 of 6 thrusters faulted) 5.29%, versus 4.53% at 0.0770). Statements comparing runs at equal training length must use 0.0770. An unqualified word like "reach" silently picks one.
[EVIDENCE: same trajectory files; exposure arithmetic P = 1-(1-0.10*u)^6 from mdp/faults.py:66 with thruster_fail_prob = 0.10]
[CONFIDENCE: HIGH]

# Why the TB scalar says 0.0770

`DORAEMON/mean/fault_severity` last-logged reads 0.0770 for E-int, which is where the recorded figure
came from. That is the iter-4749 value; the TB scalar for the final update was not the last one read.
When the two sources disagree on a resumed run, `curriculum_trajectory.json` is the completer record
— it carries every update with its iteration index, so the grid offset is visible instead of hidden.

Related: [[the_mean_preserving_beta_clamp_silently_triples_concentration_fo]] (why all four nominal-0
dims sit in this 0.06-0.11 band regardless of run).

