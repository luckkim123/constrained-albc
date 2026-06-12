---
title: "train.py --run_group creates the <group> layer (no more manual post-move)"
tags: ["albc", "conventions", "directory", "run_group", "group", "train", "layout", "att_dr_harder"]
created: 2026-06-08T05:05:17.476530
updated: 2026-06-08T05:07:00.875433
sources: []
links: ["experiment_output_directory_standard_logs_vs_experiments_index_t.md", "experiment_launch_checklist_run_id_wandb_latest_alias_naming.md"]
category: convention
confidence: high
schemaVersion: 1
---

# train.py --run_group creates the <group> layer (no more manual post-move)

train.py now CREATES the `<group>` layer itself via the `--run_group` flag (added 2026-06-08), so a campaign no longer needs a manual post-move. This closes the dr_harder mislocation root cause: previously train.py built only `logs/rsl_rl/<exp>/<run_id>/` (2 tiers) and the `<group>/` dir (e.g. dr_harder/) was created by an analysis worker moving runs by hand AFTER training -- so a forgotten move scattered runs (E5/E6 landed outside dr_harder/).

HOW IT WORKS (verified by GPU smoke 2026-06-08):
- `--run_group <name>` inserts the group segment in BOTH trees: `logs/rsl_rl/<exp>/<group>/<run_id>/` and `experiments/rsl_rl/<exp>/<group>/<run_id>/`.
- The `train` symlink is computed with `os.path.relpath` (paths.py emit_run_manifest), NOT a hardcoded depth, so the extra group level is absorbed automatically -- the link still reads `../../../../../logs/...` and resolves correctly.
- `update_latest_symlink` keys off the launch dir's PARENT, so with a group the `latest` alias lands inside the group dir (`<exp>/<group>/latest`), satisfying directory-standard principle 7 with no extra code.
- Omitting `--run_group` keeps the original `<exp>/<run_id>/` 2-tier layout (back-compat, no regression).

CODE LOCI: scripts/train.py (`--run_group` CLI + log_dir join + emit_run_manifest group= + config["run_group"]); paths.py experiments_group_dir(..., group=) and emit_run_manifest(..., group=). Tests: tests/test_paths.py group-write tests (test_experiments_group_dir_with_group, test_emit_run_manifest_group_layer + no-group back-compat). 56 sim-free pass.

TERMINOLOGY (resolves the naming the user uses vs the standard's labels -- SAME structure, different words):
- user "<learning_phase>" == standard "<exp>" == agent.experiment_name (e.g. albc_trpo_teacher / albc_trpo_student). The teacher/student training phase.
- user "<experiment_name>" == standard "<group>" == `--run_group` value (e.g. att_dr_harder). The campaign/experiment-group bucket.
- user "run_name" == standard "<run_id>" == make_run_id output (trpo_e1_..._<ts>).
- wandb project = the campaign = the group name (att_dr_harder). AttitudeOnly's agent cfg sets wandb_project="att_dr_harder" as the default; override with --log_project_name for a different campaign. This is consistent with the launch checklist's "one campaign = one project".

LAUNCH (AttitudeOnly campaign): `python scripts/train.py --task Isaac-ConstrainedALBC-AttitudeOnly-TRPO-v0 --run_group att_dr_harder --agent run_name=e1_<knob> --num_envs 4096 --max_iterations 5000 --headless --logger wandb --log_project_name att_dr_harder`. The `--run_group` value and wandb project should match the campaign name.

See [[experiment_output_directory_standard_logs_vs_experiments_index_t.md]] for the tree + 8 principles and [[experiment_launch_checklist_run_id_wandb_latest_alias_naming.md]] for the pre-launch gate.
