---
title: "obs4 student extra-observation interface: 4 deployable channels ride the observation dict through ONE shared student_input, zero-order held at the real 25 Hz bus rate; implemented and pushed 2026-08-03, not yet run"
tags: ["obs4", "student-extra-obs", "observation-interface", "zero-order-hold", "imu", "pressure", "distillation", "phase-b", "phase-c", "inconclusive"]
created: 2026-08-03T09:06:21.064863
updated: 2026-08-03T14:11:06.139256
sources: ["diagnose-20260803-223517"]
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "albc_cudnn_fix_is_a_library_path_not_a_package.md", "real_albc_deployment_state_estimation_rates_measured_from_code_a.md", "c4b_dagger_correction_measured_partial_2_5_4x_in_loop_reduction.md", "container_cudnn_is_cu13_against_cu128_torch_every_conv1d_fails_s.md", "feedback_read_metric_units_from_code.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: needs-experiment
blocked-on: "RAN 2026-08-03, INCONCLUSIVE. CORRECTED 2026-08-03 after independent review: the earlier 'misses the 3-sigma bar by 0.0044' figure was computed against the dim=0 CONTROL, which postdates the pre-registration. The pre-registration's decision table partitions B2's ABSOLUTE aggregate hard R2 with C3's own value (+0.1108) as the INCONCLUSIVE floor. On that literal statistic B2 = +0.2460 sits in [+0.1108, +0.2707) and misses GO by 0.0247 = 2.54 sigma, NOT 0.0044 = 2.92 sigma. Same band either way, but the near-miss was overstated 5.6x, so any 'it almost cleared, push harder' argument is unsupported. Also cost +0.1401 deg of hard-DR roll control past its 0.1 floor, and the pre-registered d4 corroboration FAILED. Blocked on the human choice among Phase D (teacher obs76, the only path that opens deployment since deploy specs reject gen-1), a widened-encoder arm, or recording the null."
---

# obs4 student extra-observation interface: 4 deployable channels ride the observation dict through ONE shared student_input, zero-order held at the real 25 Hz bus rate; implemented and pushed 2026-08-03, not yet run

The student distillation path can now take 4 extra observation channels that the real robot can
actually produce. Implemented as obs4 Phase A on branch `exp/obs4-extraobs` @`7c16b93` (baseline tag
`baseline-260803-obs4`, 11 commits, tests 443 -> 459, every task independently reviewed plus one
whole-branch fix wave). `main` is untouched. Plan and full task list:
`/workspace/.sp/plans/2026-08-03-obs4-student-then-teacher76-program.md`.

## The channels, and why exactly these 4

IMU specific force `a_imu_b = R_wb^T (a_w - g_w)` (3D, body frame, gravity INCLUDED because that is
what an accelerometer reads) + pressure-derived heave rate (1D, first-order LPF over a differentiated
noisy depth). Not a design preference -- it is the whole deployable set. The robot carries IMU and
pressure only, no DVL, so surge/sway velocity cannot be added no matter how useful it would be
([[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]]).

## Four decisions worth not re-deriving

**Transport = a key on the observation dict** (`observations["student_extra"]`), NOT an env attribute
written by a per-step push. The alternative is dead. `RslRlVecEnvWrapper` TensorDict-wraps the WHOLE
dict returned by `_get_observations()` with no key filtering, so a third key rides through untouched
-- VERIFIED on a real Isaac boot (4 envs, GPU0: the third key was accepted, channel[2] read 9.810 at
reset, and the zero-order-hold pairs were visible in the step stream). The env-attribute route would
have needed a push site in every consumer.

**Every encoder forward goes through ONE shared `student_input`** in `_core/student/models.py`. There
are FOUR forward sites -- DAgger collect, the GRU training loss, the end-of-rollout hidden recompute,
and eval in-loop -- and the fourth is the one a reader misses. This is the structural answer to the
`38d979e` class of bug (an eval-side copy of a training forward that silently dropped normalization
and invalidated two months of in-loop verdicts): divergence is impossible when there is one function,
so the test only has to prove routing. An AST gate over the shipped source enforces it
(`tests/test_student_extra_parity.py`), written as (must_route, allowed_unrouted) rather than a flat
set equality so that `_compute_loss_tcn` legitimately calling the encoder does not trip it.

**GRU only.** The TCN path is deliberately unwidened and raises rather than silently accepting a
mismatched width. GRU is the adopted student anyway (arm A0g). Related: the cuDNN `LD_LIBRARY_PATH`
preamble is a TCN concern only -- `StudentEncoderGRU` has no Conv1d
([[albc_cudnn_fix_is_a_library_path_not_a_package]] if that page exists; the fix is Isaac's own
prebundled cu12 cuDNN first on the path).

**Zero-order hold, `extra_obs_hold_steps=2`.** The load-bearing physical decision. Every channel these
4 derive from arrives on `/hero_agent/sensors` at <= ~25 Hz against a 50 Hz control tick
([[real_albc_deployment_state_estimation_rates_measured_from_code_a]]). Training them fresh at 50 Hz
would validate information the robot cannot deliver. The exact rate is recoverable from any real bag
(firmware ships `loop_speed` in the sensors DEPTH field; rate = loop_speed/4) -- re-set the knob once
such a bag exists, do not guess it away.

## Two failure modes that were designed out

The four sensor params (`use_student_extra_obs`, `depth_noise_std`, `heave_lag_tau`,
`accel_noise_std`, `extra_obs_hold_steps`) are persisted into the student checkpoint as
`env_sensor_cfg` and restored by `eval.py` before `gym.make`. Without that, training at hold=4 and
evaluating at hold=2 mismeasures with no error -- the same silent-divergence shape as 38d979e, one
layer out. Old checkpoints without the field still load, with a `[WARN]`.

Everything defaults OFF and the OFF path was proven not to consume any RNG, so existing seeded runs
stay bit-reproducible and the feature can sit on the branch indefinitely without contaminating a
comparison.

## Carry this into the B2 proposal

With `depth_noise_std=0.01` the ON and OFF arms draw different RNG, so B2 vs C3 is a
DISTRIBUTION-LEVEL comparison, not "the same trajectories plus four channels". Setting it to 0 buys
pairing at the cost of an unrealistically clean sensor. That trade-off is a pre-registration decision,
not an implementation detail. The lead this arm closes is
[[c4b_dagger_correction_measured_partial_2_5_4x_in_loop_reduction_]] -- its read-out is whether
`l_hat_envvar / l_true_envvar` rises off the ~0.12-0.16 floor, most at hard DR where DAgger did least.
Deploy export refuses gen-1 extra-obs students in BOTH spec files, so nothing half-wired can ship.

---

## Update (2026-08-03T09:07:04.300885)


### Correction (same day): cuDNN link

The cuDNN page referenced above is
[[container_cudnn_is_cu13_against_cu128_torch_every_conv1d_fails_s]] -- the earlier bracket in this
page named an auto-memory slug, not a wiki slug, and hedged on its existence. The claim itself stands:
the preamble is a TCN concern only because `StudentEncoderGRU` contains no Conv1d, and the fix is a
library path (Isaac's own prebundled cu12 cuDNN ahead of the container's cu13), not a package install.

---

## Update (2026-08-03T09:08:57.106332)


### Where the implementation record lives

Per-task briefs, implementer reports, every independent review verdict, and the whole-branch fix-wave
report are under
`constrained-albc/.superpowers/sdd/2026-08-03-obs4-student-then-teacher76-program/` (git-ignored
scratch, so it dies with the working tree -- read it before deleting the branch). The reviewed defect
list, including the three test gates that passed or failed for the wrong reason, is in the plan's
Review log table.

---

## Update (2026-08-03T09:54:42.683163)


### B0 -- the missing eval-side dump (found 2026-08-03 during proposal review)

The interface is complete on the TRAINING side and gated on the eval side, but nothing records the
four channels for inspection. `eval.py` writes `latent_<level>.npz` = {`l_hat`, `l_true`} and
`data_<level>.npz` = attitude/DR/joint arrays; `student_extra` appears in it only in the `env_cfg`
setup block. So the four-point bite check the arm depends on -- nonzero, time-varying, channel[2]
near +9.81, and consecutive samples repeating in PAIRS at `extra_obs_hold_steps=2` -- has no data
source. That is the E2-delay failure reproduced inside the gate written to prevent it.

B0 adds a `student_extra` capture alongside the existing latent dump. **Its definition of done
includes proving the instrument unperturbed**: re-run C3's eval from the same checkpoint under the
patched `eval.py` and confirm `latent_hard.npz` is numerically unchanged. C3's baseline came from the
unpatched instrument and B2's would come from the patched one, so the contrast spans an instrument
change -- and `38d979e` is what that costs when it is asserted instead of checked.

Eval-side rather than training-side because eval is the only side carrying the `env_sensor_cfg`
restore path, the one genuine train/eval divergence risk; the transfer argument is that both sides
call the same `compute_student_extra_obs` on the same cfg with the same env-global `_extra_tick`.

---

## Update (2026-08-03T10:45:38.859259)


### CORRECTION: nn.GRU DOES use cuDNN -- "no Conv1d" was the wrong reason

An earlier section of this page said the cuDNN `LD_LIBRARY_PATH` preamble is "a TCN concern only"
because `StudentEncoderGRU` has no `Conv1d`. **That is a non-sequitur and it is now measured wrong.**
`Conv1d` is not the only cuDNN consumer: `nn.GRU` calls `torch._cudnn_rnn_flatten_weight` inside
`flatten_parameters()` as soon as the module is moved with `.to(device)`.

Measured 2026-08-03 on the workstation: `eval.py static --encoder_type gru` dies at
`student_policy.py:93 make_student_encoder(cfg).to(device)` with
`RuntimeError: cuDNN error: CUDNN_STATUS_NOT_INITIALIZED`, and completes with

    LD_LIBRARY_PATH=/isaac-sim/exts/omni.isaac.ml_archive/pip_prebundle/nvidia/cudnn/lib:$LD_LIBRARY_PATH

**The two paths are protected asymmetrically, which is why nobody hit this.** `train_student.py`
disables cuDNN by DEFAULT (`--enable_cudnn` off => `torch.backends.cudnn.enabled = False`, lines
145-146) as the documented workstation workaround, so TRAINING is safe. `eval.py` has **no cuDNN
handling at all** (zero occurrences), so EVAL is not. The gap is pre-existing and hits every
GRU-student eval on this host, not just the obs4 arm. See
[[container_cudnn_is_cu13_against_cu128_torch_every_conv1d_fails_s]] -- that page's title says
"every conv1d fails", which is narrower than the truth: cuDNN cannot INITIALIZE here, so every
cuDNN consumer fails, RNN kernels included.

### Two metric defects found while building B0, both "the number does not mean its name"

**`time_varying` judged against zero.** numpy's `std` over identical values returns ~1e-16 (float64)
or ~1e-6 (float32), never exactly 0.0, so a `> 0` test PASSES on a genuinely frozen channel. Now
judged relative to the channel's own magnitude.

**The heave noise floor was 1.985x too high.** Taking it as `depth_noise_std / sensor_dt` (0.250)
ignores the `sqrt(2)` from differencing two INDEPENDENT depth samples AND the first-order LPF, with
the MA(1) correlation the differencing creates. Simulating the producer's real chain gives **0.126**.
Under the wrong floor a channel that is 100% noise scored 0.504 and a usable channel at s/n 1.5 read
as "below its own noise" -- and the proposal pre-registers a threshold on this number, so the unit
error would have produced a wrong verdict rather than a noisy one. Same class as
[[feedback_read_metric_units_from_code]] if that page exists in this wiki; the general rule is that a
derived quantity's units come from the arithmetic that computes it, never from its label.

---

## Update (2026-08-03T13:54:37.300266)

UPDATE 2026-08-03: the arm RAN. Phase B and Phase C are complete; this page's title still says
"not yet run" only because the title is the append-merge key.

WHAT RAN. B2 = trpo_sdeint_b2_extraobs_s30_260803_215117 (extra_obs_dim 4, env.use_student_extra_obs
True, extra_obs_hold_steps 2, otherwise C3's recipe: GRU, select, fixed beta 0.5, seed 30, 2048 envs,
frozen E-int teacher). A dim=0 control on the same commit d81e2fd was added because C3's manifest is
dirty:true on a deleted worktree; the control also settled that doubt (see the C3 provenance page).

BOTH PRE-REGISTERED GATES PASSED. Bite check: all four channels nonzero and time-varying with zero
degenerate envs at every DR level, gravity mean 9.338 (convention held), repeat fraction 0.49987
against an expected 0.5 so the 25 Hz hold is physically present, heave_snr 2.227 / 2.456 / 3.218 /
4.214 across none / soft / medium / hard -- monotone in DR difficulty, so the channel is most
informative exactly where latent fidelity is decision-grade. Not VOID.

RESULT. Against the dim=0 control, aggregate hard latent R2 +0.0905 -> +0.2460, delta +0.1555 =
+2.92 sigma against the 3-sigma GO bar of +0.1599. Both estimators agree on the band, so no demotion.
The channels DO carry information: d6 MSE -32.1%, d7 -37.0%, d8 -58.0%, dims with R2>0 rising 4/9 to
7/9, and the training-side loss_latent independently -5.9%. Three caveats sit against that: roughly
40% of the aggregate delta is denominator movement rather than error reduction; the pre-registered
d4 corroboration FAILED (d4 got 6.3% worse); and hard-DR att_norm ss_error regressed +0.1401 deg past
its own 0.1 floor, roll-specific (n_gt20 4.67 -> 7.00) while pitch and yaw improved.

DELIVERED SCOPE, unchanged: only the velocity-channel half of the c4b ask (heave rate, z only). The
history-window half is untouched and xy velocity stays unavailable (no DVL).

TWO LIVE READINGS OF THE HARD REGRESSION, which point at different next arms. (a) Capacity crowding:
four inputs added to an unwidened 128-unit GRU produced a redistribution, five dims better and four
worse -- test with a widened encoder for 13 minutes. (b) Frozen-actor mismatch: the actor was trained
on the teacher's z distribution and never saw this student's shifted l_hat; the regression
concentrating at hard is consistent with C1-latsens measuring actor latent sensitivity 4x higher
there than elsewhere, and only gen-2 (teacher obs76) removes that asymmetry. Both are live; the
report marks the capacity reading MED, not established.

---

## Update (2026-08-03T14:11:06.139256)

## Correction 2026-08-03 (post-review): the pre-registered anchor is C3, not the control

An independent review of the Phase C report found the headline sigma was computed against
trpo_sdeint_b2ctl_dim0_s30_260803_220234 (the dim=0 control), an arm added AFTER the pre-registration
was written and originally scoped only to test C3's dirty-tree provenance.

The pre-registration's "Outcome regions" table does not take a delta at all. It partitions B2's own
absolute aggregate hard R2 into bands whose INCONCLUSIVE floor IS C3's aggregate R2, and its sigma
column is headed "Sigma from C3".

| anchor | status | B2 delta (est A) | sigma | miss vs GO | band |
|:--|:--|--:|--:|--:|:--|
| C3 +0.1108 | PRE-REGISTERED | +0.1352 | +2.54 | 0.0247 | INCONCLUSIVE |
| CTL +0.0905 | supplementary | +0.1555 | +2.92 | 0.0044 | INCONCLUSIVE |

The categorical verdict is unchanged, and the control remains the better-matched comparison (same commit,
paired against C3). What changes is the narrative: 0.0247 is a comfortable miss, not a razor-thin one.

The generalizable lesson, which is why this correction is recorded rather than silently applied: when a
control arm is added to a pre-registered experiment after the fact, it does not inherit the
pre-registration's decision table. Report the literal pre-registered statistic first and the better-controlled
one as a supplement, and state the gap between them. Both reports were re-authored through the
exp-analyze RE-analysis path to carry both anchors side by side.

