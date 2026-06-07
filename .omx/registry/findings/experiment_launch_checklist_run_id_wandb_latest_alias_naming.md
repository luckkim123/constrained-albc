---
title: "experiment launch checklist: run_id / wandb / latest-alias naming"
tags: ["albc", "conventions", "launch", "wandb", "run_id", "campaign", "branch"]
created: 2026-06-07T05:58:58.720019
updated: 2026-06-07T06:10:13.430011
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
---

# experiment launch checklist: run_id / wandb / latest-alias naming

Pre-launch gate for every training run, especially campaign runs (e.g. dr_harder). Repairing these post-hoc is expensive; enforce at LAUNCH. Root cause of the dr_harder cleanup (2026-06-07): launches that skipped these checks. Full directory standard: see the companion wiki page "experiment output directory standard" and docs/plans/2026-06-07-experiment-dir-standard.md.

CHECKLIST (verify each BEFORE walking away from a launch):

0. Branch awareness BEFORE you start (branch location is free; not knowing it is the sin). Per-experiment branch separation is allowed -- branching e9 from main, from exp/e9-<topic>, or INTENTIONALLY from exp/e8 (a deliberate cumulative experiment) are all valid. The forbidden case is launching e9 while unknowingly still sitting on the previous experiment's branch (e8), thinking you are on main, so e8's code change leaks into e9 and confounds the comparison. Obligation: run `git branch --show-current` before each experiment, consciously confirm "is this base the branch point I intend for THIS experiment?", and record the chosen base (main / exp/e8 / baseline tag) in the campaign's experiments/.../<group>/DESIGN.md (results SSOT = experiments tree) so a future reader can tell an intended chain from an accident. (See rules/02-operations.md section "Comparison-experiment isolation" rule 6.)

1. run_id via make_run_id, tag MANDATORY. Pass agent.run_name (the experiment tag) so make_run_id emits <task_short>_<tag>_<ts> (label-before-date, ts last). A tag-less id (trpo_<ts>) or date-first id (<ts>_trpo) is a violation. scripts/train.py now prints a stderr [WARN] when run_name is empty. ANY launch path -- including worktree/ad-hoc scripts like train_e6.py -- MUST route the leaf through make_run_id; never hand-format it. E5/E6 broke because a worktree train script bypassed make_run_id.

2. Experiment number = CAMPAIGN-continuous ACROSS BATCHES, never reset per batch. Number e1, e2, e3, ... in one unbroken sequence spanning the whole campaign even when batches run on different days. dr_harder = Batch1 (E1-E4) + Batch2 (E5-E6) = a single E1-E6 campaign. A number that LOOKS skipped is NOT automatically free: before reusing it, check the campaign README.md + docs/archive/ for the full batch history. (2026-06-07 root cause: E5/E6 were misread as an "e3/e4 gap" and renumbered, colliding with Batch1's real E4=baseline_repro. E3=dr_both was simply never run -- a genuine no-run, not a free slot.) Assign the next number at run time; do not pre-reserve at design time.

3. wandb project = the CAMPAIGN name, fixed. All runs of one campaign log to a single --log_project_name <campaign> (e.g. dr_harder_campaign) with group=<campaign>; distinguish runs by run_name, NOT by minting a per-experiment project. wandb has NO API to move a run between projects (UI-only) -- a wrong project at launch can only be fixed by hand in the web UI. So get it right at launch.

4. latest alias lives INSIDE the group directory. For a grouped tree <exp>/<group>/<run_id>, the alias must be <exp>/<group>/latest, not <exp>/latest one level up. update_latest_symlink keys off the launch dir, so after launch run readlink on the alias and confirm it points at this run.

POST-LAUNCH VERIFY (one command each): ls the run folder name (rule 1), readlink the group/latest alias (rule 4), confirm the wandb run landed in the campaign project with the right group/tags (rule 3). If any fails, fix immediately -- the longer a mis-named run sits, the more downstream references (campaign README, report.md, manifest.json) bind to the wrong id.
