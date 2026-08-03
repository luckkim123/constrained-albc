---
title: "C3's dirty-tree provenance doubt is CLOSED: a dim=0 control on commit d81e2fd reproduces C3's iteration 0 bit-identically, so every student_distill_eint comparison against C3 stands"
tags: ["c3", "provenance", "baseline", "student", "distillation", "dirty-tree", "control"]
created: 2026-08-03T13:54:05.423137
updated: 2026-08-03T13:54:05.423137
sources: ["diagnose-20260803-223517"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# C3's dirty-tree provenance doubt is CLOSED: a dim=0 control on commit d81e2fd reproduces C3's iteration 0 bit-identically, so every student_distill_eint comparison against C3 stands

THE DOUBT. C3's manifest records git.sha 9ef4cf6 with dirty:true, and program pointing at
/workspace/constrained-albc-student/scripts/train_student.py -- a separate worktree that no longer
exists. The branch exp/student-distill-eint is also gone (only main and exp/obs4-extraobs contain
9ef4cf6), so C3's uncommitted delta at launch time is unrecoverable. The whole campaign compares
against C3, so "did that delta change anything" was an open question with no cheap answer.

HOW IT WAS SETTLED. Run trpo_sdeint_b2ctl_dim0_s30_260803_220234: C3's exact recipe (GRU, select,
fixed beta 0.5, seed 30, 2048 envs, same frozen E-int teacher) with extra_obs_dim 0, on commit
d81e2fd -- 69 commits after C3. Cost 13 minutes. Two independent confirmations came back:

TRAINING SIDE (the decisive one). Iteration 0 is identical to 6 decimals on every logged tag:
  loss_latent 0.067585, loss_action 0.003916, loss_total 0.071501,
  grad_norm 0.393604, dagger_teacher_frac 0.502889
Final-window loss_latent differs only 0.35% (C3 0.004842 vs control 0.004859), consistent with GPU
nondeterminism accumulating over 1000 iterations from an identical start.

EVAL SIDE. The control draws the same 64 envs as C3 (23/23 dr_* arrays identical), so this leg is
paired. Aggregate hard R2 +0.1108 -> +0.0905; largest per-dim R2 gap 0.1039; d6, the pre-registered
dimension, moves +0.0035 (-0.4321 -> -0.4287), i.e. unchanged. Control axis att_norm ss_error stays
sub-floor at every DR level (largest gap 0.0163 at medium, 0.0078 at hard).

CONCLUSION. The dirty delta was inert on the training path. Do not spend another control run on this
question. Note the residual honestly: because that leg is PAIRED, its true difference sd is smaller
than the unpaired 0.0533, so the -0.0203 aggregate gap is more than the 0.38 sigma it looks like
against the unpaired number -- it is the first empirical handle on the training-run-to-run component
the pre-registration explicitly excluded from its sd, at roughly 0.02 aggregate and under 0.10 per dim.

