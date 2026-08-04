# Program: dgx-final-scaleup — DGX GB10 final-teacher scale run (num_envs 32768)

**Status: PENDING USER APPROVAL — this document authorizes NO launch.** Every training launch
named here (the flagship and every optional probe) is human-gated and fires only on explicit
user approval.

**HOLD LIFTED on the experiment condition (2026-08-04 16:00); still gated on the user's §8 answers.**
The parallel session's X1-tailsplit run finished and has been jointly re-analyzed with the G1–G4
gate verdicts (§2, §8 Q3). Outcome: it **does not overturn** §1 or §3 — it reinforces both. The
tail-split delivery fixed the gen-2 latent collapse decisively (hard aggregate R2 −0.1044 → +0.0645,
delta +0.169 vs the pre-registered 0.107 threshold) while moving **no** control metric above its
registered floor — a null the measured actor sensitivity predicts for a move that size (§1), so it
neither helps nor hurts the obs76 case. What decides it is that the obs76 teacher's real advantage
does not distill: no student built from it beats the shipped one. HANDOFF-DGX.md is therefore
technically final; what remains before sending is the user's answers to §8 (Q1 machine
adoptability, Q2 32768 go/no-go, Q6 purpose string are the launch-blocking three).

Created 2026-08-04. Sources: workflow `albc-closeout-dgx-design` (run `wf_8ef2309d-9a8`,
7 evidence agents + opus synthesis + 2 adversarial verifiers; 21 verifier findings folded in),
Phase E report `student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md`,
omx wiki, and direct `doraemon_state.pt` measurements taken during the sweep. Numbers below
trace to those sources; nothing is a round-number guess.

---

## 1. Final-model declaration (as of 2026-08-04)

The final model CAN be declared today, and it is the **gen-1 pair**:

| Role | Run | Notes |
|:--|:--|:--|
| Teacher | `trpo_eint_s30_rs2350_260727_195102` (teacher_baseline_buoyfix) | 72D obs, fault-DR Arm-A, max_thrust (0.85,1.15); E-int H1 PASS 2026-07-28 |
| Student | `trpo_sdeint_c3_gruselect_s30_260729_193732` (student_distill_eint) | C3 = GRU+select, lambda=1.0, extra_obs_dim=0; adopted 2026-08-03 |
| Deploy pack | `pack_eint_c3_gru_260803_144925` | on disk, parity closed at 2f057b9 |

**gen-2 (obs76) does not supersede it — REAFFIRMED 2026-08-04 on stronger evidence.** The original
reason (negative in-loop latent R2, 10–19x train-to-in-loop MSE gap) has since been *superseded as a
reason* and replaced by a better one. X1-tailsplit proved the negative R2 was the delivery path, not
the obs76 teacher, and fixed it (hard aggregate R2 −0.1044 → +0.0645, sumMSE 0.6367 → 0.5544 at
comparable sumVar). The declaration survives anyway, because the fix bought nothing measurable: **every**
X1-vs-Phase-E control delta is below its registered floor, and hard roll dispersion drifted the wrong
way in absolute terms (2.880 → 3.130 deg).

Read that null correctly — it is *expected*, not a discovery. The +0.169 R2 swing is only a **6.69%
latent-RMSE reduction** (R2 sits near zero, so the ratio exaggerates it; 15% of the swing is
denominator drift), and the campaign's own measured actor sensitivity at hard (C1-latsens: k=0.5
injection costs +0.4232 deg) prices that at roughly **0.06 deg** — under the 0.10 deg floor. So X1
tells us the delivery path owns the latent collapse; it tells us **nothing** about whether latent
quality drives control, and it is not evidence of decoupling. Clearing the floor at hard would need
on the order of a 12% latent-RMSE reduction.

Confidence on that pricing is MED, not HIGH, and the caveat must travel with it: C1-latsens measured
a *nonlinear* curve on a *different* arm (A0g) with k=0.5 as its smallest point, so 6.69% is a ~7x
extrapolation below anything measured, and an injected random perturbation is not the same object as
a structured reconstruction improvement. It is enough to say the null is uninformative; it is not
enough to quote 0.057 deg as a measurement.

Mechanism, from the campaign owner's report `diagnose-20260804-154122` (independent analysis of the
same eval, verdict identical to this one): the gain is **covariate shift, not capacity** — X1's
*training-side* latent loss is 4.3% WORSE than the baseline's (0.004236 vs 0.004062) while its
closed-loop latent error is 12.9% better, and the train-to-in-loop gap narrows at every level
(9.7x → 3.2x at none, 17.4x → 14.5x at hard). Folding the channels into policy_obs subjects them to
the teacher's frozen normalizer statistics, so they misrepresent themselves exactly where the
deployment distribution has moved. The gap narrows but does not close at hard.

The load-bearing fact is now the paired five-arm table (all evals share DR draws post-9eac3a8):

| arm | hard roll ss_error | hard roll ss_error_std | hard survival |
|:--|--:|--:|--:|
| E-int teacher (72D) | 0.816 | 2.015 | 100.0% |
| obs76 teacher | **0.535** | **1.072** | 98.4% |
| C3 gen-1 student (shipped) | 0.971 | 2.526 | 98.4% |
| Phase E gen-2 student | 0.840 | 2.880 | 96.9% |
| X1 tail-split student | 0.855 | 3.130 | 98.4% |

The obs76 teacher is a REAL-better controller (−0.281 deg mean, −0.943 deg dispersion vs E-int at
hard, both clearing floors) — and **none of that advantage reaches any student**: all three students
sit at 2.5–3.1 deg dispersion, worse than either teacher, in an order that does not follow the
teacher order. Choosing the teacher by its own eval does not choose the better product. X1 vs C3 is a
genuine trade, not a win: −0.118 deg hard att mean (REAL, X1 better) against +0.604 deg hard roll
dispersion (REAL, X1 worse), identical survival. C3 also remains the only candidate with a verified
deploy pack — `deploy/specs/student_gru.py` deliberately **rejects** tail-mode checkpoints
(ExportContractError), so X1 is not board-exportable without extending the spec first.

Conditions attached to the declaration:

1. **C3's teacher-relative "win" language must be downgraded** (X9): the Phase E report proved
   teacher-vs-student evals share DR draws only at `none`; recomputed per-pair, C3-vs-E-int at
   hard is |d|/SE = 0.91 (roll) and 0.83 (att_norm) — under 1 SE, so the adoption is a defensible
   preference, not a decision-grade measurement. (C3-vs-A0g arm choice is unaffected — report.md
   already records all four deltas below floors.)
2. **Everything is single-seed (seed 30) screening** — never a paper number until the deferred
   4-arm x 3-seed ablation (X35) runs.
3. **Machine adoptability**: the recorded +109% same-config same-seed cross-machine isolation
   term means a DGX-trained teacher is, under the standing rule, NOT adoptable as the shipped
   final model. Unless the user overturns that rule, the 32768 run is scale exploration
   (see §8 Q1).

## 2. Pre-launch gate (blocking; zero or near-zero GPU)

| Gate | What | Cost |
|:--|:--|:--|
| G1 (X2) | **Eval pairing fix** — **CLOSED 2026-08-04**: root cause was NOT the DR source (`--doraemon-dr-from` pins only the distribution) but the global torch RNG — policy-build weight init consumes run-dependent amounts (72D vs 76D actor, student GRU), desyncing per-env draws (23/24 keys differed). Fix = per-level `torch.manual_seed(seed + level_index)` in `run_static` (commit 9eac3a8, mirrors segmented mode). Verified: 4-way assert across E-int/obs76/C3/gen-2 evals (`static_260804_14{3234,4056,4932,5821}`) = 24/24 dr/fault keys elementwise identical at all 4 levels. Paired closure verdicts: **gen-1** (C3 − E-int) only hard ss_error +0.135 (att_norm) / +0.155 (roll) deg REAL, dispersion + survival all below floor — clean distillation; **gen-2** (student − obs76 teacher) hard ss_error +0.30 REAL AND hard ss_error_std +1.82 (att_norm) / +1.81 (roll) deg REAL, i.e. the gen-2 delivery path pays a 3x-floor dispersion cost its teacher does not have; **student-vs-student** (gen-2 − C3, deployment view) hard ss_error −0.14 REAL (gen-2 slightly better mean), dispersion below floor, survival −1.56 pp below floor — the two students are near-equivalent. Superseded unpaired evals moved to `.trash/failed-evals-260804/` | done |
| G2 (X3) | **Dispersion floors** — **CLOSED 2026-08-04**: registered `ss_error_std: 0.60 deg` (attitude axes) + `survival_pct: 1.6 pp` in `_analyze/recompute_metrics.py` DECISION_FLOORS; derivation = corrected-plant cross-seed p2p on buoyanchor s30a/s31/s32 standard evals (s30 `static_260725_165657` excluded — FTC-m4 fault eval, `fault_thruster_*` keys verified); eval instrument is deterministic at fixed (ckpt, seed, draws) — C3 eval trio identical to 4 decimals — so floors encode the retrain lottery; verified live: Phase E hard roll +1.429 deg = REAL, survival −3.125 pp = REAL | done, zero GPU |
| G3 (X6) | **Obs-width paired re-eval** — **CLOSED 2026-08-04** (numbers land; ADOPTION decision stays with §8 Q3 + tailsplit): under true pairing the unpaired "soft/medium pitch regression" mostly evaporates — only soft pitch +0.111 deg survives (marginally REAL vs 0.10 floor), medium +0.095 is noise. Meanwhile obs76 teacher shows REAL hard-DR gains: ss_error att_norm −0.302 / roll −0.281 deg AND ss_error_std att_norm −1.213 / roll −0.943 / pitch −0.690 deg (beyond the 0.60 seed-lottery floor); survival hard −1.562 pp below floor. Teacher-level, obs76 is the more robust plant at hard; the obs76 LINE still loses it at distillation (see G1 gen-2 verdict). Single-seed screening — do not overturn §1 on this alone | done |
| G4 (X8 widened) | **metrics.yaml token audit** — **CLOSED 2026-08-04**: full audit found **10** drifted tokens, not 6 (the verifier's 6 plus `reward_total→Reward/total`, `att_roll_err_deg→Track/att/roll_err_deg`, `att_pitch_err_deg→Track/att/pitch_err_deg`, `yaw_rate_err→Track/yaw/rate_err`); all fixed in metric list + groups; final check: 59/59 declared tokens exist in the E-int event file, YAML parses, `pending_approval: false` | done |

Optional user-gated: **X1 3-seed DGX anchor** (4096 x 5000, seeds 30/31/32, 22.5 h) — required
ONLY if the user overturns the machine rule and wants a DGX-trained model adoptable; a corrected-plant
EVAL seed band already exists (56.0% p2p), what is missing is a corrected-plant TRAINED band on DGX.

X4 (curriculum probe) and X5 (minibatch probe) are FOLDED into the flagship's iteration-500 abort
gate (§6) instead of running as separate probes — saves 8.6 h; running them separately first
remains a valid conservative option.

## 3. Flagship config — every knob, current → recommended

Verdict shape: **the run is `num_envs=32768` and NOTHING else changes.** The record forbids every
"scale-up companion" change that intuition suggests.

| Knob | Current | Flagship | Why (evidence-backed) |
|:--|:--|:--|:--|
| num_envs | 4096 | **32768** | Fits: peak 83,170 of 124,610 MiB (~41.4 GB spare; source carries a 1,000 MiB internal inconsistency), 34.73 s/iter measured. Honest framing: curriculum-NEUTRAL by recorded code reasoning (step_interval is iteration-clocked); benefit = gradient-noise reduction, unmeasured; Arm N (8192) measured NULL at fixed box. Go/no-go is a resource call (§8 Q2). Sub-linear: 8x batch → 1.25x samples/s |
| max_iterations | 5000 | **20000 — USER DECISION 2026-08-04** | The run is a CAP, not a commitment: `max_iterations` is consumed ONLY as the loop counter (`constraint_trpo.py:636-642 set_max_iterations` is log-only; barrier constants fixed; no LR/entropy/std scheduler exists), so the first N iterations of a 20000-run are identical to an N-iteration run at the same seed/envs. With `save_interval 50` the run therefore yields a **dose-response curve nobody has measured on this plant** — eval checkpoints on the fair `none` level and keep the best; stop early when the curve turns. Cost 20000 x 34.73 s = **192.9 h = 8.04 days**; 400 ckpts x 5.9 MB = 2.4 GB. Shape at si=250: the box saturates ~iter 6750 (26 achieved expansions), so **13,250 iterations (66%) train on a frozen fully-saturated box** — that is the untested regime this run characterizes, and the only prior datapoint in it (extend8k's 1250 post-saturation iterations) degraded nominal. See the row below for why si stays 250 anyway |
| ~~max_iterations (superseded row)~~ | 5000 | ~~withdrawn~~ | The previous entry ("5000 — do NOT raise; net-negative twice (extend8k, moreiters)") had three defects. (1) It contradicted a RECORDED USER DECISION — wiki `e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite` (2026-07-16, resolved): "no iteration cap; DGX scale-up is planned", which explicitly scopes the e3 keep-5000 verdict as not a cap. (2) `moreiters` is cited backwards: at the fair `none` level it IMPROVED with extension (roll os_env_mean 16.04 → 13.03, n_gt20 21.33 → 9.33). (3) The extension effect's SIGN is `performance_lb`-dependent — the lb=250 pair degraded (17.02 → 26.99, n_gt20 4.33 → 61.33) while the internally-consistent lb=200 pair improved. Both pairs are on the RETIRED posttam plant (20-dim, no fault_severity); the current buoyfix plant has no extension datapoint at all. Value pending: see §8 Q2b |
| num_steps_per_env | 64 | 64 | Above the ~25-step floor (Rudin et al. 2021); GAE horizon ~17 steps. Cutting to 32 halves wall-clock but is an unmeasured second variable — probe first if wall-clock ever binds |
| step_interval | 250 | **250 — unchanged, RE-DECIDED for the 20000 run** | Two shapes exist at 20000 and the choice is real. (a) si=250: 80 boundaries, box saturates ~iter 6750, then 13,250 iterations at fixed maximum difficulty. (b) si≈750: 26 boundaries, saturation lands near the END, ~3x the dwell per difficulty level — which is what the recalibration protocol's "more dwell for a harder exam" logic argues for. Recommendation is (a), for three reasons: the ONE measured test of raising si (stepint400, si=400 at 8000 it) was the WORST arm of three at the fair `none` level (att_norm 0.426 vs ref5k 0.319 / extend8k 0.370); (a) keeps the run a clean ONE-variable dose-response against every run on record, which is most of what 8 days buys; and (a) reaches full DR coverage for the 4 starved dims by iter 6750 rather than only at the finish. Also unchanged: sample-clocking (÷8 → 31) remains rejected — budget 19.3 vs box saturation 3.12 would exhaust the box by ~iter 800. If the user prefers shape (b), it is a one-line change and the abort gate below still applies |
| kl_ub (DORAEMON) | 0.12 | **0.12** | kl_ub-up measured known-bad (E1: DR 3.6x wider but attitude worse everywhere). kl_step lands at cap on every accepted update → kl_ub IS the pacing constraint. Budget: reachable 20 x 0.12 = 2.40; achieved band at 5000 iters is 2.16–2.28 (18–19 updates, success-gated) — read the saturation guard against ACHIEVED |
| performance_lb | 250.0 | **250.0** | Byte-identity keeps the run comparable to both existing teachers (the only way the result is readable). Measured p25 from doraemon_state.pt (E-int 255.8 / obs76fault 260.1) is recorded HERE as the candidate for the NEXT purpose, where lb re-derivation belongs (recalibration Step 3, with box widening). Expectation at lb=250: success ≈ 0.815 (obs72 plant); human-look triggers: success > 0.95 sustained (inert-gate class) or < alpha 0.5 (infeasible) |
| alpha | 0.5 | 0.5 | E5 measured alpha-up as near-null; feasibility floor, not an expansion lever |
| DR bounds (17 midpoint dims) | HardDR box | **byte-identical — do NOT widen** | Recalibration protocol: bounds must come from measured hardware variation (blocked: no load cell / TAM arm source); box is not binding at 5000 iters (a≈b≈2.0–2.6); widening also silently moves encoder input scaling (bounds auto-derived from live DR cfg) |
| Nominal-0 dims (ocean, payload_cog_xy, obs_noise, fault_severity) | clamped Beta(1,~8-10) | **leave clamped** | Budget-conditional: at 5000 iters they reach ~10% of range; extend8k record shows three reach uniform at 8000. The one measured unclamp (E-ftc1) was REJECTED — its 2.50x endpoint gain made m4-dead rejection 2.9–5.5x worse. fault_severity stays clamped |
| buffer_size / min_episodes | 2000 / 200 | 2000 / 200 | Estimator n is CAPACITY-bound at 2000 → 32768 envs give NO variance reduction on success_rate. What changes: buffer temporal window narrows ~11 → ~1.4 iters → fresher log_probs → expect `DORAEMON/ess_ratio` to RISE |
| max_kl (TRPO) | 0.005 | 0.005 | No literature supports KL-trust-region retune under batch growth (McCandlish et al. excludes trust-region methods). Less-noisy KL estimate → accepted steps land nearer cap; watch `Loss/kl` + `Policy/line_search_success`, don't pre-tune |
| cg_iters / cg_damping / backtracks | 10 / 0.1 / 10 | unchanged | No num_envs term; dominant cost in the 34.73 s/iter figure — changing them invalidates the wall-clock estimate |
| num_mini_batches / epochs | 4 / 5 | **4 / 5 — unchanged** | Verifier-corrected: raising to 32 was self-contradictory. At 32768 the critic gets 8x data with the same 20 Adam steps and LARGER (524,288) better-conditioned minibatches — that is not starvation. If more critic steps are ever wanted, describe it as such and probe (X5) first |
| value_lr / max_grad_norm | 1e-3 / 1.0 | unchanged | No actor LR exists (natural gradient + line search); sqrt(8) value-lr scaling is defensible but unmeasured — not on a flagship |
| entropy_coef_per_dim / min_std / init_noise_std | per-dim cfg | unchanged | A2/A3 tested exactly these → DISCARD (5/5 zero-adoption sweep); Andrychowicz et al. 2020 agrees for trust-region methods |
| save_interval | 50 | 50 (~29 min/ckpt) | Crash costs ≤ 29 min of 48.2 h; E-int itself exists only because its predecessor crashed at iter ~2390 and resumed. PRE-STAGE the resume command (§5) |
| seed | 30 | 30 single | Screening protocol; multi-seed only if user overturns machine rule (X1) |
| wandb group/project | — | `teacher_final_dgx32k` (one string, both flags; user confirms) | group = project = purpose. Do NOT reuse `dgx_scale_32768` (throughput pilot, not comparison-bearing) |
| fault-DR block | Arm-A adopted values | **byte-identical; verify `fault.enable=true` in launched env.yaml** | The missed `fault.enable` diff voided a 4.9 h run once |
| max_thrust_scale | (0.85, 1.15) | byte-identical; verify live | Sourced band (T200 voltage window); reverting silently is a protocol breach (gate D-a ack rule) |
| obs width | 72D vs 76D | **72D — settled on the metrics** (only §8 Q3's requirements question is open) | Two paired results, 2026-08-04. G3: the obs76 TEACHER is REAL-better at hard (mean −0.30, dispersion −0.9~−1.2 deg) and the old pitch regression shrank to a marginal soft +0.111 deg. X1-tailsplit: that advantage does NOT reach a student — even after fixing the delivery defect, the obs76 line's best student sits at 3.130 deg hard roll dispersion, worst of the five arms, and is not board-exportable. (X1's sub-floor control deltas are NOT the evidence here — a 6.7% latent-RMSE move prices at ~0.057 deg, below floor by construction; the deciding fact is the five-arm table in §1.) So 76D buys a better teacher and not a better student. Single-seed screening throughout |
| encoder | elu+LayerNorm+softsign, latent 9, priv 28 | unchanged (settled) | `policy_obs_dim=69` in agent.yaml is a static default — runtime truth is env.yaml observation_space |
| resume | — | fresh (`resume=false`); resume command pre-staged | Hydra `agent.resume` and group-path `load_run` both fail silently; relaunch mints a NEW run id — re-derive from disk, re-key watchers |
| git provenance | E-int ran dirty:true | **clean tree, tagged branch, sha in manifest** | dirty:true already cost one voided run |

## 4. Wall-clock and cost

**20000 x 34.73 s = 192.9 h = 8.04 days** (user decision 2026-08-04). Prior figure was 5000 x
34.73 = 48.2 h. Blocking gate G1–G4 is near-zero GPU. Sub-linear scaling means 32768 buys 1.25x
samples/s over 4096 for 8x memory — the run's value is the 8x per-update batch, not throughput.

**The 8 days is a CAP, not a commitment.** Because `max_iterations` is only the loop counter, the
run's own checkpoints are a dose-response series (400 ckpts at `save_interval 50`, 2.4 GB). Eval
schedule: iterations 5000 / 7500 / 10000 / 12500 / 15000 / 17500 / 20000, each ~9 min at 64 envs.
Two rules make the cost bounded:

1. **Fair exam only.** `eval.py static` defaults `--doraemon-dr True`, which grades each run on its
   OWN learned box — so soft/medium/hard are NOT comparable across checkpoints whose curricula
   differ. Compare checkpoints on `none`, or re-eval them all under `--doraemon-dr-from <one dir>`
   (the shared-DR protocol; pairing is exact post-9eac3a8). Never read a cross-checkpoint hard
   delta as a generalization result.
2. **Stop when the curve turns.** Two consecutive eval points worse than the running best on `none`
   att_norm ss_error = stop and keep the best checkpoint. There is no penalty for stopping: the
   earlier checkpoint is already on disk.

Wall-clock if the curve turns early: 48.2 h (stop at 5000), 96.5 h (10000), 144.7 h (15000).

## 5. Launch checklist (DGX side — expanded in HANDOFF-DGX.md)

1. Clean tree on the launch branch, baseline tag, record sha.
2. Verify plant vs reference: diff launched `env.yaml` against E-int's recorded env.yaml
   (filtered, full read) — `fault.enable`, `max_thrust_scale`, obs width, DR box.
3. `TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p` launcher; no CUDA_VISIBLE_DEVICES (single GB10);
   memory via `free -m` (nvidia-smi memory unsupported on GB10).
4. run_id via make_run_id (tag mandatory, label-before-date); `--run_group` = `--log_project_name`
   = purpose string.
5. Watcher discipline: poll the PID (no self-matching pgrep), scope NaN grep to metric lines.
6. After finish: `eval.py static --doraemon-dr-from <reference> --seed 42`, no `--output_dir`,
   checkpoint via the `train` symlink path.

## 6. Monitoring + iteration-500 abort gate (verified TB tag names)

Verified against a real teacher event file (obs76fault): `DORAEMON/success_rate`,
`DORAEMON/kl_step`, `DORAEMON/mode`, `DORAEMON/ess_ratio`, `Policy/entropy`,
`Policy/mean_noise_std`, `Loss/kl`, `Policy/line_search_success`, `Constraint/barrier_penalty`,
`Grad/sigma_step`, `Grad/enc_step`, `Loss/value_function`, `Loss/cost_value`.

Abort at iteration ~500 (2 DORAEMON updates seen) if ANY of:
- `DORAEMON/kl_step` not at cap 0.12 on accepted updates AND `DORAEMON/mode` <= -2 (stall class);
- `DORAEMON/success_rate` pinned > 0.95 (inert gate) or < 0.5 (infeasible);
- any DR dim at Beta(1,1) already (premature saturation — budget arithmetic broken);
- sustained s/iter > 40 (wall-clock model broken) or `free -m` used > ~100 GB (headroom gone);
- NaN in metric lines.
This gate absorbs X4 (curriculum-at-scale) and X5 (critic-scaling) as live checks.

**Additional gates for the 20000-iteration run (2026-08-04).** The iteration-500 gate above only
catches a broken launch. Two more are needed because 66% of this run happens after the box freezes:

- **Saturation checkpoint (~iter 6750–7000).** Confirm `DORAEMON/kl_step` has gone to 0 and every
  dim reads Beta(1,1) in `doraemon_state.pt`. If saturation lands much EARLIER than 6750, the
  21-dim KL dilution assumption was wrong and the remaining budget arithmetic is void — report.
  If it has NOT saturated by ~iter 9000, expansion attrition (`mode=-3` fires in 4/4 recorded runs)
  is worse at 32768 envs than on record — also report.
- **Inert-gate watch, every eval point.** `DORAEMON/success_rate` sustained > 0.95 is the recorded
  inert-gate failure class. E-int already sits at 0.814 (alpha = 0.5), i.e. the feasibility gate is
  slack on this plant; 13,250 post-saturation iterations can push it to the ceiling. If it pins
  > 0.95, `performance_lb = 250` has stopped doing anything and the rest of the run is unguarded —
  report before continuing. (Keeping lb = 250 is the user's call for comparability; this is the
  watch that makes that choice safe.)

## 7. Backlog disposition (12 needs-experiment + 7 needs-apply-before-retrain, 2026-08-04)

needs-experiment:

| Lead (wiki slug prefix) | Disposition |
|:--|:--|
| obs4_student_extra_observation_interface | CLOSE-AND-UPDATE: blocked-on satisfied — Phase E ran 2026-08-04, report diagnose-20260804-132500; wiki status update due (X18 ext.) |
| obs76_gen_2_student_reproduces (new 2026-08-04) | CARRIED by G2 (dispersion floors) + §8 Q3 (adoption decision) |
| c4b_dagger_correction | REOPENED-CHEAP (X11): DAgger correction on gen-1 student, DGX-hosted, hours with cuDNN libpath fix |
| curriculum_recalibration_protocol | DEFER (X29): blocked on bounds sourcing (X21); governs the NEXT purpose's lb/budget re-derivation, not this run |
| experiment_idea_latency_transport_delay | DEFER (X30): off-DORAEMON blocker unchanged; priority raised by measured 25 Hz bus |
| hydrorc_is_half_recentered | DEFER (X28): probe design unwritten |
| joint1_stage_1 | DEFER (X31): needs unlimited-joint1 checkpoint |
| roll_transient_is_worst_at_none | DEFER (X34): sequenced after X35 (paper-phase 3-seed ablation); ordering question still with user |
| reward_sigma_integral (R6) | DEFER (X33): batch-pass parked per 2026-07-20 decision |
| stonefish_yaw_gap | DEFER (X36): hardware bench (XW540 step + T200 curve) |
| thruster_nonlinear_curve | DEFER (X37): T200 bench; keep-off decision stands |
| thruster_static_gain | DEFER (X38): same T200 bench decides alignment side |

needs-apply-before-retrain (all six plant items stay deferred iff this run continues the CURRENT
plant — §8 Q4; the seventh, metrics.yaml, is G4):

| Item | Disposition for THIS run |
|:--|:--|
| buoy_added_mass (guard-structure decision) | DEFER-to-plant-v2; USER-DECISION on sizing route |
| hydrorc_016d1b1 retire / HydroRC-v2 | DEFER-to-plant-v2 (re-derivation per axis required) |
| imu_45deg_offset | DEFER (user-deferred to robot bring-up, unchanged) |
| metrics_yaml_declares_doraemon_success_rate | **G4 — apply now** (widened to 6-token audit) |
| sim_hydro_nominal (TAM moment-arm band) | DEFER-to-plant-v2; ELEVATED STAKES at 48 h scale (single silent bias axis with no DR band) — named in launch ack |
| stonefish_rotational_drag | DEFER (Stonefish-side, no Isaac impact) |
| tam_vertical_single_motor (m4 remeasure) | DEFER-to-plant-v2; ELEVATED STAKES (structural allocation error no DR band covers) — named in launch ack |

Elevated-stakes warning (Q5): a plant change obsoletes every student distilled from the affected
teacher. At screening scale that sunk cost was hours; at 48 h it is days. If the B1/TAM bench can
be scheduled soon, consider sequencing it BEFORE committing the GPU time.

## 8. Open questions for the user (decisions this program cannot make)

1. **Is a DGX-trained teacher adoptable as THE final model at all?** The +109% cross-machine term
   currently forbids it → the 32768 run is scale exploration. Overturning the rule requires the
   X1 anchor (22.5 h) to have any denominator.
2. **Still want 32768?** 8x memory for 1.25x samples/s, 48.2 h, vs 3x4096 seeds at 22.5 h (a band,
   not a point), vs ~24 h at 16384 (unmeasured interpolation). Resource call. NOTE 2026-08-04: the
   32768 basis is weaker than this row implied — the only measurement is a 200-iteration probe with
   `fault.enable=false`, which cannot see DORAEMON at all (step_interval 250), and the only
   training-scale datapoint above 4096 is the 8192 arm, which measured NULL. Treat throughput and
   memory as measured, the learning outcome as NOT-DETERMINED.
2b. **ANSWERED 2026-08-04 — max_iterations = 20000** (user decision). The reasoning below is kept
   because it is what the run must be monitored against, not because the question is still open.
   The old "5000, do NOT raise" row is withdrawn (§3). What the
   record now supports: `max_iterations` enters the training code ONLY as the loop counter
   (`constraint_trpo.py:636-642 set_max_iterations` is log-only; barrier_t/barrier_alpha fixed; no
   LR/entropy/std scheduler anywhere), so there is no hidden 5000-tuned schedule that extension
   breaks — the one thing that moves with it is how far DORAEMON expands the box. What the record
   does NOT support is a specific value: the extension effect's sign flips with `performance_lb`
   (lb=250 pair degraded, lb=200 pair improved, both at the fair `none` level), every datapoint is
   on the retired posttam plant, and a naive 7000 lands curriculum saturation on the FINAL boundary
   with zero margin once counted in ACHIEVED expansions (extend8k: 26 achieved, last at iter 6750)
   and once mode=-3 attrition (fires 4/4 runs) and the 21st dim's KL dilution are subtracted.
   Deciding this needs either a bounds widening (blocked, §8 Q4) or an lb adjudication on the
   current plant.
3. **obs72 or obs76? — the metrics have now answered: obs72.** Both paired probes are in. The obs76
   teacher is genuinely better (G3), but X1-tailsplit removed the last excuse for the obs76 students
   underperformance — it fixed the delivery defect and the students still gained nothing in control.
   The only thing left for a human is the *requirements* question the metrics cannot settle: do you
   WANT the 4 real-sensor channels in the deployed observation for a reason other than performance
   (e.g. future sensor-fusion work, redundancy)? If yes, note the cost: tail-split assembly is
   mandatory and `deploy/specs/student_gru.py` must be extended first (it rejects tail mode today).
   If no, obs72 stands with no open metric question.
4. **Current plant or plant-v2 batch?** Current plant → six deferred items stay deferred (as obs4
   program decided). Plant-v2 → T200 bench + XW540 bench + buoy guard decision must close first.
5. **Schedule the B1/TAM bench before committing 48 h?** See elevated-stakes note in §7.
6. **Purpose string** `teacher_final_dgx32k` — confirm before launch (fixed for every run of the
   purpose).
7. **Re-test C3's adoption under SE statistics (X9) before it is written up?** Zero GPU; changes
   the claim's strength, not the shipped artifact. NOTE: X9 was framed around teacher-vs-student
   evals being unpaired — that is no longer true (9eac3a8). A re-run pair is now genuinely paired,
   so X9 becomes "recompute against the registered floors", cheaper and stronger than the SE plan.
8. **NEW, raised by X1 (2026-08-04): is a teacher-side scale-up the right investment at all?**
   The five-arm paired table in §1 shows every student landing at 2.5–3.1 deg hard roll dispersion
   regardless of whether its teacher sits at 1.07 or 2.02. The distillation step, not the teacher,
   is what caps the shipped artifact — and the DGX flagship optimizes the teacher. This does not
   invalidate the flagship (a better teacher is still worth having, and 32768 answers a
   scale question nothing else answers), but the user should decide it knowing that the measured
   bottleneck is downstream of what the run improves. No probe is designed for the distillation
   gap yet; a capacity arm (GRU256) is the named runner-up family and must pre-register a CONTROL
   endpoint sized through the measured exchange rate — X1 showed a 6.7% latent-RMSE gain cannot
   clear the control floor, so an arm must project a latent move of roughly 12%+ to be worth running.

## 9. Cheap follow-ups (not blocking, recorded so they are not lost)

X10 encoder sweep on both teachers (Grad/enc_step −36% question) · X11 DAgger-correction re-open ·
X12 per-env ss stats engine gap · X13 analyze_training student namespace · X14 wandb alert arming ·
X15 hard-survival root cause (2 dead envs, npz parse) · X16 DGX cuDNN libpath verify ·
X18 plan-doc/wiki status sync (incl. the two obs4-program leads) · X19 rsl-rl source verify ·
X40 gen-2 deploy pack export (only if gen-2 ever adopted).

## 10. Handoff

`HANDOFF-DGX.md` (beside this file) is the paste-as-is prompt for the DGX-side session. It embeds
the recommended defaults (32768 / obs72 / current plant / purpose `teacher_final_dgx32k` / seed 30)
— review §8 answers first, then paste.
