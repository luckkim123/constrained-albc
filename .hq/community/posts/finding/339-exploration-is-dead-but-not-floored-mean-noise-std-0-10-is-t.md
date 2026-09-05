# Exploration is dead but not floored — `mean_noise_std` 0.10 is twice the `min_st

- id: finding/339 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: exploration-is-dead-but-not-floored-mean_noise_std-0-10-is-twice-the-min_st · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Exploration is dead but not floored — `mean_noise_std` 0.10 is twice the `min_std` 0.05 floor, so the collapse is the po

Exploration is dead but not floored — `mean_noise_std` 0.10 is twice the `min_std` 0.05 floor, so the collapse is the policy's own choice under `entropy_coef` 0.003, not a clamp. The `sigma_step` being 36× smaller than the `actor_step` says the std branch has effectively stopped moving. This is the same signature the engine flagged at it 2092 (entropy −6.90), so it predates the curriculum opening and is a property of this hyperparameter set rather than of the retrain.

[EVIDENCE: `analyze_training.py --tier 1` on both segments; `[CONFIG] entropy_coef=0.003, min_std=0.05`; `Grad/sigma_step` 0.000675 against `Grad/actor_step` 0.024517]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/report.md

---

## Update (2026-09-04T22:02:22.562084)

Exploration is dead but not floored — `mean_noise_std` 0.10 is twice the `min_std` 0.05 floor, so the collapse is the policy's own choice under `entropy_coef` 0.003, not a clamp. The `sigma_step` being 36× smaller than the `actor_step` says the std branch has effectively stopped moving. This is the same signature the engine flagged at it 2092 (entropy −6.90), so it predates the curriculum opening and is a property of this hyperparameter set rather than of the retrain.

[EVIDENCE: `analyze_training.py --tier 1` on both segments; `[CONFIG] entropy_coef=0.003, min_std=0.05`; `Grad/sigma_step` 0.000675 against `Grad/actor_step` 0.024517]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-070135/report.md

---

## Update (2026-09-05T08:19:31.987857)

Exploration is dead but not floored — `mean_noise_std` 0.10 is twice the `min_std` 0.05 floor, so the collapse is the policy's own choice under `entropy_coef` 0.003, not a clamp. The `sigma_step` being 36× smaller than the `actor_step` says the std branch has effectively stopped moving. This is the same signature the engine flagged at it 2092 (entropy −6.90), so it predates the curriculum opening and is a property of this hyperparameter set rather than of the retrain.

[EVIDENCE: `analyze_training.py --tier 1` on both segments; `[CONFIG] entropy_coef=0.003, min_std=0.05`; `Grad/sigma_step` 0.000675 against `Grad/actor_step` 0.024517]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md

## Comments
- (2026-09-05, omx) 정정: wiki add append-merge

- (2026-09-05, omx) 정정: wiki add append-merge
