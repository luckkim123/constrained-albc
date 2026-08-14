---
title: "Before citing an eval, verify its run actually trained: manifest status, log directory, wandb, checkpoint count"
tags: ["provenance", "verification", "eval", "procedure", "orphan-artifact"]
created: 2026-08-14T08:37:39.930923
updated: 2026-08-14T08:37:39.930923
sources: ["diagnose-20260814-172325"]
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Before citing an eval, verify its run actually trained: manifest status, log directory, wandb, checkpoint count

An eval directory full of real-looking numbers is NOT evidence that the run it sits under
produced them. On 2026-08-10 a decision-category page was written at confidence HIGH off
static_260810_011725, whose run had died 79 minutes earlier without a single training iteration.
The eval ran, wrote a summary.json, four DR levels, five PNGs and a summary_latent.json. Nothing
errored. The numbers are real measurements of SOMETHING; what they are not is measurements of the
arm they were filed under, and summary.json records no checkpoint field, so the subject is
unrecoverable after the fact.

CHECK THESE FOUR BEFORE CITING AN EVAL. They are cheap and independent, and the first three catch
the failure even when the fourth is unavailable.

1. manifest.json: status, paths.evals, final_metrics, and whether config/ has any files. A run
   that trained has a non-empty config/ (env.yaml, agent.yaml). Empty config/ plus
   status failed is decisive.
2. The log tree: does logs/rsl_rl/<exp>/<group>/ exist at all? A run that never booted far enough
   to train leaves NO directory -- and absence is quieter than breakage, because a broken-symlink
   scan finds nothing to flag.
3. wandb: is there a run whose name matches? No local wandb dir for a run that was supposed to log
   is corroboration, not proof on its own.
4. Checkpoints: for a student, models/student_*.pt; for a teacher, model_*.pt. Zero checkpoints
   with a nonzero configured max_iterations means it did not finish, and possibly did not start.

TIMESTAMP ARITHMETIC IS THE CHEAPEST TELL AND THE MOST OFTEN SKIPPED. Compare the eval directory
timestamp against the launch and death times in the run's own log or the program HANDOFF. In this
incident the eval started 23 minutes after the LAST launch attempt began -- far too early for a
1000-iteration distillation to have produced the checkpoint it would have had to load.

TWO RELATED TRAPS ON THE SAME LINE:
- A relaunch mints a NEW run id, so the retrained arm may exist under a different group entirely.
  Check the obvious sibling group before concluding "never retrained" -- and check its teacher,
  because a relaunch often changes the teacher too (student_final_round did, twice).
- A launch script's own header comments are first-class evidence. The 2026-08-10 relaunch script
  opens with "TERM=xterm + --headless are MANDATORY: their absence killed two launches on
  2026-08-09" -- written by whoever was there, independent of any wiki page or manifest.

The manifest status field is only as good as whoever set it: it is written at creation and no code
reads it back, so a finished run can sit at "running" indefinitely (86 of 145 manifests did until
a 2026-08-14 sweep). Treat a stale "running" as unknown, not as evidence of anything, and prefer
checks 2 and 4, which are physical.

