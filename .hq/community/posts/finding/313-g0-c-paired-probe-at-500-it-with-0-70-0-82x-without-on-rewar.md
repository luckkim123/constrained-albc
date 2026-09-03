# G0-C paired probe at 500 it: WITH 0.70-0.82x WITHOUT on reward (FAIL on 5% threshold), but fault_severity 0.01 in both so the gap is delay (0,3) / thrust 13 N, not p0; Phase 3 left running

- id: finding/313 · date: 2026-09-04 · author: claude-fable
- project: constrained-albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: g0c, paired-probe, retrain-simtoreal, control_delay, thrust_coefficient, fault-dr, doraemon-mode
- summary: G0-C (seed 30, 500 it, commit 7cb7161): WITH reward 164.8 vs WITHOUT 202.1 at 500 (0.82x last, 0.77x last-50, 0.70x 400-499) = FAIL on the pre-registered 5% threshold. DORAEMON mode -3 and fault_severity 0.0100 in BOTH arms, so the fault config had not acted (effective p 0.003): the gap is the delay (0,3) and/or thrust 13 N/unit re-centering, not p0, and the p0-0.20 fallback is not the lever. No terminations, thruster_util margin larger in WITH. Phase 3 chained and left running per the night directive; next one-variable split if Phase 3 saturates >10% below the incumbent.

## Result

G0-C paired probe (PLAN §6 / §13 row 7), seed 30, 500 iterations, 4096 envs, commit 7cb7161, serial on the workstation RTX 4070:

| tag @ iteration 500 | WITH (§5 delta) | WITHOUT (incumbent cfg) | ratio |
|:--|--:|--:|--:|
| Train/mean_reward, last | 164.8 | 202.1 | 0.82 |
| Train/mean_reward, mean of last 50 | 149.7 | 195.7 | 0.77 |
| Train/mean_reward, mean 400–499 | 131.8 | 189.7 | 0.70 |
| Constraint/margin/thruster_util, last-50 | 10.6 | 5.8 | 1.82 |
| DORAEMON/mode (steps 0, 250) | −3, −3 | −3, −3 | — |
| DORAEMON/success_rate | 0.001 | 0.009 | — |
| DORAEMON/mean/fault_severity | 0.0100 | 0.0100 | 1.00 |
| Train/mean_episode_length | 1426 | 1424 | 1.00 |

Reward trajectory (WITH / WITHOUT): it 99 −110.9 / −25.8; 199 10.0 / 93.0; 299 56.8 / 150.9; 399 110.7 / 172.3; 499 164.8 / 202.1. WITH at 499 ≈ WITHOUT at ≈ 350: a 100–150-iteration lag, both still rising.

## Reading

1. **FAIL on the pre-registered threshold** (WITH within 5 % of WITHOUT): the gap is 18–30 % depending on the window.
2. **The fault config is not the cause.** `fault_severity` is 0.0100 in both arms at 500 (the curriculum has not started: mode −3 = success rate below α because reward is below `performance_lb` 250 — `doraemon.py:449`, inverted problem fails, distribution reverted). Effective per-thruster fail probability is 0.01 × 0.30 = 0.003 in WITH vs 0.001 in WITHOUT. So §10 item 2's fallback (p₀ 0.20) cannot move this number.
3. **The gap belongs to the two plant changes the user decided under rough mode**: `control_delay_steps (0,3)` and `thrust_coefficient` 13 N/unit with band (0.5, 2.0). Which of the two dominates is not separable from this pair (one-variable rule not met — the pair was pre-registered as "the two changes together").
4. **Feasibility signals are clean**: identical episode length (no terminations), thruster_util margin larger in WITH (13 N/unit uses less of the budget), value loss 1.64 vs 1.30, no divergence.
5. The plan's "`DORAEMON/mode` stays 0 in both" readout was unreachable at 500 iterations for either arm; a correct pre-registration would have been "same mode in both".

## Consequence

Phase 3 (`p3_ftc_s30`, 10 000 it) was chained after G0-C in the user's night directive and is left running (ETA ≈ 17:15 KST); the user decides in the morning whether to keep it. If Phase 3's saturated return stays > 10 % below the incumbent's (finding/071 saturation ≈ 7000–7750), the next probe is a one-variable split: delay (0,3) alone vs thrust 13 alone, 500 it each, same seed.
## Comments
