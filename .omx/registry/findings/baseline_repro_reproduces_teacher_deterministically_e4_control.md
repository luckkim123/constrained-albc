---
title: "baseline-repro reproduces teacher deterministically (E4 control)"
tags: ["baseline", "reproducibility", "determinism", "control", "dr-harder", "kl_ub"]
created: 2026-06-05T20:58:14.324131
updated: 2026-06-05T20:58:14.324131
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# baseline-repro reproduces teacher deterministically (E4 control)

DR-harder campaign E4 (baseline-repro, kl_ub=0.06 ocean nominal=0.0, no knob changed). Reproduces teacher 260525_232805 DETERMINISTICALLY: training (reward 232.74, ocean mean 0.1176, success 0.964, entropy_before -19.676, changepoints 434/3324) AND eval (all 24 axis*level ss_error cells within +-0.3% of teacher: roll hard 1.101==1.101, pitch hard 0.352==0.352). The full pipeline (env seed = agent seed fixed, eval seed fixed) is deterministic. CONSEQUENCE: this removes seed-noise as an explanation for any campaign treatment. E1's attitude regression (roll/pitch ss_error +30-70%) and translational gain (vx -14%, yaw -39%) are the PURE CAUSAL effect of kl_ub 0.06->0.12. 3-way teacher|E4|E1 confirms: E4==teacher, E1 diverges only where kl_ub acts. The 2x2 factorial has a rock-solid deterministic control corner -> E2/E3 read cleanly against it.
