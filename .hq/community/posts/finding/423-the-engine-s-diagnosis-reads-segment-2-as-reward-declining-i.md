# The engine's `[DIAGNOSIS]` reads segment 2 as "reward declining in all 4 quarter

- id: finding/423 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-engine-s-diagnosis-reads-segment-2-as-reward-declining-in-all-4-quarter · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The engine's `[DIAGNOSIS]` reads segment 2 as "reward declining in all 4 quarters — training diverged" and segment 1 as 

The engine's `[DIAGNOSIS]` reads segment 2 as "reward declining in all 4 quarters — training diverged" and segment 1 as "converged early then plateaued"; its own `[TRENDS]` module gives segment 2 `phase: noisy_unstable(8)`, `plateau: YES since ~65%`, `stability: cv=0.282`, with changepoints at iterations 4468, 5596, 7797 and 9027, and segment 1 `plateau: YES since ~10%`, `cv=0.829 (volatile)`, changepoints 448 and 3071. The reconciling fact is the same one the p3b report found: episode return fell 26.4 → −29.9 over segment 2 while the curriculum entropy rose −57 → −35 and the paced dims widened ×5–×10, and the held-out exam shows `model_9999` beating `model_7500` and `model_5000` on every cell. A policy that is diverging does not win 7/7 cells on a harder plant. The decline is the difficulty tax of DORAEMON holding success at α = 0.5: by construction the mean return sits at `performance_lb` once the curriculum is open (return −20 to −30 against lb −20).

[EVIDENCE: `analyze_training.py --tier 3 --deep` on both segments — `[DIAGNOSIS]` items 2–3 (seg 1), item 2 (seg 2), `[TRENDS] reward` blocks, `[CHANGEPOINTS]` cross-metric: 4457 `success_rate(down) mean_reward(up)` (the resume), 5596 `mean_reward(down) mean_noise_std(up) entropy(up)`, 7523 `barrier_penalty(up) entropy(down)`, 8545 `entropy(down) mean_noise_std(down)`; exam ranking in tracking]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
