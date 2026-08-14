---
title: "A checkpoint ranking established at none can dissolve at hard and ood: re-test finalists out of distribution before picking a deployment checkpoint"
tags: ["ood", "generalization", "checkpoint-selection", "eval", "paired-test", "deployment"]
created: 2026-08-09T05:18:54.691494
updated: 2026-08-09T05:18:54.691494
sources: ["diagnose-20260809-142000"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# A checkpoint ranking established at none can dissolve at hard and ood: re-test finalists out of distribution before picking a deployment checkpoint

A checkpoint ranking established at the `none` level does not survive to `hard` or `ood`. Re-test it there before using it to pick a deployment checkpoint — OOD does not necessarily INVERT the nominal ranking, but it can DISSOLVE it, and a dissolved ranking read as a live one picks the wrong model for the wrong reason.

MEASURED on trpo_dgx16k_s30_260805_185713, paired per-env over the same 64 seed-42 scenarios:

| A -> B | `none` t | `hard` t | `ood` t |
|---|---|---|---|
| 7500 -> 13400 | +7.53 (6/64) | +0.63 | +1.59 |
| 7500 -> 10000 | +13.49 (4/64) | +2.06 | +0.60 |

model_7500 beats model_13400 overwhelmingly on nominal physics — the later model wins in only 6 of 64 scenarios — and the two are statistically indistinguishable once DR is on (`hard`) or beyond the training box (`ood`). The advantage is real and it is confined to the least deployment-relevant condition: real hardware is OOD relative to sim, never nominal.

Level means (att_norm ss_error, deg): 7500 = none 0.4968 / hard 0.9224 / ood 0.9559; 13400 = none 0.5366 / hard 0.9702 / ood 1.1222.

DO NOT over-read failure counts. model_13400 is the only checkpoint with zero OOD terminations (0/64 vs 1/64 at 7500 and 10000, 3/64 at 5000). Fisher exact on 0/64 vs 1/64 gives p = 1.0. Monotone-looking failure counts at n=64 are not evidence of a robustness win.

PER-AXIS matters for the diagnosis: at `ood`, model_13400 has the BEST pitch of the four (0.4267 vs 0.4918 / 0.5614 / 0.6311) and a worse roll than 7500 (0.9470 vs 0.6986). The aggregate `ood` gap is entirely a roll gap, consistent with the lineage's standing roll-DC-bias pattern (see e5_alpha075_ood_per_axis_generalization_gap_universal_failure_ro).

PROCEDURE. Cross-checkpoint verdicts are read at `none` because it is the only invariant level (eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr). That rule is about COMPARABILITY, not about RELEVANCE. When the decision is which checkpoint to deploy rather than which config won, run `--ood` on the finalists and check whether the `none` ranking still separates them. Two checkpoints evaluated at the SAME time share one box, so their hard/ood comparison is internally valid even though it cannot be compared to another eval batch.

SOURCE: experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md, section "generalization"; eval/static_260808_162023 / 163510 / 164947 / 170426 with --ood.

