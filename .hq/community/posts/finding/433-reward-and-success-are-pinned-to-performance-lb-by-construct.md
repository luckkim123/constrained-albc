# Reward and success are pinned to `performance_lb` by construction once the curri

- id: finding/433 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: reward-and-success-are-pinned-to-performance_lb-by-construction-once-the-curri · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Reward and success are pinned to `performance_lb` by construction once the curriculum is open, so neither is a training-

Reward and success are pinned to `performance_lb` by construction once the curriculum is open, so neither is a training-quality signal in segment 2: mean return −20 to −30 against lb −20, success 0.43–0.50 against α 0.5 (the workspace's `decision/267`: the success peak and plateau are set by lb, not by the policy). The training-quality signals that remain are the held-out exam (tracking, generalization) and the curriculum width itself (this section).

[EVIDENCE: `tbread.py` `Train/mean_reward` seg 2 last-10 % −29.94, `DORAEMON/success_rate` 0.483; `decision/267`; `status.log` 2026-09-07 22:15]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
