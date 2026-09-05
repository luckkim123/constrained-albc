# `pairDR` is exactly 0 on all 16 CORE rows for `p3b_final` vs `inc13w`, so all fo

- id: finding/327 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: pairdr-is-exactly-0-on-all-16-core-rows-for-p3b_final-vs-inc13w-so-all-fo · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: `pairDR` is exactly 0 on all 16 CORE rows for `p3b_final` vs `inc13w`, so all four levels compare two policies on one di

`pairDR` is exactly 0 on all 16 CORE rows for `p3b_final` vs `inc13w`, so all four levels compare two policies on one distribution. This is not a fix: `eval.py static` still loads each scored checkpoint's own DORAEMON distribution as the hard anchor (`eval.py:1382-1404`, `debugging/319`), but at saturation both policies' `mean ± 2σ` exceeds the static box on every dim, so both clip to the *same* bounds.

[EVIDENCE: per-config eval logs under `.hq/work/p4/{p3b_final,inc13w}/`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

`pairDR` is exactly 0 on all 16 CORE rows for `p3b_final` vs `inc13w`, so all four levels compare two policies on one distribution. This is not a fix: `eval.py static` still loads each scored checkpoint's own DORAEMON distribution as the hard anchor (`eval.py:1382-1404`, `debugging/319`), but at saturation both policies' `mean ± 2σ` exceeds the static box on every dim, so both clip to the *same* bounds.

[EVIDENCE: per-config eval logs under `.hq/work/p4/{p3b_final,inc13w}/`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

`pairDR` is exactly 0 on all 16 CORE rows for `p3b_final` vs `inc13w`, so all four levels compare two policies on one distribution. This is not a fix: `eval.py static` still loads each scored checkpoint's own DORAEMON distribution as the hard anchor (`eval.py:1382-1404`, `debugging/319`), but at saturation both policies' `mean ± 2σ` exceeds the static box on every dim, so both clip to the *same* bounds.

[EVIDENCE: per-config eval logs under `.hq/work/p4/{p3b_final,inc13w}/`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
