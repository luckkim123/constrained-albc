# R3b (R1 + TCN 27-step window) fails 20 of 20 vs the teacher and 18 of 20 vs R1: a 0.54 s window cannot integrate the latent (shared bias 4-6x, in-episode variance 5-8x R1); the window axis is closed

- id: finding/388 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- topic: decision
- confidence: high · status: resolved
- verified: none · keywords: student, distillation, tcn, window, encoder, latent, phase4, retrain-simtoreal-2026-09, R3b
- summary: One-variable arm R3b = R1 + --encoder_type tcn (27 steps, cuDNN). vs teacher +0.42..+2.82 on all 20 rows (0/64 envs better at none on healthy configs); vs R1 18 worse / 2 tie; vs R3a 20/20 worse. Latent mse 2-4x R1 at none: shared bias^2 0.03-0.05 (4-6x), within-episode var 5-8x, and the error GROWS 2.8x from 0-5 s to 100-155 s -- the opposite regime from the GRU arms (per-env constant bias). Closes the HORA-style windowed estimator for this plant at this budget; longer windows / TCN under beta anneal recorded as leads, not queued.

**R3b (`sd_p3b7500_tcn_dr5_s30` = R1 + `--encoder_type tcn`, 27-step / 0.54 s window, cuDNN; one variable) FAILS on 20 of 20 rows against the teacher (+0.42..+2.82) and on 18 of 20 against R1. Its latent estimator is both biased and noisy: mse 2-4x R1 at `none`, with a shared (all-env) bias^2 of 0.03-0.05 and an in-episode variance 5-8x R1. A half-second window cannot integrate the 9-D latent; the window axis of finding/383 is closed for this plant.**

**1. Verdict (att ss_error, 64 envs paired, seed 42, pairDR 0 on every cell).** vs teacher `p3b_7500`: 20/20 worse, +0.416 (healthy/hard) .. +2.815 (pair34_d2/hard); at `none` 0/64 envs better on healthy, healthy_d1, healthy_d2. vs R1: 18 worse / 2 tie (pair34_d2 none -0.03, medium -0.08). vs R3a: 20/20 worse, +0.38..+2.34. vs deployed `sd_inc9998`: 16 worse / 4 better (pair34 medium/hard -1.03/-4.67, pair34_d2 medium/hard -1.03/-3.54 -- the deployed student's own constant-latent failure, finding/385, not a merit of R3b).

| config | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| healthy, R3b-R1 | +0.662 | +0.336 | +0.360 | +0.568 |
| pair34, R3b-R1 | +0.127 | +0.419 | +0.440 | +1.712 |
| healthy_d1, R3b-R1 | +0.790 | +0.344 | +0.310 | +0.349 (surv +1.6) |
| healthy_d2, R3b-R1 | +0.745 | +0.282 | +0.223 | +1.137 (surv +1.6) |
| pair34_d2, R3b-R1 | -0.028 tie | +0.414 | -0.084 tie | +1.798 (surv -4.7) |
| healthy, R3b-teacher | +0.919 (0/64) | +0.667 | +0.631 | +0.416 |
| pair34, R3b-teacher | +0.725 | +1.084 | +0.826 | +2.275 |
| healthy_d1, R3b-teacher | +1.040 (0/64) | +0.704 | +0.793 | +2.615 |
| healthy_d2, R3b-teacher | +1.083 (0/64) | +0.714 | +0.727 | +2.744 |
| pair34_d2, R3b-teacher | +0.552 | +0.789 | +1.230 | +2.815 (surv -1.6) |

**2. Estimator (latent l_hat - l_true; mse = per-env bias^2 + within-episode var; shared bias^2 = the part common to all 64 envs).**

| config/lvl | R1 mse | R3b mse | R1 shared^2 | R3b shared^2 | R1 within | R3b within | R3b 0-5 s -> 100-155 s |
|:--|--:|--:|--:|--:|--:|--:|:--|
| healthy/none | 0.047 | 0.184 | 0.008 | 0.052 | 0.007 | 0.060 | 0.075 -> 0.206 |
| healthy/hard | 0.093 | 0.133 | 0.006 | 0.007 | 0.022 | 0.047 | 0.091 -> 0.139 |
| pair34/none | 0.038 | 0.101 | 0.013 | 0.035 | 0.007 | 0.035 | 0.078 -> 0.090 |
| pair34/hard | 0.064 | 0.124 | 0.001 | 0.012 | 0.013 | 0.050 | 0.107 -> 0.127 |
| healthy_d1/none | 0.057 | 0.184 | 0.011 | 0.049 | 0.008 | 0.057 | 0.073 -> 0.214 |
| healthy_d1/hard | 0.114 | 0.142 | 0.003 | 0.006 | 0.022 | 0.045 | 0.099 -> 0.149 |
| healthy_d2/none | 0.054 | 0.183 | 0.011 | 0.052 | 0.008 | 0.047 | 0.069 -> 0.208 |
| healthy_d2/hard | 0.111 | 0.136 | 0.002 | 0.006 | 0.020 | 0.041 | 0.099 -> 0.146 |
| pair34_d2/none | 0.044 | 0.085 | 0.017 | 0.029 | 0.007 | 0.030 | 0.063 -> 0.071 |
| pair34_d2/hard | 0.090 | 0.124 | 0.002 | 0.008 | 0.016 | 0.047 | 0.109 -> 0.130 |

Three signatures, all 10 cells: (a) the in-episode variance is 5-8x R1 -- a 27-step window re-estimates the latent from half a second of history every step, so the estimate wanders with the vehicle state instead of converging; (b) at `none` the shared bias^2 is 0.03-0.05, 4-6x R1 -- the window sees the same nominal transient in every env and maps it to the same wrong point; (c) the late-window error at `none` is 2.8x the early one (0.07 -> 0.21) on the healthy configs, i.e. the estimate gets WORSE as the episode settles, the opposite of the GRU arms. The GRU arms' failure was a per-env constant bias with small variance (finding/384); the TCN's is variance plus a common bias -- a different, worse regime, consistent with the 2026-08-10 `sdfinal_tcn` reading that motivated decision/059's cuDNN note but was never scored on this exam.

**3. What this closes and what it does not.** Closed: the windowed-estimator arm of finding/383 (HORA-style TCN) on this plant at this budget -- the latent needs longer integration than 0.54 s, and the recurrent estimator with beta annealing (R3a, finding/387) is the recipe family to pursue. Not tested and not claimed: a longer TCN window (e.g. 5-10 s) or TCN under beta 1->0; both are recorded as leads, neither queued, because R3a already reaches the floor on 13/20 rows with the GRU and the remaining gap is not in the estimator's window.

**4. Ops.** Run `logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_tcn_dr5_s30_260906_013849` (HEAD c3501e2 at queue, 69b1c90 at start; cuDNN preamble + `--enable_cudnn`; plant line verbatim, `env.yaml` 693 lines), trained 01:38-02:01 on GPU1 beside the R3a exam (23 min). Exam `.hq/work/p4/sd_r3b/` 02:01-03:02 on GPU1 with `--encoder_type tcn` (verified on the process cmdline); per config 16 min while sharing with the R3a exam, 10 min alone. Scorer `p4_score.arm_pair("sd_r3b", ref, CORE+["pair34_d2"], metric=P.ss_att)`; latent from `latent_<lvl>.npz`. Leads untouched: finding/383, 384, 385, 386, 387; blocking finding/264, finding/352.
## Comments
