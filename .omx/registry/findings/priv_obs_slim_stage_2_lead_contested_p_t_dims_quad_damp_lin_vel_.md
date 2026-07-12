---
title: "priv-obs slim Stage-2 lead: contested p_t dims (quad_damp, lin_vel) need WITH-vs-WITHOUT A/B; union kept them"
tags: ["priv_obs", "encoder", "experiment_lead", "consolidation", "p_t_layout"]
created: 2026-07-12T12:01:49.559370
updated: 2026-07-12T12:01:49.559370
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# priv-obs slim Stage-2 lead: contested p_t dims (quad_damp, lin_vel) need WITH-vs-WITHOUT A/B; union kept them

Future-experiment lead preserved from exp/priv-obs-slim (code-complete, NEVER TRAINED) before
the branch is deleted by the 2026-07-12 consolidation. The branch lived in worktree
/workspace/constrained-albc-priv-obs-slim; its knowledge survives here + in the branch
CHANGELOG commit b5e9aee + tag baseline-260708-priv-obs-slim.

WHAT SLIM DID: p_t 27D -> 21D by removing Ixx, lin_damp_roll, quad_damp_roll, measured
lin_vel u/v/w from compute_privileged_obs. Static verification only (golden-obs tests,
bounds re-derivation); no training run ever launched, so no experiments-tree record exists.

EVIDENCE SPLIT (the load-bearing distinction):
- Ixx + lin_damp_roll: encoder z-sweep LOW tier -> removal sweep-justified. These two LANDED
  on main in the 2026-07-12 union p_t layout (27D content swap, buoy dims added).
- quad_damp_roll: z-range 0.641 (mid-HIGH); measured lin_vel: TOP-3 z-sweep sensitivity.
  Removal was a user decision AGAINST/BEYOND the sweep evidence -> slim's own CHANGELOG
  marks them PENDING Stage-2 (user-gated training run). The union KEPT both in p_t.

THE PENDING EXPERIMENT (plan 2026-07-12 section 8.4 queue item 3, only-if-option-c -> now active):
WITH-vs-WITHOUT fresh-training A/B on the consolidated baseline. One variable: drop
quad_damp_roll + lin_vel from p_t (28D -> 24D on the post-latency union layout; slim's
original "21D vs 25D" numbers are STALE -- re-derive indices from the then-current layout).
Compare: critic value-loss, explained variance, attitude tracking (att_rp, yaw_vel), and a
z-sweep on both checkpoints (encoder verification rule: sweep, not TB aggregates). Restore
the dims if value estimation or tracking degrades; only then is the removal evidence-backed.

CAVEAT: lin_vel is the asymmetric-critic's only measured-velocity channel (actor is blinded);
dropping it changes critic information, not just encoder input -- expect the effect to show in
explained-variance first. quad_damp removal also interacts with the hydro-DR sampling
(quadratic_damping_scale stays a DR dim regardless; only the observation of it is at stake).

