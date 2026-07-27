---
title: "engine-gap: analyze_training.py only runs under /isaac-sim/python.sh (system numpy 2.5.1 breaks scipy); --deep backends silently absent"
tags: ["engine-gap", "analyze_training", "omx", "interpreter", "deep"]
created: 2026-07-27T04:25:36.439969
updated: 2026-07-27T04:25:36.439969
sources: ["diagnose-fault-dr-260727"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: analyze_training.py only runs under /isaac-sim/python.sh (system numpy 2.5.1 breaks scipy); --deep backends silently absent

[ENGINE-GAP] .omx/profile/analyze_training.py cannot run on the default python3: system python 3.12.3 ships numpy 2.5.1 while system scipy 1.11.4 still imports the removed np.Inf, so tslib.py:8 (from scipy.optimize import curve_fit) dies with ImportError: cannot import name 'Inf' from 'numpy'. It runs correctly under /isaac-sim/python.sh (python 3.11.13, numpy 1.26.0, scipy 1.15.3, tensorboard 2.21.0). SEPARATELY: ruptures and hmmlearn are MISSING in BOTH interpreters, so --deep degrades to a fallback without saying so -- a report citing 'PELT changepoints' may not be citing ruptures. [WHERE] .omx/profile/analyze_training.py import preflight + tslib.py:8; the wiki page training_log_analysis_engine_reference_adapter.md documents a bare python3 invocation and claims ruptures/hmmlearn are available. [SPEC] (1) add an interpreter/dependency preflight that fails with an actionable message naming /isaac-sim/python.sh instead of a raw ImportError; (2) print a [DEEP] banner naming the actual changepoint/regime backend when ruptures/hmmlearn are absent. [EVIDENCE] fault-DR Arm A/B analysis 2026-07-27: three engine invocations exited 1 with the ImportError on python3, all three exited 0 under /isaac-sim/python.sh. [STATUS] proposed. Full prompt: /workspace/.sp/plans/2026-07-27-analysis-engine-upgrades.md (G1).
