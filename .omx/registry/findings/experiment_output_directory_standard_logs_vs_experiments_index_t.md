---
title: "experiment output directory standard (logs vs experiments index tree)"
tags: ["albc", "conventions", "directory", "layout", "run_id", "experiments", "logs", "legacy", "index", "retired"]
created: 2026-06-07T06:04:28.720146
updated: 2026-06-30T07:06:52.385941
sources: []
links: ["constrained_albc_experiment_conventions.md", "experiment_launch_checklist_run_id_wandb_latest_alias_naming.md", "experiment_result_recording_location_experiments_tree_is_ssot_no.md"]
category: convention
confidence: high
schemaVersion: 1
---

# experiment output directory standard (logs vs experiments index tree)

The approved layout for all training experiment outputs (user-approved 2026-06-07). The STRUCTURE is the invariant; the run_id name is orthogonal (a mis-named run still has the right structure). Full definition: docs/plans/2026-06-07-experiment-dir-standard.md.

STANDARD TREE (disk-verified):

constrained-albc/
  logs/rsl_rl/<exp>/<group>/<run_id>/          # TRAIN output, HEAVY, gitignored
    tb/                                        #   TensorBoard events
    checkpoints/ (or root) model_*.pt          #   checkpoints (numeric sort, model_4999.pt final)
    wandb/                                     #   wandb LOCAL run dir (disk side). The SERVER side
                                               #   (project=campaign / group / tags) is governed by the
                                               #   launch checklist, NOT by this path.
    params/{env.yaml, agent.yaml}              #   rsl_rl resolved config
  experiments/rsl_rl/<exp>/<group>/<run_id>/   # run-id index tree, LIGHT, gitignored
    train -> ../../../../../logs/rsl_rl/<exp>/<group>/<run_id>   # relative symlink (5 up) into logs
    eval/<mode>_<ts>/                          #   eval output (static_<ts>, periodic_<ts>, ...)
    encoder/sweep/                             #   encoder z-sensitivity sweep
    config/{env.yaml, agent.yaml}              #   resolved config copy
    analysis/diagnose-<YYYYMMDD-HHMMSS>/       #   exp-analyze canonical output
      report.md, report.ko.md, manifest.json, plots/
    manifest.json                              #   run_id SSOT (paths / git.sha / task)

8 PRINCIPLES (why this structure):

1. logs = heavy real data, experiments = light index. train's tb/checkpoints/wandb (multi-GB) live ONLY in logs/. experiments/ points at them via the `train` symlink and directly holds only eval/encoder/analysis/manifest. So one run = one experiments/ dir = a single entry point to every artifact (train is one symlink hop away).
2. Mirror layout rsl_rl/<exp>/<group>/<run_id>/ on both sides -> the symlink is always ../../../../../logs/... (relative, 5 up, survives tree moves).
3. <exp> = experiment_name (e.g. albc_trpo_teacher, albc_trpo_student), from agent.experiment_name.
4. <group> = campaign/purpose bucket (e.g. dr_harder). Optional 1 level. Gathers a campaign's runs in one dir.
5. <run_id> = <task_short>[_<tag>]_<ts> (label-before-date). make_run_id (paths.py:94) is the single source. task_short(Isaac-ConstrainedALBC-TRPO-v0)=trpo; tag=run_name (experiment tag, MANDATORY for experiments); ts=%y%m%d_%H%M%S (RUN_TS_FORMAT paths.py:91), trailing. NEVER date-first.
6. eval ts uses the SAME format (static_260607_041900). run_id and eval share one date-format -> no drift.
7. latest alias = inside the group dir. <exp>/<group>/latest -> <newest run_id> (relative link, run basename). No group -> <exp>/latest. If the tree is grouped, the alias MUST sit inside the group or it cannot point at that group's newest run.
8. baseline alias = <group>/baseline -> <reference run_id> (campaign baseline pointer, optional).

RELATED RULES: run_id naming + e-number campaign-continuity + wandb single-project + launch checklist are in [[experiment_launch_checklist_run_id_wandb_latest_alias_naming.md]]. Result recording (report.md/README/DESIGN) is in [[experiment_result_recording_location_experiments_tree_is_ssot_no.md]]. The experiment-discipline hub is [[constrained_albc_experiment_conventions.md]]. eval output placement (--output_dir forbidden, checkpoint via `train` symlink path) is in rule 03-analysis-quality.

---

## Update (2026-06-30T07:06:52.385941)

LEGACY / RETIRED-RUN convention (established 2026-06-30 cleanup):

- ONE legacy place: experiments/legacy/ and logs/legacy/ are the single home for retired/closed runs. Do NOT scatter a per-campaign legacy/ inside the active tree (e.g. the old experiments/rsl_rl/<exp>/legacy/dr_harder was folded up into experiments/legacy/rsl_rl/<exp>/dr_harder_e1e4_campaign on 2026-06-30). Active tree (experiments/rsl_rl/, logs/rsl_rl/) holds ONLY the run the next experiment builds on.
- Legacy MIRRORS the standard tree: experiments/legacy/rsl_rl/<exp>/<group>/<run_id>/ + logs/legacy/rsl_rl/<exp>/<group>/<run_id>/. Same mirror means the `train` symlink is recomputed (realpath --relative-to) to point experiments/legacy/.../run/train -> ../../../../../../logs/legacy/.../run (6-up when grouped, 5-up when ungrouped). Pre-run_id-standard frozen artifacts (2026-04 r2~r13 PNG plots, final_models) stay at experiments/legacy/plots and experiments/legacy/final_models (no logs side — raw logs were deleted at repo-split).
- Legacy checkpoint policy: trim to model_<final>.pt ONLY (numeric sort, e.g. model_4999.pt); move intermediate model_*.pt to /workspace/.trash/ (recoverable). NEVER alpha-sort (model_950 > model_4999 is the model-trim disaster). Active runs keep their full checkpoint set.
- MASTER INDEX: experiments/INDEX.md is the one-page grep map of every run (run_id | group | date | active/legacy/retired | 1-line result | report+logs path). It points at each run's analysis/diagnose-*/report.md (the SSOT); it does not duplicate metrics. Update it whenever a run is added or a line is retired.

