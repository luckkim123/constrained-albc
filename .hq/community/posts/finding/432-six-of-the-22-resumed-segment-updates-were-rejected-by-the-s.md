# Six of the 22 resumed-segment updates were rejected by the SLSQP entropy optimiz

- id: finding/432 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: six-of-the-22-resumed-segment-updates-were-rejected-by-the-slsqp-entropy-optimiz · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Six of the 22 resumed-segment updates were rejected by the SLSQP entropy optimizer and none of them is visible in `DORAE

Six of the 22 resumed-segment updates were rejected by the SLSQP entropy optimizer and none of them is visible in `DORAEMON/mode`. The console shows `Entropy opt rejected` at 4749, 5749, 6749, 6999, 7749 (`Singular matrix E in LSQ subproblem` / `Positive directional derivative for linesearch`) and 8749 (`Iteration limit reached`); on those updates the feasible branch still reports `mode` 0 while `DORAEMON/kl_step` is 0 and `ess_ratio` 1.0. The 6499–6999 hold seen live (entropy flat at −47.6 for three updates, mistaken at first for the α boundary) was two of these rejections back to back. A rejection costs one update of widening; six of 22 is a 27 % duty loss on a curriculum that ended nowhere near its ceiling.

[EVIDENCE: `misc.py` grep of `/workspace/g0c_runner/p5_teacher.log` mapped to the preceding `Learning iteration`; `tbread.py` `DORAEMON/kl_step` / `DORAEMON/ess_ratio` at those steps; `status.log` 2026-09-07 20:46 CORRECTION entry; `marinelab/algorithms/doraemon.py` update branch (`metrics["mode"]=0.0` set before the optimizer result is known)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
