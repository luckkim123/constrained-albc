# The eval-time anchor saturated *before* the curriculum itself converged, and the

- id: finding/328 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-eval-time-anchor-saturated-before-the-curriculum-itself-converged-and-the · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The eval-time anchor saturated *before* the curriculum itself converged, and these are different thresholds — the clip n

The eval-time anchor saturated *before* the curriculum itself converged, and these are different thresholds — the clip needs only `mean ± 2σ` to exceed the box, while convergence needs the learned distribution to fill it. `payload_mass` is the clean case: mean 1.6160, std 0.8371 gives `mean ± 2σ` = [−0.058, 3.29] → clipped to [0, 3], while the engine simultaneously reports the dim as still EXPANDING at 53.9 % of range.

[EVIDENCE: `analyze_training.py --deep` `[TIER 2] DORAEMON` table; the clipped ranges above]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

The eval-time anchor saturated *before* the curriculum itself converged, and these are different thresholds — the clip needs only `mean ± 2σ` to exceed the box, while convergence needs the learned distribution to fill it. `payload_mass` is the clean case: mean 1.6160, std 0.8371 gives `mean ± 2σ` = [−0.058, 3.29] → clipped to [0, 3], while the engine simultaneously reports the dim as still EXPANDING at 53.9 % of range.

[EVIDENCE: `analyze_training.py --deep` `[TIER 2] DORAEMON` table; the clipped ranges above]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

The eval-time anchor saturated *before* the curriculum itself converged, and these are different thresholds — the clip needs only `mean ± 2σ` to exceed the box, while convergence needs the learned distribution to fill it. `payload_mass` is the clean case: mean 1.6160, std 0.8371 gives `mean ± 2σ` = [−0.058, 3.29] → clipped to [0, 3], while the engine simultaneously reports the dim as still EXPANDING at 53.9 % of range.

[EVIDENCE: `analyze_training.py --deep` `[TIER 2] DORAEMON` table; the clipped ranges above]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
