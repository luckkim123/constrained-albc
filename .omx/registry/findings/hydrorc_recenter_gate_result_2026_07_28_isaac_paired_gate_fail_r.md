---
title: "HydroRC recenter gate result 2026-07-28: Isaac paired gate FAIL (roll n_gt20 0->18.7 envs, yaw ss +18.8%) -- transient-tail regression at all DR levels, hard-corner collapse, 7-17x fault-robustness loss; recenter not adopted, Stonefish readout not entered"
tags: ["hydrorc", "gate", "recenter", "damping", "transient", "fault-dr"]
created: 2026-07-27T23:24:46.808798
updated: 2026-07-28T09:16:04.874601
sources: ["diagnose-20260728-081953"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# HydroRC recenter gate result 2026-07-28: Isaac paired gate FAIL (roll n_gt20 0->18.7 envs, yaw ss +18.8%) -- transient-tail regression at all DR levels, hard-corner collapse, 7-17x fault-robustness loss; recenter not adopted, Stonefish readout not entered

[FINDING] The HydroRC recenter probe (trpo_hydrorc_s30_260728_013136, hydro DR nominals moved to the
Stonefish-measured effective values, single variable vs E-int) FAILED the pre-registered Isaac paired
non-regression gate and therefore never entered the Stonefish readout: roll n_gt20 0 -> 18.67 envs
(clears the 15-env REAL floor from a zero baseline; roll os_env_mean 8.18 -> 17.96 pp corroborates)
and yaw ss_error +18.8% vs the 16.8% bound (degrading at ALL levels: +18.8/+23.4/+24.3/+31.9%).
The recentered nominals are NOT adopted; E-int remains the final teacher; the Stonefish limit-cycle
Lane-2-vs-Lane-1 question stays OPEN.
[EVIDENCE: report experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md; independent report-reviewer 2 rounds, R2 approve 0 findings]
[CONFIDENCE: HIGH]

Key structure: DC steady-state intact at none (roll ss +1.9%, pitch improved -15.7%); the regression is
the step-transient tail at ALL DR levels; `hard` collapses broadly (att_norm 1.691 vs 0.719 deg,
survival 96.9 vs 100.0 -- first sub-100 in this family) because the unchanged relative DR band around a
10-100x lower rotational nominal makes the hard corner near-undamped in absolute terms. Supplementary
m4-dead: fault delta 7-17x LARGER than E-int at every level despite MORE fault-curriculum reach (10.83%
vs 7.70%) -- fault tolerance and plant damping are coupled. thruster_util J_C/d_k 0.805 (anchor level).

Next-step decision structure (human-gated, nothing queued): run P1 cross-sim joint1 swing FIRST (zero
GPU, Stonefish machine) to measure the deployment sim's closed-loop rotational damping, THEN pick the
recenter-v2 arm: (a) translational+heave-only recenter -- loses Lane-2 discriminating power on the
rotational limit-cycle axes; (b) rotational recenter + raised DR lower-corner floor -- adds a second
variable; (c) log-mean rotational recenter -- arbitrary without P1. Branch exp/hydro-recenter kept as
the v2 base; marinelab parked back on exp/max-thrust-dr.

---

## Update (2026-07-28T09:16:04.874601)

# NUMERIC CORRECTION 2026-07-28: the hard-level yaw figure is +31.8%, not +31.9%

This page's yaw-per-level series reads `+18.8/+23.4/+24.3/+31.9%`. The last figure is a
hand-transcription drift. The SSOT report `diagnose-20260728-081953` states
`+18.8/+23.4/+24.3/+31.8%`, and every copy taken verbatim from it agrees (the auto-captured finding
page `the_pre_registered_isaac_paired_non_regression_gate_fails_so_per`, all three blocks, and the
P1 cross-sim protocol spec).

Only the two hand-authored summaries drifted: this page and PLAN `teacher-final-closeout`
section 12.2, HydroRC row. PLAN has been corrected in the same pass.

Nothing downstream changes — the gate verdict rests on the `none`-level +18.8% against the 16.8%
bound and on roll `n_gt20` 0 -> 18.67 envs, neither of which is affected. Recorded so the value does
not propagate further, per the workspace rule that run results are read from the experiments-tree
report and not from a summary that copied it.

[EVIDENCE: report diagnose-20260728-081953 line 12 ("+18.8/+23.4/+24.3/+31.8% at none/soft/medium/hard"); grep across .omx/registry/findings and /workspace/.sp/plans/2026-07-28-p1-cross-sim-joint1-swing-protocol.md returns 31.8 in every verbatim copy and 31.9 only in this page and PLAN 12.2]
[CONFIDENCE: HIGH]

