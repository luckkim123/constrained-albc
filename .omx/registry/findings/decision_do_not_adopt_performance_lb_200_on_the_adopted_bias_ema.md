---
title: "DECISION: do NOT adopt performance_lb=200 on the adopted bias_ema-ON config -- success 0.989 makes the feasibility constraint inert (the lb=68 failure class)"
tags: ["performance_lb", "doraemon", "bias_ema", "p-a8", "perflb200", "adoption"]
created: 2026-07-16T05:50:26.660824
updated: 2026-07-16T05:50:26.660824
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# DECISION: do NOT adopt performance_lb=200 on the adopted bias_ema-ON config -- success 0.989 makes the feasibility constraint inert (the lb=68 failure class)

# DECISION: do NOT adopt performance_lb=200 -- on the adopted bias_ema-ON config it makes the feasibility constraint inert

Context: `use_bias_ema_obs=True` was adopted to main 2026-07-16 (commit f42a67f). The open question
was whether the perflb200 probe's `performance_lb` 250->200 (branch exp/perflb-recalib, commit
d3789a7, config.py:541) should be adopted alongside it. Answer: NO -- and the reason only becomes
visible once the two are considered TOGETHER.

[FINDING] lb=200 was calibrated against a plant/policy whose return distribution was much lower.
bias_ema observability raised the whole distribution: buffer p25 212.0 -> 261.8, p5 91.7 -> 237.1.
On the adopted config, `success = P(return >= 200)` = 0.989 -- P-B1's own p5 (237.1) already clears
200, so essentially every episode succeeds and the constraint `Ghat >= alpha` would be satisfied
unconditionally.
[EVIDENCE: doraemon_state.pt buffer_returns, trpo_biasema_260715_142543 vs trpo_baseline_260714_192020, n=2000 each, 2026-07-16 code-exec]
[CONFIDENCE: HIGH]

[FINDING] That is the same failure class the original 260608 recon existed to fix. Per
`doraemon_difficulty_has_3_separable_levers...`: lb=68 "sat BELOW the minimum observed return (81.9),
so success=return>=68 was always 1 -> the feasibility constraint Ghat>=alpha was inert -> the
curriculum widened DR unconstrained (no self-pacing)". lb=200 on the bias_ema-ON config reproduces
that shape (success 0.989, not literally 1.0, but with no live self-pacing left).
[EVIDENCE: wiki doraemon_difficulty_has_3_separable_levers_kl_ub_step_size_step_.md 2026-07-08 correction block; buffer recon above]
[CONFIDENCE: HIGH]

[FINDING] P-A8 is the empirical demonstration of what lb=200 buys, on the config it WAS calibrated for
(bias_ema OFF): 8000 iters at lb=200 drove all 20 DORAEMON params to the Beta(1,1) config ceiling
while the return distribution collapsed (buffer p25 189.5 -> 134.8, p5 66.9 -> 21.8, median 229.5 ->
199.2) and success settled at the alpha floor (0.4955). So lb=200 is the setting that lets the
curriculum widen DR until the policy is at its feasibility limit. Stacking it on top of a config that
ALSO raises returns pushes that limit further out, not closer.
[EVIDENCE: doraemon_state.pt buffer_returns, trpo_perflb200-moreiters_260715_195227 vs trpo_perflb200_260715_023744; report diagnose-20260716-035505]
[CONFIDENCE: HIGH]

# What lb SHOULD be for the adopted config

Applying the original 260608 rule (lb = the buffer's p25) to the adopted bias_ema-ON config gives
**lb = 261.8** (success 0.750 by construction). Current main is lb=250 -> success 0.882: slightly
loose against the measured p25 but inside the live self-pacing band, so no change is FORCED. Success
by candidate lb on the adopted config: 200 -> 0.989 (inert) | 220 -> 0.977 | 240 -> 0.938 |
250 -> 0.882 (current) | 261.8 -> 0.750 (measured p25 rule) | 275 -> 0.498 (below alpha, would stall).

# Caveat on the alpha comparison

DORAEMON's gate does NOT use the raw buffer mean: on update steps `current_success_rate` is an
IS-weighted estimate (`_estimate_success_rate`, doraemon.py:427) and that is what is compared to
alpha (doraemon.py:430); the raw `success.mean()` is only what gets logged BETWEEN updates
(doraemon.py:409, overwritten at :428). The raw-buffer numbers above are therefore the right
instrument for "where does this policy's return distribution sit relative to a candidate lb", but
they must NOT be read as the gate's own decision. In particular P-A8's raw 0.4955 does not contradict
its report's "success settled AT alpha, mode stayed 0" -- that reading is correct.

