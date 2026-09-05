# The training-side return gives nothing to select a checkpoint on. Across exactly

- id: finding/376 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: the-training-side-return-gives-nothing-to-select-a-checkpoint-on-across-exactly · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p3b_lb200_s30_r2050_260904_163518
- summary: The training-side return gives nothing to select a checkpoint on. Across exactly the 2500 iterations in which held-out f

The training-side return gives nothing to select a checkpoint on. Across exactly the 2500 iterations in which held-out fault-free attitude regressed by up to +1.507 deg, episode return is flat: it is 2.7 higher at the end than at the start of the window, against a within-window std of 8.79 and a fitted slope of −0.91 per 1000 iterations. A runner reading its own training curve cannot see the regression the eval matrix measures — which is why the selection rule, not the curriculum, is what this run leaves open.

[EVIDENCE: `Train/mean_reward` windowed means over the run's tfevents file — the three windows tabulated below]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-171707/report.md
## Comments
