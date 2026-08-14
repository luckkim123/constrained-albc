---
title: "The mean-preserving Beta clamp silently triples concentration for nominal-0 DR dims (30 -> 100), and those 4 dims are exactly the ones that end under-expanded"
tags: ["doraemon", "curriculum", "beta", "init_concentration", "fault_severity", "clamp", "expansion-budget", "kl_ub", "e-ftc1", "differential-diagnosis", "intervention-confirmed"]
created: 2026-07-28T09:12:53.564095
updated: 2026-07-29T08:24:52.913601
sources: ["diagnose-20260727-140324", "curriculum_trajectory.json", "doraemon.py:118-145", "next-20260728-180215", "diagnose-20260729-171553", "trpo_ftc1sevinit_s30_260729_105510"]
links: ["curriculum_recalibration_protocol_widening_the_dr_box_requires_r.md", "severity_init_head_start_converts_to_curriculum_2_50x_but_makes_.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The mean-preserving Beta clamp silently triples concentration for nominal-0 DR dims (30 -> 100), and those 4 dims are exactly the ones that end under-expanded

# Why the four nominal-0 DR dimensions all stop at 6-8% of range while the other 17 nearly saturate

Established by code-exec on `trpo_faultdr_agnostic_s30_260725_183121`'s own
`train/curriculum_trajectory.json` (2026-07-28), while designing E-ftc1.

[FINDING] `BetaDistribution.__init__` maps a dimension's nominal to `mu = (nominal - lo)/(hi - lo)`, clamps `mu` to `[0.01, 0.99]`, and if either `a_raw = mu * concentration` or `b_raw` falls below `_MIN_BETA_PARAM = 1.0` it takes a mean-preserving clamp branch. For a nominal-0 dimension with `init_concentration = 30` this always fires: `mu` clamps to 0.01, `a_raw = 0.3 < 1.0`, so the branch yields `Beta(1, 99)` — concentration **100**, i.e. 3.3x NARROWER than the configured 30. The configured `init_concentration` is therefore inert for every nominal-0 dimension; any value below 100 lands on the identical `Beta(1, 99)`.
[EVIDENCE: marinelab/marinelab/algorithms/doraemon.py:131-142 (clamp arithmetic) and :86 (_MIN_BETA_PARAM = 1.0); confirmed against the run artifact — curriculum_trajectory.json records a=1.000, b=99.000 for fault_severity at iter 0]
[CONFIDENCE: HIGH]

[FINDING] The 21 dimensions split into exactly two populations, and the split predicts the endpoint. 17 dims start `Beta(15, 15)` (concentration 30, mean 0.5, the default `(lo+hi)/2` nominal) and end near-uniform at `a ~ b ~ 1.9-3.5`. The 4 dims listed in `_NOMINAL_OVERRIDES` with nominal 0 — `ocean_current_strength`, `payload_cog_offset_xy_u`, `obs_noise_scale`, `fault_severity` — start `Beta(1, 99)` and end at means **0.0599 / 0.0699 / 0.0725 / 0.0771**, with `a` still pinned at exactly 1.000 after the full run.
[EVIDENCE: code-exec over all 21 entries of curriculum_trajectory.json trajectory[0] and trajectory[-1]; _NOMINAL_OVERRIDES at constrained_albc/envs/main/doraemon.py:90-95]
[CONFIDENCE: HIGH]

[FINDING] This is the differential-diagnosis clincher for "under-expanded" verdicts on any of those four dims: the four are physically unrelated (ocean current, sensor noise, payload CoG offset, thruster faults) yet land inside a 1.3x band, while every unclamped dim runs to near-uniform. Four independent competence frontiers do not coincidentally align that tightly. So an under-expanded nominal-0 dimension is evidence about the INITIALIZATION plus the shared budget, not about that dimension being physically hard for the policy.
[EVIDENCE: the 0.0599-0.0771 band above vs 17 dims at mean ~0.50; fault_severity is in fact the BEST of the four, which a competence explanation would not predict for the dimension whose A/B was built around it]
[CONFIDENCE: HIGH]

[FINDING] The trust-region budget is the pacing constraint on this run too, reproducing the recorded posttam pattern: reconstructing each DORAEMON update's KL from the trajectory gives exactly 0.12000 on 17 of 19 updates (exceptions: the first update, and one blocked update at iter 4500 where the distribution did not move). `fault_severity`'s share of that fixed 0.12 rises 0.00493 -> 0.01344, i.e. 4.1% -> 11.2%, because it competes with 20 other dimensions.
[EVIDENCE: torch.distributions.kl_divergence over consecutive Beta(a,b) states from curriculum_trajectory.json; as-run config/env.yaml doraemon block gives kl_ub 0.12, step_interval 250, init_concentration 30.0]
[CONFIDENCE: HIGH]

# CORRECTION to a recurring mis-citation: kl_ub here is 0.12, NOT the engine default 0.5

`DoraemonCfg.kl_ub` defaults to 0.5 in the engine (marinelab doraemon.py:41), but ALBC overrides it
to **0.12** at `constrained_albc/envs/main/config.py:601`, and the as-run `config/env.yaml` of the
fault-DR arms confirms 0.12. Any budget arithmetic quoting 0.5 overstates the per-update trust region
by 4x. (0.12 is itself the raised value from dr_harder E1, which is why raising it further is
known-bad.)

# Practical consequence

For a nominal-0 dimension the reachable endpoint is set by where the clamp puts the start, not by the
dimension's difficulty. Raising that ONE dimension's nominal just above the clamp threshold
(`mu > 1/init_concentration`, i.e. > 0.0334 at concentration 30) is a per-dimension lever that leaves
the other 20 dims bit-identical — distinct from widening DR BOUNDS, which
[[curriculum_recalibration_protocol_widening_the_dr_box_requires_r]] shows buys ceiling but no
distance. Replaying the observed KL allocation from a higher start projects roughly 3x the reach at
the same budget; the clamp escape itself, not the magnitude of the new nominal, is the dominant term.
Proposed as E-ftc1 (`next-20260728-180215`).

---

## Update (2026-07-29T08:24:52.913601)

[CONFIRMED BY INTERVENTION 2026-07-29 -- E-ftc1] The clamp diagnosis is now causally established, not just correlational. Setting _NOMINAL_OVERRIDES['fault_severity'] = 0.0771 (Arm A's own measured endpoint, so Beta(2.3130, 27.6870) clears the a>1 clamp) was the ONLY code change vs Arm A, and it raised the final DORAEMON/mean/fault_severity from 0.0771 to 0.1929 -- a 2.50x endpoint on identical iterations, envs, seed and plant. Escaping the clamp is therefore worth ~2.5x of curriculum expansion on a nominal-0 dim, and the clamp (not competence) was the binding limiter. [EVIDENCE: tb_final.py --window 200 DORAEMON/mean/fault_severity 0.19290 vs 0.07710; engine [TIER 2] param table 19.3% vs 7.7% of range; curriculum_trajectory.json final update iter 4750 Beta(1.2102, 5.0634) vs Beta(1.0000, 11.9694); analysis diagnose-20260729-171553 section 'doraemon'] [CONFIDENCE: HIGH] [CAVEAT] The expansion is NOT free of a downstream cost and does NOT transfer to robustness -- see [[severity_init_head_start_converts_to_curriculum_2_50x_but_makes_]]. Pacing held: kl_step pinned at the 0.12 cap on 16/16 executed updates, DORAEMON/mode back to 0 after warm-up, success_rate 0.7707 above alpha 0.5, and the curriculum was still accelerating at run end (trend/1k +0.0545), so 0.1929 is iteration-limited, not a ceiling.
