# Control exam: the deployed student sd_inc9998 loses to its teacher inc13w on nominal rows (+0.15 none, +0.62 hard, surv -3.1 pp) but beats it by 7.85 deg at pair34_d2/none -- a constant wrong latent (shared bias^2 0.588) acting as a damped prior, not competence; Phase 4 teacher-mode margins under delay overstate the candidate against what is on the robot

- id: finding/385 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- topic: pattern
- confidence: high · status: needs-experiment
- verified: none · keywords: control-exam, sd_inc9998, inc13w, deployed-student, student-beats-teacher, constant-latent, damped-prior, delay, teacher-mode, deployment-comparison, re-analysis, pair34_d2
- summary: sd_inc9998 vs inc13w: healthy none +0.15 / hard +0.62 (surv +3.1 pp) worse, pair34 tie to +0.28 worse, but every delay row better by 0.24-2.29 and pair34_d2 by 6.2-10.5 deg. Its latent under delay is a fixed wrong vector (mse 0.596, shared bias^2 0.588, flat from t=0): the frozen actor on a constant z_hat is more damped than on the true latent, and under a 2-step delay damped wins. vs p3b_7500 (deploy candidate, at none): candidate better on 17/20, delay margin at none +0.24 (d1) / +0.40 (d2) not the +0.6-0.7 seen teacher-vs-teacher, fault margin +0.35 to +6.9. vs sd_p3b7500: faults favour p3b lineage, nominal/delay favour the incumbent student. Deployment verdicts need student-mode exams on both sides; RE-analysis of diagnose-20260905-140134 owed with finding/378 and /382.

**Control exam: the deployed student `sd_inc9998` loses to its own teacher `inc13w` on the nominal rows (healthy/none +0.15, healthy/hard +0.62 with survival -3.1 pp) and beats it by 7.85 deg at pair34_d2/none. The win is not competence: under delay the student's latent is a constant wrong vector (shared bias^2 0.588 of mse 0.596) that happens to act as a damped prior, while the teacher, driven by the true latent, oscillates. Phase 4 compared teacher modes; against what is actually on the robot, the candidate's delay margin shrinks to +0.24 to +0.40 deg at none.**

**1. `sd_inc9998` vs `inc13w` (its teacher, teacher-mode; att ss_error; pairDR 0 except pair34_d2/hard 1e-01).**

| config | none | soft | medium | hard |
|:--|:--|:--|:--|:--|
| healthy | +0.151 worse | +0.090 tie | -0.027 tie | +0.621 worse, surv +3.1 pp |
| pair34 | -0.060 tie | +0.017 tie | +0.128 worse | +0.276 worse, surv -1.6 pp |
| healthy_d1 | -0.372 | -0.701 (64/64) | -1.986 | -1.876 |
| healthy_d2 | -0.237 | -0.650 | -1.640 | -2.291 |
| pair34_d2 | **-7.849** (63/64) | -8.830 (64/64) | -10.480 | -6.248 (pairDR 1e-01) |

Teacher-mode inc13w at pair34_d2/none is 9.36 deg; the student is 1.51.

**2. Why a student beats its teacher.** inc13w trained with `control_delay_steps (0,0)` (finding/264) and the student rolled out on the DORAEMON initial Beta with no delay either (finding/381). In-loop latent error from `latent_<lvl>.npz`:

| cell | mse | bias^2 | shared bias^2 | 0-5 s -> 100-155 s |
|:--|:--|:--|:--|:--|
| healthy/none | 0.0266 | 0.0246 | 0.0116 | 0.021 -> 0.030 |
| pair34/none | 0.0453 | 0.0381 | 0.0261 | 0.034 -> 0.052 |
| pair34_d2/none | 0.5958 | 0.5918 | **0.5877** | 0.596 -> 0.592 |
| pair34_d2/hard | 0.5659 | 0.5575 | 0.5302 | 0.584 -> 0.564 |

At pair34_d2 the estimator saturates to one fixed vector from t = 0 (no growth, no per-env structure). The frozen actor then runs on a constant z_hat; that policy is more damped than the actor on the true latent, and under a 2-step delay damped wins. It is the same defect that costs the student +0.15/+0.62 at healthy, read from the other side. A better estimator would remove this "robustness".

**3. `sd_inc9998` vs `p3b_7500` (the deploy-candidate teacher; comparable at none, pairDR 0 on all rows).** The candidate teacher is better on 17 of 20 rows: pair34 +0.35/+0.56/+1.85/+6.94, pair34_d2 +0.43/+0.62/+2.26/+6.35, healthy_d2 +0.40/+0.13/+0.27/+1.70; the deployed student is better only at healthy/hard (-0.72); ties healthy/medium, healthy_d1 soft/medium. So against what is on the robot the retrain's delay margin at none is +0.24 (d1) / +0.40 (d2), not the +0.6 to +0.7 the teacher-vs-teacher exam shows, and its fault margin is +0.35 (pair34/none) rising to +6.9 (hard).

**4. `sd_inc9998` vs `sd_p3b7500` (student vs student, the deployment question as of finding/380).** Deployed better on healthy (all four, -0.08 to -2.10), healthy_d1 soft/medium/hard, healthy_d2 soft/medium/hard, pair34 none, pair34_d2 none; the old p3b student better on pair34 medium/hard (+1.07/+4.83 against the deployed, surv -3.1 pp) and pair34_d2 medium/hard (+1.42/+3.64). Faults favour the p3b lineage, nominal and delay favour the incumbent student -- and R1 (finding/384) keeps that split.

**5. What changes.**
- A deployment verdict on this program needs student-mode exams on both sides. Teacher-mode margins (report `diagnose-20260905-140134`) are upper bounds on what a student can carry, and under delay they are not even that.
- The report's delay conclusions need the RE-analysis pass already owed for finding/378 and finding/382, carrying tables 1 and 3 here.
- Do not cite the incumbent's delay behaviour as a design property. It is an estimator failure with a lucky sign.

Evidence: `.hq/work/p4/sd_inc9998/{healthy,pair34,healthy_d1,healthy_d2,pair34_d2}/{summary.json,latent_{none,hard}.npz}` (student `student_final_round/trpo_sdfinal_c3_gruselect_inc9998_s30_260810_124813/models/student_999.pt`, teacher `teacher_iter_budget/trpo_iterbudget_s30_260805_012813/model_9998.pt`, `sd_inc_exam.sh`, GPU0, 23:09-00:00); `p4_score.arm_pair("sd_inc9998", ref, CORE+["pair34_d2"])` for ref in inc13w / p3b_7500 / sd_p3b7500.
## Comments
