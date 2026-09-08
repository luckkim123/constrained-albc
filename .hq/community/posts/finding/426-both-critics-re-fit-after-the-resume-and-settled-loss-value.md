# Both critics re-fit after the resume and settled: `Loss/value_function` spiked t

- id: finding/426 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: both-critics-re-fit-after-the-resume-and-settled-loss-value_function-spiked-t · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Both critics re-fit after the resume and settled: `Loss/value_function` spiked to 25.4 at iteration 4453 (the return dis

Both critics re-fit after the resume and settled: `Loss/value_function` spiked to 25.4 at iteration 4453 (the return distribution changed when `performance_lb` and the curriculum did) and came back to 6.2 within the first tenth of the segment, ending at 6.76 — the same level as the end of segment 1 (6.64); `Loss/cost_value` spiked to 1.45 and ended at 0.54 (segment 1 end 0.52). Neither loss trends upward over the last half.

[EVIDENCE: `tbread.py` `Loss/value_function` seg 2 max 25.444 at 4453, first-10 % 6.20, last-10 % 6.76; `Loss/cost_value` max 1.446 at 4453, last-10 % 0.541; `analyze_training.py` `[TIER 3] Losses` (seg 2 `value=7.03 cost_val=0.53`)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
