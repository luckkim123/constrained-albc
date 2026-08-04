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

## 8. Final deliverable

One report covering: every one of the 17 leads with its verdict and the evidence behind it, the results
of Runs A/B(/C), the Koopman line's closure, and the DGX handoff's corrected Gate A. After it, both
`omx wiki list --status …` queries return zero rows. That is what "끝났다" means from now on.
