---
title: "engine-gap: eval adapter covers static + segmented; periodic still unsupported"
tags: ["engine-gap", "eval-adapter", "periodic", "segmented", "coverage", "debugging"]
created: 2026-06-05T10:43:00.649099
updated: 2026-06-05T10:43:00.649099
sources: ["20260605-190606-diagnose", "exp-output-naming"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: eval adapter covers static + segmented; periodic still unsupported

[ENGINE-GAP][UPDATE 2026-06-05] eval adapter (.omx/profile/eval_adapter.py) now covers static (heavy-tail via _ed_analyze_run) AND segmented (post-switch transient via _analyze.switching). [RESOLVED segmented] adapter gained analyze_segmented(): loads summary_segmented.json directly (raw I/O only, accepts the current eval/segmented_<ts>/ layout where _sw_load_run's legacy eval_dr_switching/ subdir assumption fails) then delegates post-switch metric extraction to engine _sw_all_post_switch, applying only numpy mean/p95/max reductions (no metric math re-implemented). Verified on real student segmented dir: hard roll post-switch mean 9.28deg / max 44.45deg = meaningful DR-switch transient. [STILL UNSUPPORTED periodic] eval.py periodic emits a single data_periodic.npz with no level structure and _periodic_compute_metrics lives in eval.py which boots Isaac Sim -> NO sim-free driver in _analyze/. The adapter cannot cover periodic without either a sim-free periodic driver extracted into _analyze/ or reimplementing the periodic metric math (which would violate pure-delegation). [SPEC periodic] extract a sim-free periodic compute path into _analyze/ (mirror eval_dr.py / switching.py), reading data_periodic.npz + per-DR-step transient, then add a periodic subcommand delegating to it. [STATUS] segmented=implemented, periodic=proposed.
