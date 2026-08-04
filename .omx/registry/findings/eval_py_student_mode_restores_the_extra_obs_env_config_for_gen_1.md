---
title: "eval.py student-mode restores the extra-obs env config for GEN-1 only: a gen-2 student carries extra_obs_dim=0, so the restore block is skipped and env.use_extra_policy_obs=True must be passed explicitly or the env builds 72D against a 76D student"
tags: []
created: 2026-08-04T03:54:21.676975
updated: 2026-08-04T03:54:21.676975
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# eval.py student-mode restores the extra-obs env config for GEN-1 only: a gen-2 student carries extra_obs_dim=0, so the restore block is skipped and env.use_extra_policy_obs=True must be passed explicitly or the env builds 72D against a 76D student

## The gap

`eval.py` student mode restores the extra-obs env configuration off the CHECKPOINT rather than
from CLI flags, with an explicit rationale in the code: "a flag can be forgotten, and a forgotten
flag would silently evaluate the student against an absent key or against a DIFFERENT sensor model
than it was trained on".

That block is gated on `_sc.get("extra_obs_dim", 0) > 0` (eval.py:1109) and it sets
`env_cfg.use_student_extra_obs = True`. Both halves are GEN-1.

A gen-2 student carries `extra_obs_dim == 0` BY DESIGN -- in gen-2 the 4 channels are folded into
`policy_obs` (72 -> 76) and there is no side channel to read. So the whole block is skipped,
`use_extra_policy_obs` is never restored, the env builds at 72D, and the 76D student dim-mismatches
on load. The very failure mode the comment exists to prevent, one generation later.

## Until it is fixed

Pass `env.use_extra_policy_obs=True` explicitly on EVERY gen-2 eval, student or teacher. The
teacher side has the same hole for the same reason (the restore is student-mode-only), and that is
already recorded on the Phase D pages.

Full gen-2 student eval invocation -- note that `--teacher_ckpt` and `--encoder_type` are REQUIRED
alongside `--student_ckpt` (eval.py:243-246), because student mode runs the student encoder feeding
the FROZEN TEACHER ACTOR and needs both halves:

    eval.py static --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless \
        --student_ckpt <run>/train/student_999.pt \
        --teacher_ckpt <teacher run>/train/model_4999.pt \
        --encoder_type gru \
        env.use_extra_policy_obs=True

No `--output_dir`: the checkpoint sits under the run-id tree via the `train` symlink, so eval.py
routes artifacts to `experiments/<run_id>/eval/static_<ts>/` itself.

## Suggested fix when someone touches this path

Widen the gate to `extra_obs_dim > 0 OR the checkpoint records a gen-2 env`, and persist the gen-2
flag into the student checkpoint the same way `env_sensor_cfg` already is. The current design
persists the four sensor params but not the flag that decides which generation is in play.

