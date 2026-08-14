---
title: "A resolved wiki page does not protect a launch: the cuDNN preamble was missing from the TCN launch script and cost 37 min at 18.9 s/iter"
tags: ["cudnn", "tcn", "dagger", "student", "launch-script", "operational"]
created: 2026-08-10T07:06:17.149639
updated: 2026-08-10T07:06:17.149639
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# A resolved wiki page does not protect a launch: the cuDNN preamble was missing from the TCN launch script and cost 37 min at 18.9 s/iter

2026-08-10: launched the TCN student distill `sdfinal_tcn_select_inc9998_s30` (fallback for the
shipped GRU student) WITHOUT the cuDNN LD_LIBRARY_PATH preamble. Measured from TB, not the console:
80 iterations in 1491 s = **18.88 s/iter**, `student/time_train` 18.02 s against
`student/time_collect` 1.57 s, i.e. 1000 iterations would have taken 4.8 h. Killed 16:03 and
relaunched 16:05 with the preamble; 37 min burned.

**The knowledge already existed and was already marked resolved.** Wiki page
`container_cudnn_is_cu13_against_cu128_torch_every_conv1d_fails_s`, plus the full recipe in
`scripts/train_student.py:115-150` (D-c1, 2026-07-29) with the measurement
557.6 ms -> 7.0 ms per train step on this exact workstation. It failed to protect the run because
the knowledge lived in prose while the **operational artifact — the launch script — did not carry
it**. `launch_student.sh` (GRU) legitimately omits the preamble because a GRU has no conv, so
copying that script as the base for a TCN run silently drops the one line that decides a 13-minute
run from a 4.8-hour one. Nothing errors; the run just crawls.

RULE. Any launch script for a conv-bearing run must export, before the interpreter:

    LD_LIBRARY_PATH=/isaac-sim/exts/omni.isaac.ml_archive/pip_prebundle/nvidia/cudnn/lib:$LD_LIBRARY_PATH

and pass `--enable_cudnn`. "Conv-bearing" is wider than it looks: TCN encoder runs obviously, but
ALSO **any DAgger run regardless of encoder**, because DAgger puts a student conv1d in the
collection path too. `/workspace/launch_student_tcn.sh` now does this and fail-fasts on a missing
`libcudnn.so.9` rather than silently falling back.

DETECTION. The console log is block-buffered and shows nothing at all, so the tell is TB:
`student/time_train` near 18 s instead of ~0.2 s, or simply no checkpoint after 2 min when
`save_interval=100` (the healthy GRU run wrote `student_99.pt` one minute in).

KILL NOTE. Isaac Sim ignored SIGTERM here: `kill` left the main PID in state `Rl` after 5 s and
`kill -9` was required. Kill by PID inside `docker exec`, never `pkill -f` over ssh.

