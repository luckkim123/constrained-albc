---
title: "experiment launch checklist: run_id / wandb / latest-alias naming"
tags: ["albc", "conventions", "launch", "wandb", "run_id", "campaign", "branch"]
created: 2026-06-07T05:58:58.720019
updated: 2026-06-07T06:10:13.430011
sources: []
links: ["constrained_albc_experiment_conventions.md", "experiment_output_directory_standard_logs_vs_experiments_index_t.md", "experiment_result_recording_location_experiments_tree_is_ssot_no.md"]
category: convention
confidence: high
schemaVersion: 1
---

# experiment launch checklist: run_id / wandb / latest-alias naming

Pre-launch gate for every training run, especially campaign runs (e.g. dr_harder). Repairing these post-hoc is expensive; enforce at LAUNCH. Root cause of the dr_harder cleanup (2026-06-07): launches that skipped these checks. Full directory standard: see the companion wiki page "experiment output directory standard" and docs/plans/2026-06-07-experiment-dir-standard.md.

CHECKLIST (verify each BEFORE walking away from a launch):

0. Branch awareness BEFORE you start (branch location is free; not knowing it is the sin). Per-experiment branch separation is allowed -- branching e9 from main, from exp/e9-<topic>, or INTENTIONALLY from exp/e8 (a deliberate cumulative experiment) are all valid. The forbidden case is launching e9 while unknowingly still sitting on the previous experiment's branch (e8), thinking you are on main, so e8's code change leaks into e9 and confounds the comparison. Obligation: run `git branch --show-current` before each experiment, consciously confirm "is this base the branch point I intend for THIS experiment?", and record the chosen base (main / exp/e8 / baseline tag) in the campaign's experiments/.../<group>/DESIGN.md (results SSOT = experiments tree) so a future reader can tell an intended chain from an accident. (See rules/02-operations.md section "Comparison-experiment isolation" rule 6.)

1. run_id via make_run_id, tag MANDATORY. Pass agent.run_name (the experiment tag) so make_run_id emits <task_short>_<tag>_<ts> (label-before-date, ts last). A tag-less id (trpo_<ts>) or date-first id (<ts>_trpo) is a violation. scripts/train.py now prints a stderr [WARN] when run_name is empty. ANY launch path -- including worktree/ad-hoc scripts like train_e6.py -- MUST route the leaf through make_run_id; never hand-format it. E5/E6 broke because a worktree train script bypassed make_run_id.

2. Experiment number = CAMPAIGN-continuous, for INDEPENDENT experiments only, assigned at run time. Number the distinct experiments (each varying a knob to test a hypothesis) e1, e2, e3, ... in one unbroken sequence across the whole campaign, even when batches run on different days. CONTROLS and NEVER-RUN experiments do NOT consume an e-number: a baseline/control re-run (e.g. an exact teacher-duplicate) is bookkeeping not a new experiment, and a planned-but-never-launched experiment leaves no number. dr_harder's real experiments = E1 (kl_ub) / E2 (ocean) / E3 (alpha075) / E4 (budget_half); the baseline_repro control and the never-run dr_both carry no e-number. A number that LOOKS skipped is NOT automatically free: check the campaign README.md + docs/archive/ for the full history first. (2026-06-07 churn root cause: alpha075/budget_half were renumbered back and forth because a control was mistakenly counted into the E-series; exclude the control and the four real experiments number cleanly E1-E4.) Assign the next number at run time; do not pre-reserve at design time.

3. wandb storage = ONE project per campaign, set at launch. The wandb rules (the e5/e6 drift was a wandb-project mistake, so this is the most error-prone gate):
   - project = the CAMPAIGN name, fixed (e.g. dr_harder_campaign). Pass --log_project_name <campaign> on EVERY run of the campaign. Do NOT mint a per-experiment project name -- that is exactly what scattered E5/E6 into dr_harder_e5_alpha075 / dr_harder_e6_budget_half (a per-experiment --log_project_name at launch). One campaign = one project, full stop.
   - distinguish runs WITHIN the project by run.name (the run_id) + group=<campaign> + tags ([<campaign>, e<n>]), NOT by project. (group lets you filter one campaign even if a stray run landed elsewhere.)
   - moving a run between projects = wandb UI ONLY. The SDK/API can read and re-tag a run but CANNOT move it across projects (and cannot copy or delete). So a wrong project at launch is only fixable by hand: project Runs tab -> select run -> Move to project -> <campaign>. (Artifacts do NOT move automatically with the run.)
   - deleting an empty leftover project (after its runs moved out) = wandb UI only (Overview -> Delete project). Only delete a project you are sure is single-purpose and now empty; never delete a shared project.
   - local wandb dir: each run also writes logs/.../<run_id>/wandb/ on disk (the offline run dir). That is the disk side; the project/group/tags above are the server side. See [[experiment_output_directory_standard_logs_vs_experiments_index_t.md]] for the disk layout.

4. latest alias lives INSIDE the group directory. For a grouped tree <exp>/<group>/<run_id>, the alias must be <exp>/<group>/latest, not <exp>/latest one level up. update_latest_symlink keys off the launch dir, so after launch run readlink on the alias and confirm it points at this run.

POST-LAUNCH VERIFY (one command each): ls the run folder name (rule 1), readlink the group/latest alias (rule 4), confirm the wandb run landed in the campaign project with the right group/tags (rule 3). If any fails, fix immediately -- the longer a mis-named run sits, the more downstream references (campaign README, report.md, manifest.json) bind to the wrong id.
