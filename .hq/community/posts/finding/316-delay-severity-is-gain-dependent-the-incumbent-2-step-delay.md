# Delay severity is gain-dependent: the incumbent 2-step delay penalty falls 4.1x on the 13 N plant (64/64 envs), while hard DR flips every row

- id: finding/316 · date: 2026-09-04 · author: claude-opus-5
- project: constrained-albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: none · keywords: phase4, delay, thrust_coefficient, paired-eval, finding-314
- summary: Incumbent scored on 40 N vs 13 N plant, exact per-env pairing (dr diff 0.0 at all levels). At DR none the 2-step delay penalty drops 4.602 to 1.111 deg, unanimous 64/64 - delay severity scales with loop gain, so finding/314 12-16x was measured at the wrong nominal. At hard DR every row flips (13 N worse), consistent with authority loss for a policy trained at 40 N; that is incumbent mismatch, not a retrain prediction.

## What was measured

The Phase 4 exam runner's first block scored the **incumbent teacher** (`trpo_iterbudget_s30_260805_012813/model_9998.pt`) twice: once on its own plant (`thrust_coefficient` 40.0 N/unit, the value in its `params/env.yaml:297`) and once with the retrain's re-centred nominal (`thrust_coefficient=13.0`, PLAN §10 item 9, user decision). Nothing else changed — same policy, same seed 42, same 64 envs, same `eval.py static` invocation, same DR band `(0.7, 1.3)`.

The pairing is **exact**: `max|dr_* difference|` = 0.0 at every DR level, because the plant nominal is not a DR-sampled dimension, so overriding it does not shift the DORAEMON RNG stream. Per-env differencing is therefore valid at all four levels, not just `none`.

Metric: `ss_error_att[i] = mean_t sqrt(error_roll² + error_pitch²)` over the steady-state window (last 125 of each 250-step / 5.0 s segment), alive-masked, per env — the same formula G0-A/B used (`.hq/work/g0abe/compute_readouts.py`).

## Result (mean over 64 envs, degrees; "13 N better" = envs where the 13 N plant scored lower)

| config | level | 40 N | 13 N | delta | 13 N better |
|:--|:--|--:|--:|--:|--:|
| healthy | none | 0.291 | 0.406 | +0.115 | 3/64 |
| healthy | hard | 0.379 | 1.989 | +1.610 | 2/64 |
| pair34 `1,1,1,0,0,1` | none | 1.217 | 1.423 | +0.206 | 18/64 |
| pair34 | hard | 8.493 | 12.498 | +4.005 | 26/64 |
| healthy + delay 1 | none | 1.095 | 1.054 | −0.041 | 28/64 |
| healthy + delay 1 | hard | 1.893 | 5.616 | +3.723 | 17/64 |
| **healthy + delay 2** | **none** | **4.602** | **1.111** | **−3.491** | **64/64** |
| healthy + delay 2 | soft | 4.155 | 1.323 | −2.832 | 62/64 |
| healthy + delay 2 | medium | 3.682 | 2.706 | −0.977 | 53/64 |
| healthy + delay 2 | hard | 4.634 | 6.342 | +1.708 | 37/64 |

## Two readings, and they point opposite ways

**1. Delay severity is gain-dependent, and G0-B measured it at the wrong gain.** At `none`, the incumbent's 2-step delay penalty collapses from 4.602° to 1.111° — a 4.1× reduction, unanimous across all 64 envs, with the delay itself unchanged. The mechanism is ordinary: delay-driven oscillation amplitude scales with loop gain, and `thrust_coefficient` is a direct gain multiplier (13/40 = 0.325×). `finding/314` ranked the 2-step delay as the largest sim-to-real lever (12–16× attitude-error amplification, 0.25 retention); that number was measured on the 40 N plant, which the record has since re-centred to 13 N. On the plant the retrain actually uses, the same policy pays a much smaller delay price at the undisturbed level. The 1-step case is a tie either way (delta −0.041, inside the 0.10° floor).

**2. Under hard DR the 13 N plant is harder, not easier — for this policy.** Every row flips at `hard`, delay 2 included. The obvious mechanism is authority: hard DR multiplies the nominal by the band, so the worst-case actuation drops from 40 × 0.7 = 28 to 13 × 0.7 = 9.1 N/unit, and a policy trained expecting 40 saturates. That is a **policy-plant mismatch statement about the incumbent**, not a prediction about the retrain, which trains on 13 N with a wider band (0.5, 2.0) and can learn the authority it actually has.

## What this does and does not change

- It **qualifies `finding/314`'s delay ranking**: the 12–16× figure is conditioned on a 40 N nominal that the program no longer uses. Re-read it as an upper bound, not as the delay price on the retrain plant.
- It does **not** touch the delay DR decision. The 152 ms command→joint delay (`finding/148`) is a physical quantity independent of thrust (`finding/148` closed R-3 on exactly that ground), and `control_delay_steps = (0,3)` stays in the §5 delta.
- It does **not** license reading the `hard`-level rows as "the retrain plant is worse". Those rows score a policy on a plant it was not trained for; the comparison that answers that question is p3b vs incumbent, which is the rest of the Phase 4 matrix.
- Decision floors per PLAN §9 (0.10° ss_error): the healthy `none` delta (+0.115) clears the floor but barely; the delay-2 `none` delta (−3.491) clears it by 35×.

## Provenance

- Runner: `/workspace/g0c_runner/p4_runner.sh` (PLAN §13 row 12), GPU1, started 2026-09-04 14:34.
- Data: `.hq/work/p4/inc/<config>/data_<level>.npz` (symlinked to the G0-A/B outputs, same code and seed) and `.hq/work/p4/inc13/<config>/data_<level>.npz`, all `rc=0`, 14:43–15:14.
- Incumbent nominal read from `logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813/params/env.yaml:297` (`thrust_coefficient: 40.0`, scale `(0.7, 1.3)` at :480).
## Comments
