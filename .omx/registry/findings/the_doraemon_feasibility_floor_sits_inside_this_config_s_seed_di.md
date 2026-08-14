---
title: "The DORAEMON feasibility floor sits inside this config's seed distribution: two replicate seeds ended on opposite sides of alpha with nothing but the seed changed"
tags: ["doraemon", "performance_lb", "alpha", "seed-variance", "feasibility", "replicate", "mode", "deployment"]
created: 2026-08-14T15:06:42.900615
updated: 2026-08-14T15:06:42.900615
sources: ["diagnose-20260814-235911"]
links: ["the_deployed_teacher_trained_with_control_delay_steps_0_0_while.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The DORAEMON feasibility floor sits inside this config's seed distribution: two replicate seeds ended on opposite sides of alpha with nothing but the seed changed

Two from-scratch runs at the incumbent's exact settings, 10000 iterations, differing ONLY in seed,
finished on opposite sides of the DORAEMON feasibility floor. This is the most consequential thing
the teacher-final-replicate round measured, and it reframes several standing verdicts.

THE NUMBERS (final-50 means; performance_lb 250.0 and alpha 0.5 at config.py:608):

| | incumbent | R30 seed 30 | R31 seed 31 |
|:--|--:|--:|--:|
| Train/mean_reward | 253.35 | 240.11 | 244.47 |
| DORAEMON/success_rate | 0.650 | 0.469 | 0.536 |
| DORAEMON/mode at end | 0.0 | 1.0 | 0.0 |

MODE SEMANTICS, read from marinelab/algorithms/doraemon.py:430-453, because the field is easy to
misread: 0.0 is the NORMAL branch taken when success is at or above alpha. 1.0 means success fell
BELOW alpha, the inverted problem found a feasible point, and the main optimization then ran from
there -- a recovery branch, not a healthy one. -2.0 means the max-success point was still infeasible
and the main optimization was skipped. -3.0 is an optimization error. So mode 1.0 is NOT "better than
0.0"; it is the tell that the run is being pulled back over the floor every step.

WHAT THIS INVALIDATES. Any single-seed verdict on this config that turns on a threshold crossing.
performance_lb is not a comfortable margin below this config's return -- it runs through the MIDDLE of
its seed distribution. Concretely: the campaign's recorded "incumbent beats Arm W" comparison was n=1
against n=1, and the eval bears the same problem out. On the anchor-fair `none` level the two seeds
differ by 0.1708 deg on att_norm ss_error (1.7x the 0.10 deg floor) and the incumbent sits BETWEEN
them (R31 0.4810, incumbent 0.5070, R30 0.6517). A seed of the incumbent's own config is not
distinguishable from the incumbent.

WHAT IT DOES NOT SAY. It does not say the incumbent is bad or that the config is broken. Both seeds
trained to completion with zero constraint violations, 100% survival at every DR level, healthy
encoders and identical binding constraints. It says the FLOOR is badly placed relative to this
config's natural spread, so the floor cannot be used as a per-run pass/fail signal.

CONSEQUENCE FOR ANY FUTURE FEASIBILITY GATE. A gate of the form "run N iterations, check success >=
alpha" needs at least two seeds on this config, or a criterion that is not a threshold crossing (e.g.
compare the return TRAJECTORY against a same-seed control rather than against the floor). The open
control_delay_steps (0,1) decision carries exactly such a single-seed gate; see
[[the_deployed_teacher_trained_with_control_delay_steps_0_0_while_]].

DEPLOYMENT VERDICT FROM THE SAME ROUND: the incumbent ships unchanged. R30 clears the decision floor
in 4 of 24 floored cells and all four are worse; R31 clears 2, one better (soft att_norm -0.1014 deg)
and one worse (none roll n_gt20 +15.00 envs, i.e. 17.67 of 64 envs over the 20 pp threshold at the
NOMINAL level against the incumbent's 2.67). Full tables and the per-group diagnosis: analysis
diagnose-20260814-235911 under trpo_replicate_s30_260810_140415.

REPRODUCIBILITY, the round's other stated purpose, ANSWERED UNFAVOURABLY: a from-scratch run at the
incumbent's settings does not reproduce the incumbent's quality (R30 is 0.145 deg worse at `none`), so
the incumbent's advantage is not recoverable from its config file. That was the whole point of
removing its unreconstructible resume chain, and the answer is that the chain was not the only thing
carrying its quality.

