---
title: "engine-gap: flat-target eval records joint1 trajectory but renders no drift plot"
tags: ["engine-gap", "eval", "flat-target", "joint1"]
created: 2026-06-27T10:35:05.415030
updated: 2026-06-27T10:35:05.415030
sources: ["diagnose-20260627-192853"]
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# engine-gap: flat-target eval records joint1 trajectory but renders no drift plot

[ENGINE-GAP] static --flat-target writes joint1_cmd/joint1_target/joint1_pos into data_<level>.npz (commit 4fd53e0) but renders NO joint1-drift PNG -- the eval only emits attitude/yaw/error plots, so the drift signal the flat-target mode exists to show is invisible without a hand-written plot. [WHERE] constrained_albc/analysis/eval.py run_static plot-generation block (the section that saves summary_*.png / traj_*.png after the DR-level loop); add a joint1-drift figure when args_cli.flat_target is set. [SPEC] when flat_target: render a 2-panel fig -- (a) env-mean joint1_target(t) per DR level with std band (shows settle-then-flat = no drift), (b) violin/hist of final joint1_target per env per level (shows settle-position distribution). Save as joint1_drift_flat.png in the eval dir. [EVIDENCE] this analysis had to generate joint1_drift_flat.png by hand from the npz because the eval produced none; the drift conclusion (settle 4.7-7.8s, drift-after-settle<=0.086, bimodal settle |final|>1rad 40-56%) all came from a manual script. [STATUS] proposed.
