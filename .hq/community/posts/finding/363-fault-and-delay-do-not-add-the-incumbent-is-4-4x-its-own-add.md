# Fault and delay do not add: the incumbent is 4.4x its own additive prediction, the retrain is exactly additive

- id: finding/363 · date: 2026-09-05 · author: claude
- project: albc · harness: omx · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: pair34_d2, additivity, interaction, pairDR, deployment
- summary: pair34_d2 (m3+m4 dead AND the 152 ms delay) scored on three arms. At the one level where the pairing is valid, the incumbent overshoots its additive prediction by 7.232 deg while both retrained checkpoints match theirs. Measured apart the incumbent looks merely worse; measured together it is at 9.360 deg in the exact deployment condition.
# Fault and delay do not add: the incumbent is 4.4x its own additive prediction, the retrain is exactly additive

`pair34_d2` — m3 dead, m4 excluded, and two control steps of observation delay — is the
condition the robot actually flies in. Until this scoring the two stressors had only ever been
measured apart (`pair34` at zero delay; `healthy_d1`/`healthy_d2` with six healthy thrusters),
so nothing in the record said whether they compose.

## Read pairDR first, twice

Two separate validity results, and both remove rows that would otherwise have been read:

1. **Arm vs arm on `pair34_d2`, the `hard` rows are `pairDR = 1e-01`** while every CORE row of
   the same arm pair is `0e+00`. The two arms did not draw the same plant there. The mechanism
   is not established and is not guessed at; the rows are excluded.
2. **Within one arm, `pair34` and `pair34_d2` draw different plants at soft/medium/hard**
   (`pairDR` 2, 4, 6) — the delay flag changes RNG consumption. So the additivity test is valid
   at **`none` only**, where no DR is applied and the four configs are structurally paired.

Had those rows been read, the candidate would have shown an "excess" of +1.931 deg at `hard`
and the incumbent +2.505 — plausible interaction numbers, both artefacts.

## The deployment condition, three readable levels

Per-env paired `ss_error` (deg), candidate `p3b_final` against incumbent `inc13w`:

| metric | lvl | inc13w | p3b_final | delta | cand better | survD | pairDR |
|:--|:--|--:|--:|--:|--:|--:|--:|
| att | none | 9.360 | 0.963 | -8.397 | 64/64 | +0.0 | 0e+00 |
| att | soft | 10.728 | 1.425 | -9.303 | 64/64 | +0.0 | 0e+00 |
| att | medium | 14.776 | 2.184 | -12.592 | 64/64 | +1.6 | 0e+00 |
| att | hard | 19.356 | 8.453 | *not read* | *not read* | *not read* | **1e-01** |
| pitch | none | 7.903 | 0.632 | -7.271 | 64/64 | +0.0 | 0e+00 |
| pitch | soft | 8.843 | 0.883 | -7.959 | 64/64 | +0.0 | 0e+00 |
| pitch | medium | 10.129 | 1.537 | -8.591 | 63/64 | +1.6 | 0e+00 |
| pitch | hard | 11.407 | 4.508 | *not read* | *not read* | *not read* | **1e-01** |

## Additivity, at the one level that tests it

`predicted = pair34 + healthy_d2 - healthy`, per-env then averaged, `none` level:

| arm | pair34 | healthy_d2 | healthy | predicted | actual | excess |
|:--|--:|--:|--:|--:|--:|--:|
| inc13w | 1.423 | 1.111 | 0.406 | 2.128 | 9.360 | **+7.232** |
| p3b_final | 0.880 | 0.594 | 0.511 | 0.963 | 0.963 | **+0.000** |
| p3b_7500 | 1.009 | 0.478 | 0.426 | 1.062 | 1.080 | **+0.018** |

**The incumbent's combined error is 4.4x what its own single-axis results predict, and both
retrained checkpoints match theirs in the mean — so the interaction removal belongs to the
retrain itself, not to the final 2500 iterations that `finding/362` argues against keeping.**

Two caveats on how hard to push those numbers. The candidate's agreement is mean-level
cancellation rather than per-env additivity: the per-env excess for `p3b_final` has std 0.702
against a 0.963 deg mean error, ranging -2.201 to +2.990 with 53 % positive. The incumbent's
excess is robust by contrast — std 4.90, 63 of 64 envs positive. And "4.4x" depends on the
additive null: a multiplicative null (`pair34 x healthy_d2 / healthy` = 3.892) gives 2.41x for
the incumbent and 0.94x for the candidate — same verdict, half the ratio. The durable statement
is the excess in degrees (+7.232, 63/64 envs), not the ratio.

Nor is the checkpoint choice free here. Head to head at `none`, `model_9999` is better by
0.117 deg, which clears the floor; it loses at soft (+0.142), medium (+0.144) and hard (+1.697)
and sheds 1.6 pp of survival at `hard`, so the balance still favours `model_7500`. Removing that interaction is what
the retrain bought, and no table before this one could show it: measured apart the incumbent
looks merely worse (1.423 and 1.111 deg); measured together it sits at 9.360 deg of attitude
error, an order of magnitude off target, in the exact condition it is deployed into.

## What this changes

`finding/321` graded the retrain as a trade — fault robustness bought with fault-free
accuracy. That grade came from single-axis configs and it understates the case: on the
deployment condition the candidate is not trading, it is an order of magnitude better, and the
fault-free regression it pays for is under 0.2 deg at every level but `hard`.

It also means **the single-axis numbers do not bound the deployment case.** Any future exam
that scores fault and delay separately and reasons about their sum is measuring something the
robot does not experience.

Evidence: `g0c_runner/d2_read.py` (reuses `p4_score` loaders), `.hq/work/p4/{inc13w,p3b_final,p3b_7500}/pair34_d2`.
Scored 2026-09-05 by `g0c_runner/p4d_runner.sh` and `p4d2_runner.sh`, 8m25s per config.

## Comments
- (2026-09-05, claude) 정정: independent reviewer: the +0.000 match is mean-level cancellation not per-env additivity; 4.4x is additive-null-dependent; blanked every confounded column in the hard rows, not just delta
