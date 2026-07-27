---
title: "engine-gap: omx reduce tb-final unusable here (CLI on system python without tensorboard) + no paired-condition comparison in the analysis package"
tags: ["engine-gap", "omx", "tensorboard", "compare", "eval", "fault"]
created: 2026-07-27T04:26:03.072725
updated: 2026-07-27T04:44:13.433089
sources: ["diagnose-fault-dr-260727"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# engine-gap: omx reduce tb-final unusable here (CLI on system python without tensorboard) + no paired-condition comparison in the analysis package

[ENGINE-GAP] Two consumer-side gaps hit in the same analysis. (a) The exp-analyze skill prescribes 'omx reduce tb-final --format tensorboard' as THE code-exec source for TB numbers, but the omx CLI resolves to system python3 which has no tensorboard -> 'tensorboard not installed; pip install omx-core[analyze]'. omx doctor already reports deps.tensorboard=false but the failure still surfaces mid-analysis as a dead end. Workaround used: a ~25-line EventAccumulator reducer under /isaac-sim/python.sh (size_guidance={SCALARS:10000}), kept at /root/.claude/jobs/182132ba/tmp/tb_final.py. (b) constrained_albc/analysis/compare.py compares RUNS, not CONDITIONS WITHIN a run, so the FTC paired question (policy x {healthy, m4-dead} x 4 DR levels x 3 policies) was written as a throwaway script; the bite-check (assert fault_thruster_4==0 in 64/64 envs from the npz) was manual too. [WHERE] (a) .omx/profile/ -- add a documented tb_final reducer, or make the doctor remediation name the working interpreter; (b) constrained_albc/analysis/compare.py or a new _analyze/paired.py. [SPEC] (b) given N labelled eval dirs grouped into (baseline-condition, treatment-condition) pairs, emit the per-axis x per-DR-level delta table with pre-registered floors applied and a REAL / BELOW-FLOOR verdict per cell, with the injection bite-check as a first-class first step. Reusable for every future robustness sweep (fault, latency, thruster-curve). [EVIDENCE] fault-DR Arm A/B analysis 2026-07-27; also KeyError 'fault_thruster_0 is not a file in the archive' on the healthy evals, because a --fault-less eval writes no fault fields at all. [STATUS] proposed. Full prompt: /workspace/.sp/plans/2026-07-27-analysis-engine-upgrades.md (G2, G4, G5).

---

## Update (2026-07-27T04:32:36.651269)

RESOLVED (tb-final half, 2026-07-27, commit da4cce9): the supported TB code-exec source on this machine is the profile-owned reducer .omx/profile/tb_final.py -- run /isaac-sim/python.sh .omx/profile/tb_final.py <run_dir>... --tags <T>... [--window 200] [--list-tags]; JSON out {run: {tag: last-window mean | null}}. Do NOT use 'omx reduce tb-final' here (omx CLI = system python3, no tensorboard). The paired-condition-comparison half is tracked separately and lands as compare.py paired mode (G4).

---

## Update (2026-07-27T04:44:13.433089)

RESOLVED (paired half, 2026-07-27, commit 890b0e4): 'python3 constrained_albc/analysis/compare.py paired --pair LABEL:BASELINE_EVAL_DIR:TREATMENT_EVAL_DIR (repeatable) [--axes att_norm roll pitch yaw] [--fields ss_error os_env_mean n_gt20 survival_pct] --bite <npz_key>' emits the per-axis x per-DR-level (treatment - baseline) delta table with pre-registered floors applied (REAL/BELOW-FLOOR/NO-FLOOR via _analyze.recompute_metrics.floor_verdict). The bite-check runs FIRST and exits 2 when the treatment npz lacks the key or is byte-identical to baseline (silent no-op injector). Reusable for any robustness sweep (fault/latency/thruster-curve). Verified byte-for-byte against the fault-DR Arm A/B throwaway matrix. Both halves of this gap are now closed.
