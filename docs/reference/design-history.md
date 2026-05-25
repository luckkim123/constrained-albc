# Design History

Timeline of design/plan documents (2026-02 ~ 03) that shaped the current
`constrained_full_albc` env. Raw plan files were compressed into this lookup table.

**Lineage at a glance:** the two `2026-03-31` docs are the direct ancestors of the
current main task; `2026-03-24` (sigma decoupling) and `2026-03-27` (encoder-in-TRPO)
contributed surviving algorithm features; everything targeting `hero_agent` /
`constrained_albc` (the `2026-02-04` and both `2026-03-17` hero_agent plans, plus the
Lagrangian baseline) is superseded.

| Date | Plan | Proposed | Maps to current |
|---|---|---|---|
| 2026-02-04 | ALBC task integration | Inline `ALBCAttitudeTask` into `HeroAgentEnv`, delete `tasks/` dir | **superseded** — hero_agent deprecated; attitude-task paradigm removed when task switched to velocity tracking |
| 2026-03-17 | History-augmented encoder | Shared proprio-history TCN (`HistoryTCN`, 30×8D→32D) feeding encoder/actor/critic + Phase-2 `adapt_head` | **superseded** — current design uses flat history obs (ring buffer concatenated), no `HistoryTCN`/`adapt_head` |
| 2026-03-17 | Lagrangian baseline (3-constraint) | Controlled Lagrangian-dual baseline (fixed entropy) to compare against IPO | **not executed into product** — current algorithm is ConstraintTRPO + IPO log-barrier |
| 2026-03-17 | Analysis toolkit restructure | Consolidate analysis scripts under one dir with `common.py` SSOT bridge | **partially** → `constrained_albc/analysis/` (eval_dr, encoder_tools sweep, analyze); hero_agent-import SSOT specifics stale |
| 2026-03-24 | Sigma-KL decoupling + yaw quad-damp removal | Move `log_std` out of TRPO natural-gradient group into dedicated Adam; drop `yaw_quad_damp` from privileged obs | → **ConstraintTRPO sigma in separate Adam** (current core feature); dim change superseded by 03-31 redesigns |
| 2026-03-27 | Encoder-TRPO integration | Fold encoder params into TRPO trust region (CG + line search jointly optimize actor+encoder) | → **ConstraintTRPO** (encoder in policy params, asymmetric critic) |
| 2026-03-31 | Constraint & termination redesign | Velocity-tracking constraints (5 prob + 4 avg), continuous joints, cumulative-yaw, 81D obs redesign, 15-param DORAEMON, 24D privileged, mid-episode payload + OU current | → **`constrained_full_albc` env** (status: Implemented); current 10-constraint set is its direct descendant |
| 2026-03-31 | Full 6-DOF tracking design | Fork from `constrained_albc`; 8D action (2D arm + 6D thruster), velocity-command tracking, ConstraintTRPO + decoupled-sigma Adam + asymmetric critic | → **`Isaac-FullDOF-TRPO-v0`** (origin design doc for current main, refined by the same-day constraint redesign) |

## Detail notes

- **2026-03-31 constraint redesign** grew the constraint count to the current **10
  (5 prob + 5 avg)** and produced essentially the current env. Obs evolved 28→81→**87D**
  across this and later integral-obs work (see [experiments-archive](experiments-archive.md)).
- **Full 6-DOF design** originally specified 28D obs / 23D privileged / 210D history;
  refined by the constraint redesign to flat 55D history and, through the experiment
  campaign, to **87D obs / 24D privileged** (verified against current code).
- The **HORA/RMA 2-phase pipeline** that the history-encoder plan assumed is deprecated;
  its design doc was deleted in this consolidation (not migrated).
