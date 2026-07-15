---
title: "TAM plant-correctness fix collapses the void hard-DR roll heavy-tail (into a raised floor)"
tags: ["heavy-tail", "roll", "TAM", "plant", "teacher-baseline", "doraemon"]
created: 2026-07-14T16:38:59.611547
updated: 2026-07-14T16:38:59.611547
sources: ["diagnose-20260715-011113"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# TAM plant-correctness fix collapses the void hard-DR roll heavy-tail (into a raised floor)

DECISION/FINDING: the corrected-TAM teacher baseline (trpo_baseline_260714_192020) does NOT inherit the void baseline's (trpo_baseline_260713_031325) hard-DR roll steady-state heavy-tail — the plant fix collapses it, trading the catastrophic tail for a higher, tighter roll-error floor.

EVIDENCE (per-env roll ss = last-20%-window mean |error_roll|, code-exec on data_*.npz; eval ids cited):
- MATCHED +-15 box (static_260715_003649) vs void +-15 (static_260713_075722):
  - hard: max/median 25.3x -> 7.49x; top-6/64 share 49.1% -> 32.8%; peak_max 16.4deg -> 10.1deg.
  - ood:  max/median 28.3x -> 6.37x; top-6 share 51.9% -> 22.5%; peak_max 7.3deg -> 6.0deg.
  - Corroborated at the ONLY strictly-fair cross-run level (none, zero DR): 7.05x -> 4.26x, top-6 30% -> 18%.
- COST: the typical-env body ROSE (per-env roll: hard median 0.199 -> 0.440deg +121%, hard mean 0.389 -> 0.568deg +46%, none mean 0.229 -> 0.534deg +133%). So this is robustness-for-accuracy, not a free win.

CAVEAT (must honor): DORAEMON grades each run's hard/ood on its OWN learned DR (wiki eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr), so cross-run hard/ood ratios are NOT like-for-like; the verdict is qualitative (a >10x tail with ~half its mass in 6 envs -> a <8x tail with ~a third) and is corroborated at the fair none level. Do not present 25.3x -> 7.5x as a like-for-like delta.

GOTCHA: summary.json ss_error uses a DIFFERENT steady-state window than the per-env engine method; they are NOT interchangeable (hard roll rise +8% summary vs +46% per-env; ood disagrees in SIGN, -22% vs +6%). Use the per-env engine method for tail analysis; use summary.json only for the mean/CV cross-run view.

DUAL-BOX: widening the command box +-15 -> +-30 (same checkpoint, static_260715_004654) does NOT re-open a tail (hard roll max/median 7.49x -> 6.07x, top-6 33% -> 30%); pitch is the most box-sensitive axis (hard-pitch ss_error +80%: 0.295 -> 0.532deg). Re-visit analysis diagnose-20260715-011113 KEY QUESTION + generalization sections.
