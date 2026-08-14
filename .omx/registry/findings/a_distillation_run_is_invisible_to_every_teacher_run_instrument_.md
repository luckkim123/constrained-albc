---
title: "A distillation run is invisible to every teacher-run instrument: wrong tree, no Learning-iteration line, buffered stdout"
tags: ["albc", "student", "distillation", "dagger", "monitoring", "false-negative", "tensorboard", "logging", "dgx"]
created: 2026-08-09T16:22:18.692278
updated: 2026-08-09T16:22:18.692278
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# A distillation run is invisible to every teacher-run instrument: wrong tree, no Learning-iteration line, buffered stdout

Every instrument this project uses to tell whether a teacher run is training reports **"not
training"** for a student/distillation run that is training perfectly. All three are wrong at once,
which is enough to produce a confident false verdict -- it happened on 2026-08-10 and cost a
duplicate 1000-iteration run.

## The three mismeasurements

| instrument | teacher run | student run | what it reads |
|:--|:--|:--|:--|
| output tree | `logs/rsl_rl/albc_trpo_teacher/<group>/<run>/` | `logs/rsl_rl/albc_trpo_**student**/<group>/<run>/` | "no run directory exists" |
| progress grep | `Learning iteration N/M` (rsl_rl runner) | never printed by `train_student.py` | "0 training lines" |
| console log | grows steadily | frozen at the wandb banner | "the process is stuck at startup" |

The console freeze is plain stdout block buffering: with stdout redirected to a file, python's
prints sit in the buffer, while Isaac's own carb logging goes to the kit log elsewhere. The file
can stay at its startup size for the entire run.

## What to read instead

The TensorBoard event file inside the run directory, and `models/`:

```
logs/rsl_rl/albc_trpo_student/<group>/<run>/events.out.tfevents.*   # grows every iteration
logs/rsl_rl/albc_trpo_student/<group>/<run>/models/student_<N>.pt   # every save_interval
```

Scalar tags are `student/loss_total`, `student/loss_action`, `student/loss_latent`,
`student/grad_norm`, `student/time_collect`, `student/time_train` -- there is no `Policy/*` or
`DORAEMON/*` group, so a teacher-shaped reader returns nothing here either.

Cheapest live check: `ls -l <run>/models/` and the event file's mtime. Cheapest completeness check:
the number of scalar points on `student/loss_total` (a finished 1000-iteration run has exactly
1000, steps 0..999).

## Finding the run directory when you do not know the tree

The wandb banner in the console log prints the absolute run path even when nothing else has
flushed:

```
wandb: Run data is saved locally in /.../logs/rsl_rl/albc_trpo_student/<group>/<run>/wandb/...
```

That one line is the fastest way to learn which tree a script writes to. Read it before concluding
anything from a directory listing.

## Measured instance

The 22:26:39 launch of `sddgx16k_c3_gruselect_s30` on 2026-08-09 was declared "ran 25 minutes and
trained nothing" on the strength of all three instruments above. It had in fact completed
1000/1000 iterations (`student/loss_total` 0.05636 -> 0.00286, checkpoints `student_99.pt` ..
`student_999.pt`) and its rc=0 at 22:52:05 was a normal finish. A relaunch was issued at 01:14 on
that false premise and is a bit-identical duplicate.
