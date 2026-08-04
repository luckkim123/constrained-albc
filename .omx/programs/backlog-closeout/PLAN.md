# Backlog closeout — drive every open omx lead to a recorded verdict by 2026-08-05 24:00 KST

**Opened**: 2026-08-05 00:30 KST. **Owner directive** (verbatim intent): *"니가 알아서 내일까지 전부 다
실험 하고 해소해. 나한테 일일이 승인받을 필요없이 니가 알아서 해. … 내일 최종 결과가 나오고 나면
다시는 뭐가 남았습니다 하지 말라."*

**This document exists to survive context compaction.** A session resuming from it needs nothing else
except the files it points at. Read §0 first.

---

## 0. Standing authority and the definition of done (read before acting)

**Authority granted 2026-08-05 by the user, superseding the prior gate.** Training launches no longer
require per-run human approval. The previous standing rule — *"훈련 런을 자동 실행하지 말 것, 사람
승인 게이트다"* — is **explicitly overridden for this program only**, by a direct instruction the user
reaffirmed after being told the backlog was large. Launch what this plan schedules. Do not go back and
ask. Do not extend the authority to anything outside this plan (in particular: `git push`, the DGX
flagship send, and any hardware action all stay user-gated).

**Deadline: 2026-08-05 24:00 KST — HARD.** The user clarified this explicitly at 00:30 on 08-05
("내가 내일이라고 한건 오늘 자정까지 말한거다. 8월 5일 24시까지"). There is no 08-06 slack. From
01:25 (Koopman arm B exits) that is **~22.5 GPU0-hours**, and a teacher run at 4096 envs / 5000 iters
costs ~5 h. Four runs would fit arithmetically and leave two hours for the closeout, which one crash
erases — so the plan is **three GPU0 runs plus a seven-hour finishing window**, with a fourth added
only if Runs A and B both land clean and early. Scope is cut to fit the clock, not the other way
round; §3 says which leads close by verdict rather than by experiment precisely so this fits.

**Definition of done — the only acceptable end state.** Both of these return zero rows:

```bash
omx wiki list --status needs-experiment --root /workspace/constrained-albc
omx wiki list --status needs-apply-before-retrain --root /workspace/constrained-albc
```

Every lead ends in one of: **RESOLVED** (question answered), **CLOSED-NULL** (answered negative),
**CLOSED-OUT-OF-SCOPE** (deliberately not pursued, with the reason recorded), or **DEFERRED-HARDWARE**
(cannot progress without a bench/robot measurement, moved off the experiment queue). A lead left at
`needs-experiment` at the end is a failure of this program.

**Why the user is angry, so it does not repeat.** Prior sessions closed the RL *campaign* and reported
"experiments are done" while leaving 17 leads open in the wiki. The campaign and the ledger were
treated as separate; to the user they were one promise. From here on, "done" means the ledger is
empty, not that a campaign concluded.

---

## 1. User decisions already made (do not re-litigate, do not re-ask)

| Decision | Date | Consequence |
|:--|:--|:--|
| **Stonefish is dropped entirely** ("환경이 너무 다른 것 같다") | 2026-08-05 | Every lead whose purpose was Isaac↔Stonefish alignment dies. Do not design Stonefish probes. Do not cite Stonefish measurements as targets. |
| **Hardware-measurement items are skipped** ("실물을 재봐야 푸는 것은 그냥 넘어가자") | 2026-08-05 | T200 bench curve, XW540 step response, IMU pitch-negation, TAM CAD tolerance, m4 remeasure — all move to DEFERRED-HARDWARE, off the experiment queue. |
| Screening stays single-seed | standing | No seed replicates. Do not propose them. |
| DGX flagship `max_iterations` deferred pending the iter-budget run | 2026-08-04 | Run A below is what unblocks it. |

---

## 2. In-flight right now

**Koopman arm B** — `trpo_koopmanB_260804_202709`, PID **375807**, GPU0, 4096 envs, 5000 iters.
At 00:24 it was at iter 3984/5000, ETA ~59 min → expect exit ~01:25 KST.

Design, provenance, pre-registration and the exact eval command live in
`experiments/rsl_rl/albc_trpo_teacher/koopman_marine_obs/DESIGN.md`. **Read that file, do not
reconstruct it.** Key facts a compacted session will otherwise lose:

- Eval runs on **GPU1** (user instruction 2026-08-05) and **must** pass
  `--doraemon-dr-from logs/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102`
  — without the anchor each run is graded on its own learned DR and the 4-level verdict is meaningless.
  Anchor verified by reproduction (`eval/static_260804_203719` matches baseline `static_260804_143234`
  on 24/24 dr keys at all four levels).
- Baseline of record: `trpo_eint_s30_rs2350_260727_195102` eval `static_260804_143234` (post-pairing-fix).
- No `--output_dir`; checkpoint path through the `train` symlink. Both traps are in `.claude/rules/03`.
- Pre-registered verdict: ADOPT iff `ss_error` improves >0.10 deg on ≥2 of 4 DR levels AND
  `os_env_mean` within 10.0 pp AND `n_gt20` within 15. Otherwise NULL → close the Koopman line
  per `koopman-lifting/PLAN.md` §8. Expectation is NULL.

**Sequence when it exits**: `scripts/finalize_run_log.sh koopmanB` → eval on GPU1 (above) → verify
pairing 24/24 vs baseline → exp-analyze report → record verdict → close the Koopman program.
**GPU0 must be handed to Run A immediately; do not let it idle waiting for the eval.**

---

## 3. Lead disposition — all 17, with the action that closes each

### 3a. CLOSE by verdict, zero GPU (8 leads)

| Lead | Verdict to record |
|:--|:--|
| `stonefish_yaw_gap_claim_review…` | CLOSED-OUT-OF-SCOPE — purpose was Isaac↔Stonefish arm-actuator alignment; Stonefish dropped 2026-08-05. |
| `thruster_static_gain_gap…` | CLOSED-OUT-OF-SCOPE — the gap was *Stonefish 20.03 N vs Isaac*; with Stonefish gone the comparison has no second side. Residual "is Isaac's gain right" needs the T200 bench → DEFERRED-HARDWARE. |
| `stonefish_rotational_drag…` | CLOSED-OUT-OF-SCOPE — Stonefish-side mesh/ellipsoid question. The Isaac-side damping question survives inside `hydrorc_016d1b1`, do not duplicate it. |
| `thruster_nonlinear_curve_t200…` | DEFERRED-HARDWARE — its own 2026-07-02 decision keeps `enable_thrust_curve=False` until measured; user skipped measurement. |
| `imu_45deg_offset…` | DEFERRED-HARDWARE — user already deferred it 2026-07-20 pending a real-robot convention measurement; zero sim-side impact meanwhile. |
| `tam_vertical…` | DEFERRED-HARDWARE — blocked on m4 remeasurement (hardware fault). |
| `sim_hydro_nominal…` | DEFERRED-HARDWARE — only the TAM moment-arm band remains and it needs a CAD/bracket source. The max_thrust half already closed 2026-07-27. |
| `c4b_dagger_correction…` | CLOSED-NULL — the arm ran 2026-08-03 and missed the GO bar by 0.0247 (2.54σ) while costing +0.1401 deg hard roll; Phase D and X1 both ran afterwards and neither rescued it. Seed replicate excluded by the standing single-seed rule. |

### 3b. RESOLVE by cheap measurement, GPU1 evals (3 leads)

These three are the "needs-apply-before-retrain" plant items. **Do not blindly apply them** — applying
changes the plant and voids E-int as the comparison baseline for the DGX flagship. Instead measure
whether the policy is even sensitive to the error, then record an evidence-backed verdict.

| Lead | Action |
|:--|:--|
| `buoy_added_mass…` | Run an eval of E-int's `model_4999.pt` under the CORRECTED geometric added mass (broadside ~2.0, axial ~1.6 kg) vs the current value, same anchor, GPU1, ~15 min each. If deltas are sub-floor → CLOSED-NULL "known model error, policy insensitive, accepted for gen-1". If supra-floor → that is a real finding: record it and fold the fix into Run B. |
| `hydrorc_016d1b1…` | Same treatment. Derive the corrected damping per axis from geometry/literature (desk work, no GPU), then eval E-int under corrected vs current. Verdict by the same rule. |
| `hydrorc_is_half_recentered…` | Subsumed by the two above once Stonefish is removed from its blocker list. Record as RESOLVED-BY pointing at whichever of the two covers it; do not run a third eval. |

### 3c. TRAINING runs, GPU0 (4 leads → 2 runs)

| Lead | Folded into |
|:--|:--|
| `curriculum_recalibration_protocol…` | **Run A** — the iter-budget run measures exactly the saturation question this lead's Step 0 left open on the current plant. |
| `reward_sigma…` (R6) | **Run B** — the page itself says "fold into the sim-to-real retrain batch". |
| `roll_transient…` (nominal-corner exposure) | **Run B** — DORAEMON nominal sampling floor. |
| `experiment_idea_latency…` | **Run C** if time allows; otherwise CLOSED-OUT-OF-SCOPE with the blocker stated (needs a `_PARAM_DEFS` dim or a measured `performance_lb` recalibration — a code change this program has no room to validate). Decide at the Run B checkpoint. |

### 3d. DROP with a recorded reason (2 leads)

| Lead | Reason |
|:--|:--|
| `joint1_stage_1_gate…` (Stage 2) | CLOSED-OUT-OF-SCOPE — needs a prerequisite station-keeping policy on unlimited joint1 physics (2-run chain) and the shipped task is attitude-only, so arm drift does not bound the deliverable. Stage 1's verdict (drift is real, wall-artifact refuted) stands and is the durable result. Reopen when arm manipulation becomes the task. |
| `the_obs76_teacher…` (distillation gap) | Attempt a student arm on GPU1 **only if** it fits alongside the GPU0 queue (student runs are cheap; GRU never hit the cuDNN conv1d bug). Any arm must pre-register a CONTROL endpoint, not a latent one — X1 proved latent gains need not transfer. If it does not fit, CLOSED-OUT-OF-SCOPE recording that all five measured students land at 2.5–3.1 deg hard roll dispersion regardless of teacher, i.e. the ceiling is the distillation step and gen-1 ships as-is. |

---

## 4. Run schedule (GPU0 serial, GPU1 parallel)

All times KST on 2026-08-05. The 17:00 line is a **hard cutoff for starting anything on GPU0** — a run
begun after it cannot finish, be evaluated and be written up before midnight.

| When | GPU0 | GPU1 |
|:--|:--|:--|
| ~01:25 | Koopman arm B exits → hand GPU0 to Run A **immediately**, do not wait on its eval | Koopman arm B eval (anchored, ~15 min), then its report |
| 01:30–06:30 | **Run A — iter-budget preflight** (~4.9 h) | buoy added-mass sensitivity evals; HydroRC derivation (desk); the eight §3a verdicts written to the wiki |
| 06:40–11:40 | **Run B — batch retrain** (~5 h) | HydroRC sensitivity evals; Run A analysis + DGX Gate A correction |
| 11:50–16:50 | **Run C** — latency-DR *or* the distillation student arm, whichever the Run B checkpoint says is worth more | Run B eval + analysis |
| 17:00–24:00 | *(4th run ONLY if A and B both landed early and clean — otherwise GPU0 idle)* | Run C eval, all remaining reports, wiki closeout, final deliverable |

**Slip rule.** If Run A overruns past 07:00 or crashes, drop Run C and keep Runs A+B only. If Run B
overruns past 12:30, drop Run C outright. The closeout report and an empty ledger are the deliverable;
an extra experiment that leaves the ledger open is worth nothing here.

**Run A is already fully specified** in `/workspace/.sp/plans/2026-08-05-preflight-iter-budget-launch.md`
— launch command, plant-verification diff, the three questions it answers, and five instrument traps.
Follow it verbatim; do not redesign it. Preconditions verified 2026-08-05 00:30: `RESUME_SRC` resolves
to E-int and both `model_4999.pt` and `doraemon_state.pt` are present. The only blocking precondition
left is arm B's exit.

**Run A is non-negotiable** because two things wait on it: the DGX flagship's `max_iterations` choice,
and Gate A in `.omx/programs/dgx-final-scaleup/HANDOFF-DGX.md`, which currently carries a saturation
iteration (6750) derived from the **retired posttam plant** and must be replaced with a measured value
before that handoff is sent.

**Run B composition** (decide finally at ~06:00, after Run A's mid-run read): a single arm carrying the
parked reward/curriculum items together — decoupled `integral_gate_threshold` (R6) plus the DORAEMON
nominal-corner floor — judged as a **package** against E-int on the shared anchor. Combining is
deliberate and authorized: both were parked *for* a batch, and if the package clears the floor it is
adopted wholesale, while if it fails the components get decomposed only if the user asks. Record the
package composition in the campaign DESIGN.md before launch.

---

## 5. Protocol traps that have already cost this project runs

- **`env.fault.enable=True` is mandatory on every teacher launch.** The cfg default is `False` and
  `--resume` restores weights only. Omitting it silently trains a fault-disabled plant — the diff that
  voided a 4.9 h run and made `trpo_obs76_s30_260803_233239` VOID.
- **Every cross-run eval needs `--doraemon-dr-from <E-int log dir>`.** Default `--doraemon-dr=True`
  grades each run on its own learned DR; only `none` is anchor-invariant.
- **No `--output_dir`; checkpoint via the `train` symlink.** Otherwise output scatters out of
  `experiments/<run_id>/eval/`.
- **Verify the plant by diffing the run's dumped `env.yaml` against E-int's, in full.** Not by sha, not
  by branch topology. E-int ran `dirty: true`, and a committed-diff check already missed `fault.enable`.
- **A relaunch mints a new run id** — re-derive it from disk and update every watcher/report that keyed
  on the old one.
- **Watcher discipline**: poll the training PID directly (a `pgrep` pattern self-matches) and scope any
  NaN grep to metric lines only. Both mistakes have silently killed watchers here.
- **`DORAEMON/kl_step` is 0.0 on every non-boundary iteration** — scan all steps, never a fixed stride.
- **Do not `git add -A`**; another session may share this tree. Stage explicit paths.
- **Report `sumMSE`/`sumVar` beside any R² delta, and convert a proxy delta to its objective-side
  prediction before pricing it.** A +0.169 R² swing was only a 6.69% RMSE cut and a sub-floor control
  null was the *prediction*, not a discovery — two sessions independently got this wrong on 2026-08-04.

---

## 6. Context discipline

Analysis, report authoring and review go to **subagents** (user authorized 2026-08-05). The main
session keeps: the schedule, launch decisions, verdicts, and the wiki closeout. Do not read whole
eval dumps or transcripts into the main context — dispatch and keep the conclusion.

## 7. Decisions taken under the authority grant (append-only, newest last)

**2026-08-05 00:40 — GPU0 handoff armed.** A watcher polls arm B's PID directly (a `pgrep`
pattern self-matches, which has silently killed watchers here) and launches Run A the moment
it exits, so GPU0 never idles waiting for a human or for arm B's eval.

**2026-08-05 00:45 — nine leads closed by verdict, no GPU.** Section 3a's eight plus joint1
Stage-2 from 3d. Open backlog 17 -> 8. Two of the nine forked to new slugs on the first
attempt because their stored titles had drifted from their slugs (`wiki add` merges by
slugify(title)); the forks were removed through the library path gc uses and re-merged with
round-trip-verified titles. Commit `8b63074`.

**2026-08-05 00:44 — the buoy added-mass measurement is not the one section 3b assumed.**
Reading the engine changed the design. The geometric target (broadside ~2.0 kg) **cannot be
set directly**: `hydrodynamics.py:215` raises at construction when
`added_mass / body_mass >= 1.0`, and the buoy's body mass is 0.93 kg. A second, silent guard
clamps the DR-scaled coefficient at `0.95 * body_mass` on every reset
(`events.py:273`) — including at the `none` DR level, so a naive coefficient raise would have
been a silent no-op, the exact failure mode we were told to avoid. But the applied wrench is
`M_a * acc * added_mass_stability_factor` (`hydrodynamics.py:361`) and **the factor carries no
guard**, so splitting the target between coefficient and factor reaches the geometric
*effective* added mass with both guards satisfied. Two points run on GPU1 against E-int, with
rotational terms held byte-equal so only translational added mass moves:
`x2` (0.7 * 0.8) and `geometric` (0.5 * 4.0 = 2.0 surge/sway, 0.4 * 4.0 = 1.6 heave).
Baseline needs no run — `eval/static_260804_203719` is the same checkpoint, GPU, branch and
anchor. **Carry into the report**: effective added mass of 2.0 kg on a 0.93 kg body is what
the guard exists to forbid, so if the geometric point diverges, that IS the finding — the
explicit external-wrench formulation cannot represent the correct value at all, and the wiki
page's option (c) (move added mass into the mass matrix) is the only route. That is an engine
item, not a coefficient item.

**2026-08-05 00:49 — `hydrorc_016d1b1` gets a bracket, not a re-derivation.** Commit 016d1b1
is **not on marinelab main** (only on branch `exp/hydro-recenter`), so the damage never landed
and the shipped plant still has the pre-recenter analytical values. Its other blocker was a
question to the Stonefish side, now out of scope. What is left is only "does hull yaw damping
matter enough to justify re-deriving every axis", which a +/-10x bracket on the yaw entry
answers without a training run. Queued on GPU1 behind the buoy points.

**2026-08-05 00:50 — Run B is R6 alone; the DORAEMON nominal-corner floor is NOT implemented.**
Three reasons, in order of weight. (1) The mechanism does not exist and would have to be built:
no `nominal_floor_prob` anywhere, so it needs a new field plus forced-nominal sampling inside
`DoraemonScheduler.sample()`. (2) That change breaks the importance-sampling contract the
curriculum controller runs on — forced-nominal envs are not draws from the Beta, so either
their weights are wrong or they must be excluded from the IS buffer, and neither variant can
be validated inside this program's clock. A subtly-wrong curriculum would make Run B
uninterpretable: a bad result could not be attributed between mechanism and implementation.
(3) The lead's own page carries a 2026-07-30 retraction stating it is **not** unblocked,
because its "after C3" prerequisite is the teacher canonical ablation the user deferred to the
paper phase on 2026-07-23. Building a risky engine change to run an item its own page marks
parked is the wrong trade against a hard deadline. The lead therefore closes
CLOSED-OUT-OF-SCOPE with the mechanism recorded, which is the pruning the authority grant
explicitly asked for.

**2026-08-05 00:52 — Runs B and C are the two arms of one R6 sweep.** Design at
`experiments/rsl_rl/albc_trpo_teacher/teacher_integral_gate/DESIGN.md` (the experiments tree
is gitignored, so that file is disk-only). The wiki proposes no numeric value for R6, so a
two-point A/B would rest entirely on a guess about direction; the sweep answers direction with
data instead. Run B widens the settling band `(0.10 -> 0.20)` rad, Run C narrows it to 0.05,
and E-int is the 0.10 reference that needs no run. The widening direction is the
mechanism-motivated one: an env with a sustained offset past 5.73 deg is gated OUT of the
integral accumulator, so the policy never observes the bias that is hurting it — the envs that
most need the signal are the ones the gate silences. Both arms are CLI-only
(`env.integral_gate_threshold=[...]`), change no observation dimension, no DR box bound and no
reward scale, so the shared E-int anchor stays valid.

**2026-08-05 01:28 — Run A launched, GPU0 idle time one minute.** Arm B exited 01:27:08, the
watcher finalized its stdout and launched Run A at 01:28:08 as PID 873942, run id
`trpo_iterbudget_s30_260805_012813`. Plant verified rather than assumed: the `env.yaml` diff
against E-int is 30 lines and every one is expected — three base64 noise-model blobs differing
only in the pickled storage id (payload bytes identical), `log_dir`, and seven tail fields the
cfg class grew after E-int ran, all at defaults. Positively confirmed: `observation_space: 72`,
`fault.enable: true`, `thruster_health_range [0.0, 0.5]`, `performance_lb 250.0`, `kl_ub 0.12`,
`step_interval 250`. Resume confirmed by `Learning iteration 4999/9999`. ETA about 06:28.

**2026-08-05 01:28 — buoy added mass RESOLVED, and it inverted the expected verdict.** Section
3b anticipated "policy insensitive, accept for gen-1". What the three measured points actually
show is a **numerical stability cliff**: zero REAL flags at 2x effective (ratio 0.60), survival
down 18.75-31.25 pp at the representable ceiling (ratio 0.95), and 0/64 alive before step 1000
at the geometric value (ratio 2.15). The ceiling point's ss_error deltas are
survivorship-contaminated and must NOT be quoted as control degradation. So the geometric value
is unreachable by any coefficient or factor setting, raising the cap and retuning the factor are
measured dead ends, and the mass-matrix route is a **gen-2 engine item**. Gen-1 accepts the error
on the narrower ground that the policy is insensitive across a range that does not reach the true
value — carried to the DGX handoff in exactly that form, not as "resolved". Full verdict on the
wiki page; commit `598db89`.

**2026-08-05 01:31 — a new eval trap, found by hitting it.** The arm B eval failed in 16 s with a
state_dict size mismatch (actor 88 vs 81, critic 116 vs 109 — exactly `MARINE_FEATURE_DIM = 7`).
`eval.py` restores `agent.yaml` from the run directory but rebuilds the ENV cfg from Hydra
defaults plus the CLI, so `use_marine_feature_obs` fell back to False and the env was built 72D
for a 79D policy. Same class as `env.fault.enable=True` on a resumed launch: **a config-derived
plant or observation setting is not carried by a checkpoint.** Retry queued with the flag; the
koopman DESIGN.md eval command is corrected and the class is recorded on the wiki.

**2026-08-05 01:50 — both HydroRC leads resolved; `needs-apply-before-retrain` reaches ZERO.**
016d1b1 is not on marinelab main, so the damage never landed and the retirement this page asked
for is already the de-facto state. Its remaining item (re-derive every damping axis before a
HydroRC-v2) is only worth doing if hull damping is a lever the policy feels, and a +/-10x bracket
says it is not: zero REAL flags and unchanged survival at both ends of a 100x span. The same
bracket answers `hydrorc_is_half_recentered`, whose surviving mechanism was a 45x hull-damping
drop letting buoy damping dominate — swept more than twice that far, nothing above floor. Both
interventions verified to bite (`dr_lin_damp_5` 0.1597 -> 0.01597, 23/24 other keys identical).
Commit `ee3bcac`. **Open backlog 17 -> 3.**

---

**2026-08-05 02:07 — the control-delay sweep was measuring nothing; killed and re-run.** The
Hydra override `env.randomization.control_delay_steps=[N,N]` does not survive `apply_dr_config()`,
which rebuilds the randomization config before env creation and again at every DR level;
`control_delay_steps` is not a `_DR_TUPLE_FIELDS` dim, so it reverted to `(0,0)` every time. d1's
`data_hard.npz` was elementwise identical to the stock baseline across all 40 keys. I checked d1
against the baseline BEFORE waiting for d3, precisely because this project has been burned by a
silent eval-side no-op before, and that early check is what saved the remaining GPU1 time. The
supported instrument is the dedicated flag `--control-delay N`, which eval.py applies both before
`env.__init__` (so the `DelayBuffer` is allocated at all) and after each per-level
`apply_dr_config` — the code comment at `eval.py:1312-1314` documents this exact trap, so the
instrument was right and my invocation was wrong. queue3 was killed mid-d2, both output
directories carry a `VOID.txt`, and `gpu1_queue5.sh` re-runs the sweep with a self-abort gate.
The gate was validated in both directions before being trusted: 0 differing keys on the known
no-op, 10 on the known-real yaw-damping arm.


**2026-08-05 02:21 — Koopman arm B is NULL, and the line is closed.** The retry eval ran clean on the
correct flag. Pairing is 24/24 dr+fault keys at all four levels against BOTH the pre-registered GPU0
baseline and the same-device GPU1 reproduction; the two return the same verdict to within 0.001, which
settles empirically the concern that the decision floors declare themselves "paired same-machine"
while the pre-registration named a cross-device baseline. Survival is 100 % at every level in both
runs, so nothing here is survivorship-contaminated. Both ADOPT conditions fail: `att_norm` `ss_error`
clears the 0.10 deg floor at `hard` only — one of the two levels required — and regresses at `medium`;
roll `n_gt20` at `none` goes 0.00 → 20.33 against a floor of 15.

The shape is worth more than the verdict. The heavy tail is monotonically WORSE as the exam gets
EASIER (none 0.00 → 20.33, soft 0.33 → 8.33, medium 1.00 → 5.00, hard 5.00 → 6.67), which is the
opposite of a robustness trade. The mechanism is transient: at nominal the steady-state error is
unchanged (0.4037 → 0.4003) while overshoot rises 7.96 → 13.74 pp and pitch rise time slows 23 %.
`os_env_mean` is worse in **8 of 8** level-by-axis cells and **no single cell clears its 10.0 pp
floor** — the floors are a per-cell noise test and do not aggregate, so a regression of exactly this
shape passes them in silence. I only caught it by reading the sign pattern after the flag list came
back looking mixed. Recorded on the wiki
(`koopman_phase_1_arm_b_null_marine_feature_lifting_buys_no_contro.md`), in the campaign ledger as a
`discarded` event, and as a CLOSED banner on `koopman-lifting/PLAN.md`. Arm C's ≥15 GPU-h is not spent.


**2026-08-05 02:27 — the delay sweep bites now, and that exposed a SECOND defect that also sits in
the 2026-07-24 Z4 result already on the wiki.** With `--control-delay 1` the `none` level differs from
the baseline on 9 of 40 npz keys, all of them trajectory keys, with **0 of 23 `dr_`/`fault_` keys
moving** — a clean paired injection. But at `soft` and `medium` **23 of 23 DR keys move too**, which
means the two runs are no longer being graded on the same physics.

The cause is in the env, proven from code rather than inferred. `_draw_control_delay`
(`albc_env.py:66-85`) returns early at `hi <= 0` and **skips its `torch.randint`**; at `d >= 1` it
draws one integer per env per reset. So a `d=0` run and a `d>=1` run consume different amounts of RNG,
and every DR draw after the first reset diverges. `none` looks paired only because at 0 % DR there is
nothing to shift.

I checked the recorded Z4 sweep for the same signature and it has it: d0-vs-d1 is 0/23 DR keys at
`none` and **23/23 at soft, medium and hard**. Among the d>=1 points the pairing survives only where
survival matches — d2 vs d3 pair at all four levels (both 92.19 % at hard), while d1 breaks against
them at medium and hard (98.44 %), because a different death count means a different number of resets
means a different number of `randint` calls.

**Consequence for the wiki.** Z4's `none` column (d1 +134 %, d2 +415 %, d3 +790 %) is a valid paired
measurement and stands. Z4's `hard` column (d1 1.7x, d2 8.4x, d3 12.8x) is **unpaired** — it compares
delay against a different DR sample — and the ALBC decision floors explicitly declare themselves
"paired same-machine", so they do not apply to it. The effect sizes at hard are far too large to be
sampling noise, so the qualitative claim survives; the specific multipliers do not, and should not be
quoted as precise. I am NOT fixing the RNG consumption: that is an env-code change mid-program, it
would void E-int as the comparison baseline, and it is exactly the class of edit this program has
already declined twice.


**2026-08-05 02:31 — the Run A analysis tooling is built and validated BEFORE the run lands.**
`/root/.claude/jobs/3999bdb3/tmp/saturation.py` answers the preflight plan's three questions from a
run's TensorBoard scalars. It reproduces the extend8k reference exactly — 26 expansions, last at
6750, `success_rate` 0.813 → 0.789 (min 0.7595), `entropy_before` exactly 2 distinct values over
n=1250 — so it is calibrated against a known answer rather than trusted.

Building it early paid for itself twice.

**It caught a bug in my own first version.** The naive reading of "last expansion at 5748, then 223
iterations of `kl_step` = 0" is *saturated at 5748*. It is not: `kl_step` reads exactly 0.0 on every
non-boundary iteration, and the boundaries are 250 apart, so the gap between two boundaries always
looks like a freeze. The script now infers `step_interval` from the observed spacing and refuses to
declare saturation until at least one whole boundary has been MISSED. Re-validated in both
directions: extend8k → SATURATED at 6750 (4 boundaries missed); Run A at iter 5988 → NOT saturated,
next boundary due ~5998. Without this I would have reported a false saturation iteration at 06:35 and
written it into Gate A.

**And it corrected two facts in the preflight plan.** (a) The predicted boundary phase is wrong: the
plan says to expect iterations ending 249/499/749/999, the actual ones end **248/498/748** — a
one-off that would make a targeted grep find nothing. (b) Run A carries **21** DORAEMON params
(`fault_severity` is present, extend8k had 20), which is exactly why the plan forbids comparing
`entropy_before` across plants: extend8k sits at -18.20, Run A at -22.53.

**Early Step-0 signal, not yet a verdict** (iter 5988 of 9999): `DORAEMON/success_rate` reads 0.84
against `alpha` = 0.5. The curriculum protocol's Step 0 says that when success >> alpha the
feasibility gate is INERT and `performance_lb` is mis-set — a confound to fix, not a co-variable.
Note this is the OPPOSITE of the posttam-era failure, where lb sat at ~101 % of nominal return and
stalled the curriculum at mode -2. Confirm at the end of the run before recording it.


**2026-08-05 02:40 — I attributed the delay-sensitivity difference to the wrong variable, and the
plant diff caught it.** With d1 and d2 in hand, E-int's paired `none` response looked much steeper
than the Z4 anchor's (roll `ss_jitter` 4.84x vs 2.19x at d1; 11.54x vs 4.80x at d2), and the obvious
mechanism was E-int's gated integral observation — an integrator in the loop is the textbook
destabilizer under dead time.

Then I diffed the two runs' recorded `params/env.yaml`. **The anchor already has
`use_integral_obs: true`, `integral_gated: true`, `integral_dims: 3` and the same 72D observation
space.** The integral channel is not what separates them, so the mechanism I had reached for cannot
be the explanation. Retracted before it was written anywhere but here.

What actually differs is **fault DR**: `fault.enable` is `false` on the anchor and `true` on E-int,
and E-int additionally carries the `max_thrust_scale` (0.85, 1.15) and `fault_severity_range`
(0.0, 1.0) dims. (`integral_gate_threshold` appears only in E-int's file because the field was ADDED
by the R1 decouple with a byte-identical default; the anchor's gate ran at the same 0.10 through the
shared reward sigma.)

So the surviving observation is that the fault/thrust-DR-trained policy has far better nominal
jitter (0.1331 vs 0.3384) and that entire margin is delay-fragile. That is **cross-run, cross-plant
and single-seed** — hypothesis-generating, not a controlled contrast, and it must be written that
way. The controlled, quotable part of this sweep is only E-int's own within-run paired response at
`none`.


**2026-08-05 02:50 — the latency lead is CLOSED-OUT-OF-SCOPE for gen-1, carried as a gen-2
requirement. Backlog 3 → 2.** The sweep finished clean: survival 100 % at every level and every
delay point, so nothing is contaminated. E-int's paired `none` response is 2.55x / 6.46x / 12.24x on
`att_norm` `ss_error` and 4.84x / 11.54x / 20.55x on roll `ss_jitter` at 20 / 40 / 60 ms. The
measured bus staleness (0-40 ms on attitude) brackets d1-d2, where this teacher's nominal attitude
error goes **0.50 → 3.23 deg**. So the user's 2026-07-20 "latency belongs in the final config"
decision is now confirmed on the actual final teacher rather than on the superseded anchor.

The training half is deliberately not run, and the reason is scheduling plus interpretability, not
disinterest. BLOCKER 2 admits exactly two fixes: a DORAEMON `_PARAM_DEFS` dim, which is a curriculum
engine change that would void E-int as the DGX baseline and could not be validated before the
deadline — the same objection that killed the nominal-corner floor — or a MEASURED `performance_lb`
recalibration, which needs a pilot run plus the real run, i.e. two of the three GPU0 slots, all of
which are committed to Runs A and B/C. A naive delay-ON run without either fix reproduces
`trpo_e1_latdr` exactly and answers nothing; running it merely to have run something would have been
the worse call. The recipe is written into the page so a gen-2 session starts from it.

Two things were added to the page beyond the verdict. The **Z4 correction** (its `hard` column is
unpaired; its `none` column stands), and the **Hydra-override trap** pointing at the eval.py page.

Artifact hygiene, because these three eval dirs were unidentifiable: `--control-delay` is an argparse
flag, so it leaves the Hydra override record EMPTY — and an empty override list was already the
signature of the failed Koopman eval, so that decoder now means two different things. Each sweep dir
now carries its own `eval.log` (4 injection markers, one per level) and
`<E-int run>/eval/README.md` is a full index of all twelve evals with both decoders and the pairing
matrix.


## 8. STATE AT LAST COMPACTION — read this first on resume (overwrite each time)

**Written 2026-08-05 02:52 KST.** Everything below is live at that moment. Re-derive from disk
rather than trusting it if the clock has moved much; a relaunch mints a new run id and strands
every id recorded here.

### Open leads: 3, all with a run in flight

| Lead | Closes on | Status |
|:--|:--|:--|
| `curriculum_recalibration_protocol…` | **Run A** | in flight, ETA 06:36 |
| `reward_sigma…` (R6) | **Run B**, launches when Run A exits | not started |

`experiment_idea_latency…` is **CLOSED** (02:50, CLOSED-OUT-OF-SCOPE for gen-1). Open leads: **2**.

`omx wiki list --status needs-apply-before-retrain` already returns **zero rows**. Done means
`--status needs-experiment` does too.

**Already finished this session and NOT to be redone**: the Koopman line is CLOSED as NULL
(campaign ledger `discarded`, wiki page, CLOSED banner on `koopman-lifting/PLAN.md`); campaign
drift is fixed (`omx campaign-drift` returns `ok: true`); Gate A's `Train/mean_reward` reference
band in `HANDOFF-DGX.md` is sharpened to p5-p95 plus the full excursion.

### What is running

- **GPU0 — Run A.** PID 873942, run id `trpo_iterbudget_s30_260805_012813`, group
  `teacher_iter_budget`, resumed at iteration 4999 heading to 9999, ETA about **06:36**.
  Stdout `/workspace/constrained-albc/logs_queue/iterbudget_s30.log` — use the ABSOLUTE path,
  the shell cwd resets to `/workspace` between calls and the relative path silently fails.
  TB dir: `logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/latest/`. Plant verified.
- **GPU1 — IDLE.** All five queue scripts are finished. Nothing is scheduled on it until
  Run B's eval. (queue3 was KILLED at 02:07 as a proven no-op; queue5 re-ran the sweep correctly.)
  Poll the PID directly; a `pgrep` pattern self-matches and has killed watchers here before.

### Analysis tooling already built and VALIDATED (do not rewrite)

All in `/root/.claude/jobs/3999bdb3/tmp/`, each calibrated against a case with a known answer:

| Script | What it does | Validated against |
|:--|:--|:--|
| `saturation.py <run_dir>` | the preflight plan's 3 iteration-budget questions from TB scalars | reproduces extend8k exactly (26 expansions, last 6750, success 0.813→0.789, entropy_before 2 distinct values over n=1250); refuses to over-call on in-progress Run A |
| `floor_verdict.py <base> <treat> [label]` | applies the decision floors, survival first, suppresses survivorship-contaminated levels | 0 REAL on self-comparison; reproduces the buoy-ceiling result (18 flags, all suppressed) |
| `delay_table.py [d1_dir …]` | delay-response table beside the Z4 anchor sweep | reproduces the Z4 wiki numbers (none d1 2.34x, d3 8.90x) |

Run them with `/isaac-sim/python.sh` when they need `tensorboard`; plain `python3` suffices for
the two that only read JSON/npz.

### Which eval is which

Every eval of the E-int checkpoint lands in
`experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/`
under a timestamp, so they are indistinguishable by name. The authoritative decoder is
**`outputs/2026-08-05/<HH-MM-SS>/.hydra/overrides.yaml`**, whose directory time matches the eval
directory's timestamp.

| eval dir | overrides | meaning |
|:--|:--|:--|
| `static_260804_143234` | — | campaign baseline of record (post-pairing-fix) |
| `static_260804_203719` | — | same checkpoint reproduced on **GPU1** from this branch; the same-device baseline every 08-05 eval below is paired against |
| `static_260805_004401` | buoy added_mass + factor 0.8 | buoy **x2** — zero REAL |
| `static_260805_005359` | buoy added_mass + factor 4.0 | buoy **geometric** — 0/64 alive, run crashed, directory INCOMPLETE |
| `static_260805_010019` | buoy added_mass + factor 1.257 | buoy **ceiling** — survival -18.75 to -31.25 pp |
| `static_260805_012834` | hull damping yaw x0.1 | yaw damping **low** — zero REAL |
| `static_260805_013827` | hull damping yaw x10 | yaw damping **high** — zero REAL |
| `static_260805_014845` | `control_delay_steps=[1,1]` | delay d1 — **VOID, no-op** |
| `static_260805_015843` | `control_delay_steps=[2,2]` | delay d2 — **VOID, no-op, killed mid-run** |

The failed arm B eval left `outputs/2026-08-05/01-28-01/` with an EMPTY override list — that
emptiness is the bug itself (the missing `env.use_marine_feature_obs=True`).

**The two VOID rows are the delay-instrument trap, caught 02:07.** Passing
`env.randomization.control_delay_steps=[N,N]` as a Hydra override does nothing:
`apply_dr_config()` rebuilds the randomization config once before env creation (`eval.py:1308`)
and again at every DR level, and `control_delay_steps` is not a `_DR_TUPLE_FIELDS` dim, so it
reverts to the dataclass default `(0,0)` each time. d1 came out elementwise identical to
`static_260804_203719` across all 40 npz keys — and `eval.py`'s own `--control-delay` help text
calls delay-off "byte-identical to stock", so the identity WAS the signature of a dead injector.
Both directories carry a `VOID.txt` on disk. The supported instrument is the dedicated flag
**`--control-delay N`** (`eval.py:1309-1317` and `1462-1468`), which sets the value before
`env.__init__` so the `DelayBuffer` is allocated AND re-sets it after each per-level
`apply_dr_config`. The re-run is `gpu1_queue5.sh` (PID 942451), which gates itself: after d1 it
diffs against the baseline and aborts the remaining points if the count of differing keys is 0.
That gate was verified to fail on the known no-op (0 keys) and pass on the known-real yaw-damping
arm (10 keys) before being trusted.

### Next actions, in order

1. **When the delay sweep finishes**: compare d1/d2/d3 against `static_260804_203719` with
   `compare.py paired`. **The sweep is worthless unless d1, d2 and d3 differ from each other** —
   a previous eval-side delay injector in this project ran and changed nothing, and the silent
   no-op was caught only by byte-identical results. Then close `experiment_idea_latency` on the
   measured answer, recording explicitly that only the CONTROL-ACTION half was measured and the
   sensor-observation staleness half was not.
2. **When the arm B eval retry finishes**: verify pairing 24/24, apply the pre-registered verdict
   in `koopman_marine_obs/DESIGN.md` section 3 (expectation NULL), and close the Koopman program.
3. **When Run A finishes (~06:28)**: read the three questions in
   `/workspace/.sp/plans/2026-08-05-preflight-iter-budget-launch.md` — saturation iteration,
   `success_rate` at and after saturation, whether the post-saturation stretch is quiet. Scan ALL
   steps for `DORAEMON/kl_step > 0`; it reads exactly 0.0 on every non-boundary iteration, and a
   resumed run is phase-shifted so boundaries land on iterations ending 249/499/749/999. Then
   correct **Gate A** in `.omx/programs/dgx-final-scaleup/HANDOFF-DGX.md`, which still carries a
   saturation iteration derived from the retired posttam plant.
4. **Immediately after**: launch **Run B** — the command is in
   `experiments/rsl_rl/albc_trpo_teacher/teacher_integral_gate/DESIGN.md` section 6
   (`env.integral_gate_threshold=[0.20,0.20,0.20]`, and `env.fault.enable=True` is mandatory).
   Run C (`[0.05,0.05,0.05]`) follows if the clock allows; **17:00 is a hard cutoff for starting
   anything on GPU0**.
5. **Finally**: one report covering all 17 leads, Runs A/B(/C), the Koopman closure and the
   corrected Gate A — ending with both `omx wiki list --status …` queries returning zero rows.

### Still user-gated, do not do autonomously

`git push`, sending the DGX handoff, and any hardware action.

## 9. Final deliverable

One report covering: every one of the 17 leads with its verdict and the evidence behind it, the results
of Runs A/B(/C), the Koopman line's closure, and the DGX handoff's corrected Gate A. After it, both
`omx wiki list --status …` queries return zero rows. That is what "끝났다" means from now on.
