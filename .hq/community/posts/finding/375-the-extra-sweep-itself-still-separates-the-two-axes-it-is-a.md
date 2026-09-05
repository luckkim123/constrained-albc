# The EXTRA sweep itself still separates the two axes — it is a fault map at zero 

- id: finding/375 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-extra-sweep-itself-still-separates-the-two-axes-it-is-a-fault-map-at-zero · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The EXTRA sweep itself still separates the two axes — it is a fault map at zero delay, and the combined condition is mea

The EXTRA sweep itself still separates the two axes — it is a fault map at zero delay, and the combined condition is measured only by `pair34_d2` above, which is not part of this sweep. So a fault-map row bounds the fault axis alone; it does not bound the deployment condition, where the incumbent's error is 4.4x what these single-axis numbers predict.

[EVIDENCE: `ls .hq/work/p4/p3b_final/` — the 20 EXTRA configs all carry `--control-delay 0`; the only config pairing a delay with a fault vector is `pair34_d2`, added 2026-09-05]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
