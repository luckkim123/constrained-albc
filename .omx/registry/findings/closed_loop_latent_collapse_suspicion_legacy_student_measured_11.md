---
title: "Closed-loop latent collapse suspicion: legacy student measured 11-17x worse in-loop, deployed student unverified"
tags: ["experiment-lead", "distillation", "covariate-shift", "latent", "student", "sim-to-real", "eval", "albc", "priv-obs"]
created: 2026-07-21T10:03:29.000311
updated: 2026-07-21T10:16:52.443487
sources: []
links: ["albc_stage_2_is_teacher_driven_off_policy_bc_with_mixed_latent_a.md", "experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co.md", "next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md", "student_distillation_converges_to_a_residual_that_rules_out_late.md", "engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact.md"]
category: decision
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
---

# Closed-loop latent collapse suspicion: legacy student measured 11-17x worse in-loop, deployed student unverified

A legacy student's latent estimate degraded 11-17x when it drove the loop itself, versus its
open-loop training residual. The DEPLOYED student has never been run through this diagnostic. The
honest statement is "there is precedent for collapse and the deployed checkpoint is unverified",
NOT "the student collapses".

## The instrument already exists -- zero new code

`constrained_albc/analysis/eval.py` student mode runs the student IN THE LOOP and writes
`latent_<level>.npz` (`l_hat`, `l_true`) plus `summary_latent.json` across all four DR levels.
`_summarize_latent` (`eval.py:897-915`) emits `overall_mse`, `per_dim_mse`, `l_true_envvar_mean`,
`l_hat_envvar_mean`, `l_true_tvar_mean`, `l_hat_tvar_mean`, `per_env_rmse_mean/std`. The probe
below is one eval invocation, not an engineering task.

## Legacy measurement (`trpo_student_tcn_260526_043607`, 87D-era, training loss_latent 0.0144, 4 envs)

| DR level | in-loop latent MSE | `l_true_envvar_mean` | ratio |
|:--|--:|--:|--:|
| none | 0.1612 | 0.0 | (undefined -- see below) |
| soft | 0.2058 | 0.0297 | 6.9x |
| medium | 0.2500 | 0.0659 | 3.8x |
| hard | 0.1942 | 0.0800 | 2.4x |

The in-loop error is 2-8x LARGER than the env-to-env variance the latent is supposed to resolve
(R^2 deeply negative -- predicting the global mean would beat it), and 11-17x worse than the same
student's open-loop training residual.

## The decisive row is `none`

At DR level `none`, `l_true` is a CONSTANT: `l_true_envvar_mean` = 0.0 and `l_true_tvar_mean` ~ 1e-9
(the privileged vector is the fixed DR parameter set). Yet the in-loop error is 0.161, and `l_hat`
itself moves -- envvar 0.062, tvar 0.0019. A student estimating a constant should output a constant.
Instead it is being dragged around by the instantaneous state.

That signature is **covariate shift**, not multimodality: the student is reacting to states its
training distribution never contained. The teacher-driven rollout documented in
[[albc_stage_2_is_teacher_driven_off_policy_bc_with_mixed_latent_a]] is the direct candidate cause --
the student is never trained on the distribution it induces.

## UNVERIFIED -- state this every time

The deployed pack_B student `trpo_student_tcn_260629_085241` has **never** had this diagnostic run.
The legacy student differs on three axes at once: 87D-era observation space, only 4 eval envs, and a
training `loss_latent` (0.0144) about 4x worse than the deployed student's 0.00493. The legacy
numbers are a precedent, not a measurement of the deployment.

## Next probe (this lead's experiment)

Run `eval.py` student mode ONCE using the student + teacher checkpoints named in pack_B's
`MANIFEST.json`, then compare `summary_latent.json`'s per-level in-loop MSE against the same level's
`l_true_envvar_mean` -- the same table as above, for the deployed checkpoint. The run also yields, for
free, the task-metric oracle gap: teacher driven by `z_gt` vs student driven by `z_hat`.

WARNING -- do NOT auto-launch training. If any retrain follows from the result, queue it via
`omx queue-launch` and stop at the human gate.

## Related

- [[experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co]] -- the state-conditioned-z
  idea meshes directly with this observation; if z is already a function of `o_t`, the student's
  state-dragging behavior changes meaning.
- [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]] -- decide whether this lead
  earns a line in the retrain manifest (it is a diagnosis probe, not a code change, so it likely
  does NOT block the retrain -- but the decision should be recorded there rather than left implicit).
- [[student_distillation_converges_to_a_residual_that_rules_out_late]] -- the open-loop bound whose
  scope limit this page is.
- [[engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact]] -- adjacent eval-npz coverage gap.

---

## Update (2026-07-21T10:16:52.443487)

## Connection to A4 (priv-obs slim, 2026-07-21)

A4 (`trpo_privslim24d_260721_114717`) dropped `root_lin_vel_b` from the teacher's
privileged vector and failed every eval clause of its band (`none` roll ss_error +73.6%,
pitch +95.3%), resolving `lin_vel` as LOAD-BEARING rather than redundant: `envs/main`'s
`compute_policy_obs` is 20D and carries no linear velocity in any form ("no DVL on real
robot"), so the privileged channel was its only route into the network.

That matters here because the student's observation is the 69D attitude-only history --
it likewise cannot see linear velocity directly. Whatever the teacher was doing with
`lin_vel`, the student must reconstruct from its observation history alone. A4 confirms
the channel is one whose removal collapses tracking, which raises the prior that
in-loop student degradation is concentrated on exactly the latent content `lin_vel`
drove (the anchor z_sweep shows Lin Vel U/V/W driving 9/9, 9/9 and 8/9 latent dims).

This is CIRCUMSTANTIAL, not evidence: A4 measured a teacher ablation, not a student
reconstruction failure, and a history-based estimator may well recover the signal.
The discriminating measurement is the next probe's `per_dim_mse` -- if the latent dims
that `lin_vel` drives carry disproportionate error relative to the other dims, the
suspicion is supported; if the error is flat across dims, this connection is refuted
and the in-loop gap lies elsewhere.

