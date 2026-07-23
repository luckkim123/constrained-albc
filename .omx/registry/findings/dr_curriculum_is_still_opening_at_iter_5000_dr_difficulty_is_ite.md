---
title: "DR curriculum is still opening at iter 5000 -- DR difficulty is iteration-limited, not bounds-limited"
tags: ["doraemon", "curriculum", "dr", "beta"]
created: 2026-07-23T04:54:57.071654
updated: 2026-07-23T04:54:57.071654
sources: ["diagnose-20260723-134359"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# DR curriculum is still opening at iter 5000 -- DR difficulty is iteration-limited, not bounds-limited

FINDING: at 5000 iters the DORAEMON Beta curriculum has NOT reached its box bounds and is still widening monotonically when training stops. EVIDENCE (curriculum_trajectory.json, buoyanchor s30, mean Beta parameters over the 20 DR params): iter 0 a=12.900 b=27.600; 1000 a=10.033 b=20.816; 2000 a=5.920 b=11.793; 3000 a=3.584 b=6.668; 4000 a=2.261 b=3.767; 4750 a=1.670 b=2.469. At the last snapshot 0 of 20 params have reached the a=b=1 full-width bound: the 17 physical params sit at a=b in 1.57-2.66 on all three seeds, and the three one-sided params (payload_cog_offset_xy_u, ocean_current_strength, obs_noise_scale) sit at a=1, b=6-11. CONSEQUENCE: widening the DR BOUNDS cannot act on a box the curriculum never reaches within 5000 iters, so the bounds-widening half of curriculum_recalibration_protocol is inert at this iteration budget (Z2's saturation was observed on 8k runs at iter 7000). It also explains why every scale-up failed: more iterations buy a HARDER DR box rather than a better policy, and the nominal roll transient is what pays (A1: +13.5 pts worse). Re-visit: analysis diagnose-20260723-134359 section 'doraemon'.
