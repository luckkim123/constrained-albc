---
title: "engine-gap: eval_adapter heavy-tail lacks median-based tail ratio + top-k concentration"
tags: ["engine-gap", "heavy-tail", "eval", "roll"]
created: 2026-07-14T16:28:26.273925
updated: 2026-07-14T16:28:26.273925
sources: ["diagnose-20260715-011113"]
links: []
category: decision
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# engine-gap: eval_adapter heavy-tail lacks median-based tail ratio + top-k concentration

[ENGINE-GAP] eval_adapter.py heavy-tail (delegating to _analyze.eval_dr._ed_compute_heavy_tail) reports ss_mean/ss_std/ss_max/peak_mean/peak_max/pct_peak_gt_thresh/pct_ss_gt_tenththresh per axis/level, but NOT the two tail-shape metrics rule03's heavy-tail KEY QUESTION actually needs: per-env ss MEDIAN (hence max/median tail-extremity ratio) and the top-k/64 share of total ss (tail concentration). In the trpo_baseline_260714_192020 vs void-anchor analysis these had to be recomputed in an ad-hoc scratch script (per_env_roll.py) from the raw data_*.npz.
[WHERE] workspace post-processing source: constrained_albc/analysis/_analyze/eval_dr.py, _HeavyTail dataclass + _ed_compute_heavy_tail() (add ss_median, max_over_median, topk_share fields; k default 6), and surface them in _ed_print_report / the eval_adapter heavy-tail JSON.
[SPEC] For each axis/level compute per-env ss (already = err_abs[s:].mean(axis=0)); add ss_median=float(np.median(ss)), max_over_median=ss.max()/ss.median (guard median>0), topk_share=sum(sorted(ss)[-k:])/ss.sum() with k configurable (default 6). Flag heavy-tail when max_over_median>10 AND topk_share>~0.4 (the void hard-roll signature: 25x / 49%; the post-TAM signature 7.5x / 33% falls below).
[EVIDENCE] KEY QUESTION of analysis diagnose-20260715-011113: void hard-roll max/median 25.3x, top-6 share 49.1% vs post-TAM MATCHED 7.49x / 32.8% — the collapse is only visible via these two derived metrics, which the engine does not emit.
[STATUS] proposed
