# No constraint is violated at the end of either segment and none was violated at 

- id: finding/429 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: no-constraint-is-violated-at-the-end-of-either-segment-and-none-was-violated-at · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: No constraint is violated at the end of either segment and none was violated at any point of the resumed segment: all te

No constraint is violated at the end of either segment and none was violated at any point of the resumed segment: all ten logged `Constraint/viol/*` maxima over segment 2 are negative (the closest to zero is `arm_joint_vel` at −0.39), and `Constraint/barrier_penalty` sits at −0.166 with zero spikes above 0.01. Segment 1's warm-up did cross four constraints (`Constraint/viol/arm_joint_vel` max 9.81, `Constraint/viol/thruster_util` 8.76, `Constraint/viol/yaw_rate` 2.11, `Constraint/viol/joint1_pos` 0.30) and had recovered all of them by its last tenth. The margins that widened under the curriculum are the thruster and settling ones (`Constraint/margin/thruster_util` 18.8 → 20.1); the ones that narrowed are the rate limits (`Constraint/margin/rp_rate` 9.0 → 8.7, `Constraint/margin/yaw_rate` 6.4 → 5.8) — the policy is moving faster on a wider plant, still inside the box. The profile's `cumul_yaw` constraint (`Constraint/margin/cumul_yaw`, `Constraint/viol/cumul_yaw`) is not logged by this run (only `Episode/cumul_yaw_deg` exists in the TB tag set), so it is absent rather than zero.

[EVIDENCE: `tbread.py` constraint block (raw TB `Constraint/margin/*`, `Constraint/viol/*` tags, 10 of each; tag set enumerated with `EventAccumulator.Tags()`); `analyze_training.py` `[TIER 2] Constraints` (`barrier_penalty last=-0.1662 spikes(>0.01)=0 max=-0.150`)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
