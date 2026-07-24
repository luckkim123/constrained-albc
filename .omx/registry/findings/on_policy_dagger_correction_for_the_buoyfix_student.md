---
title: "On-policy DAgger correction for the buoyfix student"
tags: ["distillation", "student", "covariate-shift", "dagger", "albc", "sim-to-real", "next-experiment"]
created: 2026-07-24T03:35:28.710539
updated: 2026-07-24T07:18:57.305669
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: needs-experiment
blocked-on: "PARTIAL adoption measured; residual = observability floor (longer history window + explicit velocity channel), a separate training experiment"
---

# On-policy DAgger correction for the buoyfix student

The buoyfix student (current recipe, obs=72) was measured in-loop by E4 (2026-07-24) and shows SEVERE
closed-loop latent collapse: overall_mse 72-82x the open-loop base at every DR level, and it
UNDER-disperses (l_hat_envvar 0.003-0.013 vs l_true_envvar 0.019-0.095) -- it fails to track the
cross-env latent variation the teacher expresses. This is covariate shift: the student is never
trained on the state distribution it induces when it drives the loop. See the resolved diagnostic lead
closed_loop_latent_collapse_suspicion_legacy_student_measured_11 for the full result table.

PROPOSED NEXT EXPERIMENT (not yet designed/scoped): an on-policy (DAgger-style) distillation
correction -- roll out under the STUDENT-driven policy, relabel the visited states with the teacher
ground-truth latent, and aggregate those into the distillation set so the student learns on its own
induced distribution rather than teacher-only rollouts. Base recipe (encoder=elu+LayerNorm+softsign,
latent_dim=9, TCN student) is fixed; this changes the DISTILLATION PROCEDURE, not the teacher/encoder.

GATE: needs a proper exp-design proposal (discriminating probe + single-variable framing) THEN a
human-gated training launch -- do NOT launch. cuDNN: distillation is conv1d-heavy, so host on the DGX
(probe PASSED, torch 2.9.0+cu130) or fix the container cudnn image (see
container_cudnn_is_cu13_against_cu128_torch lead). No deployment claim for the buoyfix student until
this correction is measured to reduce the in-loop MSE.

---

## Update (2026-07-24T03:59:19.951519)

## 2026-07-24 DESIGNED + reviewer-approved (proposal next-20260724-124841, label C4b-dagger)

The exp-design proposal is now WRITTEN and independently reviewed (proposal-reviewer verdict `approve`, 0 major issues; one minor citation-tightening applied): `experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/proposals/next-20260724-124841.md`. Recorded as `teacher_baseline_buoyfix` campaign planned intent.

DESIGN (single variable = rollout action source): the distillation's `_collect_rollout` currently steps the env with the TEACHER action every step (runner.py:171), so the student only ever trains on the teacher's state distribution -- the covariate-shift mechanism E4 confirmed. The correction steps the env with `beta*a_teacher + (1-beta)*a_student` (beta annealed 1->0), while the teacher relabeling (`buffer.add(l_t, a_t)`) stays UNCHANGED. `a_student` is computed no-grad from the student's own latent over its history, reusing `StudentInLoopPolicy.__call__` (analysis/student_policy.py) TCN-ring / GRU-hidden machinery. beta==1 reduces exactly to the current recipe, so it is genuinely one variable. Streaming (not aggregated) on-policy relabel. New `dagger_*` StudentCfg fields + `--dagger_*` args needed.

DISCRIMINATION (why this is a probe, not just applying the obvious fix): H1 covariate-shift -> on-policy data drops in-loop MSE sharply (crosses below l_true_envvar at >=1 level, l_hat/l_true ratio rises toward ~1). H2 observability/capacity floor -> <=2x improvement, still >> l_true_envvar, residual concentrated on lin-vel-driven dims (a history-only student cannot manufacture a signal the obs does not carry). If H2 wins, the answer is observability (longer history / velocity channel), NOT more DAgger. Readout = re-run the E4 in-loop diagnostic on the DAgger student.

STATUS: still needs-experiment (the training run has NOT happened). Now blocked ONLY on a human-gated training launch, DGX-hosted (cuDNN healthy: torch 2.9.0+cu130, conv1d probe PASSED) -- DAgger runs the student conv1d during collection too, so the workstation cuDNN-off workaround would make it prohibitively slow on BOTH phases. Cheap prior available before committing: pull E4's per_dim_mse geography (uniform -> shades H1; lin-vel-concentrated -> shades H2).

---

## Update (2026-07-24T04:25:09.180110)

## 2026-07-24 IMPLEMENTED + committed + pushed (be42a2f), ready to launch

Code is done, independently code-reviewed (APPROVE, 0 HIGH defects; 2 optional LOW addressed:
collection-time eval-mode parity guard + gated ring allocation), and PUSHED to origin as branch
exp/dagger-correction @ be42a2f (off main 88e0849; baseline tag baseline-260724-dagger). Changes:
config.py dagger_beta_start/end/anneal_iters + dagger_beta_at(); runner._collect_rollout beta-mixed
env.step + _dagger_action reusing the eval StudentInLoopPolicy ring/hidden; train_student.py
--dagger_* args + --enable_cudnn (gates the workstation cu13/cu128 disable so the DGX runs conv1d
full-speed). Sim-free tests/test_dagger_schedule.py + E4 regression = 6 passed. DGX launch prompt:
.sp/plans/2026-07-24-dgx-C4b-dagger-launch.md (+ be42a2f-dagger-correction.patch relay fallback).
NOW blocked ONLY on the human pasting that prompt on the DGX (--dagger_beta_end 0.0 --dagger_anneal_iters 600).

---

## Update (2026-07-24T07:18:57.305669)

[MEASURED on DGX 2026-07-24] C4b ran to completion (code be42a2f exp/dagger-correction; TCN student from anchor s30 model_4999, 4096 envs, 1000 iters, beta 1.0->0.0 over 600 anneal VERIFIED from tfevents, --enable_cudnn, seed 42, wandb 6mezo5uz, 19.4 min). Open-loop loss_latent 0.00518 (teacher-only 0.00493). Step-4 in-loop diagnostic vs the E4 teacher-only baseline (base residual 0.002145): none 0.15584->0.03833 (4.07x reduction), soft 0.16190->0.04419 (3.66x), medium 0.16829->0.06798 (2.48x), hard 0.17613->0.14794 (1.19x). l_hat_envvar 0.0031/0.0032/0.0062/0.0119; l_hat/l_true ratio 0.16/0.12/0.14/0.13 (essentially unchanged from E4's 0.14-0.18). VERDICT: INTERMEDIATE / PARTIAL. NOT clean H1 (covariate shift fully fixed): overall_mse never drops below l_true_envvar, under-dispersion (6-8x env collapse) UNTOUCHED. NOT H2 (observability floor, no help): none/soft dropped 4x, far beyond H2's <=2x -> covariate shift WAS a real, DAgger-addressable component. MIXED: big win at low DR collapsing to 1.19x at hard, under-dispersion floor persists and worsens with DR. CONSEQUENCE: PARTIAL adoption -- keep on-policy DAgger (cuts closed-loop latent error 2.5-4x at low-mod DR) but NOT sufficient alone; residual needs the OBSERVABILITY angle (longer history window and/or explicit velocity channel). No blanket deployment claim. per_dim_mse (hard dims 5/7/3) EXPLORATORY only (z_sweep caveat). CONVERGENT EVIDENCE: Z4 (20ms delay -> 2x degrade) and RT-a (nominal-corner real) independently point at the SAME temporal/observability fragility -> the observability retrain is now a triply-supported lead. DGX output: logs/rsl_rl/albc_trpo_student/trpo_buoyfix_dagger_s30_tcn_260724_133040/ (PULL via Mac; workstation can't reach ksm-nas). DGX-local wiki page: c4b_dagger_correction_measured_partial_2_5_4x_in_loop_reduction_.

