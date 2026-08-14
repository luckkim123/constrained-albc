---
title: "Detached isaaclab.sh launches die instantly with ansi+tabs unknown terminal type unless TERM is set -- and every health probe reads it as a clean finish"
tags: ["albc", "launch", "isaaclab", "term", "detached", "nohup", "dgx", "silent-failure", "monitoring", "headless"]
created: 2026-08-09T13:19:16.635276
updated: 2026-08-09T16:22:57.824799
sources: []
links: ["a_distillation_run_is_invisible_to_every_teacher_run_instrument_.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Detached isaaclab.sh launches die instantly with ansi+tabs unknown terminal type unless TERM is set -- and every health probe reads it as a clean finish

A training launch fired from a detached script (nohup, systemd, a `wait_and_launch` poller, cron)
dies in the same second it starts, with an exit code of 1 and a log containing exactly one line:

```
'ansi+tabs': unknown terminal type.
```

`isaaclab.sh` shells out to `tput`, which needs `TERM`. A detached process has no TTY, so `TERM`
is unset or `dumb`, and the launcher exits before Isaac Sim boots. **Fix: prefix the launcher with
`TERM=xterm`.**

## Why it is dangerous rather than merely annoying

Nothing about it looks like a crash. There is no traceback, no CUDA error, no OOM — so every
health probe that greps for `Traceback|out of memory|RuntimeError|Killed|Segmentation fault`
reports `ERR=0`. A `pgrep`-based liveness check reports `ALIVE=0`, which is indistinguishable
from "finished successfully". The run simply never existed, and the GPU sits idle.

## Measured instance (2026-08-09)

`~/wait_and_launch_student.sh` on the DGX was staged at 17:27 to launch the C3-recipe student the
moment the teacher probe cleared. Its wait log:

```
[wait] teacher clear at 2026-08-09T22:15:29+09:00, settling 60s
[wait] launching student  2026-08-09T22:16:29+09:00
[wait] student exited rc=1 at 2026-08-09T22:16:29+09:00
```

Launched and dead within the same second. The recipe was fine; it never ran. Discovered only
because a separate session checked the GPU after the probe finished.

## Rule

Any launcher invocation that is not typed into an interactive shell gets `TERM=xterm`. And a
detached launcher must log more than the child's stdout — check the child is still alive ~120 s
after launch and record that, because rc=1 in the same second is otherwise invisible until
someone happens to look at the GPU.

---

## Update (2026-08-09T16:17:16.989376)

Two independent launch-environment defects on the DGX share one signature: the training run does
not exist, and every health probe reports it as a clean finish. They stack -- fixing the first
uncovers the second, which is why one night produced four failed launches of the same recipe.

## Defect 1 -- no TERM: instant death, rc=1

A launch fired from a detached script (nohup, systemd, a `wait_and_launch` poller, cron) dies in
the same second it starts. The whole log is one line:

```
'ansi+tabs': unknown terminal type.
```

`isaaclab.sh` shells out to `tput`, which needs `TERM`. A detached process has no TTY, so `TERM`
is unset or `dumb`. **Fix: prefix the launcher with `TERM=xterm`.**

## Defect 2 -- no --headless: 25 minutes of nothing, rc=0

Past the TERM gate, a launcher missing `--headless` boots the GUI experience file instead of
`isaaclab.python.headless.kit`. On a display-less box the window never opens:

```
[Error] [omni.appwindow.plugin] IAppWindow::startup failed
xcb_connection_has_error() returned true
[Warning] [carb.windowing-glfw.plugin] GLFW initialization failed.
```

Isaac still builds the whole scene (2048 envs, "Starting the simulation", ~29 s), sits for ~25
minutes, then shuts down **rc=0 having trained nothing** -- zero `Learning iteration` lines, no run
directory written. `--headless` is an `AppLauncher` flag, so it works on every `scripts/*.py`
entry point including `train_student.py`.

## Why both are dangerous rather than merely annoying

Neither looks like a crash. No traceback, no CUDA error, no OOM -- so a probe grepping
`Traceback|out of memory|RuntimeError|Killed|Segmentation fault` reports `ERR=0`, and a
`pgrep` liveness check reports `ALIVE=0`, which is indistinguishable from "finished successfully".
Defect 2 is worse: it exits **rc=0**, so even a wrapper checking the exit code records success.

## Measured instance (2026-08-09 -> 08-10)

`~/wait_and_launch_student.sh` was staged at 17:27 to launch the C3 student when the teacher probe
cleared. Its wait log records four launches:

```
22:16:29 launching -> student exited rc=1 at 22:16:29   (defect 1)
22:21:59 launching -> student exited rc=1 at 22:21:59   (defect 1)
22:26:39 launching -> student exited rc=0 at 22:52:05   (defect 2, 25 min, trained nothing)
```

Relaunched 2026-08-10 01:14 with both fixes (`~/launch_student_now.sh`); alive and syncing to wandb
within 90 s. The recipe was never at fault.

## Rule

Any launcher invocation not typed into an interactive shell gets **both** `TERM=xterm` and
`--headless`. Diff a new launch script against a known-good one (`launch_teacher_envscale_dgx.sh`,
`launch_dgx32k.sh`) rather than against intent. And a detached launcher must verify more than the
child's exit code: confirm a `Learning iteration` line appears in the log, because both defects
produce a log that grows and a process that exits without ever training.

---

## Update (2026-08-09T16:21:57.372974)

A launch fired from a detached script (nohup, systemd, a `wait_and_launch` poller, cron) dies in
the same second it starts, rc=1, and the whole log is one line:

```
'ansi+tabs': unknown terminal type.
```

`isaaclab.sh` shells out to `tput`, which needs `TERM`. A detached process has no TTY, so `TERM`
is unset or `dumb`. **Fix: prefix the launcher with `TERM=xterm`.**

## Why it is dangerous rather than merely annoying

It does not look like a crash. No traceback, no CUDA error, no OOM -- so a probe grepping
`Traceback|out of memory|RuntimeError|Killed|Segmentation fault` reports `ERR=0`, and a `pgrep`
liveness check reports `ALIVE=0`, which is indistinguishable from "finished successfully". The run
simply never existed and the GPU sits idle.

## Measured instance (2026-08-09)

`~/wait_and_launch_student.sh` was staged at 17:27 to launch the C3 student when the teacher probe
cleared. It fired three times:

```
22:16:29 launching -> rc=1 at 22:16:29   TERM missing
22:21:59 launching -> rc=1 at 22:21:59   TERM missing
22:26:39 launching -> rc=0 at 22:52:05   SUCCEEDED, 1000/1000 iterations
```

## `--headless` is NOT part of this failure -- verified, do not "fix" it

The third attempt ran **without `--headless`** and trained to completion anyway: 1000 TB points on
`student/loss_total` (0.05636 -> 0.00286) and all ten checkpoints `student_99.pt` .. `student_999.pt`.
On this display-less box the GUI path emits
`IAppWindow::startup failed` / `xcb_connection_has_error() returned true` /
`GLFW initialization failed` -- and Isaac carries on regardless. Those lines are **noise, not a
diagnosis**. `--headless` is still worth adding (faster boot, fewer extensions), but its absence
does not stop training, and an rc=0 exit after ~25 minutes on a 1000-iteration student run is the
*expected duration of success*, not evidence of a silent failure.

An earlier revision of this page claimed the opposite. It was wrong -- see
[[a_distillation_run_is_invisible_to_every_teacher_run_instrument]] for the three mismeasurements
that produced that false verdict.

## Rule

Any launcher invocation not typed into an interactive shell gets `TERM=xterm`. Diff a new launch
script against a known-good one (`launch_teacher_envscale_dgx.sh`, `launch_dgx32k.sh`). And before
declaring a detached launch dead, confirm against the run's OUTPUT TREE, never against its console
log alone.

---

## Update (2026-08-09T16:22:57.824799)

A launch fired from a detached script (nohup, systemd, a `wait_and_launch` poller, cron) dies in
the same second it starts, rc=1, and the whole log is one line:

```
'ansi+tabs': unknown terminal type.
```

`isaaclab.sh` shells out to `tput`, which needs `TERM`. A detached process has no TTY, so `TERM`
is unset or `dumb`. **Fix: prefix the launcher with `TERM=xterm`.**

## Why it is dangerous rather than merely annoying

It does not look like a crash. No traceback, no CUDA error, no OOM -- so a probe grepping
`Traceback|out of memory|RuntimeError|Killed|Segmentation fault` reports `ERR=0`, and a `pgrep`
liveness check reports `ALIVE=0`, which is indistinguishable from "finished successfully". The run
simply never existed and the GPU sits idle.

## Measured instance (2026-08-09)

`~/wait_and_launch_student.sh` was staged at 17:27 to launch the C3 student when the teacher probe
cleared. It fired three times:

```
22:16:29 launching -> rc=1 at 22:16:29   TERM missing
22:21:59 launching -> rc=1 at 22:21:59   TERM missing
22:26:39 launching -> rc=0 at 22:52:05   SUCCEEDED, 1000/1000 iterations
```

## `--headless` is NOT part of this failure -- verified, do not "fix" it

The third attempt ran **without `--headless`** and trained to completion anyway: 1000 TB points on
`student/loss_total` (0.05636 -> 0.00286) and all ten checkpoints `student_99.pt` .. `student_999.pt`.
On this display-less box the GUI path emits
`IAppWindow::startup failed` / `xcb_connection_has_error() returned true` /
`GLFW initialization failed` -- and Isaac carries on regardless. Those lines are **noise, not a
diagnosis**. `--headless` is still worth adding (faster boot, fewer extensions), but its absence
does not stop training, and an rc=0 exit after ~25 minutes on a 1000-iteration student run is the
*expected duration of success*, not evidence of a silent failure.

An earlier revision of this page claimed the opposite. It was wrong -- see
[[a_distillation_run_is_invisible_to_every_teacher_run_instrument_]] for the three mismeasurements
that produced that false verdict.

## Rule

Any launcher invocation not typed into an interactive shell gets `TERM=xterm`. Diff a new launch
script against a known-good one (`launch_teacher_envscale_dgx.sh`, `launch_dgx32k.sh`). And before
declaring a detached launch dead, confirm against the run's OUTPUT TREE, never against its console
log alone.
