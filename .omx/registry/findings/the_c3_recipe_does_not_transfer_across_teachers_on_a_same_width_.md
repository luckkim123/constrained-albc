---
title: "The C3 recipe does not transfer across teachers: on a same-width dgx16k teacher it loses at every DR level and reverses its hard win"
tags: ["albc", "student", "distillation", "c3", "gru", "dagger", "teacher-swap", "transfer", "dgx16k", "eval", "reproducibility"]
created: 2026-08-10T02:39:53.980778
updated: 2026-08-10T02:39:53.980778
sources: ["trpo_sddgx16k_c3_gruselect_s30_260809_222658", "static_260810_011725"]
links: ["x1_tail_split_restores_the_gen_2_latent_collapse_but_moves_no_co.md", "training_loss_latent_is_not_a_valid_corroborator_of_an_eval_side.md", "gru_memory_and_corrected_dagger_mixing_compound_c3_is_the_campai.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
---

# The C3 recipe does not transfer across teachers: on a same-width dgx16k teacher it loses at every DR level and reverses its hard win

The C3 recipe was re-run verbatim on a different teacher and lost to that teacher at every DR level, reversing the sign of the result C3 is known for.

## What ran

- Student `trpo_sddgx16k_c3_gruselect_s30_260809_222658`, group `student_distill_dgx16k`, 2026-08-09, 25 min on the DGX.
- Recipe is C3 verbatim: GRU 128 (head 64), `dagger_mix=select`, beta fixed 0.5, `lambda_latent` 1.0, 2048 envs x 1000 iter, seed 30. Bite check `student/dagger_teacher_frac = 0.49851`, so the select branch was exercised (beta alone cannot distinguish select from blend).
- Exactly ONE variable against C3: the teacher. `teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/model_13400.pt` in place of E-int.
- **Both teachers have `observation_space = 72`.** This is therefore a pure teacher-lineage swap with NO delivery-path change -- unlike Phase E (obs76, 76D), where teacher swap and delivery path were confounded and X1 had to separate them.
- Eval `static_260810_011725`, seed 42, 64 envs, `--doraemon-dr-from` pinned to the same teacher run the teacher's own eval (`static_260808_160132`) used, so both sides sit on identical DR levels.

## Result: worse at every level, sign reversed at hard

| att_norm ss_error, deg (floor 0.10) | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| teacher dgx16k | 0.5366 | 0.5411 | 0.6426 | 0.9702 |
| student (C3 recipe) | 0.8483 | 0.6356 | 0.9110 | 1.3728 |
| student - teacher | +0.3118 | +0.0945 | +0.2684 | +0.4026 |

Three of the four deltas clear the 0.10 floor in the WORSE direction; only soft is sub-floor and therefore unclaimed. C3's own hard delta was -0.1537, a decision-grade WIN. The sign is reversed and the magnitude is 2.6x.

Per-axis at hard: roll 0.7789 -> 1.1078, pitch 0.4211 -> 0.6264, yaw 0.0195 -> 0.0166. Roll carries the loss, as it has in every earlier arm of this line.

## Survival: the student dies where its teacher does not

Student hard survival 98.4% (1 death of 64); the dgx16k teacher's own eval is 100.0% (0 deaths). [[x1_tail_split_restores_the_gen_2_latent_collapse_but_moves_no_co]] found X1 matching its obs76 teacher's death count exactly (1 and 1) and read that as the H1 teacher-lineage side. Here the counts do not match, so death count is not simply inherited from the teacher.

## loss_latent fails as a corroborator, third instance

Open-loop `loss_latent` is 0.00207 -- 42% of C3's 0.004924, the lowest in this line -- while the eval is the worst in this line. In-loop `overall_mse` is 0.0360 / 0.0327 / 0.0377 / 0.0435 (none/soft/medium/hard), a 17-21x gap over the training loss. This reproduces [[training_loss_latent_is_not_a_valid_corroborator_of_an_eval_side]] a third time and extends the covariate-shift signature, which obs76 measured at 10-19x.

## Latent shape: shrinkage on the axis that must resolve, jitter on the axis that must be still

At hard, `l_true_envvar_mean` 0.047247 against `l_hat_envvar_mean` 0.020350: the student compresses across-env spread by 57% (medium 50%, 0.029966 -> 0.015044). In the other direction `l_true_tvar_mean` 0.003089 against `l_hat_tvar_mean` 0.007287: the true latent is near-constant within an episode because it is the reset-fixed DR vector, yet the prediction wobbles 2.4x more than the truth does.

Do NOT compare these in-loop MSE values against C3's numbers directly. The teachers differ, so the z target and its denominator differ; only the within-run teacher-vs-student contrast above is anchored. This is the same denominator trap the X1 self-correction records.

## What this constrains

[[gru_memory_and_corrected_dagger_mixing_compound_c3_is_the_campai]] should be read as a result about C3-on-E-int, not about the C3 recipe as such. Two teacher swaps have now failed to carry it: obs76 Phase E (confounded with delivery path) and dgx16k (this run, unconfounded). The mechanism that ties the C3 advantage to its original teacher is unidentified, and no probe currently isolates it.

