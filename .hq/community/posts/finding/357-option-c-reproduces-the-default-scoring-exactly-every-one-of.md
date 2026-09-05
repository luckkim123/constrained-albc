# Option C reproduces the default scoring **exactly**: every one of the 24 rows in

- id: finding/357 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: option-c-reproduces-the-default-scoring-exactly-every-one-of-the-24-rows-in · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Option C reproduces the default scoring **exactly**: every one of the 24 rows in the `p3b_finalC vs inc13w` tables match

Option C reproduces the default scoring **exactly**: every one of the 24 rows in the `p3b_finalC vs inc13w` tables matches the `p3b_final vs inc13w` tables digit for digit, and the underlying trajectory files are byte-identical.

[EVIDENCE: md5 of `data_hard.npz` — candidate `healthy` `00c782e493fb370f95ec4dc0387f3317` in both `.hq/work/p4/p3b_final/` and `.hq/work/p4c/p3b_finalC/`; candidate `pair34` `80065dc144126a68c328044e5d0f7f83` in both; reference `healthy` `72f4242f0f1937d9cc5effc0ae53fa36` in both]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Option C reproduces the default scoring **exactly**: every one of the 24 rows in the `p3b_finalC vs inc13w` tables matches the `p3b_final vs inc13w` tables digit for digit, and the underlying trajectory files are byte-identical.

[EVIDENCE: md5 of `data_hard.npz` — candidate `healthy` `00c782e493fb370f95ec4dc0387f3317` in both `.hq/work/p4/p3b_final/` and `.hq/work/p4c/p3b_finalC/`; candidate `pair34` `80065dc144126a68c328044e5d0f7f83` in both; reference `healthy` `72f4242f0f1937d9cc5effc0ae53fa36` in `.hq/work/p4/inc13w/healthy/` and `.hq/work/p4c/inc13w/healthy/`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge
