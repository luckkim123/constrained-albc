---
title: "constrained-albc experiment conventions"
tags: ["albc", "setup", "conventions", "branch", "isolation"]
created: 2026-06-02T08:08:01.219310
updated: 2026-06-07T06:30:00.000000
sources: []
links: ["experiment_output_directory_standard_logs_vs_experiments_index_t.md", "experiment_launch_checklist_run_id_wandb_latest_alias_naming.md", "experiment_result_recording_location_experiments_tree_is_ssot_no.md"]
category: convention
schemaVersion: 1
confidence: high
---

# constrained-albc experiment conventions

This is the experiment-discipline hub. The full experiment ruleset (storage layout, launch naming + wandb, result location, branch hygiene) lives across these four convention pages -- this one is the entry point:
- [[experiment output directory standard (logs vs experiments index tree)]] -- where outputs live (logs vs experiments index tree).
- [[experiment launch checklist: run_id / wandb / latest-alias naming]] -- run_id naming, tag, e-number, latest alias, wandb single-project.
- [[experiment result recording location (experiments tree is SSOT, not docs/results)]] -- where results are recorded (report.md / README.md / DESIGN.md).

## Project setup

Objective: reduce attitude/lin-vel tracking error under DR while satisfying 10 ConstraintTRPO constraints. Metric vocab (TB, 134 tags): reward_total, att_roll/pitch_err_deg, lin_err_x/y/z, yaw_rate_err, entropy, noise_std, z_std, line_search_success, barrier_penalty, Constraint/viol+margin (10 each), DORAEMON success_rate. keep_policy: pass_only. output_root: experiments. Sources: tensorboard (events.out.tfevents) + wandb. Algorithm: ConstraintTRPO + IPO + asymmetric encoder (latent_dim=9, elu+LayerNorm+softsign). Ocean current enabled. Eval is eval_dr static (separate from training-log analysis).

## Branch hygiene = experiment isolation (user-approved 2026-06-07)

Per-experiment branch separation is allowed. The forbidden thing is NOT a branch location -- it is "proceeding while unaware of the current branch" (unconscious accumulation).

- Branch location is free by intent. Branching e9 from main, from exp/e9-<topic>, or INTENTIONALLY from exp/e8 (a deliberate cumulative experiment, e.g. evolving e8's change into e9) are all valid. The rule is only that you CHOOSE the base consciously.
- Forbidden = awareness failure. The case to prevent: launching e9 while unknowingly still on the previous experiment's branch (e8), thinking you are on main, so e8's code change leaks into e9 and confounds the comparison.
- Obligation = know the branch + confirm the intended base, every time. Run `git branch --show-current` before each experiment, then confirm "is this base the branch point I intend for THIS experiment?" before proceeding. This conscious check is the price of allowing per-experiment branches.
- Record the chosen base. Write the branch point (main / exp/e8 / baseline tag) into the campaign's tracability docs so a future reader can tell an intended chain from an accident (see tracability below + the result-recording page).

## Experiment tracability (record before/with each run)

Baseline run id, experiment branch / branch base, the applied code change, and the verdict go into the campaign's experiments tree: experiments/.../<group>/DESIGN.md (plan/intent, before the run) and experiments/.../<group>/README.md (summary/verdict, after). Even without a worktree, record which baseline tag/branch the experiment forked from. The result SSOT is the experiments tree, not docs/results -- see [[experiment result recording location (experiments tree is SSOT, not docs/results)]].

## Git isolation procedure (lives in rules/02-operations.md, not here)

The git-native isolation procedure -- annotated baseline tag (`baseline-<YYMMDD>-<topic>`), exp/<topic> branch, merge-on-adopt / `git branch -D` on-discard, worktree promotion only for 2+ GPU parallel runs -- is a git workflow and stays in rules/02-operations.md section "Comparison-experiment isolation". This page covers the experiment-discipline half (branch awareness + tracability); that section covers the git-procedure half.
