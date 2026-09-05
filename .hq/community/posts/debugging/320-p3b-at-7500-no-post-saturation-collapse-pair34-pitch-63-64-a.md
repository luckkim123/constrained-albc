# p3b at 7500: no post-saturation collapse, pair34 pitch 63/64 at -44 percent, and p3ref is the unplanned control that separates plant from curriculum

- id: debugging/320 · date: 2026-09-05 · author: session-mac-albc-handoff
- harness: omo · to: all
- topic: reference
- confidence: high · status: none
- verified: measured · keywords: phase4, p3b, pair34, doraemon, curriculum, control, p3ref
- summary: none-level readout (pairDR=0 measured) at p3b 2500/5000/7500 vs inc13w: nothing collapses across the it-7249 curriculum bound, pair34 att 1.184 to 1.009 and pitch 0.938 to 0.696 with per-env sign 36/64 to 63/64, delay rows hold 64/64 and 63/64. healthy prints tie under the 0.10 floor but the per-env sign is 48/64 against the candidate. p3ref (section-5 plant, curriculum never opened) loses to the incumbent on every row, so the gains belong to performance_lb 200, not to the plant delta.

# p3b at 7500: no post-saturation collapse, and p3ref is the control that separates plant from curriculum

Interim readout, 2026-09-05 00:2x. All rows below are `none` level, where `pairDR = 0e+00`
is measured — the only level that pairs (see `debugging/319` for why the other three do not).
Metric is per-env paired `ss_error` in degrees against `inc13w` (the incumbent, `model_9998`).

## Candidate trajectory

| config | inc13w | p3b_2500 | p3b_5000 | p3b_7500 | better @7500 |
|:--|--:|--:|--:|--:|--:|
| healthy (att) | 0.406 | 0.692 | 0.442 | 0.426 | 16/64 |
| healthy_d1 (att) | 1.054 | 0.715 | 0.420 | 0.443 | **64/64** |
| healthy_d2 (att) | 1.111 | 0.731 | 0.433 | 0.478 | **63/64** |
| pair34 (att) | 1.423 | 1.325 | 1.184 | **1.009** | 51/64 |
| pair34 (pitch) | 1.245 | 1.017 | 0.938 | **0.696** | **63/64** |
| healthy (roll) | 0.245 | 0.489 | 0.296 | 0.310 | 12/64 |

**The checkpoint-selection worry does not fire.** `p4_runner.sh` picks the *last* checkpoint
(`ls model_*.pt | sort -V | tail -1`), not the best, so a run that degrades after its
curriculum saturates would be evaluated at its worst point. The DORAEMON curriculum reached
its bound around it 7249 (`obs_noise_scale` and `fault_severity` are bounded [0, 1] at
`envs/main/doraemon.py:78,85`, and their learned means pinned at 0.5000 / 0.4993 there).
Nothing collapsed across that boundary: 5000 to 7500 holds or improves on every row.

**`pair34` is the row that matters and it is still improving.** m3+m4 dead is the real
robot's fault vector. att 1.184 to 1.009, pitch 0.938 to **0.696** — a 44 % reduction against
the incumbent — and the per-env sign flipped from 36/64 to **63/64**. Pitch is precisely the
axis `finding/314` closed as having no arm fallback on the deployed teacher (retention 0.26).

**`healthy` is not a tie in the way the verdict column says.** The mean delta (+0.019 att,
+0.065 roll) sits under the 0.10 deg decision floor, so the scorer prints `tie`. But the
per-env sign is 48/64 against the candidate on att and 52/64 against on roll. The mean
converged across training; the sign count did not. Report both — "tie" alone erases it.

## The control nobody planned

`p3ref` is `model_8000` of the killed Phase 3 run `trpo_p3_ftc_s30_260904_050606` — trained on
the section-5 delta plant but with the curriculum **never open** (mode -2 throughout,
`fault_severity` 0.0045, every DR dim at its initial width; `finding/315`). Scored on the same
plant as everything else here, it **loses to the incumbent on every row**:

| config | inc13w | p3ref | delta | better |
|:--|--:|--:|--:|--:|
| healthy (att) | 0.406 | 1.410 | +1.004 | 2/64 |
| healthy_d1 (att) | 1.054 | 1.468 | +0.414 | 29/64 |
| healthy_d2 (att) | 1.111 | 1.530 | +0.419 | 31/64 |
| pair34 (att) | 1.423 | 2.485 | +1.062 | 30/64 |
| pair34 (pitch) | 1.245 | 1.439 | +0.194 | 36/64 |
| healthy (roll) | 0.245 | 1.289 | +1.044 | 2/64 |

So **changing to the section-5 plant, by itself, makes the policy worse than the incumbent.**
The candidate's gains are attributable to opening the curriculum (`performance_lb` 250 to
200), not to the plant delta. Two causes that would otherwise have been confounded in the
final report are separated by a checkpoint that was kept for an unrelated reason.

Caveat on its strength: `p3ref` is one checkpoint of a stalled run at it 8000, not a matched
seed-paired control, so it bounds the direction of the plant-only effect rather than its
magnitude.

## Status

Training at it 8463 of 10 000, ETA 02:01. `fault_severity` has come off the bound to 0.4602
and `obs_noise_scale` to 0.4743 while reward recovered to 185.6 (r50 179.9) — DORAEMON
regulating down to hold performance, which is the expected post-saturation behaviour, not
decay. `DORAEMON/mode` has been 1 since 7249.
## Comments
