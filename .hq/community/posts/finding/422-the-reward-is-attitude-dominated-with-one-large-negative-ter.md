# The reward is attitude-dominated with one large negative term — yaw — and every 

- id: finding/422 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-reward-is-attitude-dominated-with-one-large-negative-term-yaw-and-every · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The reward is attitude-dominated with one large negative term — yaw — and every other shaping term an order of magnitude

The reward is attitude-dominated with one large negative term — yaw — and every other shaping term an order of magnitude smaller; no term runs away across either segment. `Reward/yaw` (the profile's `Reward/yaw_vel` slot; the term became a yaw-position term with the `yaw-position` merge) is −2.15 → −2.31 and is the reason `Reward/total` is negative at the end (−1.00) even though `Reward/att_rp` is +2.33.

[EVIDENCE: `tbread.py` first/last-10 % windows on both segments; `analyze_training.py --tier 3` `[TIER 3] Rewards` block (segment 2: att_rp 2.26, bias −0.95, smoothness −0.04, thruster −0.02, torque −0.08, yaw −2.44, total −1.26)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
