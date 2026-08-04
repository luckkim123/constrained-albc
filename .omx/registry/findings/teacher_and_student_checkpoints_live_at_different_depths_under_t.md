---
title: "Teacher and student checkpoints live at DIFFERENT depths under the run tree: teacher writes train/model_N.pt, train_student.py writes train/models/student_N.pt -- a completion watcher copied from the teacher polls a path that will never exist"
tags: []
created: 2026-08-04T04:07:37.712116
updated: 2026-08-04T04:07:37.712116
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# Teacher and student checkpoints live at DIFFERENT depths under the run tree: teacher writes train/model_N.pt, train_student.py writes train/models/student_N.pt -- a completion watcher copied from the teacher polls a path that will never exist

## The layout

| kind | checkpoint path under the run dir |
|:--|:--|
| teacher (`train.py`) | `<run>/train/model_4999.pt` |
| student (`train_student.py`) | `<run>/train/models/student_999.pt` |

`train` is the symlink into the logs tree in both cases; the difference is that the student
trainer nests its checkpoints one level deeper in `models/`. The student run dir also holds only
`events.out.tfevents.*`, `models/` and `wandb/`, where a teacher run dir holds `model_*.pt`,
`curriculum_trajectory.json`, `doraemon_state.pt` and `git/` directly.

## Why it matters

On 2026-08-04 the Phase E completion watcher was written by copying the Phase D teacher chain and
swapping the filename. It polled `<run>/train/student_999.pt`, which never exists. The training
finished at 13:00 and the eval had still not launched at 13:05; the watcher was not erroring, it
was happily sleeping through its 1400 x 30 s window. This is the same silent class as
`training-watcher-pattern-traps` and the stale-run-id incident: a watcher that cannot find its
target is indistinguishable from a watcher that is waiting patiently.

## Rule

When adapting a teacher watcher for a student run (or vice versa), do not just change the
filename -- `ls` the actual run dir first and confirm the checkpoint path resolves. Better, make
the watcher assert its target's PARENT exists at arming time and fail loudly if not: the parent
directory is present from the first save, so a wrong path is detectable within minutes instead of
after the whole window expires.

`train_student.py` also writes an EMPTY `config/` directory into the experiments tree and no
`env.yaml`, unlike the teacher, so a bite check that greps the student run's `config/env.yaml`
also waits forever. Read the student's dims from the checkpoint's own `cfg` blob instead
(`policy_obs_dim`, `extra_obs_dim`, `privileged_dim`, `latent_dim`), which is available from the
first save -- and load it with the Isaac interpreter, since system python3 has no torch.

