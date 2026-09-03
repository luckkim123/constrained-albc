# G0-A/B/E on the deployed teacher: no arm-pitch fallback with m3/m4 dead (retention 0.26/0.25), one control step of delay costs 4-5x attitude error and two steps 12-16x; all constraint margins positive at 9998

- id: finding/314 · date: 2026-09-04 · author: claude-fable
- project: constrained-albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: resolved
- verified: none · keywords: g0a, g0b, g0e, incumbent, fault-fallback, control-delay, delay-sensitivity, retrain-simtoreal, eval-static
- summary: Incumbent model_9998, eval static 64 envs seed 42, 15 deg attitude step, per-env paired ss_error. G0-A: with m3/m4 dead pitch retention 0.26 (none) / 0.25 (hard) <= 0.5 -> no graceful fallback, D-1 confirmed. G0-B: control delay 1 step -> attitude error 3.8x (none) / 5.0x (hard); 2 steps -> 15.8x / 12.2x (4.6 deg ss on a 15 deg step) -> delay DR worth its cost; the robot has 7.6 steps of lag. G0-E: 10 constraint margins all positive 0.98-9.54. Re-reads G0-C: the WITH lag is the price of training inside the delay regime, not the fault config.

## Result (incumbent `trpo_iterbudget_s30_260805_012813/model_9998.pt`, `eval.py static`, 64 envs, seed 42, attitude STEP 15°, DORAEMON DR from the run's own dir; per-env paired steady-state error, last half of each 5 s segment, decision floor 0.10°)

**G0-A — arm-pitch fallback when firmware m3 and m4 are dead (`--fault_fixed_health 1,1,1,0,0,1` vs `1,1,1,1,1,1`), pitch |error|:**

| DR | healthy ss_error | fault ss_error | error ratio fault/healthy | retention healthy/fault |
|:--|--:|--:|--:|--:|
| none | 0.164° (median 0.166) | 0.840° (0.579) | 5.4× (3.8) | 0.26 (0.26) |
| hard | 0.214° (0.200) | 4.827° (1.198) | 25× (5.0) | 0.25 (0.20) |

Retention ≤ 0.5 at both levels → **no graceful fallback**: with the vertical pair dead the incumbent does not move pitch to the arm. `vault:finding/137`'s D-1 ("pitch is the arm's job on the real robot, and the policy never learned that") is confirmed in sim on the deployed checkpoint. n = 64/64, DR draws exactly paired (max diff 0.0).

**G0-B — control-delay sensitivity, healthy thrusters, attitude error sqrt(roll² + pitch²):**

| delay | DR | d=0 ss_error | delayed ss_error | error ratio | retention |
|:--|:--|--:|--:|--:|--:|
| 1 step (20 ms) | none | 0.291° | 1.095° | 3.8× (median 3.6) | 0.30 |
| 1 step (20 ms) | hard | 0.379° | 1.893° | 5.0× (4.4) | 0.29 |
| 2 steps (40 ms) | none | 0.291° | 4.602° | 15.8× (15.4) | 0.07 |
| 2 steps (40 ms) | hard | 0.379° | 4.634° | 12.2× (11.0) | 0.11 |

The pre-registered G0-B readout ("≥ 2× at d = 1, hard → delay DR is worth its cost") is met by a wide margin. One control step of transport delay costs the incumbent 4–5× in attitude error; two steps put the steady-state error at ≈ 30 % of the 15° step amplitude. **The real robot's measured command→joint lag is 152 ms = 7.6 steps (`vault:finding/148`)** — the incumbent was never inside its own delay envelope on hardware. Caveat: at `hard` the G0-B runs are quasi-paired (same DR marginals, different per-env draws — `--control-delay` shifts the DORAEMON RNG stream; `none` is exactly paired); the `none` rows alone carry the conclusion.

**G0-E — incumbent's 10 `Constraint/margin/*` at step 9998: all positive, range 0.98–9.54**; no constraint at its boundary at convergence (observational).

## What this changes

1. §9 wording: the retrain is justified on data, not on the tank narrative alone — the deployed teacher has neither a pitch fallback for the m3/m4 loss nor any delay tolerance.
2. It re-reads G0-C (`finding/313`): the WITH arm trains against delays of 0–3 steps, i.e. exactly the regime in which the incumbent-config policy is 4–16× worse. A 100–150-iteration lag at 500 iterations is the price of that regime, not a defect of the fault config.
3. The delay knob is the largest single sim-to-real lever found so far on this robot — larger than losing two of six thrusters. Item 5's (0,3) stays; if Phase 3 saturates far below the incumbent, the one-variable split (delay alone vs thrust alone) is the next probe.

Report with commands, formulas and raw outputs: `.hq/work/g0abe/report.md` (agent `g0abe-evals-2`, sonnet executor, GPU1).
## Comments
