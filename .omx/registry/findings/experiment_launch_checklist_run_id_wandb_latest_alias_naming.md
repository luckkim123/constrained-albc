---
title: "experiment launch checklist: run_id / wandb / latest-alias naming"
tags: ["albc", "conventions", "launch", "wandb", "run_id", "campaign", "branch", "project", "baseline", "comparison"]
created: 2026-06-07T05:58:58.720019
updated: 2026-07-13T06:12:04.653539
sources: []
links: ["constrained_albc_experiment_conventions.md", "experiment_output_directory_standard_logs_vs_experiments_index_t.md", "experiment_result_recording_location_experiments_tree_is_ssot_no.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
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

---

## Update (2026-07-13T05:42:02.267825)

## Rule 3 clarification (2026-07-13): the campaign = the comparison set, NOT the phase/group

Rule 3 said "one project per campaign" but did not pin down what draws the campaign boundary, so
"new phase P7 -> new project p7_tail" read as legitimate. It is not. Concrete drift: P7 launched
`--run_group p7_tail --log_project_name p7_tail agent.run_name=e1_latdr` while its baseline lived in a
separate group `baseline` (project `baseline`). Both under `<exp>=albc_trpo_teacher`, two groups -> two
projects -> the web UI cannot overlay them (group filter is within-project only; no move-run API).

The fixed reading:
- **The wandb project (`--log_project_name`) = the set of runs you will overlay in one chart** — a baseline
  and every experiment you compare against it. It is NOT a phase (P6/P7) and NOT the `--run_group`.
- **`--log_project_name` defaults to the group name ONLY for a single-group campaign** (dr_harder:
  campaign == group == project, baseline_repro control lived in that same group/project, so it worked).
  The general assertion "wandb project = group name" is TRUE only in that single-group case; do not
  generalize it.
- **When a baseline and its comparison experiments sit in different `--run_group`s, set
  `--log_project_name` to the shared campaign name for all of them**, and distinguish baseline vs
  experiment by `--run_group` + `run.name` + tags. Never let the project follow the group there.
- Already split (like P7 vs baseline): fix is wandb UI Move-to-project only (SDK cannot move/copy/delete
  across projects). Do not kill a running run to "fix" its project — project is fixed at launch; move it
  after it finishes, or (no-move workaround) build a wandb Report pulling both projects' panels.

Pre-launch check to add to the rule-3 gate: before a comparison launch, run
`--log_project_name <baseline's project>` (confirm it matches the baseline you intend to overlay), not a
fresh per-phase name.

---

## Update (2026-07-13T06:12:04.653539)

## Rule 3 REVISED (2026-07-13, user decision): wandb project = PHASE, campaign = group

Supersedes both the original "one project per campaign" wording and the earlier 2026-07-13
"campaign = comparison set" clarification. Motivation: a 2026-07-13 audit found 17 wandb
projects under the entity (most holding 1-6 runs) — per-campaign projects make cross-campaign
web comparison impossible and scatter the project list.

- wandb project (`--log_project_name`) = the WORK PHASE, named `<exp_short>_<phase>`.
  Currently open phase: `teacher_baseline_opt` (= albc_trpo_teacher's baseline-optimization
  arc: finding/optimizing the new reference baseline). EVERY campaign in the phase logs here.
- campaign = `--run_group` (unchanged); run identity = run_id via make_run_id + tags.
- A phase opens/closes ONLY by explicit user declaration (a qualitatively new goal, e.g.
  optimal baseline adopted -> sim-to-real, student distillation). Default = keep logging to
  the currently open phase project. This guardrail is what stops the 17-project scatter from
  recurring under phase names.
- Cross-project migration CORRECTION to the "UI only" claim above: `wandb sync
  --include-synced -p <project> <local run dir>` re-uploads a run (same run id, history,
  config, group) into another project whenever the local `.wandb` file still exists
  (verified wandb 0.28.0; local run dirs are cwd-relative `constrained-albc/wandb/run-<ts>-<id>/`).
  "UI only" applies only when local files are gone. Artifacts/media do not migrate
  automatically; after verifying the new copy (history step count), delete the old-project
  copy (API `run.delete()` if available, else UI) and retire the emptied project via UI.
- Pending migration (post p7_tail training, 2026-07-13): baseline `0dghehbh` + e1 `7xe8vyut`
  + e2 -> `teacher_baseline_opt`; then update both campaign DESIGN.md wandb references and
  retire the empty `baseline` / `p7_tail` projects.

