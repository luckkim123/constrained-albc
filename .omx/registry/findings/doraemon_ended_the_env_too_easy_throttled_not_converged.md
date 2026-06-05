---
title: "DORAEMON ended the env too easy (throttled, not converged)"
tags: ["doraemon", "curriculum", "kl_ub", "difficulty", "dr"]
created: 2026-06-02T10:23:47.559392
updated: 2026-06-02T10:23:47.559392
sources: ["20260602-192051-diagnose"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# DORAEMON ended the env too easy (throttled, not converged)

On run 260525_232805_trpo_main_teacher the DR curriculum was STILL actively widening at the final iter (iter 5000), so the env ended too easy — it did NOT converge to a physics/policy ceiling. Deciding evidence (TB, analysis 20260602-192051-diagnose Axis 2): DORAEMON/entropy_before rose +15.62 nats monotonically, end-slope still +1.82/1000iter (no plateau, decile fit R2=0.994); all 4 physics-param stds ended at their run-max (ocean/payload/added_mass/lin_damp last==max). The throttle is kl_ub: DORAEMON/kl_step hit the cap exactly on every update (19/19=100%, value=0.0600) and only 19/20 expected updates fired in 5000 iters. success_rate sat ~0.97 vs target alpha=0.50 (+0.465 unused headroom; marinelab doraemon.py:40). IS reliability was fine (ess_ratio>=0.865, no reverts) so ESS is NOT the limiter. CONCLUSION for next experiment: to harden the env, raise kl_ub (0.06 -> higher) and/or extend iterations; success at 0.97 proves policy room. ocean_current_strength is the weakest-hardened axis (only 36% of uniform-range diversity, mean drifted only 0.010->0.118) -> harden first. 3 of 4 param MEANS stayed nominal (symmetric Beta widened width only), so the hard tail is under-sampled even as std grew -> consider shifting Beta centers, not just widths.
