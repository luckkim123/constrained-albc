---
title: "Where is Arm W losing the 8 points of return: per-DR-dimension quintile decomposition (M3)"
tags: ["doraemon", "curriculum", "feasibility", "diagnosis", "arm-w", "performance-lb", "quintile", "M3", "blocked", "engine-gap"]
created: 2026-08-10T02:35:14.326657
updated: 2026-08-14T07:46:42.763605
sources: ["arXiv:2311.01885", "wiki-backlog-20260814"]
links: ["engine_gap_the_analysis_engine_and_omx_reduce_are_both_unusable_.md", "engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact.md", "doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "two engine-gaps: no per-env episode-return channel in eval.py, and _per_env_ss_stats does not expose its per-env vector"
---

# Where is Arm W losing the 8 points of return: per-DR-dimension quintile decomposition (M3)

OPEN LEAD, opened 2026-08-10 after M2 eliminated exploration as the cause of Arm W's failure.

The question. Arm W (trpo_rampw_kl006_s30_260809_161913) ended with Train/mean_reward 241.69 against performance_lb 250.0 and 0/21 curriculum dims saturated, while the reference run held 258.56 and locked 21/21. Both reached the same maximum DR width on ocean_current_strength (0.2887) and carried statistically identical action noise (see exploration_is_not_coupled_to_curriculum_width_dr_grew_10_29x_wh). So the deficit is in the return itself. The open question is WHERE the return is lost: is it spread evenly across the randomization box, or is one dimension's upper range physically infeasible and dragging the mean under the floor?

The test. Bucket episodes by the DR value actually sampled for each env into quintiles, per dimension, and read mean episode return per bucket. Existing rollout logs; no training run required. The 21 declared dims are the candidates, with ocean_current_strength, payload_cog_offset_xy_u, water_density and fault_severity the priors (largest measured widening, 10-29x over it 5000-18205).

Decision rule, fixed before looking:
- If one or two dimensions show their top quintile far below the rest (order of 200 versus 250+) while the remaining buckets sit above the floor, the bottleneck is a specific infeasible range and the fix is a ceiling cap on that dimension, NOT more iterations, NOT exploration, NOT a lower performance_lb.
- If the return deficit is spread roughly evenly across every dimension's quintiles, the specific-dimension hypothesis is rejected and the remaining candidate is a global plant or reward-scale issue.

Why this is the right next probe. It is the same diagnosis the DORAEMON authors reached on their own failing environments: they attribute Walker2D and Swimmer degradation to "the agent's exposure to harder/infeasible parameters, which destabilize training" (arXiv:2311.01885). Their remedy was to track the best-performing checkpoint rather than to change exploration - which is also what the selection pass now running does for us.

Related decision already on the table: D5, the T200 command-to-thrust bench plus XW540-T260 step response, is the only path that would RAISE the DR ceiling rather than cap it. If M3 identifies an infeasible thruster-side range, D5 becomes the follow-on rather than an independent item.

Not yet started. Blocked on nothing - the workstation is busy with the Arm W selection pass and the 2-way finalist until roughly 13:20 KST on 2026-08-10, and the DGX is running Arm D, but M3 itself needs no GPU beyond reading logged rollouts.

---

## Update (2026-08-14T07:46:42.763605)

COST CORRECTION 2026-08-14. This page says "Existing rollout logs; no training run required" and
"Blocked on nothing". Both are FALSE, verified in code today. M3 stays open and stays the right probe,
but it is not free and a session that picks it up expecting a read-only analysis will stall.

BLOCKER 1 -- THERE IS NO PER-ENV EPISODE RETURN ANYWHERE.
- `constrained_albc/analysis/eval.py` writes no reward or return channel at all. The static-eval
  `data_<level>.npz` carries 40 keys: 23 `dr_*` per-env parameter arrays plus trajectories
  (`actual_roll_deg`, `error_roll`, `yaw_rate`, `action_magnitude`, `terminated`, `time_to_failure`,
  `fault_injection`, ...). Checked the key list directly on
  `teacher_final_ramp/trpo_rampw_kl006_s30_260809_161913/eval/static_260810_122553/data_hard.npz`.
- The training side has only the AGGREGATE: `Train/mean_reward` is one scalar per iteration in
  TensorBoard. Per-env returns are never persisted.
So "mean episode return per bucket", the quantity this page's decision rule is written on, cannot be
computed from anything on disk.

BLOCKER 2 -- THE OBVIOUS PROXY IS ALSO UNREACHABLE, AND FOR A REASON ALREADY ON RECORD.
`Reward/att_rp` dominates the reward (6.96 of 8.86 total), so per-env steady-state attitude error is
the natural substitute. It is computed -- and then thrown away.
`constrained_albc/analysis/_analyze/recompute_metrics.py:234 _per_env_ss_stats` builds `per_env_mean`
and `per_env_std` (the 64-vectors) and returns four aggregated scalars. No consumer can reach the
vector. This is EXACTLY item 4 of [[engine_gap_the_analysis_engine_and_omx_reduce_are_both_unusable_]],
which was filed when the same wall stopped a different test, and which states the resolution: return
the per-env arrays alongside the scalars, or expose a `per_env=True` variant. That page also records
why the workaround is forbidden -- reproducing the segment/settled-window logic outside the repo is the
duplicated-code-path failure 38d979e already cost this campaign.

BLOCKER 3 -- STATISTICAL POWER, EVEN ONCE 1 AND 2 ARE FIXED.
The static eval runs 64 envs (`eval.py:71`, `--num_envs` default 64). Quintiles over 21 dimensions
give ~12.8 envs per bucket per dimension, and the page's decision rule asks to distinguish a top
quintile "of order 200 versus 250+" -- a ~20% effect -- across 21 simultaneous comparisons. That needs
a large-n eval, not the standard 64. Whoever runs M3 should size n first and say what effect it can
resolve.

WHAT M3 ACTUALLY COSTS, THEN: one additive instrumentation change to eval.py (a per-env episode-return
channel, opt-in), one small change to `_per_env_ss_stats` (expose the per-env vector), and one
high-num_envs eval of the two runs. The eval.py precedent to copy is
[[engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact]], which delivered
`--save-policy-obs` / `--save-action-std` as opt-in flags with byte-identical default output.

WHAT DOES NOT CHANGE. The premise is confirmed on the completed run, not merely the 11k snapshot:
Arm W's final `Train/mean_reward` is 241.63 (final-200 window) / 242.34 (final-1000) against
`performance_lb` 250.0, and the return is FLAT for the last 9,000 iterations -- so the deficit is
permanent and the question "where is it lost" is still the right one. See
[[doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_]], now closed with that data.

