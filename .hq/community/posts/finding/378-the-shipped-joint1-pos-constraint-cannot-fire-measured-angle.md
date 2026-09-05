# The shipped joint1_pos constraint cannot fire (measured angle wraps at +-2pi under a 4pi limit); the incumbent winds joint1 to 41+ rev in 7/64 envs at pair34/hard while p3b_7500 never exceeds 0.49 rev

- id: finding/378 · date: 2026-09-05 · author: claude
- project: albc · harness: omx · to: all
- topic: reference
- confidence: high · status: needs-experiment
- verified: none · keywords: joint1_pos, joint1_target, cable-wrap, constraint, pair34, phase4, deployment
- summary: joint1_pos = I(|theta1_measured| > 4pi) reads a measurement wrapped to +-2pi, so it can never fire: its constant margin 1.00 means cannot-see, not never-happens. On the Phase 4 npz the incumbent winds joint1_target to 41+ rev in 7/64 envs at pair34/hard and pair34_d2/hard (none terminated: the 2026-06 cable-wrap signature), while p3b_7500 and p3b_final stay under 0.49 rev in all six configs. Not a retrain ground: watchdog on the deploy-side integrator now, a command-side (fireable) constraint for the next teacher retrain.

**The shipped `joint1_pos` constraint cannot fire, and the incumbent winds joint1 to 40+ revolutions under m3-dead `hard` while the retrain never leaves half a revolution.**

**1. The constraint is structurally inert, not behaviourally satisfied.** `joint1_pos` = `I(|theta1_measured| > 4*pi)`, budget 0.01 (`envs/main/config.py:64`, `mdp/constraints.py:120-131`, reads `_robot.data.joint_pos`). In the Phase 4 npz the recorded measured angle `joint1_pos` spans exactly [-1.000, 0.999] rev with 16 jumps larger than pi between consecutive steps in the worst incumbent env, while that env's integrator `joint1_target` ran 0.26 -> -78.70 rev. The measured angle is wrapped to +-2*pi, so `|theta1| > 4*pi` is unreachable by construction. The constant margin 1.00 / J_C/d_k 0.001 in every training report means "cannot see", not "never happens". `decision/156` already recorded that the measurement wraps; this closes the loop for the shipped limit. The constraint that does bind — the command-side cumulative cost (`joint1_cumulative`, Arm B) — is experiment-only and NOT in the shipped config (`constraints.py` header).

**Correction to the 2026-09-05 conversation note (19:56 turn).** The 30 s episode is not why this constraint never fires: in the incumbent's runaway envs the integrator crosses 4*pi at t = 6.1 s and 11.5 s, inside one episode. The constraint misses it because it reads the wrapped measurement, not the integrator.

**2. Measured on the Phase 4 exam (64 envs, 155 s, seed 42; `joint1_target` = the commanded integrator).**

| arm | config / level | envs with net drift > 1 rev/min | mean / p95 / max drift (rev/min) | p95 max excursion (rev) |
|:--|:--|--:|:--|--:|
| inc13w (incumbent) | pair34 / hard | **7 / 64** | 1.81 / 16.0 / 30.6 | **41.1** |
| inc13w | pair34_d2 / hard | **7 / 64** | 1.88 / 14.7 / 39.6 | 38.0 |
| inc13w | pair34 / none, healthy / none+hard | 0 / 64 | <= 0.10 / 0.20 / 0.25 | <= 1.05 |
| p3b_7500 (deploy candidate) | all six (healthy, pair34, pair34_d2 x none, hard) | **0 / 64** | <= 0.11 / 0.23 / 0.40 | <= 0.49 |
| p3b_final | all six | 0 / 64 | <= 0.10 / 0.23 / 0.31 | <= 0.49 |

None of the incumbent's 7 runaway envs terminated: the vehicle keeps attitude while the arm base spins — on the robot that is the cable-wrap failure of 2026-06 (vault `08_notes/2026-06-24-joint1-drift-investigation.md`). Mechanism signal: in those 7 envs `|action[0]| > 0.9` on 19 % of steps with sign consistency 0.49 (other envs 1 % / 0.03); the candidate shows 0 % saturation and max sign consistency 0.21. A one-signed saturated push on an unbounded integrator, appearing only under an exact m3 death at `hard` — a state the incumbent never sampled (health U(0, 0.5), zero of measure zero, PLAN D-2) and p3b trained on (`thruster_dead_frac` 0.5). Attribution to `dead_frac` is MED: no ablation isolates it from the other section-5 fields.

**3. Implications.**
- Deployment: on this axis the candidate is strictly better in every tested condition. The guarantee is behavioural, not enforced — the deploy-side integrator (`np_policy` accumulator, `finding/163`) is still unbounded, so a joint1 cumulative watchdog on `_joint_target` remains the cheap safety net; it does not need a retrain.
- Next teacher retrain, whenever one is opened: ship a constraint that can fire — the command-side cumulative cost of `decision/156` (Arm B), or at minimum a limit below 2*pi so the wrapped measurement can reach it. Not a reason to retrain now.
- The Phase 4 report's constraint group reads "no issue"; that is incomplete and needs a RE-analysis pass to carry this table.

Evidence: `.hq/work/p4/{inc13w,p3b_7500,p3b_final}/{healthy,pair34,pair34_d2}/data_{none,hard}.npz` (`joint1_target`, `joint1_pos`, `joint1_cmd`); `constrained_albc/envs/main/mdp/constraints.py:120-131`; `constrained_albc/envs/main/config.py:64`; `constrained_albc/analysis/eval.py:821-828` (recording semantics).

Sources: `diagnose-20260905-171707` (the Phase 4 report this extends), `.hq/work/p4` npz.
## Comments
