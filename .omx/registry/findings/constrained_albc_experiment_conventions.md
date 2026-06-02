---
title: "constrained-albc experiment conventions"
tags: ["albc", "setup", "conventions"]
created: 2026-06-02T08:08:01.219310
updated: 2026-06-02T08:08:01.219310
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
---

# constrained-albc experiment conventions

Objective: reduce attitude/lin-vel tracking error under DR while satisfying 10 ConstraintTRPO constraints. Metric vocab (TB, 134 tags): reward_total, att_roll/pitch_err_deg, lin_err_x/y/z, yaw_rate_err, entropy, noise_std, z_std, line_search_success, barrier_penalty, Constraint/viol+margin (10 each), DORAEMON success_rate. keep_policy: pass_only. output_root: experiments. Sources: tensorboard (events.out.tfevents) + wandb_offline (project=constrained_albc). Algorithm: ConstraintTRPO + IPO + asymmetric encoder (latent_dim=9, elu+LayerNorm+softsign). Ocean current enabled. Eval is eval_dr static (separate from training-log analysis).
