---
title: "priv-obs slim Stage-2 lead: contested p_t dims (quad_damp, lin_vel) need WITH-vs-WITHOUT A/B; union kept them"
tags: ["priv_obs", "encoder", "experiment_lead", "consolidation", "p_t_layout", "lin_vel", "resolved", "premise-error", "auto-captured"]
created: 2026-07-12T12:01:49.559370
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260721-190151", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: ["doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: resolved
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

---

## Update (2026-07-20T07:54:39.478862)

STATUS PROMOTION (2026-07-20 wiki sweep): the Stage-2 WITH-vs-WITHOUT A/B (drop quad_damp_roll + lin_vel from p_t, 28D -> 24D on the post-latency union layout) is an unstarted fresh-training probe; promoted to needs-experiment for backlog visibility.

---

## Update (2026-07-21T10:03:35.439470)


# LEAD CLOSED 2026-07-21 (A4) — RESOLVED: the contested dims are LOAD-BEARING, keep 28D

[FINDING] A4 (`trpo_privslim24d_260721_114717`, p_t 28D -> 24D, 5000 iters) fails every eval
clause of its pre-registered band, at the confound-free `none` level:

| criterion | required | measured |
|---|---|---|
| none roll ss_error | within +/-5% (<= 0.2256) | 0.3730 (+73.6%) |
| none pitch ss_error | within +/-5% (<= 0.2043) | 0.3799 (+95.3%) |
| none roll CV | within +/-5% (<= 18.2%) | 41.9% (+142.0%) |
| none pitch CV | within +/-5% (<= 10.4%) | 29.5% (+198.1%) |

[EVIDENCE: summary.json trpo_privslim24d_260721_114717 eval static_260721_180055 vs anchor
trpo_biasema_260715_142543 eval static_260716_160156; analysis diagnose-20260721-190151 §verdict]
[CONFIDENCE: HIGH]

[FINDING] THE LEAD'S PREMISE WAS WRONG — record this so no future experiment re-derives it.
`lin_vel` was marked "contested" because it is a MEASURED quantity and therefore looked
redundant inside privileged obs. In `envs/main` that reasoning does not hold:
`compute_policy_obs` is 20D = command(3) + euler(3) + body ang_vel(3) + arm(5) + thruster(6),
with NO linear velocity in any form, deliberately ("Linear velocity is excluded -- no DVL on
real robot"). The privileged channel was the ONLY route by which linear velocity reached the
network, so dropping it was an ABLATION, not a de-duplication.
[EVIDENCE: constrained_albc/envs/main/mdp/observations.py compute_policy_obs torch.cat read
directly at HEAD 2026-07-21]
[CONFIDENCE: HIGH]

[FINDING] Two independent lines confirm the dropped dims were live signal:
- the ANCHOR's encoder drove 9/9, 9/9, 8/9 latent dims from Lin Vel U/V/W with max z ranges
  0.5951 / 0.6852 / 0.8563 (quad_damp_roll: 7/9, 0.6693);
- `Loss/value_function` degraded +39.7% in A4, the largest training-side delta by far, while
  every Policy/* and Grad/* tag stayed within 2.2% — localising the damage to the critic, the
  asymmetric consumer of p_t.
[EVIDENCE: encoder_tools.py sweep on model_4999.pt of both runs; TB last-200-iter means]
[CONFIDENCE: HIGH]

[FINDING] The ENCODER is exonerated — this was not a capacity or representation failure. z_std
/ z_min / z_max match the anchor within 1.5%, no dimension went newly dead (A4 minimum 3/9),
and the anchor's one DEAD parameter (Joint Stiffness, 0/9, max range 0.0411) REVIVED under A4
(4/9, 0.1673). The network reorganised competently around a strictly poorer input.
[EVIDENCE: encoder_tools.py sweep both runs; TB Encoder/* last-200-iter means]
[CONFIDENCE: HIGH]

[FINDING] SCOPE LIMITS on this closure (do not overstate it):
- BUNDLE verdict: `quad_damp_roll` and the 3 `lin_vel` dims were dropped in the SAME run. The
  mechanism argues for lin_vel, but `quad_damp_roll` is not formally cleared. If slimming is
  ever wanted again, re-scope it to `quad_damp_roll` ALONE.
- A4 took 19 DORAEMON expansions vs the anchor's 18, so its soft/medium/hard columns are a
  harder exam; only `none` is confound-free. The verdict rests on `none` only.
[EVIDENCE: TB DORAEMON/kl_step step lists; see the correction on
[[doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step_]]]
[CONFIDENCE: HIGH]

STATUS: resolved. No further A/B needed for lin_vel. The union-28D layout stands as the default.

---

## Update (2026-07-21T10:04:57.511551)

STATUS SET resolved 2026-07-21 by A4 (see the LEAD CLOSED section above). Remaining scope, if slimming is ever revisited: quad_damp_roll ALONE (never bundled with lin_vel).

---

## Update (2026-07-21T10:05:13.097666)

The 'Parked under the 2026-07-20 batch-pass decision' annotation is obsolete: the batch pass RAN this probe as A4 on 2026-07-21 and it resolved. Nothing is pending.

---

## Merged from a4_fails_every_eval_clause_of_its_pre_registered_band_by_a_wide_.md (2026-07-23T07:32:14.143051)

# A4 fails every eval clause of its pre-registered band by a wide margin, so the l

A4 fails every eval clause of its pre-registered band by a wide margin, so the lead resolves exactly as the band's alternative branch specifies: keep 28D, the contested dims are load-bearing.

[EVIDENCE: summary.json `none/roll/ss_error` 0.3730 vs 0.2149, `none/pitch/ss_error` 0.3799 vs 0.1946; CV computed as ss_error_std/ss_error = 0.1564/0.3730 and 0.1122/0.3799 vs anchor 0.0372/0.2149 and 0.0193/0.1946]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md


---

## Merged from lin_vel_is_not_a_redundant_privileged_dim_in_envs_main_the_polic.md (2026-07-23T07:32:14.143051)

# `lin_vel` is NOT a redundant privileged dim in `envs/main`. The policy observati

`lin_vel` is NOT a redundant privileged dim in `envs/main`. The policy observation is 20D and contains command(3) + euler(3) + body angular velocity(3) + arm(5) + thruster(6) — no linear velocity in any form, by explicit design ("Linear velocity is excluded -- no DVL on real robot"). Removing `root_lin_vel_b` from p_t therefore deleted linear velocity from the entire network, not a duplicate copy of it.

[EVIDENCE: `constrained_albc/envs/main/mdp/observations.py` `compute_policy_obs` torch.cat contents read directly at HEAD; docstring lines 17-18 and 24 confirm "no measured lin_vel" / "no lin_vel_err"]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
