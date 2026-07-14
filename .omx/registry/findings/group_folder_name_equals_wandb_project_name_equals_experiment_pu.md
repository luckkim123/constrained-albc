---
title: "Group folder name equals wandb project name equals experiment purpose (unified naming, 2026-07-14 revision)"
tags: ["naming", "convention", "group", "run_group", "wandb", "project", "tree"]
created: 2026-07-14T06:07:26.744195
updated: 2026-07-14T06:07:26.744195
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

