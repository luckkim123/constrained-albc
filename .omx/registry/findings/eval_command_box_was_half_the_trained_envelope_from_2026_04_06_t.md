---
title: "Eval command box was HALF the trained envelope from 2026-04-06 to 2026-07-15 -- every pre-posttam attitude number is optimistic"
tags: ["eval-methodology", "command-box", "att-amp", "yaw-rate", "comparability", "historical-numbers", "teacher-baseline-opt", "april-2026", "rule03", "cross-run"]
created: 2026-07-20T06:24:10.057411
updated: 2026-07-20T06:24:10.057411
sources: ["8c07584", "7f09681", "f4583fd", "11dcad64", "static_260713_075722", "static_260715_003649", "static_260715_004654"]
links: ["tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_.md", "april_2026_entropy_collapse_campaign_machinery_bug_solved_conver.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Eval command box was HALF the trained envelope from 2026-04-06 to 2026-07-15 -- every pre-posttam attitude number is optimistic

For 2026-04-06 through 2026-07-15, every eval in this project graded policies on EXACTLY HALF the
command envelope they were trained on -- on both the attitude and the yaw-rate axis. All absolute
attitude numbers from that window are therefore optimistic and are NOT comparable to post-2026-07-15
full-box numbers.

## The two boxes and when they changed

TRAINING box (`envs/main/config.py:471,473`):
- `11dcad64` (2026-04-01): `att_cmd_rp_range = +-pi/4` (+-45 deg), `yaw_rate_cmd_range = +-0.5`
- `f4583fd` (2026-04-06): att narrowed to `+-pi/6` (+-30 deg). yaw_rate UNTOUCHED, +-0.5 from day one.
- No further change through HEAD (2026-07-20); `bc73680` (06-12) was a rename only.

EVAL box (`analysis/_eval_dr/trajectory.py:14-16`):
- `7f09681` (2026-04-04): introduced `ATT_AMP_DEG = 15.0`, `YAW_RATE_AMP = 0.25`, `LIN_VEL_AMP = 0.25`.
- `f2411cf` (04-06) and `ec3eac7` (05-25, extraction refactor): touched the file, values PRESERVED.
- `8c07584` (2026-07-15 00:30): `ATT_AMP_DEG 15 -> 30`, `YAW_RATE_AMP 0.25 -> 0.5`, with new
  `--att-amp-deg` / `--yaw-rate-amp` CLI overrides so the old box can still be reproduced.

`git log --all -S"ATT_AMP_DEG"` finds exactly three value-touching commits, so the +-15/+-0.25 box
was in force continuously from 2026-04-04 to 2026-07-15 00:30. There is no window where it drifted.

## Timeline

| window | training box (att / yaw) | eval box (att / yaw) | runs graded in it |
|---|---|---|---|
| 04-01 - 04-04 | +-45 deg / +-0.5 | (eval harness not yet written) | -- |
| 04-04 - 04-06 | +-45 deg / +-0.5 | +-15 deg / +-0.25 | earliest April runs |
| **04-06 - 07-15 00:30** | **+-30 deg / +-0.5** | **+-15 deg / +-0.25 (HALF on both axes)** | the whole April 49-run campaign; the whole `teacher_baseline_opt` campaign incl. VOID baseline `trpo_baseline_260713_031325` (eval `static_260713_075722`) |
| 07-15 00:36 onward | +-30 deg / +-0.5 | +-30 deg / +-0.5 by default | `teacher_baseline_posttam` full-box evals, e.g. `static_260715_004654` |

## Verified empirically, not just from the diff

Eval npz files carry the raw `target_roll_deg` / `target_pitch_deg` / `target_yaw_rate` arrays, so
the box a given eval actually used is directly measurable:
- VOID `teacher_baseline_opt/trpo_baseline_260713_031325/eval/static_260713_075722/data_none.npz`:
  `max|target_roll_deg| = 15.0`, `max|target_yaw_rate| = 0.25`
- POSTTAM `trpo_baseline_260714_192020/eval/static_260715_003649` (MATCHED): 15.0 / 0.25 -- produced
  post-`8c07584` using the explicit `--att-amp-deg 15 --yaw-rate-amp 0.25` override, precisely so it
  would be comparable to the VOID numbers.
- POSTTAM `.../static_260715_004654` (FULL, same checkpoint, 10 min later): 30.0 / 0.5.

So the VOID-vs-POSTTAM(MATCHED) comparison IS apples-to-apples on the command box. Any comparison of
a pre-07-15 run against a post-07-15 FULL-box eval is NOT.

## How to use this

1. When quoting any attitude number from the April campaign or `teacher_baseline_opt`, state that it
   was measured on the half box. Do not place it in a table next to a full-box number without a note.
2. When re-evaluating an old checkpoint for comparison, pass `--att-amp-deg 15 --yaw-rate-amp 0.25`
   to reproduce the historical box, or re-evaluate BOTH sides at full box. Never mix.
3. The half-box bias is not uniform across axes: on the same checkpoint, doubling the box raises the
   roll floor ~15% but hard-pitch ss_error ~80% (0.295 -> 0.532 deg). Pitch is the axis whose
   historical numbers were most flattered. See
   [[tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_]].
4. Structural robustness does generalise across the box: doubling it did NOT re-open a heavy-tail
   (hard roll max/median 7.49x -> 6.07x). So the half-box era's TAIL conclusions survive; it is the
   ACCURACY numbers that were flattered. See
   [[tam_plant_correctness_fix_collapses_the_void_hard_dr_roll_heavy_]].

## Limitation

The April campaign's raw TB/wandb data and all but two checkpoints were deleted 2026-05-25 (see
[[april_2026_entropy_collapse_campaign_machinery_bug_solved_conver]]), so its numbers cannot be
re-measured at full box -- only annotated. Only `experiments/legacy/final_models/r13_{A,B}/model_4999.pt`
survive and could in principle be re-evaluated, though the runtime that produced them no longer exists.

