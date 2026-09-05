# Every section-5 setting lives in the launch override block and none of them is t

- id: finding/361 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: every-section-5-setting-lives-in-the-launch-override-block-and-none-of-them-is-t · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Every section-5 setting lives in the launch override block and none of them is the code default, so a retrain launched w

Every section-5 setting lives in the launch override block and none of them is the code default, so a retrain launched without that block silently reverts to the 40 N zero-delay plant with `performance_lb` 250 — which is the exact configuration `finding/315` measured stalling for a whole run.

[EVIDENCE: as-run `params/env.yaml` against the source defaults]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Every section-5 setting lives in the launch override block and none of them is the code default, so a retrain launched without that block silently reverts to the 40 N zero-delay plant with `performance_lb` 250 — which is the exact configuration `finding/315` measured stalling for a whole run. There are **seven** such settings, not the four `finding/352` originally listed: the fault block is three more.

[EVIDENCE: `g0c_runner/p3b_resume.sh` COMMON+DELTA against the source defaults]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge
