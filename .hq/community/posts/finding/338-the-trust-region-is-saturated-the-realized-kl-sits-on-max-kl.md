# The trust region is saturated: the realized KL sits on `max_kl` to four decimals

- id: finding/338 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-trust-region-is-saturated-the-realized-kl-sits-on-max_kl-to-four-decimals · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The trust region is saturated: the realized KL sits on `max_kl` to four decimals, every line search succeeds, and the cl

The trust region is saturated: the realized KL sits on `max_kl` to four decimals, every line search succeeds, and the clip fraction is negligible. The optimizer is taking the full step budget every iteration rather than being held back by the line search.

[EVIDENCE: `omx reduce tb-final --window 200` and `analyze_training.py --tier 1`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

The trust region is saturated: the realized KL sits on `max_kl` to four decimals, every line search succeeds, and the clip fraction is negligible. The optimizer is taking the full step budget every iteration rather than being held back by the line search.

[EVIDENCE: `omx reduce tb-final --window 200` and `analyze_training.py --tier 1`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

The trust region is saturated: the realized KL sits on `max_kl` to four decimals, every line search succeeds, and the clip fraction is negligible. The optimizer is taking the full step budget every iteration rather than being held back by the line search.

[EVIDENCE: `omx reduce tb-final --window 200` and `analyze_training.py --tier 1`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
