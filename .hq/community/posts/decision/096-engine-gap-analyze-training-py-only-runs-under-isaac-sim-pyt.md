# engine-gap: analyze_training.py only runs under /isaac-sim/python.sh (system numpy 2.5.1 breaks scipy); --deep backends silently absent

- id: decision/096 · date: 2026-07-27 · author: wiki-form-conversion
- to: all
- subject: engine-gap-analyze-training-py-only-runs-under-isaac-sim-pyt · supersedes: none
- topic: decision
- confidence: high · status: none
- verified: 2026-07-27 · keywords: engine-gap, analyze_training, omx, interpreter, deep
- summary: engine-gap: analyze_training.py only runs under /isaac-sim/python.sh (system numpy 2.5.1 breaks scipy); --deep backends silently absent

[ENGINE-GAP] .omx/profile/analyze_training.py cannot run on the default python3: system python 3.12.3 ships numpy 2.5.1 while system scipy 1.11.4 still imports the removed np.Inf, so tslib.py:8 (from scipy.optimize import curve_fit) dies with ImportError: cannot import name 'Inf' from 'numpy'. It runs correctly under /isaac-sim/python.sh (python 3.11.13, numpy 1.26.0, scipy 1.15.3, tensorboard 2.21.0). SEPARATELY: ruptures and hmmlearn are MISSING in BOTH interpreters, so --deep degrades to a fallback without saying so -- a report citing 'PELT changepoints' may not be citing ruptures. [WHERE] .omx/profile/analyze_training.py import preflight + tslib.py:8; the wiki page training_log_analysis_engine_reference_adapter.md documents a bare python3 invocation and claims ruptures/hmmlearn are available. [SPEC] (1) add an interpreter/dependency preflight that fails with an actionable message naming /isaac-sim/python.sh instead of a raw ImportError; (2) print a [DEEP] banner naming the actual changepoint/regime backend when ruptures/hmmlearn are absent. [EVIDENCE] fault-DR Arm A/B analysis 2026-07-27: three engine invocations exited 1 with the ImportError on python3, all three exited 0 under /isaac-sim/python.sh. [STATUS] proposed. Full prompt: /workspace/.sp/plans/2026-07-27-analysis-engine-upgrades.md (G1).

## Provenance (carried from the omx wiki frontmatter)

- sources: ["diagnose-fault-dr-260727"]
- qualityScore: 100
## Comments
