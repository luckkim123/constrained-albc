---
title: "teacher encoder: 0 dead latent dims, keys on lateral CoG/CoB offsets"
tags: ["encoder", "z-sweep", "teacher"]
created: 2026-06-06T10:55:06.773233
updated: 2026-06-06T10:55:06.773233
sources: ["diagnose-20260606-194621"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# teacher encoder: 0 dead latent dims, keys on lateral CoG/CoB offsets

Teacher (trpo_main_teacher_260525_232805) asymmetric encoder is healthy, NOT collapsed: z-sweep over 24 DR params shows 0/9 dead latent dims (per-z-dim max |z_range| across all params > 0.44 for 8 dims, z[7]=0.441; dead = max range<0.1). Mean active_dims 8.4/9. Gradient channel alive: Policy/encoder_grad_norm=0.231, Grad/enc_step=0.0094 (not the <1e-4 DEAD threshold). z saturation fine: Encoder/z_std=0.449, range [-0.731,0.733] inside softsign. The encoder responds MOST to lateral CoG/CoB offsets + body mass (Payload CoG Y 6.64, Main CoG Y 6.45, Main CoB Y 6.26, Body Mass 5.90 total z movement) and LEAST to water_density 0.95 / quad_damp 1.21 / thrust_coeff 1.53. This matches physics: lateral mass-center offset perturbs roll/pitch = exactly the axis that struggles under hard DR. EVIDENCE: encoder/sweep/summary.json; engine TIER1. Re-analysis diagnose-20260606-194621 section encoder. Confirms encoder verification per rule 03 (z_sweep required, not TB aggregate alone).
