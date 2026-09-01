# training-log analysis engine (reference adapter)

- id: finding/291 · date: 2026-06-02 · author: wiki-form-conversion
- harness: omx · to: all
- subject: training-log-analysis-engine-reference-adapter · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: 2026-07-27 · keywords: adapter, analyze, engine
- summary: training-log analysis engine (reference adapter)

The TB/wandb training-log diagnostic engine lives at .omx/profile/analyze_training.py (+ tslib.py). Self-contained: numpy/yaml/tensorboard/scipy/ruptures/hmmlearn only, no Isaac Sim. Run: ALBC_LOGS_ROOT=<logs/rsl_rl> python3 .omx/profile/analyze_training.py [run-index|path] [--deep --tier 3 --stride N --focus PAT]. Outputs CONFIG/TIER1/TIER2/DIAGNOSIS + (--deep) PELT changepoints/HMM regime/lead-lag/plateau. Use for 'why stalled/diverged'; use monitor.py plot for quick PNG dashboard. Evidence: verified working from .omx/profile on run trpo_main_teacher_260525_232805 (Jun 2 2026).

---

## Update (2026-07-27T04:31:00.539129)

INTERPRETER REQUIREMENT (2026-07-27, supersedes the bare-python3 invocation above): the engine is NOT runnable under system python3 (numpy 2.5.1 + scipy 1.11.4 predate the np.Inf removal; no tensorboard). Run it under the Isaac Sim interpreter: /isaac-sim/python.sh .omx/profile/analyze_training.py [run|--list ...]. A preflight (commit 5a28c64) now exits 2 with an actionable [PREFLIGHT] message under a broken interpreter instead of a raw ImportError. ruptures/hmmlearn are MISSING in BOTH interpreters on this machine, so --deep changepoints come from the CUSUM fallback (not PELT) and HMM regime detection is skipped -- format_deep now prints a [DEEP] banner naming the actual backend, so cite the banner's algorithm, not 'PELT', in reports.

## Provenance (carried from the omx wiki frontmatter)

- qualityScore: 70
- qualityReasons: ["no-source-marker", "generic-only-tags"]
## Comments
