# Yaw has no `ss_error` row because the exam is a roll/pitch attitude step; yaw is

- id: finding/325 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: yaw-has-no-ss_error-row-because-the-exam-is-a-roll-pitch-attitude-step-yaw-is · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Yaw has no `ss_error` row because the exam is a roll/pitch attitude step; yaw is regulated as a rate and a cumulative bu

Yaw has no `ss_error` row because the exam is a roll/pitch attitude step; yaw is regulated as a rate and a cumulative budget rather than tracked to a setpoint. Its evidence lives in the constraint section (`yaw_rate` margin 8.65, `cumul_yaw` margin 1.00) and in the reward decomposition (`Reward/yaw_vel` 1.33).

[EVIDENCE: `analyze_training.py --tier 3`; `eval.py static` emits `error_roll`/`error_pitch` only]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

Yaw has no `ss_error` row because the exam is a roll/pitch attitude step; yaw is regulated as a rate and a cumulative budget rather than tracked to a setpoint. Its evidence lives in the constraint section (`yaw_rate` margin 8.65, `cumul_yaw` margin 1.00) and in the reward decomposition (`Reward/yaw_vel` 1.33).

[EVIDENCE: `analyze_training.py --tier 3`; `eval.py static` emits `error_roll`/`error_pitch` only]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Yaw has no `ss_error` row because the exam is a roll/pitch attitude step; yaw is regulated as a rate and a cumulative budget rather than tracked to a setpoint. Its evidence lives in the constraint section (`yaw_rate` margin 8.65, `cumul_yaw` margin 1.00) and in the reward decomposition (`Reward/yaw_vel` 1.33).

[EVIDENCE: `analyze_training.py --tier 3`; `eval.py static` emits `error_roll`/`error_pitch` only]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
