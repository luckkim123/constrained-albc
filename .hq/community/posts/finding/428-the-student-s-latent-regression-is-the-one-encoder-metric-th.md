# The student's latent regression is the one encoder metric that moved during dist

- id: finding/428 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-student-s-latent-regression-is-the-one-encoder-metric-that-moved-during-dist · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The student's latent regression is the one encoder metric that moved during distillation, and it moved *up* once DAgger 

The student's latent regression is the one encoder metric that moved during distillation, and it moved *up* once DAgger handed the rollouts to the student: `student/loss_latent` fell 0.161 → 0.041 (minimum at iteration 146, β ≈ 0.76) and then rose to 0.075 by the end, plateauing after β reached 0 at 600; `student/loss_action` traced the same shape (0.0067 → 0.0010 at 146 → 0.0029). This is the expected DAgger signature — the state distribution shifts to the student's own visits, which are harder to label — not a fit failure; the exam scores above are the arbiter, and the engine has no student adapter, so these are raw-TB windows.

[EVIDENCE: `tbread.py` on `trpo_sd_p5_r3a_s30_260908_015931` (`student/loss_latent` min 0.04105 at 146, last-10 % 0.07544; `student/loss_action` min 0.00100 at 146, last-10 % 0.00286; `student/dagger_beta` 0 from 600); `analyze_training.py` on the student run returned `iters=0` (no adapter for `student/*` tags)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
