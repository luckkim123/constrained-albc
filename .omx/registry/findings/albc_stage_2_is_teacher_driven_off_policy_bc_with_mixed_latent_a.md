---
title: "ALBC stage 2 is teacher-driven off-policy BC with mixed latent+action labels (differs from RMA/HORA on both axes)"
tags: ["distillation", "student", "off-policy", "methods", "rma", "taxonomy", "albc"]
created: 2026-07-21T10:03:20.346113
updated: 2026-07-21T10:03:20.346113
sources: []
links: ["closed_loop_latent_collapse_suspicion_legacy_student_measured_11.md", "student_distillation_converges_to_a_residual_that_rules_out_late.md", "student_distillation_roll_heavy_tail_is_a_teacher_policy_propert.md", "experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# ALBC stage 2 is teacher-driven off-policy BC with mixed latent+action labels (differs from RMA/HORA on both axes)

ALBC's stage-2 distillation is NOT the RMA/HORA phase-2 recipe it is often assumed to be. It
differs on BOTH of the two axes that define such a method: which policy drives the rollout, and
which quantities are regressed. State it correctly in any methods section.

## Axis 1 -- rollout driver: the teacher, always (off-policy BC, no DAgger)

`constrained_albc/envs/_core/student/runner.py:145-164`, `_collect_rollout`:

```
a_t, l_t = self.teacher.act(obs, privileged)   # teacher is frozen: policy.eval() + @torch.no_grad
self.buffer.add(obs, privileged, l_t, a_t, prev_dones)
obs_next, _rew, dones, extras = self.env.step(a_t)   # env stepped with the TEACHER action
```

The student never drives the environment -- not on the first iteration, not on the last. There is
no DAgger-style mixing schedule and no student-in-the-loop data collection anywhere in the runner.
`configure_env_for_student` (`runner.py:37-66`) additionally disables DORAEMON and overwrites
`env_cfg.randomization` with a fresh hard `DomainRandomizationCfg`, so the collection distribution
is STATIC hard DR, not a curriculum.

## Axis 2 -- labels: latent AND action, not latent-only

`runner.py:176-189`, `_compute_loss_tcn` (the GRU path at 191-207 is identical in structure):

```
l_hat  = student(obs_window_normalized)                 # (M, 9)
a_hat  = teacher.actor_forward(teacher.normalize_obs(obs_t), l_hat)   # (M, 8), frozen actor
loss   = F.mse_loss(a_hat, a_t) + lambda_latent * F.mse_loss(l_hat, l_t)
```

`lambda_latent = 1.0` (`_core/student/config.py:70`). `teacher.actor_forward` is deliberately NOT
decorated with `@torch.no_grad` (unlike `act` and `encode_privileged`), so the action term
backpropagates through the frozen actor into `l_hat` and reaches only the student network. This is
the Lee 2020-style mixed latent+action objective, not a pure latent regression.

## Contrast with the literature

RMA (arXiv:2107.04034) and HORA (arXiv:2210.04887) phase 2 both unroll the environment with the
STUDENT's own estimate `z_hat`, i.e. on-policy adaptation-module training. ALBC differs on both
axes simultaneously: label type AND rollout driver. Do not cite ALBC stage 2 as "RMA-style phase 2".

## Methods sentence (quotable verbatim)

> teacher-driven behavior cloning under static hard domain randomization; the student never
> generates the state distribution it is evaluated on.

## Side note: the oracle-gap probe is already instrumented

`||pi(o, z_hat) - pi(o, z_gt)||` is exactly `loss_action`, already logged every iteration. No new
instrumentation is needed to measure how much the latent error costs in action space -- on the
teacher's distribution. On the CLOSED-LOOP distribution it is not measured; see
[[closed_loop_latent_collapse_suspicion_legacy_student_measured_11]].

Related: [[student_distillation_converges_to_a_residual_that_rules_out_late]] (the residual bound
this rollout scheme scopes), [[student_distillation_roll_heavy_tail_is_a_teacher_policy_propert]],
[[experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co]].

## Code verified 2026-07-21

- `_collect_rollout` teacher-driven: `runner.py:147,151,154`.
- Frozen teacher: `_core/student/teacher.py:137` (`policy.eval()`), `:170` (`@torch.no_grad` on `act`);
  `actor_forward` at `:160` is intentionally undecorated so gradients flow.
- Loss + lambda: `runner.py:186-189`, `config.py:70`.

