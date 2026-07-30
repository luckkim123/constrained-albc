---
title: "Group folder name equals wandb project name equals experiment purpose (unified naming, 2026-07-14 revision)"
tags: ["naming", "convention", "group", "run_group", "wandb", "project", "tree", "purpose-drift"]
created: 2026-07-14T06:07:26.744195
updated: 2026-07-30T04:46:28.970075
sources: ["user-decision-2026-07-14"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Group folder name equals wandb project name equals experiment purpose (unified naming, 2026-07-14 revision)

USER DECISION 2026-07-14 (REVISES the 2026-07-13 "wandb project = phase, never the group/campaign name" rule):

RULE: the experiment output-tree GROUP folder name = the wandb PROJECT name = the experiment PURPOSE, as ONE unified, self-documenting name. They are the same concept and must carry the same legible name. Do NOT split one purpose into multiple cryptic sub-campaign groups.

- Tree: experiments|logs/rsl_rl/<exp>/<group>/<run_id>. The <group> value = --run_group = the purpose = the wandb --log_project_name value. Example: `teacher_baseline_opt` is BOTH the group folder AND the wandb project.
- Launch (go-forward): `--run_group teacher_baseline_opt --log_project_name teacher_baseline_opt` (same string for both). run_id itself is still `make_run_id` output (`<task_short>[_<tag>]_<ts>`), tags/e-numbers still distinguish individual probes WITHIN the group.
- When the PURPOSE genuinely changes (a different experiment goal, e.g. student distillation), create a NEW group AND a NEW wandb project with the SAME new legible name. group and project always move together now.

WHAT THIS SUPERSEDES: the 2026-07-13 decision kept wandb project COARSE (= "phase", stable across many campaigns) and the <group> folder FINER (= per-campaign, e.g. `baseline`, `p7_tail`), explicitly forbidding project from following the group name. The user found that split needlessly complex: the group unit and the project unit both encode "experiment purpose", so having two different names for the same thing (folder `p7_tail` vs project `teacher_baseline_opt`) is confusing with no payoff at this scale. The 2026-07-14 rule collapses them into one name.

ANTI-SCATTER LESSON PRESERVED (why this does NOT reintroduce the 17-project scatter of 2026-07-13): scatter came from making projects TOO GRANULAR (a new project per small campaign) so related runs spread across many uncomparable wandb projects. The new rule avoids that by defining PURPOSE broadly: `teacher_baseline_opt` spans the baseline reference AND all its tail-shrink probes (e1-e4), so all those runs land in ONE group = ONE project and stay comparable in one wandb workspace. Scatter is prevented by keeping the purpose broad, not by splitting project from group.

APPLIED 2026-07-14: merged the former `baseline/` and `p7_tail/` groups into a single `teacher_baseline_opt/` group (both logs+experiments trees; 5 runs; train symlinks re-pointed; DESIGN.md of each preserved as DESIGN.baseline.md / DESIGN.p7_tail.md; `latest` -> e4). joint1_constraint (Arm-B) had already been retired to legacy/ the same day. See experiments/INDEX.md. The .omx campaign ledger keeps `baseline`/`p7_tail` as historical campaign ids; go-forward campaigns use the unified purpose name.

---

## Update (2026-07-20T08:57:49.384443)

2026-07-20 user confirmation (D0 of the teacher batch campaign): the Stage-A mechanism probes (A1 step_interval, A2-A5) CONTINUE the open purpose teacher_baseline_posttam -- same plant, same anchors, so no genuinely new purpose exists yet; the A1 launch (run trpo_stepint400_260720_175705) uses --run_group teacher_baseline_posttam --log_project_name teacher_baseline_posttam agent.run_name=stepint400. A genuinely new purpose opens ONLY at Stage B (hull-volume plant change): teacher_v2_plant. User also vetoed "final" in any purpose/run name (more experiments may follow) -- do not propose names containing "final".

---

## Update (2026-07-30T04:46:28.970075)

## CORRECTION 2026-07-30: the 2026-07-20 "open purpose" claim went stale, and the predicted new-purpose name never happened

[FINDING] This page's 2026-07-20 statement that teacher_baseline_posttam is the open purpose, and that a genuinely new purpose would open only at Stage B under the name teacher_v2_plant, are both superseded by what actually happened: the buoyfix plant change opened teacher_baseline_buoyfix (not teacher_v2_plant), posttam took its last run on 2026-07-21, and the purposes actually live on 2026-07-30 are fault_dr (teacher) and student_distill_eint (student).

[EVIDENCE] Newest-dated run dirs per group under experiments/rsl_rl/, counted 2026-07-30: teacher_baseline_opt 5 runs last 260714; seed_floor_dgx 3 last 260721; teacher_baseline_posttam 10 last 260721; e3_dgxscale_buoyfix 1 last 260722; buoyfix_s30_tcn 3 last 260724; teacher_baseline_buoyfix 7 last 260728 (holds the final E-int teacher trpo_eint_s30_rs2350_260727_195102); student_distill_eint 7 last 260729; fault_dr 5 last 260729. So posttam had been dormant for eight days and through two purpose changes while both this page and .claude/rules/02-operations.md still named it "currently open".

[CONFIDENCE] HIGH

Closed purposes, each a DIFFERENT plant -- do not add runs to any of them: teacher_baseline_opt (pre-TAM-fix), teacher_baseline_posttam (superseded by the buoyfix plant change), teacher_baseline_buoyfix (final E-int teacher lives here).

The durable lesson is about WHERE the live purpose is recorded, not about which name is current. Every hardcoded copy of "the currently open purpose" has gone stale, because the purpose changes per campaign while the documents naming it are edited only when someone happens to notice. On 2026-07-30 the hardcoded name was removed from .claude/rules/02-operations.md and replaced with the derivation: read the newest-dated run dirs under experiments/rsl_rl/<exp>/<group>/, cross-check omx campaign-status, and confirm with the user before launching into a group. Treat the same way here -- the group list above is dated evidence, not a standing declaration, so re-derive it rather than trusting this paragraph on a later date.

The naming RULE itself is unchanged and still binding: group folder name == wandb project name == the one broad self-documenting purpose, the same string passed to --run_group and --log_project_name, fixed for every run until the user declares a new purpose. Only the "which one is it right now" annotation was wrong.

