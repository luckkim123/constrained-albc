---
title: "`lin_vel` is NOT a redundant privileged dim in `envs/main`. The policy observati"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `lin_vel` is NOT a redundant privileged dim in `envs/main`. The policy observati

`lin_vel` is NOT a redundant privileged dim in `envs/main`. The policy observation is 20D and contains command(3) + euler(3) + body angular velocity(3) + arm(5) + thruster(6) — no linear velocity in any form, by explicit design ("Linear velocity is excluded -- no DVL on real robot"). Removing `root_lin_vel_b` from p_t therefore deleted linear velocity from the entire network, not a duplicate copy of it.

[EVIDENCE: `constrained_albc/envs/main/mdp/observations.py` `compute_policy_obs` torch.cat contents read directly at HEAD; docstring lines 17-18 and 24 confirm "no measured lin_vel" / "no lin_vel_err"]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
