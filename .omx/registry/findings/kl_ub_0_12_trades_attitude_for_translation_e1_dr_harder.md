---
title: "kl_ub 0.12 trades attitude for translation (E1 dr-harder)"
tags: ["doraemon", "kl_ub", "dr-harder", "attitude", "trade-off", "eval"]
created: 2026-06-05T15:58:22.919589
updated: 2026-06-05T15:58:22.919589
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
---

# kl_ub 0.12 trades attitude for translation (E1 dr-harder)

DR-harder campaign E1: kl_ub 0.06->0.12 (2x trust-region cap). RESULT = curriculum-speed knob, NOT quality knob. DORAEMON expanded DR 3.6x (ocean mean 0.118->0.421, std 0.105->0.269, entropy_before -19.7->-16.9) in same 5000 iter. BUT eval_dr static (vs teacher baseline): attitude SS error WORSE every DR level (roll hard 1.10->1.48deg +34%, pitch hard 0.35->0.60deg +69%); translation BETTER (vx hard -14%, yaw hard -39%). roll heavy-tail n_gt20 med/hard 8.7/8.7->19.3/15.3 (more attitude blowups). Survival 100% all levels (not death-spiral) + roll undershoot hard 8.8% => policy STABLY-WRONG on attitude: DC bias not oscillation (ss_jitter ~ teacher). Mechanism: harder ocean current absorbed by tilting roll -> steady-state offset. LESSON: do NOT push kl_ub to 0.18 to fix attitude; kl_ub speeds curriculum which trades rotation for translation. For SS-error-priority (user #1), kl_ub-up counterproductive on attitude. E2(ocean nominal 0.3 @ baseline speed)/E3 now discriminate speed-vs-tail root cause.
