---
title: "engine-gap: eval adapter only covers static; periodic unsupported, segmented partial"
tags: ["engine-gap", "eval-adapter", "periodic", "segmented", "coverage"]
created: 2026-06-05T10:15:51.918237
updated: 2026-06-05T10:15:51.918237
sources: ["20260605-190606-diagnose"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: eval adapter only covers static; periodic unsupported, segmented partial

[ENGINE-GAP] The omx eval heavy-tail adapter (.omx/profile/eval_adapter.py) only fully covers 'static' eval. eval.py has 3 modes: static (data_<none/soft/medium/hard>.npz), segmented (same data_<level>.npz + summary_segmented.json), periodic (data_periodic.npz single file). [WHERE] adapter delegates 100% to constrained_albc/analysis/_analyze/eval_dr._ed_analyze_run, which loops f'data_{level}.npz' over none/soft/medium/hard (eval_dr.py:43). [SPEC] (1) periodic: _ed_analyze_run cannot find data_periodic.npz (no level structure) -> returns empty; needs a periodic-aware branch reading the single file + per-DR-step transient analysis. (2) segmented: data_<level>.npz so adapter RUNS, but segmented's point is DR-switch ADAPTATION (transient at each switch), which steady-state heavy-tail does not capture; needs switch-transient metrics. [EVIDENCE] teacher re-analysis 20260605-190606-diagnose used static only; grep confirms 0 periodic handling in _ed_analyze_run. [STATUS] proposed.
