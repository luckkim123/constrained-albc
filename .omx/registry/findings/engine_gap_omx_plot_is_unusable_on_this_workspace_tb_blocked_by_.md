---
title: "engine-gap: omx plot is unusable on this workspace -- TB blocked by system-python tensorboard, eval npz blocked by 1-D-only series"
tags: ["engine-gap", "omx-plot", "tensorboard", "eval-npz", "plotting"]
created: 2026-07-29T08:26:09.673242
updated: 2026-07-29T08:26:09.673242
sources: ["diagnose-20260729-171553"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: omx plot is unusable on this workspace -- TB blocked by system-python tensorboard, eval npz blocked by 1-D-only series

[ENGINE-GAP] omx plot cannot render either of this workspace two plot sources, so every exp-analyze report here must hand-render plots into the scratch dir before omx promote-plots. [WHERE] omx_core/ingest.py format registry (TB path) and its 1-D series guard (npz path); the workaround lives in the session scratch script, not in a shared module -- a profile-owned plotting adapter alongside .omx/profile/tb_final.py would be the right home. [SPEC] (a) TB: omx plot --format tensorboard dies with "tensorboard not installed" for the same reason omx reduce tb-final does -- the CLI entry point resolves to system python3. Either ship a profile-owned plot reducer runnable under /isaac-sim/python.sh, mirroring tb_final.py, or make the CLI re-exec under a configured interpreter. (b) eval npz: omx plot --format npz rejects every trajectory series with "is in the file but is N-D; only 1-D arrays are plottable" because eval data_LEVEL.npz stores (T, n_env) arrays. Add a reduction argument (per-env index, or mean/quantile across the env axis) so N-D trajectory arrays become plottable instead of being refused. [EVIDENCE] Both failures reproduced this session on trpo_ftc1sevinit_s30_260729_105510: TB path on its events file, npz path on eval/static_260729_165750/data_none.npz series actual_roll_deg. Only the 20 dr_ scalars (1-D, per-env DR draws) are currently offered. [STATUS] proposed. Companion existing page: engine_gap_analyze_training_py_only_runs_under_isaac_sim_python_ (same system-python root cause).
