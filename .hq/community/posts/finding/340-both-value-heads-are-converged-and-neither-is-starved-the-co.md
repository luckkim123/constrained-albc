# Both value heads are converged and neither is starved: the cost critic tracks th

- id: finding/340 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: both-value-heads-are-converged-and-neither-is-starved-the-cost-critic-tracks-th · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Both value heads are converged and neither is starved: the cost critic tracks the reward critic within 25 %, which is wh

Both value heads are converged and neither is starved: the cost critic tracks the reward critic within 25 %, which is what a working constrained setup looks like.

[EVIDENCE: `omx reduce tb-final --window 200`; `analyze_training.py --tier 3` Losses]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

Both value heads are converged and neither is starved: the cost critic tracks the reward critic within 25 %, which is what a working constrained setup looks like.

[EVIDENCE: `omx reduce tb-final --window 200`; `analyze_training.py --tier 3` Losses]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Both value heads are converged and neither is starved: the cost critic tracks the reward critic within 25 %, which is what a working constrained setup looks like.

[EVIDENCE: `omx reduce tb-final --window 200`; `analyze_training.py --tier 3` Losses]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
