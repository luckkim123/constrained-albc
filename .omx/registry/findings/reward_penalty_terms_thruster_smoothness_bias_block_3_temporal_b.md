---
title: "Reward penalty terms thruster/smoothness/bias block 3 temporal bands (magnitude/jerk/DC-offset); bias EMA makes a Markov reward see non-Markov drift"
tags: ["reward", "penalty", "bias-ema", "smoothness", "thruster", "jerk", "markov", "heavy-tail"]
created: 2026-06-14T07:38:12.435122
updated: 2026-06-14T07:38:12.435122
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# Reward penalty terms thruster/smoothness/bias block 3 temporal bands (magnitude/jerk/DC-offset); bias EMA makes a Markov reward see non-Markov drift

The three reward penalty terms (thruster / smoothness / bias) in envs/main block three DIFFERENT temporal bands -- effectively a frequency decomposition of what the instantaneous (Markov) tracking reward cannot see. Code-verified `envs/main/mdp/rewards.py` + `albc_env.py`, 2026-06-14.
COMMON STRUCTURE: each `Reward/*` value = `f(state) * k * dt` (`rewards.py:197` `scaled = value * weight * dt`). The function returns a NON-NEGATIVE magnitude; the negative weight `k` subtracts it. So all three function bodies return positive "badness", and `k<0` turns it into a penalty. Late values ~-0.05 in the baseline = policy pushed these costs near zero.
THE THREE BANDS:
- thruster (MAGNITUDE / 0 Hz): `thruster_energy` `:145` = mean of squared thruster cmds `(1/6) sum a_i^2` over `_actions[:,2:]` (6 thrusters; arm is [:,:2]). Actions are clamped to [-1,1] at albc_env.py:446, so it is a normalized [0,1] quadratic cost on raw control effort = energy efficiency. weight k_thr=-0.35 (strongest penalty after bias).
- smoothness (HIGH-FREQ / jerk): `action_smoothness` `:150` = mean(da^2) + mean(d2a^2) over all 8 actions. da = a_t - a_{t-1} (1st diff = velocity), d2a = a_t - 2 a_{t-1} + a_{t-2} (2nd diff = JERK). 3-tap filter via the `_prev_actions`/`_prev_prev_actions` buffers shifted each step at albc_env.py:444-446. 1st diff alone misses constant-velocity drift; 2nd diff catches it. weight k_s=-0.1. Directly relates to the report jitter (AC oscillation) metric.
- bias (DC OFFSET / very-low-freq): `bias_ema_penalty` `:157` = sum_i w_i * bias_ema_i^2, w=(1.5,1,1) over [roll,pitch,yaw_rate]. bias_ema is an EMA of the per-axis tracking error updated each step at albc_env.py:1046: `bias_ema = a*bias_ema + (1-a)*err`, alpha=0.99 (effective ~100-step = 2 s window at 50 Hz). weight k_bias=-2.0 (STRONGEST). Squared form so gradient grows with offset.
WHY bias is the subtle one (the key idea): per-step tracking reward is MARKOV -- it sees only instantaneous error and is structurally BLIND to "the policy parks roll at a steady +2deg offset" (each step's error is small so per-step reward is satisfied, but it never reaches 0). The EMA is a PERSISTENCE FILTER: symmetric jitter averages to ~0 and disappears, only a one-sided sustained offset survives. Putting the EMA into env state and exposing it as a penalty lets a Markov reward express a NON-Markov objective (kill sustained DC bias). Same trick as the `cumulative_yaw` constraint. This is the heavy-tail driver: report shows median env tracks tight (~0.2deg) but a minority hold a DC offset -> that is exactly what bias targets.
NON-OBVIOUS CONTRACTS:
- EMA updated ONLY when k_bias != 0 (albc_env.py:1036) -> zero wasted compute when the term is disabled (k_bias default 0).
- bias_ema RESET to 0 per episode (albc_env.py:1441) -> a within-episode quantity, not cross-episode.
- roll-heavier weight (1.5,1,1) mirrors att_roll_weight=1.5: both compensate weak roll TAM authority (0.007 m moment arm vs pitch 0.145 m).
TUNING HISTORY (config.py:391-396): k_bias=-2.0 is the r11_emabias setting, verified STRONGEST single intervention across 24 runs. r12 halved it to -1.0 -> hard roll regressed 0.62 -> 1.26 (rank #1 -> #7). r13 restored full -2.0.
