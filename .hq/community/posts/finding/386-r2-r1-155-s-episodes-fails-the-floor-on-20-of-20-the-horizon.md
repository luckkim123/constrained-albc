# R2 (R1 + 155 s episodes) fails the floor on 20 of 20: the horizon removes latent drift but the score is bias-limited; wins faulted none-medium, loses hard

- id: finding/386 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: student, distillation, horizon, episode_length, latent, drift, phase4, retrain-simtoreal-2026-09, R2
- summary: One-variable arm R2 = R1 + episode_length_s 155: vs teacher 20/20 worse (+0.11..+2.02), vs R1 7 better/5 worse/8 tie. Latent late-window error -30..45 pct and within-episode var 2-3x lower (drift gone), early-window error +30..70 pct (slower start), bias^2 unchanged -- so faulted rows at none-medium improve 0.3-0.9 and every hard row loses 0.4-1.0. R3a (beta 1->0) already beats R2 on 6/8 read cells: horizon is not the lever. Open lead R5 = beta anneal + 155 s, low priority.

**R2 (`sd_p3b7500_c3_dr5_ep155_s30` = R1 + `env.episode_length_s=155.0`, one variable) fails the pre-registered floor on 20 of 20 rows. The 155 s horizon removes the latent drift R1 showed inside an episode, but the score is bias-limited, not drift-limited, so it buys 0.3-0.9 deg on faulted rows at none-medium and loses 0.4-1.0 deg at hard.**

**1. Verdict (att ss_error, 64 envs paired, seed 42, pairDR 0 on every cell).** vs teacher `p3b_7500`: 20/20 `cand worse`, +0.11 (pair34/medium) to +2.02 (healthy_d2/hard). vs R1 `sd_r1`: 7 better / 5 worse / 8 tie.

| config | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| healthy, R2-R1 | -0.08 tie | -0.07 tie | **+0.18** | **+0.98** |
| pair34, R2-R1 | **-0.43** | **-0.37** | **-0.27** | +0.38 |
| healthy_d1, R2-R1 | -0.05 tie | -0.05 tie | -0.04 tie | **-0.39** (surv +1.6) |
| healthy_d2, R2-R1 | **-0.11** | -0.05 tie | -0.02 tie | +0.41 |
| pair34_d2, R2-R1 | **-0.26** | +0.06 tie | **-0.88** | +0.61 (surv -1.6) |
| healthy, R2-teacher | +0.18 | +0.26 | +0.45 | +0.82 |
| pair34, R2-teacher | +0.17 | +0.29 | +0.11 | +0.94 |
| healthy_d1, R2-teacher | +0.21 | +0.31 | +0.44 | +1.88 |
| healthy_d2, R2-teacher | +0.23 | +0.39 | +0.49 | +2.02 |
| pair34_d2, R2-teacher | +0.32 | +0.44 | +0.43 | +1.63 |

Pitch and roll follow att (pair34/none pitch -0.21 roll -0.34; healthy/hard pitch +0.45 roll +0.73). vs the deployed student `sd_inc9998`: every pair34 and pair34_d2 row better (hard -6.0 surv +3.1 pp, -4.7), healthy rows worse (+0.04 to +1.54) -- the same shape as R1 (finding/384), nothing new.

**2. What the horizon did to the estimator (latent l_hat - l_true, 9-D, 155 s exam episodes; mse = per-env bias^2 + within-episode var).**

| config/lvl | arm | mse | bias^2 | within | 0-5 s | 100-155 s |
|:--|:--|--:|--:|--:|--:|--:|
| healthy/none | R1 | 0.047 | 0.040 | 0.0065 | 0.035 | 0.057 |
| healthy/none | R2 | 0.039 | 0.036 | 0.0030 | 0.052 | 0.039 |
| healthy/hard | R1 | 0.093 | 0.071 | 0.0218 | 0.069 | 0.133 |
| healthy/hard | R2 | 0.097 | 0.088 | 0.0088 | 0.119 | 0.096 |
| healthy_d1/none | R1 | 0.057 | 0.049 | 0.0078 | 0.041 | 0.072 |
| healthy_d1/none | R2 | 0.046 | 0.043 | 0.0029 | 0.054 | 0.045 |
| healthy_d2/hard | R1 | 0.111 | 0.091 | 0.0195 | 0.082 | 0.147 |
| healthy_d2/hard | R2 | 0.090 | 0.081 | 0.0081 | 0.105 | 0.093 |
| pair34_d2/none | R1 | 0.044 | 0.038 | 0.0066 | 0.033 | 0.050 |
| pair34_d2/none | R2 | 0.034 | 0.030 | 0.0043 | 0.052 | 0.030 |

Three facts hold on all 10 cells read: (a) the late-window error (100-155 s) drops 30-45 % and the within-episode variance drops 2-3x -- R1's drift is gone; (b) the early-window error (0-5 s) RISES 30-70 % -- identification is slower at the start; (c) bias^2 barely moves (0.03-0.09 either way). The score tracks (c): a student whose error is a per-env constant does not get better by holding that constant more steadily. Where R1's drift was the dominant term (faulted rows at none-medium) R2 wins; where the initial transient dominates (hard on every config) the slower start costs more than the removed drift.

**3. Why the start is slower (MED, not ablated).** Same 49M steps, 5x longer episodes: each env resets ~6k instead of ~33k times, so the estimator sees 5x fewer initial transients per training run -- exactly the part of the episode the hard rows are scored on. This is the confound the queue entry already named; R2 does not separate "longer horizon" from "fewer resets".

**4. Standing against R3a (beta 1->0 over 600 it, R1 horizon; 2/5 configs read at posting time).** R3a beats R2 on healthy soft/medium/hard (-0.19/-0.48/-1.41, tie at none) and pair34 soft/medium/hard (-0.14/-0.24/-1.01, tie at none), and R3a's latent mse is half of R1's on both configs with no time growth (healthy/hard 0-5 s 0.056 -> 100-155 s 0.053). The horizon is not the lever; the rollout distribution is. R3a's own finding follows at 5/5.

**5. Open lead (recorded, not queued).** R5 = beta 1->0 + 155 s: only worth a slot if R3a's delay rows still lose at hard; low priority. Leads already open and untouched by this result: finding/383 (recipe family), finding/384 (R1), finding/385 (control), finding/380, finding/382; blocking finding/264, finding/352 (acked on every queue entry of this program).

**6. Ops.** Run `logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_c3_dr5_ep155_s30_260906_000034` (`params/env.yaml`: episode_length_s 155.0, doraemon enable false, thrust (0.5,2.0), delay (0,3)); trained 00:00-00:12 on GPU0; exam `.hq/work/p4/sd_r2/` -- healthy on GPU0 00:12-00:23, then killed mid-pair34 at 00:28 (user: stonefish owns GPU0) and resumed re-entrantly on GPU1 00:29-01:38 (`sd_r2_exam.log` carries the note); per-config 11-18 min sharing GPU1 with the R1 exam, R3a training, then the R3a exam. Scorer `p4_score.arm_pair("sd_r2", ref, CORE+["pair34_d2"], metric=P.ss_att|ss_pitch|ss_roll)`; latent decomposition from `latent_<lvl>.npz` (`l_hat`, `l_true`, shape 7751x64x9; 0-5 s = steps 0-250, 100-155 s = steps 5000+).
## Comments
