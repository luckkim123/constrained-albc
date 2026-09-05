# R4a (R1 + 10k it, beta 0.5) fails 20 of 20 vs the teacher and 16 of 20 vs R3a: budget on the constant-beta recipe trades none/soft for medium/hard; a same-seed second realization of R1 is within 0.10 of R1 at none/soft but 0.2-0.7 apart at medium/hard; the hard-level exam mean is a tail statistic and R3a ties the teacher median there

- id: finding/389 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: student distillation, R4a, training budget, DAgger beta 0.5, reproducibility, same seed, run-to-run variance, noise floor, tail, median, P90, latent mse, Phase 4 exam, retrain-simtoreal-2026-09
- summary: R4a = R1 + 10k iterations (beta 0.5). vs teacher 0/0/20, vs R3a 4/0/16, vs R1 8 better (all none/soft) / 9 worse (all medium/hard); loss_latent floors at it 2k at R1 value. Second realization of R1 (same seed, R4a student_999): weights relL2 0.88, exam 11 tie / 2 / 7 vs R1 -- noise ~0.1 at none/soft, 0.2-0.7 at medium/hard; its latent mse is 2-7x R1 at the same score. Mean att at hard is tail-made (teacher 3.33/0.66/5.47 mean/median/P90); R3a ties the teacher median on all four core hard cells. Budget on beta 0.5 closed; R3a verdict is single-realization; R4c readable at 0.10 on none/soft only.

**R4a (`sd_p3b7500_c3_dr5_it10k_s30` = R1 + MAXIT 10000, DAgger beta 0.5 constant; one variable) FAILS 20 of 20 rows against the teacher (+0.10..+2.61) and 16 of 20 against R3a (the 4 ties are all at `none`). Against R1 it is a trade, not a gain: 8 rows better, every one at none/soft (-0.10..-0.36), 9 rows worse, every one at medium/hard (+0.18..+1.05). The training loss floors at it ~2k at R1's own value (0.018) and the next 8k iterations do not move it. Budget on the constant-beta recipe is closed. Two measurements ride along: (a) a second realization of the R1 recipe with the SAME seed (R4a's `student_999.pt`) differs from R1 by relL2 0.88 in weights and lands within 0.10 of R1 on 11 of 20 exam rows -- 9 of the 10 none/soft rows -- but 0.2-0.7 apart at medium/hard, so a single-realization delta below ~0.3 (medium) / ~0.7 (hard) is inside the noise; (b) the exam mean at `hard` is a tail statistic for every arm including the teacher (healthy/hard mean 3.33 / median 0.66 / P90 5.47), and R3a ties the teacher's MEDIAN on all four core configs at hard -- its hard+delay losses are P90 effects, not typical-env effects.**

**1. Verdict (att ss_error, 64 envs paired, seed 42, pairDR 0 on every cell).** vs teacher `p3b_7500`: 0 tie / 0 better / 20 worse. vs R3a: 4 tie / 0 better / 16 worse. vs R1: 3 tie / 8 better / 9 worse. vs deployed `sd_inc9998`: 5 tie / 7 better / 8 worse (better on every pair34-type medium/hard row by 1.3-5.4, worse on every healthy-type soft..hard row by 0.24-1.49). Pitch vs teacher 7 tie / 0 / 13 worse; roll 1 tie / 0 / 19 worse. Pre-registered floor (pair34 within 0.10 of the teacher): missed on all four rows.

| config | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| healthy, R4a-teacher | +0.102 | +0.159 | +0.485 | +0.770 |
| pair34, R4a-teacher | +0.235 | +0.391 | +0.567 | +1.530 |
| healthy_d1, R4a-teacher | +0.139 | +0.265 | +0.563 | +2.560 (surv -1.6) |
| healthy_d2, R4a-teacher | +0.160 | +0.365 | +0.687 | +2.605 |
| pair34_d2, R4a-teacher | +0.361 | +0.570 | +0.724 | +2.063 (surv +1.6) |
| healthy, R4a-R1 | -0.155 | -0.172 | +0.214 | +0.922 |
| pair34, R4a-R1 | -0.363 | -0.274 | +0.181 | +0.968 |
| healthy_d1, R4a-R1 | -0.111 | -0.095 tie | +0.080 tie | +0.293 |
| healthy_d2, R4a-R1 | -0.178 | -0.067 tie | +0.183 | +0.998 (surv +1.6) |
| pair34_d2, R4a-R1 | -0.219 | +0.195 | -0.590 | +1.047 (surv -1.6) |
| healthy, R4a-R3a | +0.003 tie | +0.088 tie | +0.521 | +1.357 |
| pair34, R4a-R3a | +0.120 | +0.241 | +0.695 | +1.599 |
| healthy_d1, R4a-R3a | +0.039 tie | +0.216 | +0.494 | +0.907 (surv -1.6) |
| healthy_d2, R4a-R3a | +0.077 tie | +0.320 | +0.614 | +0.779 |
| pair34_d2, R4a-R3a | +0.193 | +0.419 | +0.565 | +0.912 (surv +1.6) |

**2. Training.** `student/loss_latent` (beta 0.5, so comparable to R1 and NOT to R3a -- finding/386): it 999 0.0232, it 1999 0.0176, it 4999 0.0186, it 9999 0.0179; mean of the last 50 it 0.0186 vs R1's 0.0188. The floor is reached by it ~2k and `grad_norm` halves (0.064 -> 0.032) on a flat loss. finding/384's "loss still falling at it 1000" lead is closed on this recipe: the loss stops at 2k and the exam does not follow it down. 108 min for 9999 it on GPU0 alone (92 it/min).

Exam latent (l_hat - l_true; mse = per-env bias^2 + within-episode var): R4a is the best of the three at `none` (healthy 0.021 vs R1 0.046 / R3a 0.029; pair34 0.023 vs 0.038 / 0.021) and between them at `hard` (healthy 0.064 vs 0.093 / 0.048; pair34 0.063 vs 0.064 / 0.042; healthy_d1 0.080 vs 0.114 / 0.056; healthy_d2 0.076 vs 0.110 / 0.055; pair34_d2 0.073 vs 0.090 / 0.049), with a within-episode variance of 0.001-0.007 (the estimate is a per-env constant) and no drift. A lower mean latent error than R1 at hard sits next to a worse mean attitude error than R1 at hard -- section 4 explains why.

**3. Reproducibility: a second realization of R1 (`sd_r4a999` = R4a's own `student_999.pt`, same code, same seed s30, same recipe to it 999).** The 86,537 encoder parameters differ from R1's `student_999.pt` by relL2 0.878 (max |dw| 0.70): the rollout stream is not deterministic and 1000 DAgger iterations turn that into a different student. Exam vs R1: 11 tie / 2 better / 7 worse (pitch 9 / 1 / 10, roll 13 / 3 / 4); vs teacher 1 tie / 0 / 19 worse (R1: 0 / 1 / 19).

| config | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| healthy, R1'-R1 | +0.009 tie | +0.037 tie | +0.276 | +0.213 |
| pair34, R1'-R1 | +0.076 tie | +0.082 tie | +0.721 | +0.503 |
| healthy_d1, R1'-R1 | +0.009 tie | +0.026 tie | -0.016 tie | -0.296 (surv +1.6) |
| healthy_d2, R1'-R1 | -0.081 tie | +0.005 tie | -0.033 tie | +0.309 |
| pair34_d2, R1'-R1 | +0.090 tie | +0.186 | -0.382 | +0.192 |

Read: at none/soft the recipe reproduces to within 0.10 (9 of 10 rows); at medium/hard it does not (|delta| 0.19-0.72 on 8 of 10). The verdict CLASS is stable; a cell-level delta between two single realizations is not a result below ~0.3 at medium and ~0.7 at hard. Consequences: R3a's 18/20 wins over R1 (-0.15..-1.16) are mostly above that band, but its 11 ties with the teacher are single-realization and can move by a class on re-run; R4c - R3a is readable at the 0.10 floor on none/soft rows only.

The second realization's latent is 2-7x worse than R1's at the same score: mse healthy/none 0.096 vs 0.046, pair34/none 0.268 vs 0.038, pair34_d2/none 0.285 vs 0.044, hard 0.15-0.24 vs 0.06-0.11; shared bias^2 up to 0.18; drift 0.067 -> 0.422 at pair34/none (R1: 0.033 -> 0.045). Per dim at pair34/none its bias^2 is 0.14-0.40 on dims 0, 1, 2, 4, 8, whose true across-env variance is <= 0.010 -- a large constant wrong value on dims that carry no plant information -- and the exam charges it +0.08. Latent mse is not a sufficient statistic for the score: the actor is insensitive to most of the error and the direction that matters is not isolated by the mean.

**4. Why the mean and the mse disagree: the mean at hard is a tail statistic.** Per-env att ss_error, mean / median / P90 (64 envs):

| cell | teacher | R1 | R3a | R4a | R1' |
|:--|:--|:--|:--|:--|:--|
| healthy/none | 0.43 / 0.40 / 0.54 | 0.68 / 0.50 / 1.23 | 0.52 / 0.50 / 0.73 | 0.53 / 0.50 / 0.67 | 0.69 / 0.67 / 0.81 |
| pair34/none | 1.01 / 0.96 / 1.20 | 1.61 / 1.19 / 2.97 | 1.12 / 1.02 / 1.51 | 1.24 / 1.01 / 2.52 | 1.68 / 1.76 / 2.12 |
| healthy/hard | 3.33 / 0.66 / 5.47 | 3.18 / 1.15 / 4.76 | 2.74 / 0.67 / 4.85 | 4.10 / 1.08 / 9.64 | 3.39 / 1.23 / 6.06 |
| pair34/hard | 5.83 / 1.07 / 16.09 | 6.39 / 1.81 / 19.30 | 5.76 / 1.08 / 16.32 | 7.36 / 2.36 / 20.96 | 6.90 / 2.10 / 18.48 |
| healthy_d1/hard | 2.27 / 0.82 / 5.04 | 4.54 / 1.31 / 9.45 | 3.92 / 0.81 / 9.00 | 4.83 / 2.08 / 11.80 | 4.24 / 1.43 / 11.71 |
| healthy_d2/hard | 2.35 / 0.85 / 4.49 | 3.96 / 1.64 / 7.28 | 4.18 / 1.00 / 10.03 | 4.96 / 2.60 / 12.88 | 4.27 / 1.66 / 13.33 |
| pair34_d2/hard | 6.76 / 2.00 / 20.98 | 7.77 / 3.78 / 22.65 | 7.91 / 3.13 / 25.01 | 8.82 / 4.48 / 24.25 | 7.96 / 4.05 / 20.54 |

Three readings. (a) The teacher's own hard mean is 3-5x its median: the top decile of envs makes the mean. (b) R3a ties the teacher's MEDIAN at hard on all four core configs (0.67 vs 0.66, 1.08 vs 1.07, 0.81 vs 0.82, 1.00 vs 0.85); its +1.65 / +1.83 mean losses on healthy_d1/hard and healthy_d2/hard are P90 9.0 vs 5.0 and 10.0 vs 4.5 -- a tail of envs, not the typical env. (c) R4a is worse than R3a in both the median (1.08-4.48) and the P90 (9.6-24) at hard; per env, corr(att, latent mse) is +0.36..+0.46 for R4a and R3a at hard with the 16 worst-latent envs at 7-17 deg and the 16 best at 0.8-2.2, while R1 shows no such correlation (r -0.03..+0.06, worst/best 2.36/3.25): R1 is uniformly mediocre, the annealed and the long-budget arms are bimodal. That is how R4a's lower mean latent error at hard coexists with a worse mean attitude error. At none the same holds in miniature: median 0.50 for R1, R3a and R4a alike, P90 1.23 -> 0.73 / 0.67, and corr(att, latent) +0.79 (R1, worst/best 2.87/0.89), +0.74 (R4a), +0.69 (R1'), +0.07 (R3a, 1.00/1.04) -- R3a removed the nominal tail, R4a shrank it. Lead (scoring tooling, no training): report median and P90 per cell next to the mean. The pre-registered floor of this program stays mean-based and no verdict is re-declared here.

**5. What this closes and what it opens.** Closed: the budget axis of finding/383 for the constant-beta recipe, and finding/384's under-training lead. Open, in order of information per GPU-hour: (i) a second realization of R3a (seed 31, or s30 again) -- the candidate recipe's verdict is single-realization and the noise measured here is a class wide at medium/hard; not queued. (ii) R4c (R3a + 10k, `pending-launch.json`, queued 02:30) stays pending approval; its prediction is updated on R4a's evidence: budget lowers the nominal P90 and raises the hard median and P90, so R4c most likely ties R3a at none/soft and loses hard+delay by more; read it at the 0.10 floor on none/soft rows, and at medium/hard by median/P90 or deltas above ~0.7 only. (iii) R4b (student actor fine-tuned on the student's own states) unchanged. Leads untouched: finding/380, 382, 383, 384, 385, 386, 387, 388; blocking finding/264, finding/352 unchanged.

**6. Ops.** Run `logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_c3_dr5_it10k_s30_260906_021704` (HEAD 9e0dfa5 at start, dirty 0; plant line verbatim, `env.yaml` 693 lines; 100 checkpoints `student_99..9999.pt`). Wrapper `student_p3b_r4a.sh` took GPU0 through the `/workspace/GPU0_FREE` hand-off at 02:16:58 (host `gpu0_watch.sh`, finding HANDOFF 3.9s), trained 02:17-04:05 on GPU0 alone. Exam `.hq/work/p4/sd_r4a/` 04:05-04:50 on GPU0 (9 min/config beside the GPU1 exam). Second-realization exam: symlink dir `/workspace/g0c_runner/r4a999_ckpt/models/student_999.pt` -> R4a's it-999 checkpoint, `sd_exam_generic2.sh` on GPU1 04:07-04:55, arm `sd_r4a999`, marker `SD_R4A999_EXAM_DONE`. Scripts in `.hq/work/p4/`: `r4a_prep.py` (TB scalars + weight diff), `r4a_score.py` (arm_pair x7 + latent decomposition), `r4a_dims.py` (per-dim bias, per-env corr), `r4a_tail.py` (mean/median/P90). Both GPUs idle from 04:55, tmux empty.
## Comments
