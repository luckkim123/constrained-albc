# Phase 3 p3_ftc_s30 stalled: DORAEMON mode -2 for the whole run, fault_severity 0.0045 and every DR dim at its initial width -- performance_lb 250 was tuned for the 40 N zero-delay plant, the delta plateaus at ~237

- id: finding/315 · date: 2026-09-04 · author: claude-fable
- project: constrained-albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: phase3, doraemon-stall, performance_lb, mode-2, fault_severity, retrain-simtoreal, finding-023, decision-063
- summary: Phase 3 read at it 8010/10000: reward plateau 233-243 (incumbent 252.7), success 0.30-0.41 < alpha 0.5, DORAEMON mode -2 at 32/33 updates, fault_severity 0.010->0.0045 (incumbent 0.50), obs_noise/current 0.01, all 21 DR dims at initial width. Effective fail prob 0.0014: this teacher saw no faults and no DR. Cause = performance_lb 250 tuned for the 40 N zero-delay plant; the delta (thrust 13 N/unit, delay (0,3), both non-DORAEMON channels) lowers the achievable return so the alpha gate never releases (finding/023 signature, decision/063 joint re-tuning). DECISION-REQUIRED: re-tune performance_lb (~200) and relaunch as p3b; current checkpoint kept as the no-DR reference for Phase 4.

## Observation (Phase 3 `trpo_p3_ftc_s30_260904_0506xx`, read at iteration 8010 of 10 000, 13:2x KST)

| quantity | Phase 3 (retrain delta) | incumbent `iterbudget_s30` at 9998 |
|:--|--:|--:|
| Train/mean_reward (plateau since ≈ it 1600) | 233–243, last 236.5 | 252.7 (last-200 mean) |
| DORAEMON/success_rate | 0.30–0.41 (last 0.36) | 0.65 |
| DORAEMON/mode | **−2 at 32 of 33 updates** (one +1 at 4500) | 0 |
| DORAEMON/mean/fault_severity | 0.010 → **0.0045** | 0.50 (Beta(1,1)) |
| DORAEMON/std/fault_severity | 0.0099 → 0.0045 | 0.2887 |
| obs_noise_scale / ocean_current mean | 0.013 / 0.007 | 0.50 / 0.50 |
| added_mass_scale std | 0.090 → 0.046 | 0.289 |
| every other DR dim (21 total) | mean at nominal, std at or below its initial width | saturated to the full box |
| thruster_util margin | 13–15 | — |
| episode length | 1418–1429 (no terminations) | — |

**The curriculum never opened.** Mode −2 = success rate below α = 0.5 with the inverted problem's max-success point still infeasible (`doraemon.py:441-445`), so DORAEMON kept the initial narrow distribution for the whole run; fault severity actually shrank. Effective per-thruster fail probability at the end: 0.0045 × 0.30 = **0.0014** — this teacher has seen essentially no faults, no observation noise, no current, and a DR box a fraction of the incumbent's width. It is the opposite of the program's deliverable.

## Cause

`performance_lb` 250 was tuned for the 40 N/unit, zero-delay plant (incumbent plateau 252.7, success 0.65). The §5 delta moved the achievable return down to ≈ 237 (thrust 13 N/unit + band (0.5,2.0) and control delay (0,3) — both NON-DORAEMON channels: a fixed nominal and a uniform band), so fewer than half the envs ever clear 250 and the α gate never releases. This is the `finding/023` signature ("an off-DORAEMON channel that costs return stalls the curriculum below the alpha floor, mode −2 entire run") reproduced with two plant changes instead of one. G0-C's 500-iteration readout (`finding/313`) was the early face of the same thing — the WITH arm was already tracking toward a lower ceiling, and `decision/063`'s warning ("changing the box needs joint re-tuning" of the DORAEMON knobs) applies to re-centering the plant as much as to widening the box.

## What this is not

Not an optimizer failure (one +1 update happened; reward is stable; no terminations), not the fault config (severity never rose above 0.011 — p₀ 0.30 was never exercised), not a code defect in the G0-I sampler (bit-identical at d = 0, tested; here the fault path was simply inactive).

## Options (DECISION-REQUIRED: the PLAN forbids a silent `performance_lb` edit)

1. **Re-tune `performance_lb` to the new plant's return scale** — e.g. 200 (plateau 237 → success > 0.5 early, the gate releases; the incumbent's ratio lb/plateau = 0.99 is not reproducible without knowing the new plateau under a widened box, so 200 is a floor guess, checked by watching `DORAEMON/mode` turn 0/1 and `fault_severity` rise within the first 1 000 iterations, ≈ 75 min). Relaunch as `p3b`, same delta otherwise.
2. `hard_performance_constraint false` — lets the entropy step run below α; changes the DORAEMON contract (not tried on this plant).
3. Revert one plant change — delay to (0,1) or thrust back to 40 — but `finding/314` shows delay is the largest sim-to-real lever and 13 N/unit came from the tank measurement, so this trades the program's purpose for the old gate.

Recommended: 1, launched after (or instead of) the remaining 2 h of Phase 3; the current checkpoint is still worth a Phase 4 eval as the "no-DR, no-fault, delay+thrust" reference point.
## Comments
