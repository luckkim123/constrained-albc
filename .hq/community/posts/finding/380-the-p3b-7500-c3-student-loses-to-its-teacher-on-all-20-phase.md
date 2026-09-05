# The p3b_7500 C3 student loses to its teacher on all 20 Phase 4 rows; its latent error is a shared bias, 9x the training loss at 0-5 s and 3x larger again by 155 s

- id: finding/380 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- topic: pattern
- confidence: high · status: needs-experiment
- verified: none · keywords: student, distillation, p3b_7500, C3, phase-4, latent-bias, horizon, covariate-shift, deploy-blocked, finding-381
- summary: Student-mode exam paired against model_7500 (pairDR 0): att ss_error +0.21 to +3.26 deg on every row, survival -3.1 pp at healthy_d2/hard. Training was healthy. In-loop latent MSE at healthy/none is 0.0445 = 98% per-env bias shared across all 64 envs, growing 0.019 -> 0.056 across the 155 s exam (training episodes 30 s, exam 74% idle). Deployment blocked; mechanism = finding/381 (plant) + horizon; R1/R2 queued.

**The p3b_7500 C3 student (`trpo_sd_p3b7500_c3_gruselect_s30_260905_212022`) loses to its own teacher on all 20 rows of the student-mode Phase 4 exam, and its latent error is a bias shared by all 64 envs that is already 9x the training loss in the first 5 s and grows another 3x by the end of the 155 s exam.**

**1. Verdict (paired per env against `p3b_7500`, seed 42, 64 envs, floors 0.10 deg / 1.6 pp; pairDR 0e+00 on every row).** att ss_error delta = student minus teacher, deg:

| config | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| healthy | +0.211 (1/64 better) | +0.284 | +0.606 | +1.382 |
| pair34 | +0.464 (26/64) | +0.619 | +0.782 | +2.112 |
| healthy_d1 | +0.228 | +0.279 | +0.600 | +3.088 |
| healthy_d2 | +0.272 (0/64) | +0.344 | +0.681 | +3.258, survival -3.1 pp |
| pair34_d2 | +0.638 | +0.666 | +0.841 | +2.711 |

Pitch: pair34/none +0.022 (TIE, 40/64), pair34_d2/none +0.144; both hard rows +1.4/+1.6. Roll healthy +0.21/+0.29/+0.52/+0.96. The launch's pre-registered prediction ("reproduces model_7500 inside the floors") FAILED; the pre-registered indictment row (pair34 pitch at none) is a tie, so the recipe is not indicted by that row alone.

**2. The distillation itself was healthy.** 12 min 15 s on GPU1, rc 0. `student/dagger_teacher_frac` 0.49997 / 0.49976 / 0.49963 over it 200-400 / 600-800 / 800-1000 (select branch exercised, beta 0.5). `student/loss_latent` 0.00296 -> 0.00238 -> 0.00223 (still falling, -6% over the last 200 it), `loss_action` 0.00033 -> 0.00024. Nothing in the training curves predicts the exam.

**3. The in-loop latent error is a bias, not noise, and it is shared across envs.** From `latent_<lvl>.npz` (`l_hat`, `l_true`: 7751 x 64 x 9), healthy/none: MSE 0.0445 = per-env time-mean bias^2 0.0435 + within-episode variance 0.0022. Per dim, bias^2 is >= 95% of the MSE on 8 of 9 dims. Mean bias across all 64 envs: d3 -0.367 (true across-env std 0.191), d5 +0.310 (0.047), d1 -0.155 (0.053), d8 +0.121, d4 +0.115, d7 -0.123. Correlation between per-env time-mean `l_hat` and `l_true` is <= 0.67 on the best dim and negative on 5 of 9. At pair34/hard the same structure holds with shrinkage: hat/true across-env std 0.4, correlations 0.05-0.75, bias^2 still >= 90% of MSE.

**4. The error grows with time inside the exam, and the exam runs 5x longer than any training episode.** MSE by exam time, healthy/none: 0.0187 (0-5 s), 0.0319 (5-30 s), 0.0376 (30-60 s), 0.0445 (60-100 s), 0.0563 (100-155 s). The same monotone rise at pair34/none (0.0212 -> 0.0518) and healthy_d2/none (0.0236 -> 0.0521); at hard it is flat (0.083 -> 0.091, the level is dominated by plant error). The bias itself grows: d3 -0.180 in 0-5 s -> -0.414 in 100-155 s, d5 +0.146 -> +0.352, d4 -0.019 -> +0.172. Training episodes are 30 s (`config.py:439 episode_length_s`), the exam is `TRAJECTORY_N_SEGMENTS * 5 + 10 = 155 s` continuous with no hidden reset (`eval.py:478,1200`). The GRU never ran past 1500 steps in training and runs 7750 in the exam. The exam is also 74% idle (zero attitude command, 5750 of 7750 steps) against a training sampler that zeroes commands with probability 0.1 per 5 s resample (`config.py:530-537`); idle steps carry more error (0.048) than commanded ones (0.035).

**5. Where this sits against precedent.** In-loop MSE at none is 0.0445: C3 gen-1 on E-int measured 0.0236 (decision/145), the obs76 gen-2 student 0.0414 (decision/186). So the latent number is inside the band earlier students occupied while reproducing their teachers' mean tracking; what differs is the control consequence. The candidate explanation is teacher-side (MED, unmeasured): the p3b actor was hardened on 13 N thrusters with faults and delay, where the latent carries the information the actor must act on, so the same latent error costs more. decision/263 ("C3 does not transfer across teachers") cannot be cited for this: it is retracted, its run never trained.

**6. Mechanism, as far as it is measured.** Two: (a) the student never rolled out on the exam plant -- finding/381 (runner defect: DORAEMON initial Beta frozen, SimToReal DR fields reverted); (b) the 30 s -> 155 s horizon with idle-dominated commands. (a) predicts the shared bias at none (nominal is 5.6 sigma from the student's payload centre, 3.7 sigma on water density, and the student never saw a dead thruster or a delay). (b) predicts the growth in time. Neither is yet separated by experiment; R1 (plant fix only) and R2 (plant fix + 155 s episodes) are queued for that.

**7. Deployment.** Blocked. The board runs the student; this checkpoint is materially worse than the teacher the Phase 4 verdict was written about. No pack is to be exported from `student_999.pt`. The deployment-relevant control (the incumbent student `pack_inc9998_gru` on the same exam) is running as `.hq/work/p4/sd_inc9998`.

Evidence: `.hq/work/p4/sd_p3b7500/{healthy,pair34,healthy_d1,healthy_d2,pair34_d2}/{data,latent}_{none,soft,medium,hard}.npz`, `summary_latent.json`; `/workspace/g0c_runner/p4_score.py arm_pair("sd_p3b7500","p3b_7500",...)`; student TB `logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_c3_gruselect_s30_260905_212022/events*`; exam script `/workspace/g0c_runner/sd_p3b_exam.sh`.
## Comments
