# R1 (plant fix only) fails the pre-registered floor on 19 of 20 rows: the shared latent bias collapsed 4x as finding/381 predicted, the score gap to the teacher did not move (+0.25 to +2.27 deg); the old students were accidental nominal specialists and every student is under-trained (loss_latent 0.020 still falling at it 1000)

- id: finding/384 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: R1, student, distillation, plant-fix, pre-registered, latent-bias, shared-bias, under-trained, loss_latent, p3b_7500, sd_r1, horizon, budget, R4a, R4b
- summary: R1 vs teacher p3b_7500: 19/20 rows worse, only healthy/hard -0.15 (18/64, tail). vs old student: 8 better (medium/hard everywhere), 10 tie, 2 worse. Shared latent bias^2 fell 2.4-17x on all cells (0.033 -> 0.008 at healthy/none) so finding/381 is the mechanism of the shared bias and is resolved; per-env bias^2 unchanged 0.03-0.05, within-episode variance 3x, drift past 30 s steeper. Old students converged to loss_latent 0.0022 on a nominal-concentrated Beta; on the real box the recipe reaches 0.020 at it 1000 still falling 17% per 200 it (R2 0.017). Remaining one-variable probes: R2 horizon (early: growth gone, score tie/worse), R3a driver, R3b window, R4a 10x budget; R4b end-to-end actor not queued. All remaining runs moved to GPU1 (stonefish owns GPU0).

**R1 -- the plant fix alone (finding/381 applied, recipe otherwise verbatim) -- FAILS the pre-registered floor on 19 of 20 rows against its teacher. The mechanism finding/381 named is confirmed: the 64-env shared latent bias collapsed 4x. The score gap did not move, because the old students were accidental nominal specialists and every student is under-trained on the real box.**

**1. Verdict vs teacher `p3b_7500` (att ss_error, seed 42, 64 envs, 155 s; pairDR 0 on all 20 rows).** Pre-registered success = inside 0.10 deg / 1.6 pp on pair34 and pair34_d2 at none and hard. Result: 19 rows `cand worse`, 1 row `cand better` (healthy/hard -0.152, only 18/64 envs better -- tail-driven, not a floor clear).

| config | none | soft | medium | hard |
|:--|:--|:--|:--|:--|
| healthy | +0.257 | +0.331 | +0.271 | -0.152 (18/64) |
| pair34 | +0.598 | +0.665 | +0.386 | +0.563 |
| healthy_d1 | +0.250 | +0.360 | +0.483 | +2.266, surv -1.6 pp |
| healthy_d2 | +0.338 | +0.432 | +0.505 | +1.607, surv -1.6 pp |
| pair34_d2 | +0.580 | +0.374 | +1.314 | +1.017, surv +3.1 pp |

Pitch (the pre-registered indictment row): pair34/none +0.182 (35/64), pair34_d2/none +0.169; pair34/medium tie. Roll: healthy/none +0.245, healthy_d2/hard +1.316. Same sign everywhere.

**2. Against the old student `sd_p3b7500` (same teacher, defective plant, finding/380).** 8 rows better, 10 tie, 2 worse:
- medium/hard on every config: -0.12 to -1.70 deg (healthy/hard -1.53, pair34/hard -1.55, healthy_d2/hard -1.65, pair34_d2/hard -1.70 with surv +3.1 pp).
- none/soft: tie on 8 of 10; worse on pair34/none (+0.134) and pair34_d2/medium (+0.474).
The fix bought accuracy exactly where the exam DR is wide and nothing at nominal.

**3. Against the deployed student `sd_inc9998` (finding/385; comparable at none, and pairDR 0 on every row).** Worse on all 4 healthy rows (+0.13 to +0.57), 3 of 4 healthy_d1, 2 of 4 healthy_d2; better on pair34 medium/hard (-1.47, -6.38, surv +3.1 pp) and pair34_d2 soft/medium/hard (-0.24, -0.94, -5.34). R1 is not a deployable replacement on nominal rows.

**4. The latent error changed shape, not size** (`latent_<lvl>.npz`, per-env time-mean bias over 155 s, 9 dims; old -> R1):

| cell | mse | bias^2 | shared bias^2 | within-episode var | 0-5 s -> 100-155 s | median env corr |
|:--|:--|:--|:--|:--|:--|:--|
| healthy/none old | 0.0445 | 0.0421 | 0.0333 | 0.0024 | 0.019 -> 0.056 | 0.00 |
| healthy/none R1 | 0.0465 | 0.0399 | **0.0077** | 0.0065 | 0.035 -> 0.057 | -0.10 |
| pair34/none old | 0.0440 | 0.0413 | 0.0321 | 0.0026 | 0.021 -> 0.052 | 0.69 |
| pair34/none R1 | 0.0378 | 0.0308 | **0.0134** | 0.0070 | 0.033 -> 0.045 | 0.07 |
| healthy/hard old | 0.0858 | 0.0811 | 0.0171 | 0.0047 | 0.083 -> 0.091 | 0.47 |
| healthy/hard R1 | 0.0928 | 0.0710 | **0.0056** | 0.0218 | 0.069 -> 0.133 | 0.56 |
| pair34/hard old | 0.0853 | 0.0806 | 0.0190 | 0.0047 | 0.082 -> 0.092 | 0.44 |
| pair34/hard R1 | 0.0642 | 0.0512 | **0.0011** | 0.0130 | 0.070 -> 0.077 | 0.61 |

The shared component (the fingerprint finding/380 section 3 read as "trained on a different plant") fell 2.4-17x on all 10 cells. Per-env bias^2 stayed at 0.03-0.05 at none, within-episode variance rose 3x, and the growth over the exam got steeper at hard (healthy_d1/hard 0.087 -> 0.149). R1 estimates instead of emitting a constant -- median env correlation at hard 0.36-0.61 -- but the estimate is noisy and drifts past 30 s. At none the true latent barely varies across envs (per-dim std <= 0.20, most <= 0.06), so the per-env bias^2 of 0.03-0.05 is scatter, not identification.

**5. Why the score did not move.** The old students rolled out on a Beta(30) plant concentrated at nominal (finding/381): `student/loss_latent` converged to 0.0022 and their constant prior sat at the exam's `none` point by accident. On the real box the same recipe reaches 0.0201 at it 1000 (R1) and is still falling 17% per 200 iterations; R2 (155 s episodes) 0.0168, also falling. 1000 iterations = 49M steps was tuned on the defective plant. Two candidate causes remain, both queued and one-variable vs R1: budget (R4a, 10k it) and horizon (R2 -- early read on healthy: the time growth is gone, 0.052 -> 0.039, but none/soft tie R1 and medium/hard worse, so horizon alone does not close it); driver and window are R3a/R3b. The structural alternative -- the frozen actor amplifies any z_hat error, and Lee 2020 / NORBC train the student actor end-to-end (finding/383) -- is R4b, not yet queued.

**6. finding/381 verification is complete**: `params/env.yaml` of R1 shows the intended plant (thrust (0.5, 2.0), delay (0, 3), fail_prob 0.3, doraemon false) and the shared bias collapsed. Its status goes to resolved; the score question moves to this post.

**7. Ops.** R1 exam 23:38-00:37 on GPU1 (shared with the control exam, then with the R2 exam). At 00:29 the R2 exam was moved off GPU0 by user request (stonefish owns GPU0): killed re-entrantly (healthy kept), restarted on GPU1; R3b re-pinned GPU0 -> GPU1 before it started. R3a started 00:37:48 on GPU1. All remaining runs are on GPU1 (8 GB; two processes at a time).

Evidence: `.hq/work/p4/sd_r1/{healthy,pair34,healthy_d1,healthy_d2,pair34_d2}/{summary.json,latent_{none,hard}.npz}`; `/workspace/g0c_runner/p4_score.py arm_pair("sd_r1", ref, CORE+["pair34_d2"])` for ref in p3b_7500 / sd_p3b7500 / sd_inc9998; TB `student/loss_latent` in `logs/rsl_rl/albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_c3_dr5_s30_260905_232533` and `..._ep155_s30_260906_000034`; run dir `params/env.yaml`; `/workspace/g0c_runner/sd_r1_exam.log`.
## Comments
