---
title: "obs4 Phase D result 2026-08-04: folding the 4 deployable channels into policy_obs (72 -> 76) PASSES H1 with margin; it buys hard-DR tail and spread with a REAL pitch steady-state regression at soft/medium"
tags: []
created: 2026-08-04T00:44:17.984523
updated: 2026-08-04T00:44:17.984523
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# obs4 Phase D result 2026-08-04: folding the 4 deployable channels into policy_obs (72 -> 76) PASSES H1 with margin; it buys hard-DR tail and spread with a REAL pitch steady-state regression at soft/medium

## Verdict

Controlled run `trpo_obs76fault_s30_260804_043926` vs the E-int teacher
`trpo_eint_s30_rs2350_260727_195102` (eval `static_260729_133417`). One variable: policy_obs
72 -> 76. Report `diagnose-20260804-093500` (report-review approve, report-coverage 7/7).

Pre-registered H1 (no nominal-level floor regresses AND hard att_norm within floors) **PASSES
both clauses, not narrowly**:

| clause | metric | E-int | E-obs76 | delta | floor |
|:--|:--|--:|--:|--:|--:|
| 1 | none roll n_gt20 (envs of 64) | 0.00 | 4.33 | +4.33 | 15 |
| 1 | none roll os_env_mean (pp) | 8.18 | 11.75 | +3.57 | 10 |
| 1 | none pitch ss_error (deg) | 0.2132 | 0.2743 | +0.0612 | 0.10 |
| 2 | hard att_norm ss_error (deg) | 0.7189 | 0.7297 | +0.0108 | 0.10 |

The obs76 teacher is ELIGIBLE for Phase E. Phase E itself remains a human-gated launch.

## What the widened observation actually does

Gains concentrate at the hard-DR corner, which is where a teacher is hard to distill from:

- roll heavy tail REMOVED: peak_max 63.19 -> 4.20 deg, %env above the 20 deg threshold 2% -> 0%.
- pitch tail also cut: peak_max 13.06 -> 2.80 deg.
- hard att_norm ss_error_std 1.2791 -> 0.8034 (-37.2%); the none -> hard spread ratio drops from
  6.5x to 1.8x.
- roll and yaw transients improve at every level (yaw os_env_mean 4.04/3.99/3.41/5.06 ->
  1.40/1.61/1.90/3.09 pp; yaw loses its only over-threshold env at hard).
- Survival stays 100% at all four levels in both runs.

## The cost, which is REAL and outside H1's clauses

roll ss_error improves at ALL FOUR levels while pitch ss_error degrades at ALL FOUR, clearing the
0.10 deg floor at soft (+0.1336) and medium (+0.1204). H1 clause 1 tests `none` only and clause 2
tests `hard` att_norm only, so this passes the gate while still being a real regression -- do not
report the GO without it.

The trade is NOT the plant: it appeared in the same direction at all four levels in the voided
fault-free attempt (`trpo_obs76_s30_260803_233239`, deltas +0.0391/+0.0922/+0.1052/+0.3062) as
well. Whether it is the observation or the seed is unresolved -- this campaign has no seed
replicate anywhere.

`Constraint/margin/rp_rate` is the one constraint whose pressure moves materially (JC/dk
0.349 -> 0.438, margin 6.51 -> 5.62), which is the roll/pitch rate budget the trade would touch.
Association across two single-seed runs, not a measured mechanism.

## The unexpected result: the encoder leans out

`Grad/enc_step` drops 35.9% here and 36.3% in the fault-free attempt -- a 0.4 pp difference across
a plant change that moved `Constraint/margin/thruster_util` by 1.34 and `DORAEMON/success_rate`
by 0.06. So it tracks the observation width, not the plant. `Policy/encoder_grad_norm` moves the
same way (-14.1%). The latent itself is unchanged in scale (`Encoder/z_std` 0.393 -> 0.382).

The encoder sees the SAME 28D privileged input in both runs, so nothing in its own input changed.
Plausible reading: a policy with direct acceleration feedback leans less on the latent. That is
precisely the coupling Phase E's student has to reproduce, so **run `encoder_tools.py sweep` on
both teacher checkpoints before Phase E** -- per-dimension sensitivity is the instrument;
`Encoder/z_std` cannot certify it.

