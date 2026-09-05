# R3a (R1 + DAgger beta 1->0) is the first student inside the 0.10 floor: 11 of 20 rows tie the teacher, 2 beat it, latent error halved and drift gone; residual = pair34 none/soft +0.12/+0.15 and hard+delay +1.2..+1.8

- id: finding/387 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: student, distillation, dagger, beta, anneal, latent, phase4, retrain-simtoreal-2026-09, R3a, floor
- summary: One-variable arm R3a = R1 + beta annealed 1.0->0.0 over 600 it. vs teacher 11 tie / 2 better / 7 worse (R1 and R2: 0 tie, 19-20 worse); vs R1 18/20 better; vs deployed student every faulted row better by 0.24-7.0 deg. Exam latent mse halves on all 14 cells read (per-env bias^2, drift flat). Pre-registered floor on pair34 missed by 0.015/0.050 at none/soft. Delay makes the same latent error cost 3x more (healthy/hard -0.59 vs healthy_d1/hard +1.65) with no single mis-read dim. Training loss ranks arms backwards (0.037 vs 0.020) -- exam latent only. R4c = R3a recipe + 10k it queued, not fired.

**R3a (`sd_p3b7500_c3_dr5_beta0_s30` = R1 + DAgger beta annealed 1.0 -> 0.0 over 600 it, one variable) is the first student inside the pre-registered 0.10 floor on most of the exam: 11 of 20 rows tie the teacher, 2 beat it, and the exam latent error is half of R1's with the in-episode drift gone. It still misses the floor where it was pre-registered (pair34 none/soft +0.115/+0.150) and loses hard+delay by +1.2..+1.8, so the rollout distribution was the lever and the residual is now budget or structure.**

**1. Verdict (att ss_error, 64 envs paired, seed 42, pairDR 0 on every cell). vs teacher `p3b_7500`: 11 tie / 2 better / 7 worse. vs R1: 18 better / 2 worse. vs deployed `sd_inc9998`: 12 better / 4 tie / 4 worse.**

| config | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| healthy, R3a-teacher | +0.099 tie | +0.071 tie | -0.036 tie | **-0.587** (33/64) |
| pair34, R3a-teacher | +0.115 | +0.150 | **-0.129** | -0.069 tie |
| healthy_d1, R3a-teacher | +0.100 | +0.049 tie | +0.069 tie | +1.653 |
| healthy_d2, R3a-teacher | +0.083 tie | +0.045 tie | +0.073 tie | +1.827 |
| pair34_d2, R3a-teacher | +0.167 | +0.151 | +0.159 | +1.151 |
| healthy, R3a-R1 | -0.158 | -0.260 | -0.307 | -0.435 |
| pair34, R3a-R1 | -0.483 | -0.515 | -0.514 | -0.632 |
| healthy_d1, R3a-R1 | -0.150 | -0.312 | -0.414 | -0.613 (surv +1.6) |
| healthy_d2, R3a-R1 | -0.255 | -0.387 | -0.431 | +0.220 |
| pair34_d2, R3a-R1 | -0.413 | -0.223 | -1.156 | +0.135 (surv -3.1) |

vs deployed: pair34 all better (hard -7.01, surv +3.1 pp), pair34_d2 all better (hard -5.20), healthy none/soft tie, medium -0.13, hard +0.13; healthy_d1 none -0.14 / hard +0.18; healthy_d2 none -0.31 / hard +0.13. Pitch vs teacher: 15 tie, 2 better (healthy/hard -0.20, pair34/medium -0.12), 3 worse (delay hard +0.62/+0.68/+0.91). Roll vs teacher: 11 tie, 2 better, 7 worse -- pair34 and pair34_d2 none/soft +0.11..+0.17 and delay hard +1.40/+1.54/+0.81. The two att rows R3a loses to R1 (healthy_d2/hard, pair34_d2/hard) are the hard+delay tail; everywhere else it is 0.15-1.16 better.

**2. Estimator (latent l_hat - l_true; mse = per-env bias^2 + within-episode var; 0-5 s vs 100-155 s windows).**

| config/lvl | R1 mse | R3a mse | R1 bias^2 | R3a bias^2 | R1 0-5 s -> 100-155 s | R3a 0-5 s -> 100-155 s |
|:--|--:|--:|--:|--:|:--|:--|
| healthy/none | 0.047 | 0.029 | 0.040 | 0.024 | 0.035 -> 0.057 | 0.028 -> 0.041 |
| healthy/hard | 0.093 | 0.048 | 0.071 | 0.043 | 0.069 -> 0.133 | 0.056 -> 0.053 |
| pair34/none | 0.038 | 0.021 | 0.031 | 0.017 | 0.033 -> 0.045 | 0.030 -> 0.024 |
| pair34/hard | 0.064 | 0.042 | 0.051 | 0.037 | 0.070 -> 0.077 | 0.057 -> 0.045 |
| healthy_d1/hard | 0.114 | 0.056 | 0.092 | 0.051 | 0.087 -> 0.149 | 0.064 -> 0.063 |
| healthy_d2/hard | 0.111 | 0.055 | 0.091 | 0.049 | 0.082 -> 0.147 | 0.063 -> 0.061 |
| pair34_d2/hard | 0.090 | 0.049 | 0.074 | 0.041 | 0.078 -> 0.109 | 0.061 -> 0.053 |

On all 14 cells read the mse halves, the reduction is per-env bias^2 (variance was already small), and the time growth R1 showed at hard is flat. Per embedding dim at hard the error is 0.4-0.6 of the true latent variance on every dim for R3a (0.7-1.9 for R1): the estimator explains roughly half the plant variance, up from almost none. Two things it did NOT fix: (a) at `none` the true latent variance is near zero on 6 of 9 dims yet the error stays 0.02-0.09 -- a constant offset at the nominal point, and R3a's shared bias^2 there is slightly larger than R1's on healthy (0.015 vs 0.008) and healthy_d2 (0.018 vs 0.011); (b) under delay the same latent error costs far more -- healthy/hard (mse 0.048) beats the teacher by 0.59, healthy_d1/hard (mse 0.056) loses by 1.65, and the delay-vs-no-delay error difference is spread evenly across the 9 dims (sum 0.43 vs 0.51), not one mis-read dim. The teacher's action is simply more sensitive to z-hat error once a step of delay is in the loop.

**3. Why beta 1->0 works (textbook DAgger, MED on the mechanism, HIGH on the effect).** beta 0.5 constant (R1, the incumbent recipe) rolls half the batch out under the teacher, so the student never sees the states its own errors produce; 1->0 over 600 it trains the first 60 % on teacher states and the last 40 % on the student's own, which is where the per-env bias gets corrected. Caveat recorded in finding/386 and HANDOFF 3.9s: R3a's TRAINING loss_latent is 0.037 vs R1's 0.020 because it is measured on the student's own harder state distribution -- training curves rank these arms backwards; only the exam latent error counts.

**4. Against the pre-registered criterion.** The floor was "within 0.10 deg of the teacher on pair34". R3a reads +0.115 / +0.150 / -0.129 / -0.069 there: two rows miss by 0.015 and 0.050, two pass. So the criterion is NOT met as written, while the exam as a whole moved from 0/20 (R1) and 0/20 (R2) to 13/20 rows at or better than the floor. Deployment-relevant reading: R3a beats the deployed student on every faulted row by 0.24-7.0 deg and ties it on nominal rows; it is 0.13-0.18 behind the deployed student only on hard+delay, which finding/385 showed the deployed student "wins" through a constant wrong latent acting as a damped prior.

**5. Next arm (queued, NOT fired).** R4c `sd_p3b7500_c3_dr5_beta0_it10k_s30` = R3a recipe + 10k iterations (ANNEAL stays 600 so R4c-R3a isolates budget and R4c-R4a isolates the anneal at 10k). Prediction: if under-training on the real box is the remaining term (finding/384: loss still falling at it 1000), per-env bias^2 falls further, pair34 none/soft close to inside 0.10 and the hard+delay rows move toward the teacher; if budget adds nothing on top of the anneal (R4a vs R1 near-null), R4c ties R3a within 0.10 everywhere and the residual is structural -> R4b (student actor fine-tuned on the student's own states, Lee 2020 / NORBC). R4a (beta 0.5 + 10k, running on GPU0 since 02:17) reads first. Leads untouched by this result: finding/383, 384, 385, 386, 380, 382; blocking finding/264, finding/352 (acked on this queue entry as on every one of this program).

**6. Ops.** Run `logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_c3_dr5_beta0_s30_260906_003754` (HEAD c3501e2, plant line thrust (0.5,2.0) delay (0,3) payload (0,3) inertia (0.4,2.0) fault 0.3; `params/env.yaml` 693 lines), trained 00:37-00:59 on GPU1 sharing the card with the R2 exam (21 min vs 12-13 alone). Exam `.hq/work/p4/sd_r3a/` 00:59-02:26 on GPU1 (11-17 min per config beside the R2 exam, then R3b training and exam). Scorer `p4_score.arm_pair("sd_r3a", ref, CORE+["pair34_d2"], metric=P.ss_att|ss_pitch|ss_roll)`; latent from `latent_<lvl>.npz` (`l_hat`,`l_true`, 7751x64x9).
## Comments
