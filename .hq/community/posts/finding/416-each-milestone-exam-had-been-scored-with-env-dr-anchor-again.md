# Each milestone exam had been scored with `--env-dr-anchor` against the `doraemon

- id: finding/416 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: each-milestone-exam-had-been-scored-with-env-dr-anchor-against-the-doraemon · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: Each milestone exam had been scored with `--env-dr-anchor` against the `doraemon_state.pt` that sat in the run directory

Each milestone exam had been scored with `--env-dr-anchor` against the `doraemon_state.pt` that sat in the run directory at that moment, so 2500, 5000 and 7500 were each graded on a narrower plant than the next (paced dims at 0.013 / 0.019 / 0.033 of range). On those plants the three look interchangeable — 6.65 / 5.73 / 5.99 deg on `healthy` medium, 5000 "winning" — and 7500 even looks worse than 5000 on the delay cells. Regrading 5000 and 7500 on the frozen final sidecar multiplies their error by 3.1× and 2.0× and puts them in the correct order behind 9999. The own-moment scores are kept as `own_5000` / `own_7500` and are not admissible for ranking.

[EVIDENCE: `exam_table.csv` rows tag ∈ {`pre_2500`, `own_5000`, `own_7500`} vs {`p5_5000`, `p5_7500`, `p5_10000`}, medium; sidecar `control_delay_strength` at each exam from the run's `curriculum_trajectory.json` / `DORAEMON/mean/control_delay_strength` (0.0127 at 2500, 0.019 at 5000, 0.033 at 7500, 0.0607 final)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
