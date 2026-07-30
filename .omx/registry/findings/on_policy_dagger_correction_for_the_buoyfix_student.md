---
title: "On-policy DAgger correction for the buoyfix student"
tags: ["distillation", "student", "covariate-shift", "dagger", "albc", "sim-to-real", "next-experiment", "c3-gruselect", "id-collision"]
created: 2026-07-24T03:35:28.710539
updated: 2026-07-30T05:05:43.720025
sources: ["diagnose-20260729-161459", "diagnose-20260729-172500", "diagnose-20260729-184021", "diagnose-20260729-192128"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "MEASURED 2026-07-29 by arm C2 (trpo_sdeint_c2_daggersel_s30_260729_185634, analysis diagnose-20260729-192128). The mechanism half of this lead is CLOSED: replacing the action blend with per-env-per-step Bernoulli policy selection reverses the sign of B4b's latent regression and beats it at every DR level (-31.4/-30.5/-9.5/-8.7% in-loop latent MSE). dagger_mix=select is ADOPTED as the default mechanism. What remains open is the CONTROL half at screening resolution: C2 improves on the anchor at all four levels but every delta is sub-floor (max 0.0904 vs the 0.1 deg floor), and the dispersion signal (C2 has the campaign's lowest medium CV 63.6% and hard tail n_gt20 4.00) still sits on ss_error_std, for which the profile declares no floor. Next arm: select mixing on a GRU encoder -- C2 and A0g win on DIFFERENT axes (C2 roll at medium/hard, A0g pitch everywhere), so combining them is the first proposal in this campaign with two independent reasons to expect a gain."
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

---

## Update (2026-07-24T08:18:41.484275)

## Residual structure characterized per-dim (workstation deep analysis, 2026-07-24)

The C4b DAgger student's raw in-loop latent was pulled to the workstation and dissected per-dim
(analysis: `experiments/rsl_rl/albc_trpo_student/trpo_buoyfix_dagger_s30_tcn_260724_133040/analysis/diagnose-latent-260724/`).
This characterizes WHAT the residual "partial adoption" floor is:

- The DAgger student's in-loop residual is an ENV-VAR UNDER-DISPERSION, not random error: it reproduces
  <=16% of the teacher latent's env-to-env spread, flat across all 4 DR levels (structural floor).
- 8 of 9 latent dims collapse (env-var ratio <0.10); only 1 dim (the least-informative) partially
  reconstructs. Temporal variance is preserved, so the encoder is alive -- it loses the slow env-identity.
- Interpretation: DAgger fixed the covariate-shift half of the gap (in-loop mse cut 4.07x at none) but the
  irreducible half is observability -- the attitude-only obs cannot see the force/heave signal the collapsed
  dims encode. No amount of on-policy correction recovers information absent from the input.
- Therefore this lead's residual is CLOSED as "explained": the next move is the observability retrain
  (velocity channel +/- longer history), tracked under the closed_loop_latent_collapse lead. This DAgger
  lead needs no further correction-side experiment.

---

## Update (2026-07-29T03:36:16.750379)

## 2026-07-29 VERDICT REVERSED by E0 -- DAgger is a win, not a null

The C4b readout that closed this lead ("residual EXPLAINED as observability under-dispersion; no
correction-side experiment remains") was produced by the broken `eval.py static` latent instrument
(see `closed_loop_latent_collapse_suspicion_legacy_student_measured_11`, fix `38d979e`). Re-measuring
the SAME DAgger checkpoint `trpo_buoyfix_dagger_s30_tcn_260724_133040` against the SAME plain-BC
checkpoint `trpo_buoyfix_s30_tcn_260722_184632` with the corrected instrument reverses the reading.

PAIRED CONTRAST, identical environments (per-env DR matched 23/23 at hard), single variable =
rollout action source (`dagger_beta_end` 0.0 with 600-iter anneal vs the inert 1.0):

| level | axis | plain BC | DAgger | factor | CV plain | CV DAgger |
|:--|:--|--:|--:|--:|--:|--:|
| hard | roll | 1.3441 deg | 0.5936 deg | 0.44x | 431% | 212% |
| hard | pitch | 0.6861 deg | 0.4232 deg | 0.62x | 418% | 296% |
| medium | roll | 0.7728 deg | 0.5427 deg | 0.70x | 184% | 90% |
| medium | pitch | 0.3307 deg | 0.2717 deg | 0.82x | 151% | 48% |

DAgger roughly halves hard-level roll error AND halves env-to-env dispersion. Its in-loop MSE relative
to its own open-loop residual is 12.7x (0.06576 / 0.005178) against plain BC's 37.0x
(0.07932 / 0.002145).

THIS RESOLVES C4b's OWN PRE-REGISTERED DISCRIMINATION TOWARD H1 (covariate shift). C4b's H2 branch
required a residual concentrated on lin-vel-driven dims that a history-only student cannot manufacture;
instead the plain-BC student resolves all 9 latent dims at hard, so the information is present and the
on-policy correction is what closes the gap.

CAVEATS. n=1 seed per arm; the two students carry different open-loop bases (0.002145 vs 0.005178) so
the MSE-ratio leg mixes in a training-fit difference -- the attitude contrast is the stronger leg. Both
students were distilled from the buoyanchor teacher on the pre-gate-D-a plant, so these are relative
readings, not the campaign baseline; A0 (fresh TCN from E-int) establishes that. Design note carried
forward: prefer a FIXED mixing ratio over the annealed schedule (VIRAL/SLIM), which is what B4b tests.
Report:
`experiments/rsl_rl/albc_trpo_student/trpo_buoyfix_dagger_s30_tcn_260724_133040/analysis/diagnose-20260729-e0-instrument/report.md`.

---

## Update (2026-07-29T07:26:51.837646)

UPDATE 2026-07-29 -- first direct measurement of a fixed-ratio DAgger against the FINAL (E-int) teacher, campaign student_distill_eint arm B4b (run trpo_sdeint_b4b_beta05_s30_260729_153436, analysis diagnose-20260729-161459).

Setup: dagger_beta held at 0.5 for all 1000 iters (bite verified: student/dagger_beta first=last=0.500000, n=1000), encoder deliberately left at TCN so beta is the single variable against the A0 anchor.

Result: a sub-floor NULL on control. att_norm ss_error deltas vs A0 = 0.0245/0.0316/0.0570/0.0776 deg (none/soft/medium/hard), all below the eval's declared 0.1 deg screening floor. Direction is consistent (better at none/soft/hard, worse at medium) but no level is decision-grade at n=1.

Against it: absolute in-loop latent MSE is WORSE than plain BC at every level -- 0.046257/0.040382/0.045696/0.071386 vs A0's 0.032975/0.030741/0.040636/0.068040 (+40.3%/+31.4%/+12.5%/+4.9%). This is the only eval-side comparison in the arm that is comfortably above measurement noise, and it points the wrong way.

For it (both unadjudicated): B4b has the lowest hard-level dispersion in the campaign, teacher included (att_norm CV 148.2% vs A0 178.2%, A0g 168.3%, teacher 177.9%) -- the exact place DAgger theory predicts a gain; and the covariate-shift multiplier at hard falls 22.4x -> 18.7x, though that denominator is a beta-0.5 mixed-rollout loss, not an open-loop one, so it is inflated by construction.

Cost: free. student/time_train 0.219250 s vs A0's 0.218941 s.

So the lead's premise is now TESTED rather than untested, and the answer at screening resolution is 'no measurable effect'. It is NOT the same as 'DAgger does not work' -- the dispersion signal survives and the protocol simply cannot resolve it at n=1 with 64 envs. Closing this lead requires either a floor for ss_error_std or a higher-resolution eval, not another single-seed arm.

---

## Update (2026-07-29T08:39:06.362590)

UPDATE 2026-07-29 (post-B1a/B1b): the lambda bracket run later the same day reinforces this page's
conclusion from a different direction. lambda_latent 0 and 4 both produced sub-floor control nulls too,
so THREE independent objective-side interventions (dagger_beta 0.5, lambda 0, lambda 4) have now failed
to move control above the screening floor, while the one representational intervention (A0g, TCN -> GRU)
cleared it at two of four levels. The reading is that on this plant the leverage is representational,
not objective-shaped, and further DAgger tuning is a poor use of an arm.

Note the shared measurement caveat: this page's covariate-shift multiplier and B1a's both have a
denominator that is not like-for-like with the anchor's (a beta-mixed rollout loss here, an
unoptimized monitored loss there). In both cases the comparison that survives is the ABSOLUTE in-loop
latent MSE, and in both cases it points against the intervention.

---

## Update (2026-07-29T09:41:58.612023)

UPDATE 2026-07-29 (C1-latsens): this lead is no longer speculative on either axis.

WHY B4b UNDER-TESTED IT. `runner.py:260` returns `beta * a_teacher + (1.0 - beta) * a_student` -- a
continuous blend of two 8-D thruster commands, not the stochastic policy selection DAgger's
distribution argument requires. Where the two policies disagree the blend issues commands neither
would (opposing thruster pairs averaging toward zero net thrust), so the rollout visits a third
distribution belonging to neither. That is a sufficient explanation for B4b's otherwise puzzling
result: its absolute in-loop latent MSE was WORSE than plain BC at every DR level (+40.3 / +31.4 /
+12.5 / +4.9%), which training on a blend-artifact distribution predicts and genuine DAgger does not.

WHY IT IS NOW WORTH AN ARM. C1-latsens measured the frozen actor's transfer function and found the
control lever is real but concentrated at hard DR: 1.070 deg per unit of latent perturbation at hard
against 0.036 at none and 0.027 at medium. On-policy collection is precisely the mechanism that
reduces in-loop error at hard, where the student's own trajectories diverge most from the teacher's.
Halving A0g's hard in-loop latent error projects to roughly -0.42 deg, about 4x the decision floor.

THE ARM. Replace the blend with per-env Bernoulli selection at the same beta = 0.5. One variable
against B4b; A0 remains the shared beta = 1 reference, where blending and selection coincide exactly.
Judge it on hard-level in-loop latent MSE first (the quantity the sensitivity curve says matters) and
on att_norm at hard second.

---

## Update (2026-07-29T10:22:54.711181)

RESOLVED (mechanism half) 2026-07-29 by arm C2. The blend-vs-select question this page raised after
C1-latsens is now measured, and the answer is unambiguous.

| in-loop latent MSE vs the plain-BC anchor A0 | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| B4b, action blending | +40.3% | +31.4% | +12.5% | +4.9% |
| C2, policy selection | -3.7% | -8.6% | +1.7% | -4.2% |
| C2 vs B4b | -31.4% | -30.5% | -9.5% | -8.7% |

Single variable between the two arms is `dagger_mix`. Bite check used a mechanism-EXCLUSIVE metric,
`student/dagger_teacher_frac` = 0.500072, because a logged `dagger_beta` reads 0.5 under either
mechanism and therefore proves nothing about which ran.

The decisive structural observation: open-loop training is INDISTINGUISHABLE between the two
(`loss_latent` 0.003799 vs 0.003809, `loss_total` 0.004018 vs 0.004016), and the arms separate only
in-loop. That is exactly the signature a covariate-shift correction should have, and it rules out the
difference being a generic optimization effect.

So B4b's null was never evidence that on-policy correction fails on this plant. It was evidence that a
convex blend of two 8-D action vectors is not on-policy correction: where the policies disagree the
blend issues commands neither would (opposing thruster pairs averaging toward zero net thrust) and
visits states neither induces.

Control did NOT reach decision grade: C2 beats the anchor at all four DR levels, a first for the
campaign, but every delta is under the declared 0.1 deg floor (max 0.0904). A0g keeps the adoption
because its advantage sits in pitch, which drives att_norm.

---

## Update (2026-07-30T05:02:58.713679)

## CLOSED 2026-07-30: the "next arm" this lead proposed already ran as C3, and it produced the campaign's only decision-grade win over the teacher

[FINDING] The recommendation at the end of the 2026-07-29 C2 entry -- "next arm: select mixing on a GRU encoder, because C2 and A0g win on DIFFERENT axes" -- was already executed as arm C3 before this lead was re-read; the arm question is therefore closed, and the result is stronger than "combine two partial wins": C3 is the first arm in the campaign to beat the TEACHER by a decision-grade margin at any DR level.

[EVIDENCE] Arm C3 = trpo_sdeint_c3_gruselect_s30_260729_193732, ran 2026-07-29, analysis diagnose-20260729-200134. Its checkpoint cfg confirms the exact proposed combination (encoder_type gru, dagger_mix select, gru_hidden 128, gru_head_hidden 64), verified by loading student_999.pt on 2026-07-30. Report findings: hard att_norm 0.5652 vs teacher 0.7189 = -0.1537 deg against the declared 0.1 deg floor (next-best student margin over the teacher at hard is A0g's -0.0693, sub-floor); the hard win is carried by BOTH axes independently (C3 roll 0.4469 and pitch 0.2540 are each the campaign's lowest and each below the teacher's 0.5999 / 0.2803, where C2 owned roll but lost pitch and A0g owned pitch but lost roll -- exactly the two-axis argument this lead predicted); best in-loop latent tracking at EVERY level (C3 vs A0g -22.5/-36.0/-31.5/-18.2%, C3 vs C2 -25.8/-42.0/-18.5/-7.0%), so the encoder change and the mixing change compound rather than trade off; survival 100% at all four levels; and it is the campaign's CHEAPEST arm (time_train 0.082394 s vs A0g 0.088227 and C2 0.218553).

[CONFIDENCE] HIGH

Why C3 nonetheless did not displace the adopted A0g: the two baselines answer different questions. Against the TEACHER at hard the margin is decision-grade (-0.1537 deg, above the 0.1 floor). Against the INCUMBENT A0g every level is sub-floor and the easy end is marginally adverse: C3 - A0g = +0.0331 / +0.0108 / +0.0004 / -0.0844 deg across none/soft/medium/hard. C3 also gives ground on dispersion where A0g is strongest -- att_norm CV at none 53.5% vs A0g 33.2%, at medium 108.8% vs A0g 78.9% (both the campaign's worst) -- while owning the hard end (CV 132.4% and ss_jitter 0.1877 deg, each better than the teacher's 177.9% / 0.2337). So "A0g adopted, C3 a hard-only improvement" is the accurate reading; do NOT restate it as "C3 failed".

Two collateral results worth carrying, because they were produced by this arm and are not recorded on the C2 entry:
- C1-latsens's hard-level sensitivity slope, measured independently on a different arm by perturbation injection, PREDICTS C3's observed hard control gain to within 4% (C1: 1.070 deg per unit ||delta l_hat|| at hard; C3's hard in-loop MSE 0.060606 vs A0g's 0.074132 implies about 0.076 units, predicting about 0.081 deg; observed 0.0844 deg). The level ORDERING matches too, independently of magnitude. That is a cross-arm prediction confirmation of the latent-sensitivity instrument, not just another arm result.
- Under the PRE-correction reading of the P1 ratio metric C3 would have been rejected as the campaign's worst arm (lowest ratio at all four levels, 3 of 9 dims below the 0.1 threshold at none). Under the corrected reading (ratio == R2, so the target is R2) it is the best-tracking AND best-calibrated arm: aggregate R2 at hard +0.1108 vs C2 +0.0459 and A0g -0.0887, with the smallest ratio-to-R2 gap (0.188 vs 0.436 / 0.433). This arm is the sharpest single demonstration of why that metric correction mattered.

What is NOT closed by this, and where the training thread actually continues: the dispersion signal still sits on ss_error_std, for which the profile declares NO floor -- that is a profile floor-declaration decision, not an arm. And the campaign's next TRAINING arm is the nominal-corner exposure lead (roll_transient_is_worst_at_none_dr...), whose blocked-on read "sequenced after C3" and is now unblocked. C3's none-level dispersion being the campaign's worst is direct evidence for that lead, since the nominal corner is exactly where it degrades.

Status moved to resolved: no arm remains for the DAgger-mechanism question. The mechanism (dagger_mix=select) was adopted from C2, and the GRU+select combination this lead proposed has been measured.

---

## Update (2026-07-30T05:05:43.720025)

## CORRECTION 2026-07-30 (same day): the closing paragraph above named the wrong next training arm

[FINDING] The paragraph "the campaign's next TRAINING arm is the nominal-corner exposure lead, whose blocked-on read 'sequenced after C3' and is now unblocked" is WRONG and is retracted. That lead's "after C3" refers to the TEACHER canonical C3 -- the 4-arm x 3-seed ablation set deferred to the paper phase by user decision 2026-07-23 -- not to this campaign's C3/gruselect arm. The two C3s are unrelated ids that share a label.

[EVIDENCE] Resolved 2026-07-30 by three checks on the roll_transient page and PLAN.md: the sequencing note is dated 2026-07-24, before student_distill_eint existed (2026-07-29); its data is teacher-side (trpo_buoyanchor_s30_260722_134743 RT-a shared exam); and PLAN.md section 3 (line 142) lists C3 as a canonical TEACHER id, defined at 216/325/352/618 as 12 runs / ~60 h / DEFERRED to the paper phase. PLAN.md:156 already warns that C1-C3 labels double as per-document harness numbering and are excluded from the experiment-id scheme.

[CONFIDENCE] HIGH

Corrected statement of what remains after this lead closes: the DAgger-mechanism arm question is closed (mechanism adopted from C2, GRU+select measured as C3). No next training arm follows from THIS lead. The dispersion signal still sits on ss_error_std with no declared floor, which is a profile floor-declaration decision rather than an experiment. Choosing the campaign's next training arm is a separate, human-gated decision and does not fall out of this page.

