---
title: "experiment launch checklist: run_id / wandb / latest-alias naming"
tags: ["albc", "conventions", "launch", "wandb", "run_id", "campaign"]
created: 2026-06-07T05:58:58.720019
updated: 2026-06-07T05:58:58.720019
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
---

# experiment launch checklist: run_id / wandb / latest-alias naming

Pre-launch gate for every training run, especially campaign runs (e.g. dr_harder). Repairing these post-hoc is expensive; enforce at LAUNCH. Root cause of the dr_harder Batch-2 mess (2026-06-07): launches that skipped these checks.

CHECKLIST (verify each BEFORE walking away from a launch):

1. run_id via make_run_id, tag MANDATORY. Pass agent.run_name (the experiment tag) so make_run_id emits <task_short>_<tag>_<ts> (label-before-date, ts last). A tag-less id (trpo_<ts>) or date-first id (<ts>_trpo) is a violation. scripts/train.py now prints a stderr [WARN] when run_name is empty. ANY launch path -- including worktree/ad-hoc scripts like train_e6.py -- MUST route the leaf through make_run_id; never hand-format it. E5/E6 broke because a worktree train script bypassed make_run_id.

2. Experiment number = campaign-continuous, assigned at run time. Number e1, e2, e3, ... in one unbroken sequence per campaign. Do NOT pre-reserve numbers at design time (Batch-1 reserved e3/e4, never ran them -> Batch-2 jumped to e5/e6, leaving a gap). Take the next free number when you actually launch.

3. wandb project = the CAMPAIGN name, fixed. All runs of one campaign log to a single --log_project_name <campaign> (e.g. dr_harder_campaign) with group=<campaign>; distinguish runs by run_name, NOT by minting a per-experiment project. wandb has NO API to move a run between projects (UI-only) -- a wrong project at launch can only be fixed by hand in the web UI. So get it right at launch.

4. latest alias lives INSIDE the group directory. For a grouped tree <exp>/<group>/<run_id>, the alias must be <exp>/<group>/latest, not <exp>/latest one level up. update_latest_symlink keys off the launch dir, so after launch run readlink on the alias and confirm it points at this run.

POST-LAUNCH VERIFY (one command each): ls the run folder name (rule 1), readlink the group/latest alias (rule 4), confirm the wandb run landed in the campaign project (rule 3). If any fails, fix immediately -- the longer a mis-named run sits, the more downstream references (docs/results, report.md, manifest.json) bind to the wrong id.

