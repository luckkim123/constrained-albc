# Training flagged the regression almost not at all. Read from the run's tfevents,

- id: finding/367 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: training-flagged-the-regression-almost-not-at-all-read-from-the-run-s-tfevents · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: Training flagged the regression almost not at all. Read from the run's tfevents, `DORAEMON/mode` is 1 at every logged st

Training flagged the regression almost not at all. Read from the run's tfevents, `DORAEMON/mode` is 1 at every logged step from 7249 to 9999 with a single exception — **0 at it 8499**, inside the regression window — and reward recovered to 185.6 (r50 179.9) by it 8463 while `fault_severity` came off its bound to 0.4602. One isolated mode-0 hold is not a signal anyone would act on, but "nothing flagged it" overstates the silence, and the earlier reading of "mode 1 from 7249 onward" was wrong.

[EVIDENCE: `DORAEMON/mode` scalars from `events.out.tfevents.*`, steps 7249-9999: 1,1,1,1,1,**0**,1,1,1,1,1,1 (`curriculum_trajectory.json` carries no mode field — its keys are `param_names`/`param_bounds`/`trajectory`)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
