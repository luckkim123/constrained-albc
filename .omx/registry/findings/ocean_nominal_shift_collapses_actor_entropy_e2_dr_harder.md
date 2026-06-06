---
title: "ocean nominal shift collapses actor entropy (E2 dr-harder)"
tags: ["doraemon", "ocean_current", "nominal", "entropy_collapse", "overfit", "dr-harder"]
created: 2026-06-06T02:05:25.918621
updated: 2026-06-06T02:05:25.918621
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
---

# ocean nominal shift collapses actor entropy (E2 dr-harder)

DR-harder campaign E2: ocean_current_strength nominal 0.0->0.3 (DORAEMON distribution CENTER shift, kl_ub stays baseline 0.06). Reached SAME ocean coverage as E1-kl_ub (mean 0.409 vs 0.421) but via center-shift not curriculum-speed. NEW failure mode distinct from E1: actor entropy COLLAPSED -0.63 (omx TIER1, 'exploration dead') vs E1 entropy LOW-but-alive 0.16 vs teacher 0.29. E2 reward HIGHEST 257.97 (vs E1 216, teacher 232) + success 0.972 + entropy collapse = classic OVERFIT signature. Mechanism: nominal=0.3 raises the LOWER bound of sampled ocean current, starving weak/no-current episodes -> policy specializes to strong current, high reward on the narrowed training dist, dead exploration. Baseline nominal=0 samples the full no->strong range. Encoder z-sweep still healthy (active 9/9, mean max_zr 0.962 ~ teacher) -> collapse is in the ACTOR action entropy, NOT the encoder. KEY for speed-vs-tail: E1(speed) and E2(center-shift) reach same coverage by different means; E1 keeps entropy alive but hurts attitude, E2 kills entropy. eval none/soft levels = the overfit confirmation (expect E2 worse at weak DR if overfit). LESSON: shifting DORAEMON nominal up is NOT a free way to get hard-current coverage -- it collapses exploration. Prefer methods that widen variance from nominal=0 over methods that move the center.
