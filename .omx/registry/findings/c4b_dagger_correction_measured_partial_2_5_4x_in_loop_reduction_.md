---
title: "C4b DAgger correction measured: partial (2.5-4x in-loop reduction at low-mod DR, under-dispersion floor persists at hard)"
tags: ["dagger", "student", "distillation", "covariate-shift", "albc", "observability", "dgx", "c4b", "obs4", "phase-c", "inconclusive"]
created: 2026-07-30T06:06:14.644675
updated: 2026-08-04T15:35:29.675077
sources: ["diagnose-20260803-223517"]
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "real_albc_deployment_state_estimation_rates_measured_from_code_a.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "The observability arm this lead asked for RAN 2026-08-03 and returned INCONCLUSIVE. CORRECTED 2026-08-03 after independent review: the pre-registered statistic is anchored on C3, not on the dim=0 control, so the miss is 0.0247 = 2.54 sigma, NOT 0.0044 = 2.92 sigma. Same arm as the obs4 interface page -- count once. The 4 channels measurably reduce latent error (d6 -32.1%, dims with R2>0 going 4/9 to 7/9) but land a comfortable 0.0247 below the GO bar and cost +0.1401 deg of hard-DR roll control. The lead stays OPEN because the hypothesis was neither confirmed nor refuted. Next step is a human choice among Phase D (teacher obs76), a widened-encoder arm, a seed replicate, or recording the null."
---

# C4b DAgger correction measured: partial (2.5-4x in-loop reduction at low-mod DR, under-dispersion floor persists at hard)



C4b on-policy DAgger correction RAN on the DGX 2026-07-24 at constrained-albc be42a2f (branch exp/dagger-correction, single commit off main 88e0849). Training: TCN student, anchor teacher trpo_buoyanchor_s30_260722_134743/model_4999.pt, 4096 envs, 1000 iters, dagger_beta 1.0->0.0 linear over 600 then held, --enable_cudnn (DGX cuDNN healthy), seed 42. Runtime 19.4 min (~1.16 s/iter). beta anneal VERIFIED from tfevents: iter0=1.0, 100=0.833, 300=0.5, 500=0.167, 600=0.0, held after -- args took, STOP condition passed. Final open-loop loss_latent=0.00518 (teacher-only was 0.00493; higher as beta drops = expected self-distribution, not a regression). time_collect ~0.72-0.84 s (cuDNN on, far below the ~17 s cuDNN-off penalty). New student: logs/rsl_rl/albc_trpo_student/trpo_buoyfix_dagger_s30_tcn_260724_133040/models/student_999.pt.

STEP-4 IN-LOOP READOUT (eval.py static, 64 envs, 4 DR levels; base open-loop residual 0.002145) vs the E4 teacher-only student baseline (trpo_buoyfix_s30_tcn_260722_184632):
- none    DAgger overall_mse=0.03833 (17.9x base) vs E4 0.15584 (72.7x) -> 4.07x reduction;  l_true_envvar=0.01935  l_hat_envvar=0.00312 (ratio 0.16)
- soft    DAgger overall_mse=0.04419 (20.6x base) vs E4 0.16190 (75.5x) -> 3.66x reduction;  l_true_envvar=0.02623  l_hat_envvar=0.00321 (ratio 0.12)
- medium  DAgger overall_mse=0.06798 (31.7x base) vs E4 0.16829 (78.5x) -> 2.48x reduction;  l_true_envvar=0.04429  l_hat_envvar=0.00615 (ratio 0.14)
- hard    DAgger overall_mse=0.14794 (69.0x base) vs E4 0.17613 (82.1x) -> 1.19x reduction;  l_true_envvar=0.09473  l_hat_envvar=0.01189 (ratio 0.13)

VERDICT: INTERMEDIATE / PARTIAL (mixed cause: covariate shift is real AND DAgger-addressable, but an under-dispersion floor persists that DAgger does NOT fix).
- H1 (covariate shift, DAgger fully works) NOT met by the pre-registered signature: overall_mse is NOT below l_true_envvar at ANY level (0.038>0.019 at none, gap widens with DR), and l_hat_envvar did NOT rise toward l_true_envvar -- the l_hat/l_true ratio stayed ~0.12-0.16, essentially unchanged from E4's ~0.14-0.18. The student STILL under-disperses across envs by 6-8x.
- H2 (pure observability floor, DAgger no help) also NOT clean: at none/soft DAgger cut in-loop error 4.07x/3.66x, far more than H2's "<=2x improvement" clause. So covariate shift WAS a substantial real component -- closing the train/deploy distribution gap materially reduced closed-loop error (72.7x base -> 17.9x base at none).
- Net: the improvement is large but DR-dependent -- 4x at none, collapsing to 1.19x at hard -- and the under-dispersion failure mode (l_hat_envvar collapse) is untouched at every level. overall_mse still exceeds l_true_envvar everywhere. This is a mixed cause: partly covariate shift (DAgger helped, keep it) and partly an observability/capacity floor that worsens with DR (DAgger cannot fix it; worst at hard).

CONSEQUENCE: partial adoption. On-policy DAgger distillation is worth keeping (it demonstrably cuts closed-loop latent error 2.5-4x at low-moderate DR), but it is NOT sufficient alone for deployment: the residual cross-env under-dispersion, worst at hard DR, needs the observability angle (longer history window and/or an explicit velocity channel) as a complementary fix. No blanket deployment claim. per_dim_mse (hard: dims 5/7/3 dominate 0.286/0.254/0.182) is EXPLORATORY only per the z_sweep caveat, not a criterion.

---

## Update (2026-08-03T09:05:26.635075)


## 2026-08-03 -- the observation-interface blocker is delivered (implementation only, not yet run)

This lead has been blocked since 2026-07-30 on "an observation-interface implementation" that arm E1
needed. That implementation now exists and is pushed: obs4 Phase A on branch `exp/obs4-extraobs`
@`7c16b93` (baseline tag `baseline-260803-obs4`, 11 commits, tests 443 -> 459). Everything defaults
OFF and is byte-identical when off, so it does not disturb any existing run.

WHAT IT DELIVERS, precisely -- 4 channels published as a `student_extra` key on the observation dict
and concatenated into the student encoder input through ONE shared `student_input` function:
IMU specific force (3D, body frame, gravity included) + pressure-derived heave rate (1D, first-order
LPF over a differentiated noisy depth).

WHAT IT DOES NOT DELIVER, against this lead's own wording ("longer history window and/or an explicit
velocity channel"): it is the VELOCITY-CHANNEL half only, and even that half is partial -- heave rate
is the z axis alone. Surge/sway velocity remain unmeasurable on this robot (IMU + pressure only, no
DVL -- see [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]]). The history-window
half is untouched. So an arm built on this interface tests whether DEPLOYABLE extra observability
moves the under-dispersion floor; a null result would NOT rule out the history-window option.

The channels are zero-order held at extra_obs_hold_steps=2 because the real sensor bus publishes at
<= ~25 Hz against a 50 Hz control tick -- see
[[real_albc_deployment_state_estimation_rates_measured_from_code_a]]. That is deliberate: training at
50 Hz would validate information the robot cannot deliver.

NEXT STEP for this lead: proposal B2-extraobs (one variable, extra_obs_dim 0 -> 4 plus
use_student_extra_obs=True, against the C3 recipe), then a human-gated launch. The read-out that
closes this lead is the same one it opened with: does l_hat_envvar / l_true_envvar rise off the
~0.12-0.16 floor, and does it rise most at hard DR where DAgger did least (1.19x).

---

## Update (2026-08-03T09:54:25.298034)


## 2026-08-03 -- the arm is designed; read the proposal before acting on this lead

Proposal `next-20260803-184816` (label `B2-extraobs`) is written, lint-clean, independently reviewed
across four rounds, and recorded as campaign intent on `student_distill_eint`. Three things in it
change how THIS page's own numbers should be read, and they matter more than the arm:

**The "under-dispersion floor" framing on this page is superseded.** The B1b correction proved
`Var(l_hat)/Var(l_true) = R2` for a calibrated predictor, so the ratio's healthy target is R2, not 1
-- a weak-but-honest predictor is REQUIRED to have a low ratio. The 0.12-0.16 ratios this page cites
as the residual failure are not by themselves a defect claim. The live quantity is R2.

**Do not rank latent dims by R2 without inspecting the denominator.** Measured on C3 at hard: d6's
R2 is -0.432 but its in-loop MSE (0.0546) is the SECOND-LOWEST of all nine dims -- its R2 is worst
because its target variance is second-smallest. d2's R2 is negative while it is the BEST-tracked dim
in the entire latent (MSE 0.0016, 34x below the next). The only dim that is a failure in absolute
terms is d4 (MSE 0.0849, highest of nine). Two successive drafts of the proposal made this mistake
before it was caught.

**The run-to-run noise scale is measurable for free and it is large.** Resampling the 64 eval envs in
`latent_hard.npz` gives sd 0.038 on aggregate hard R2 at 64 envs (env-draw only -- a LOWER bound),
so a B2-minus-C3 difference has sd 0.053 if the two evals draw independent env sets. Of the five
negative dims only d6 has a deficit larger than its own noise (3.5 sigma; d4 1.5, d2 0.7, d8 0.2,
d3 0.1). A single-seed screening run therefore cannot cleanly separate "the channels help" from
"they do not" unless the effect is large -- the proposal states this rather than hiding it in a band.

---

## Update (2026-08-03T10:45:53.656856)


### 2026-08-03 -- prerequisite cleared; only the human gate remains

B0 is done (commit `d81e2fd`): `eval.py` now records the extra channels and the bite check that
guards this arm's verdict can actually execute. The instrument was proven unperturbed rather than
assumed -- re-running C3's own eval under the patched code reproduces all four `latent_*.npz`, all
four `data_*.npz`, `summary.json` and `summary_latent.json` bit-identically to the stored
2026-07-29 artifacts, so a B2-vs-C3 comparison does not span an instrument change.

Two corrections from that work bear on how this lead's own numbers should be read. First, the heave
channel's noise floor as originally specified was 1.985x too high, which would have made a
100%-noise channel look usable-adjacent; that is the same units-from-the-label failure that the
ratio-vs-R2 confusion on this page already cost the campaign once. Second, `nn.GRU` uses cuDNN via
its RNN kernels, so the eval step needs the `LD_LIBRARY_PATH` preamble on this workstation even
though there is no `Conv1d` anywhere in the student -- `train_student.py` hides this by disabling
cuDNN by default while `eval.py` has no such guard.

---

## Update (2026-08-03T13:54:59.336112)

UPDATE 2026-08-03: the observability angle was tested and is still open.

The channels that were supposed to close the gap this lead identified do carry real information --
in-loop latent MSE falls on five of nine dims, the pre-registered worst-deficit dim d6 by 32.1%, and
the training-side loss agrees at -5.9%. But the effect does not clear the bar that was set before the
run, and it comes with a control cost the lead did not anticipate.

WHAT THIS SPECIFICALLY MEANS FOR THE UNDER-DISPERSION FLOOR AT HARD. The floor is NOT purely an
information limit: adding the whole deployable sensor set moved the aggregate only +2.92 sigma. Nor
is it purely a training limit: five config axes had already failed to move it and these channels did.
The per-dim pattern -- five dims better, four worse, inside an unwidened 128-unit GRU -- suggests the
information lane and the capacity lane are BOTH live rather than one being the answer.

AN IMPORTANT NEGATIVE, pre-registered and therefore worth keeping: d4 is the only dim that is an
absolute-error failure (highest MSE of the nine on a mid-range variance), and the channels made it
6.3% WORSE. Whatever d4's deficit is, it is not an observability deficit. Do not spend another
observation-side arm on d4.

STILL UNADDRESSED BY THIS ARM: the history-window half of this lead's ask, and xy velocity (no DVL,
structurally unavailable). B2 holds only its own four channels at 25 Hz; it does NOT address the
staleness of the main 72D observation vector, which belongs to the latency/transport-delay lead.

---

## Update (2026-08-03T14:11:06.239650)

## Correction 2026-08-03: the observability arm's sigma was anchored on the wrong arm

The Phase C figure this lead was updated with on 2026-08-03 ("0.0044 below the 3-sigma bar") used the
dim=0 control as the anchor. The pre-registration anchors on C3. Corrected: B2's aggregate hard R2
of +0.2460 misses the GO bar of +0.2707 by 0.0247, which is 2.54 sigma from C3, not 2.92.

This does not change what this lead is waiting for -- the arm was and remains INCONCLUSIVE -- but it
removes the "almost cleared the bar" reading that a follow-up in the same direction would have leaned on.

---

## Update (2026-08-04T15:35:29.675077)

## VERDICT 2026-08-05 -- CLOSED-NULL (backlog-closeout program)

The observability arm this lead asked for RAN on 2026-08-03 and returned a measured miss, not an
unanswered question. Against the pre-registered C3 anchor the shortfall is 0.0247 (2.54 sigma)
below the GO bar, and the four channels cost +0.1401 deg of hard-DR roll control. The channels
do measurably reduce latent error (d6 -32.1 percent, dims with positive R2 going 4/9 to 7/9),
but a latent gain that does not reach control is exactly the pattern X1-tailsplit later
confirmed: +0.169 R2 bought zero control improvement.

Two further arms ran after this lead was written and neither rescued it. Phase D put the four
channels in the TEACHER (trpo_obs76fault_s30_260804_043926): the obs76 teacher is genuinely a
better controller at hard DR, but none of that advantage survives distillation to any student.
X1-tailsplit isolated the delivery path and closed the latent gap without moving control.

The remaining options named on this page were a seed replicate (excluded by the standing
single-seed screening rule) and a widened-encoder arm (the obs76 page carries that question and
requires it to pre-register a CONTROL endpoint). Recording the null is therefore the correct
close: the hypothesis was tested three ways and did not clear its own bar. obs72 stays default.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

