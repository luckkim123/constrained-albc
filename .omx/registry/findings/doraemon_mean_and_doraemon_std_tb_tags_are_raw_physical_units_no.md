---
title: "DORAEMON/mean and DORAEMON/std TB tags are RAW PHYSICAL UNITS, not normalized xi -- Beta(a,b) inversion from them is valid for only 3 of the 20 params"
tags: ["doraemon", "tensorboard", "beta", "metric-definition", "label-vs-implementation", "trap", "posttam"]
created: 2026-07-20T17:22:49.093810
updated: 2026-07-20T17:22:49.093810
sources: ["diagnose-20260721-020253", "doraemon_state.pt"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# DORAEMON/mean and DORAEMON/std TB tags are RAW PHYSICAL UNITS, not normalized xi -- Beta(a,b) inversion from them is valid for only 3 of the 20 params

Do NOT reconstruct a DORAEMON parameter's Beta(a,b) by inverting the TB tags `DORAEMON/mean/<p>` and `DORAEMON/std/<p>`. Those are logged in the parameter's RAW PHYSICAL UNITS, not in the normalized xi in [0,1] that the Beta lives on. The inversion (c = m(1-m)/s^2 - 1; a = m*c, b = (1-m)*c) therefore returns garbage -- b near 0 or negative -- for any param whose physical range is not [0,1]. [EVIDENCE: A1 run trpo_stepint400_260720_180208 final TB values -- water_density mean=1009.9931 std=7.2275; body_mass_scale mean=1.0003 std=0.1198; payload_mass mean=1.4910 std=0.7248 -- none of which lie in [0,1]] [CONFIDENCE: HIGH]\n\nThe inversion happens to be CORRECT for exactly three params, because their physical range IS [0,1]: obs_noise_scale, ocean_current_strength, payload_cog_offset_xy_u -- the same three the posttam reports call the 'deployment params'. Verified: TB inversion on A1 gives b = 5.635 / 5.401 / 5.502, and doraemon_state.pt dist_b's three largest values are 5.635 / 5.502 / 5.401. This coincidence is why the trap is easy to miss -- the method looks validated on the params people happen to check. [EVIDENCE: TB inversion vs torch.load(doraemon_state.pt)['dist_b'] on the same run, exact agreement to 3 decimals] [CONFIDENCE: HIGH]\n\nThe correct source for Beta shape is the checkpointed state: torch.load(<run>/train/doraemon_state.pt)['dist_a'] and ['dist_b'], two 20-element tensors in the config's DR param order. Use it for any all-param question (saturation counts, box width, per-dim shape). Reserve the TB tags for the 3 [0,1] params or for trend plots in physical units. [EVIDENCE: doraemon.py:776 saves {'dist_a': self.dist._a.clone(), 'dist_b': self.dist._b.clone()}] [CONFIDENCE: HIGH]
