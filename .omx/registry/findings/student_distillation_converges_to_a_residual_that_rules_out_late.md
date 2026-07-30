---
title: "Student distillation converges to a residual that rules out latent multimodality (teacher-visited distribution only)"
tags: ["distillation", "student", "latent", "multimodality", "diffusion-rejection", "albc", "envs-main"]
created: 2026-07-21T10:03:15.840005
updated: 2026-07-30T03:49:59.271337
sources: []
links: ["albc_stage_2_is_teacher_driven_off_policy_bc_with_mixed_latent_a.md", "closed_loop_latent_collapse_suspicion_legacy_student_measured_11.md", "student_distillation_roll_heavy_tail_is_a_teacher_policy_propert.md", "experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Student distillation converges to a residual that rules out latent multimodality (teacher-visited distribution only)

Student distillation converges to a residual small enough to rule out latent multimodality -- but ONLY on the teacher's visited state distribution. This is the second independent reason to reject a diffusion policy for the student head (the first being that there is no evidence of multimodal targets to begin with).

## Measured convergence (F.mse_loss = elementwise mean, z in (-1,1)^9, last-50-iter mean)

| pack | student run_id | loss_latent | loss_action | total |
|:--|:--|--:|--:|--:|
| pack_B (deployed) | `trpo_student_tcn_260629_085241` | 0.00493 | 0.00226 | 0.00720 |
| pack_A | `trpo_student_tcn_armA_260629_105521` | 0.00358 | 0.00182 | 0.00539 |

## The argument

An MSE regressor converges to the conditional mean, so its residual is lower-bounded by the
conditional variance of the target: `residual >= E[Var(z|h)]`. Measured residual 0.00493 therefore
gives `E[Var(z|h)] <= 0.0049`.

The meaningful denominator is `l_true_envvar_mean` (variance of the teacher latent ACROSS envs),
independently measured at 0.030 (soft) to 0.080 (hard) in the eval-latent diagnostic. The residual
is <= 6% of the spread the latent is supposed to resolve. A multimodal `p(z|h)` -- two or more
separated modes -- cannot fit inside a conditional variance that small. Multimodality is
structurally excluded, not merely unobserved.

## Trap 1 (arithmetic): do NOT use `l_true.var()` as the denominator

The flat `l_true.var()` = 0.189 is dominated by the mean OFFSETS BETWEEN the 9 latent dimensions,
not by any within-dimension spread. `l_true` is also time-invariant within an episode
(`l_true_tvar_mean` ~ 1e-9) because the privileged input is the episode's DR parameter vector,
fixed at reset. The only denominator that carries information is the env-axis variance,
`l_true_envvar_mean`.

## Trap 2 (identification): the deployed student is under `logs/legacy/`

Verified on disk: pack_B's `checkpoints.student_tcn.path` in `MANIFEST.json` resolves to
`logs/legacy/rsl_rl/albc_trpo_student/trpo_student_tcn_260629_085241/`, while the ONLY student
directory under `logs/rsl_rl/albc_trpo_student/` is `trpo_student_tcn_armA_260629_105521` --
which belongs to pack_A. Picking "the student in logs/rsl_rl" without cross-checking MANIFEST.json
selects the wrong pack, exactly inverted.

## Scope limit (important)

This bound holds ONLY on the state distribution the teacher visits, because that is the only
distribution the training loss ever sampled (the rollout is teacher-driven -- see
[[albc_stage_2_is_teacher_driven_off_policy_bc_with_mixed_latent_a]]). It says nothing about the
closed-loop distribution the student actually induces at deployment; a separate, much worse
open-loop-vs-closed-loop gap has been measured on a legacy student and is tracked in
[[closed_loop_latent_collapse_suspicion_legacy_student_measured_11]].

Related: [[student_distillation_roll_heavy_tail_is_a_teacher_policy_propert]],
[[experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co]].

## Code verified 2026-07-21

- `constrained_albc/envs/_core/student/runner.py:186-189` -- `loss_latent = F.mse_loss(l_hat, batch.l_t)` (elementwise mean).
- `deploy/joint1_constraint/pack_B_5000iter_260629_090902/MANIFEST.json` -- student path under `logs/legacy/`.
- `constrained_albc/analysis/eval.py:897-915` -- `_summarize_latent` defines `l_true_envvar_mean` / `l_true_tvar_mean`.

---

## Update (2026-07-30T03:49:59.271337)

[PATH UPDATE 2026-07-30] The pack_A run cited in this page's table,
trpo_student_tcn_armA_260629_105521, has MOVED. This page's line stating that its
directory is under logs/rsl_rl/albc_trpo_student/ is now stale.

New locations (both trees, mirrored):
  logs/legacy/rsl_rl/albc_trpo_student/trpo_student_tcn_armA_260629_105521
  experiments/legacy/rsl_rl/albc_trpo_student/trpo_student_tcn_armA_260629_105521

Why it moved: it was one of six runs sitting loose directly under <exp>/ with no group
layer, which left campaign-drift reporting unregistered groups. Supersession was
fact-checked before the move rather than assumed -- its teacher is
joint1_constraint/trpo_avg_constraint_d05_260628_040906 from the retired joint1
lineage, whereas the live student campaign (student_distill_eint) distills E-int. Byte
totals were verified identical on both sides and the train symlink was recreated at the
new depth. The run_id is unchanged, so every citation that names the id rather than a
path still resolves.

