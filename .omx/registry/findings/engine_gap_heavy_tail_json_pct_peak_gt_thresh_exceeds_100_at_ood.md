---
title: "engine-gap: heavy_tail.json pct_peak_gt_thresh exceeds 100% at ood level (denominator bug)"
tags: ["engine-gap", "heavy-tail", "ood", "eval-adapter", "debugging"]
created: 2026-06-08T03:03:19.015251
updated: 2026-07-13T05:18:28.658920
sources: ["diagnose-20260608 dr_harder replot"]
links: ["teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# engine-gap: heavy_tail.json pct_peak_gt_thresh exceeds 100% at ood level (denominator bug)

[ENGINE-GAP] heavy_tail.json field pct_peak_gt_thresh returns >100% (e.g. 312.5%, 781.2%) at the ood level for E1/E2/E4 -- impossible for a percentage of 64 envs.
[WHERE] The heavy_tail.json writer (omx eval_adapter path delegating to constrained_albc/analysis/_analyze/eval_dr._HeavyTail, line 88: pct_peak_gt_thresh=100*(peak>threshold).sum()/max(N,1)). The ood-level peak array is NOT being reduced per-env (N=64) before the comparison -- 312.5%=200/64, 781.2%=500/64, i.e. peak carries ~5x the env count (likely a (T,N)-not-reduced or level-concatenation shape bug specific to the ood branch). in-dist levels (none..hard) are correct.
[SPEC] Ensure the ood-level per-env peak is reduced to shape (N,) (err[s:].max(axis=0)) before the >threshold fraction, identical to in-dist. The correct teacher/E1/E2 ood roll heavy-tail is 3.1% (2/64), E4 ood 7.8% (5/64) -- verified by recomputing per-env directly.
[EVIDENCE] dr_harder replot 2026-06-08: existing E1 heavy_tail.json ood roll pct_peak_gt_thresh=312.5; direct per-env recompute gives 3.1%. Same N=64 used.
[STATUS] proposed
Workaround for analysis: do NOT cite heavy_tail.json pct_peak_gt_thresh at ood; recompute per-env or cite peak_max (absolute, trustworthy). cf dr_harder_heavy_tail_correction_peak_20_is_not_zero_at_medium_ha.

---

## Update (2026-07-13T05:18:28.658920)

[STATUS] resolved-by-refactor (verified 2026-07-13, post-p7_tail planning session). The bug is NOT reproducible at HEAD (105818e): the current writer constrained_albc/analysis/_analyze/eval_dr.py::_ed_compute_heavy_tail derives ss/peak AND the denominator N from the SAME (T,N) array (lines 76-91), so pct_peak_gt_thresh > 100% is structurally impossible. Re-verified on real data: trpo_baseline_260713_031325 eval static_260713_075722 has identical shapes (7750, 64) for none/hard/ood; inline recompute of ood roll pct_peak>20deg gives 0.0% (0/64 envs), well-formed. The 2026-06-08 >100% values came from the pre-split eval_dr.py implementation, which the analysis god-file split replaced. No code change needed; workaround note (do not cite old E1/E2/E4 ood heavy_tail.json values) still applies to those OLD artifacts.
