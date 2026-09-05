# The checkpoint choice is not free on this config. Head to head at `none` — the o

- id: finding/374 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-checkpoint-choice-is-not-free-on-this-config-head-to-head-at-none-the-o · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The checkpoint choice is not free on this config. Head to head at `none` — the only structurally paired level, and the d

The checkpoint choice is not free on this config. Head to head at `none` — the only structurally paired level, and the deployment condition — `model_9999` is better by 0.117 deg, which clears the 0.10 floor. It loses at soft (+0.142), medium (+0.144) and hard (+1.697) and sheds 1.6 pp of survival at `hard`, so the balance still favours `model_7500`, but "costs nothing here" would be wrong.

[EVIDENCE: `p4_score.arm_pair("p3b_final", "p3b_7500", ["pair34_d2"])`, `pairDR = 0e+00` on all four levels]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
