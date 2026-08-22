# Program: teacher-final-replicate — reproducible final teacher, 2 seeds, incumbent config

Opened 2026-08-10 by the transcript-audit session. Supersedes `dgx-final-teacher` for the
final-model question; that program's Arm W/Arm D results are inputs here, not continuations.

## Objective (user, verbatim)

> 이번 주 목요일에 실제 실기동(field test)에 나간다. 이것이 진짜 마지막 학습이고,
> 워크스테이션·DGX 산출물 중 더 나은 쪽이 실제 로봇에 배포된다.

> 참고로 보드의 코드는 얼마든지 수정 가능하긴 해. 그럼 어떻게 해야하는데?
> 최종 학습 모델을 만들려면 어떻게 해야하는건데

Decisions taken by the user 2026-08-10 in response to the audit:

> 돌린다 — 현직과 같은 설정으로 시드 2개 (권장)

> GRU 본선 + TCN 폴백 동시 준비 (권장)

## What this round is, and what it is not

This round does **not** attempt a better teacher. The audit
(`vault: notes/2026-08-10-final-training-prompt-audit.md`) established that every lever tried
this campaign is exhausted or refuted:

| lever | outcome |
|---|---|
| `num_envs` 4096 → 16384 | +250 pre-saturation iterations, best 0.4968° vs 4096's 0.5070° — inside single-seed noise, at ~11x compute |
| `kl_ub` 0.12 → 0.06 (Arm W) | 20000 iterations, 0/21 saturated, lost the finalist to the incumbent |
| `entropy_coef_per_dim` ×2 | measured against the correct single-variable control (`trpo_dgx16k_s30_260805_185713`), success 0.42469 vs 0.73864 and reward 244.29 vs 260.80 at iter 900–1100, `DORAEMON/mode` −2 (contracting) vs 0 (expanding). The PASS verdict compared against a 4096 workstation run — a swapped baseline |
| `performance_lb` ↓ | a curriculum gate, not a quality dial. Changing it makes this round incomparable to the incumbent |

The remaining candidate for the feasibility ceiling is a global plant/reward-scale gap
(thruster static gain, measured 4.65x in the usable band with DR 0), which requires the
unbooked T200/XW540 bench session. Out of reach inside this week.

So the round's purpose is narrower and achievable:

1. **Reproducibility.** The incumbent `model_9998` is the tail of a 3-run resume chain whose own
   `agent.yaml` records `load_run: RESUME_SRC` — a literal placeholder. Its lineage is not
   reconstructible from its saved config. A from-scratch run at the same settings produces a
   final artifact whose provenance is a single config file.
2. **Seed variance.** The current "incumbent beats Arm W" verdict is n=1 vs n=1. Two more points
   make the finalist a real comparison.
3. **No downside.** If both lose to the incumbent, the incumbent ships unchanged.

The critical path is the deploy chain (below), not this training.

## Config provenance — every key, incumbent vs this round

The failure mode this table exists to prevent: a run named "final" whose config was assembled
from defaults plus whatever knob the conversation happened to name. Every differing key is
listed with a reason; every identical key is listed as deliberately held.

Incumbent = `teacher_iter_budget/trpo_iterbudget_s30_260805_012813` (4096 envs, `model_9998`).

### Deliberately changed (3 keys)

| key | incumbent | this round | reason |
|---|---|---|---|
| `resume` | `true` | **`false`** | the whole point — remove the unreconstructible resume chain |
| `load_run` / `load_checkpoint` | `RESUME_SRC` / `model_4999.pt` | unset | follows from `resume: false` |
| `seed` | 30 | **30 (WS) / 31 (DGX)** | seed 30 reproduces; seed 31 measures seed sensitivity |
| `max_iterations` | 5000 (incremental on a 4999 base → `model_9998`) | **10000** | absolute budget matching the incumbent's endpoint. With `resume: false`, `max_iterations` is absolute, not incremental (verified: `e3_extend10k` set 10000 with `resume: true` and produced `model_14998`) |

### Deliberately held (every other tunable)

| key | value | why held |
|---|---|---|
| `num_envs` | 4096 | 16384 buys nothing (table above). Holding it also means the DORAEMON episode-count parameters need no rescaling — the Arm D defect cannot recur here |
| `doraemon.kl_ub` | 0.12 | 0.06 failed to saturate |
| `doraemon.performance_lb` | 250.0 | re-derivation deferred: it changes curriculum behaviour and would make this round incomparable to the incumbent. Inputs for the re-derivation are recorded in the audit note for the next round |
| `doraemon.alpha` | 0.5 | the other half of the feasibility gate; untouched for the same reason as `performance_lb` |
| `doraemon.step_interval` | 250 | iteration-clocked; `num_envs` unchanged so the 1/k rescale does not apply |
| `doraemon.buffer_size` | 2000 | episode-count; `num_envs` unchanged. Note: 2000 was never tuned *for* 4096 — it is the dataclass default and no env config overrides it |
| `doraemon.min_episodes` | 200 | same as above |
| `doraemon.init_concentration` | 30.0 | never swept in 25 run groups; held because changing it moves where the curriculum starts |
| `doraemon.min_ess_ratio` | 0.01 | held |
| `algorithm.entropy_coef_per_dim` | (0.01, 0.01, 0.001×6) | ×2 is a regression against the correct control (table above). Additionally inert on 5 of 8 dims, which are hard-projected to `min_std_per_dim` every step |
| `algorithm.min_std_per_dim` | (0.1, 0.1, 0.05×6) | already probed and ruled out as the lever (`trpo_minstdthr008`) |
| `algorithm.max_kl` | 0.005 | TRPO trust region, unchanged all campaign |
| `algorithm.num_mini_batches` | 4 | the 4 → 16 recommendation is specifically a 16384-env critic-scaling correction; irrelevant at 4096. Never applied in any run in the tree |
| `algorithm.barrier_t` / `barrier_alpha` | 100.0 / 0.02 | verified fixed for the run's life; `set_max_iterations()` is logging-only (`constraint_trpo.py:636-642`) |
| `num_steps_per_env` | 64 | batch-size half; must match across both machines for any cross-run comparison |
| `observation_space` / `use_bias_ema_obs` | 72 / `true` | current plant generation. `bias_ema_alpha` 0.99 |
| `env.fault.enable` | `true` | matches incumbent and both prior arms |
| `save_interval` | 50 | held |

### Explicitly deferred, NOT silently dropped

| item | state | why deferred |
|---|---|---|
| `control_decimation` 1 → 5 | still 1 in code, OPEN-AMBIGUOUS since 2026-06-29 | `teacher-final-closeout/PLAN.md:240` — applying it invalidates the saturation anchor. Its stated resolution point is "robot bring-up", which is this Thursday. **[DECISION-REQUIRED: control_decimation]** |
| latency in the final training config | recorded user direction 2026-07-20, "not actionable yet" | `teacher-final-closeout/PLAN.md:225` — blocked on a missing instrument (Z4). Surfaced here rather than dropped. **[DECISION-REQUIRED: latency_obs]** |
| `plant_change_batch_v2` (5 physics corrections) | not applied | user decision 2026-08-05 to skip hardware-measurement items; bench session has no booked date |
| `performance_lb` / `alpha` re-derivation | not applied | see table above; inputs recorded for the next round |
| `fault_severity` nominal 0.0 → 0.0771 | not applied | one-variable change documented in `fault_dr/trpo_ftc1sevinit/DESIGN.md`, never carried forward. Applying it now would break comparability with the incumbent |

## Code provenance — the two machines are on different commits, verified inert

| machine | branch | HEAD |
|---|---|---|
| workstation (container `marinelab-isaaclab`) | `exp/koopman-marine-obs` | `8a41029` (8 commits unpushed) |
| DGX (native) | `main` | `1062dc2` |

`main` is a strict ancestor of `exp/koopman-marine-obs` (merge-base = DGX HEAD, `0 / 88`). The 88
commits plus the 8 unpushed ones add only observation-widening toggles, all defaulting to
`False` / `""`, plus analysis-side `eval.py` options. No reward, DR, DORAEMON-curriculum, or
algorithm file is touched by either diff. The 8 unpushed commits are entirely the Koopman
step-2/3 line, which was NULLed and closed (`koopman_module_path: str = ""` default → no-op).

Neither machine's working tree has an uncommitted source change (DGX: one `.pyc`; workstation:
`.omx/` bookkeeping only).

**Mitigation for the one residual risk**: `eval.py` differs by +234 lines between branches, and
it is the selection instrument. Therefore **all selection and finalist evaluation runs on the
workstation**, on one `eval.py`, against one anchor. DGX checkpoints are copied to the
workstation for evaluation; they are never scored in place.

## Runs

Both 4096 envs. Measured steady-state rates: workstation 3.44 s/iter (Arm W full 19999-iteration
run), DGX 4096 solo 5.5 s/iter (`bench_spark`, `seed_floor_dgx` seed 30). Two concurrent DGX runs
degrade to 12.0 s/iter each — no parallel gain, so DGX carries exactly one run.

| arm | machine | seed | iters | ETA |
|---|---|---|---|---|
| R30 | workstation, cuda:0 (RTX 4070) | 30 | 10000 | **9.6 h** |
| R31 | DGX | 31 | 10000 | **15.3 h** |

### Launch commands — APPROVED AND EXECUTED 2026-08-10 14:04 KST

User approval, verbatim: "그대로 발사 — 현직 복제 R30 + 시드 R31, 10000 iter (권장)".

⚠️ **Path correction, verified before launch**: inside the container `HOME=/root` and
`~/workspace` does **not** exist. The `~/workspace/...` form carried in `dgx-final-teacher`'s
PLAN is wrong for the container and correct only for the DGX. Both launches were staged as
scripts and `bash -n` syntax-checked before firing, so no quoting error could reach the shell.

R30, workstation — `/workspace/launch_R30.sh` in container `marinelab-isaaclab`,
fired with `docker exec -d marinelab-isaaclab bash /workspace/launch_R30.sh`
(fire-time path, kept for provenance; on 2026-08-14 the script was filed per
`scripts/finalize_run_log.sh` as the run's own `launch.sh` — see HANDOFF.md §1):

```bash
cd /workspace/constrained-albc
TERM=xterm /workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 \
  --num_envs 4096 --max_iterations 10000 --headless --seed 30 \
  --run_group teacher_final_replicate \
  --logger wandb --log_project_name teacher_final_replicate \
  env.fault.enable=True \
  agent.run_name=replicate_s30 \
  > /workspace/constrained-albc/R30_launch.log 2>&1
```

R31, DGX — `~/launch_R31.sh`, fired with
`ssh ksm-nas 'setsid nohup ~/launch_R31.sh > /dev/null 2>&1 < /dev/null &'`:

```bash
cd "$HOME/workspace/constrained-albc"
TERM=xterm "$HOME/workspace/isaaclab/isaaclab.sh" -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 \
  --num_envs 4096 --max_iterations 10000 --headless --seed 31 \
  --run_group teacher_final_replicate \
  --logger wandb --log_project_name teacher_final_replicate \
  env.fault.enable=True \
  agent.run_name=replicate_s31 \
  > "$HOME/R31_launch.log" 2>&1
```

Neither command carries an `env.doraemon.*` or `agent.algorithm.entropy_coef_per_dim` override.
That absence is the deliberate content of this round and is what the held-keys table certifies.

Liveness confirmed 14:04 KST: three-process chain present on both machines
(`isaaclab.sh` → `python.sh` → `kit/python/bin/python3 scripts/train.py`) with the intended
argv on each. Artifact confirmation (`model_50.pt`) is the actual gate and is polled separately.

No `env.doraemon.*` override and no `agent.algorithm.entropy_coef_per_dim` override appears in
either command — that absence is deliberate and is what the held-keys table above certifies.

### Launch-environment guards (both learned the hard way 2026-08-09/10)

- `TERM=xterm` — detached shells have no TTY; `isaaclab.sh` calls `tput` and dies rc=1 with
  `'ansi+tabs': unknown terminal type`.
- `--headless` — display-less boxes.
- **Never `CUDA_VISIBLE_DEVICES`.** Isaac Sim uses Omniverse device enumeration; remapping breaks
  it. The 2026-08-10 12:48 student run launched with `CVD=1`, logged
  `Skipping NVIDIA GPU due CUDA being in bad state`, and exited rc=0 with zero checkpoints. If a
  device must be pinned, use the Isaac Lab flag `--device cuda:N`; neither command above needs it
  because the default is already `cuda:0`, which is the RTX 4070 on the workstation.
- **Verify by artifact, not by rc.** After launch, confirm the run directory exists and
  `model_50.pt` appears within ~5 min (workstation) / ~8 min (DGX).
- Killing: never `pkill -f <pattern>` over ssh — it matches the ssh command line and kills the
  shell first. Kill by PID.

### Pre-launch gates

- [ ] `omx wiki list --status needs-apply-before-retrain` — expected empty. **Empty is not
      reassurance here**: the audit found the entropy/`num_mini_batches` findings carry no status
      field at all and are invisible to this gate. The held-keys table above is the real gate.
- [ ] Both machines idle (`docker exec ... nvidia-smi`; `ssh ksm-nas nvidia-smi`).
- [ ] Workstation GPU 0 is the RTX 4070 (12 GB) — 4096 envs measured ~11.3 GB, does not fit the
      4060's 8 GB.
- [ ] Container is `marinelab-isaaclab`, not the decoy `marinegym-isaaclab`.

## Deploy chain — the actual critical path

Runs in parallel with training and does not depend on it. The audit's finding is that the only
ship-blocking defect is here, not in the teacher.

**Blocker**: board `np_policy.py:57` hardcodes `POLICY_OBS_DIM = 69`; every pack from the current
plant generation is 72D (`obs: 72, teacher_input: 81`). `np_policy.py:153-155` raises on mismatch,
so the policy will not load. The obs assembler is not shipped inside packs, so no re-export fixes
it. Board code is user-authorised for modification (2026-08-10).

Port spec, fully determined from `albc_env.py:1389-1398` and `:1235`:

```
err3      = [roll_err, pitch_err, yaw_rate_err]        # board already computes these
_bias_ema = a * _bias_ema + (1 - a) * err3             # a = 0.99  (cfg.reward.bias_ema_alpha)
policy_obs = concat(policy_obs, _bias_ema)             # appended last, initial value zeros
```

The 3 channels carry no sensor noise (zero-padded in both `_OBS_NOISE_STD` and `_OBS_BIAS_MAG`).

Order of work:

1. Export a deploy pack from the already-completed incumbent student
   (`student_final_round/trpo_sdfinal_c3_gruselect_inc9998_s30_260810_124813/models/student_999.pt`)
   via `scripts/export_deploy_pack.py` (`docs/how-to/deploy-pack-export.md`).
2. Port the 3 `_bias_ema` channels into the board's `_assemble_obs`; bump `POLICY_OBS_DIM` to 72.
3. Close 1e-5 parity in-container **and on the board** (numpy 1.11.0 — `keepdims` is silently
   ignored there; the existing code already avoids it, keep it that way).
4. **GRU primary + TCN fallback** (user decision). The GRU runtime path has never been closed on
   the physical board (`albc_rl/CHANGELOG.md` v1.0.0: TCN-only deployment, `test_gru [SKIP]`).
   Export both; if board-side GRU parity does not close, ship TCN.
5. `ssh agent-jetson 'cd ~/catkin_ws/src/robot/albc_rl && git log -1 --oneline && git status -s'` —
   confirm the board clone carries the applied fixes (accumulator seed `b28648c`, gyro `e9a8f01`)
   and that the firmware is flashed with the gyro-publishing build.
6. Delete or clearly mark stale: `deploy/student_albc_260607/numpy_port/np_policy.py` is a Jun 12
   pre-fix duplicate at exactly the path every diagnosis cites (`:75,87`). Copying it to the board
   reintroduces the accumulator defect fixed in June.

Target: a shippable incumbent-based artifact by **Tuesday**, so Wednesday is buffer. The
replicate runs, if they win, swap in on Wednesday.

## Open wiki leads — disposition by slug

`omx wiki list --status needs-experiment` returns 5. None is dropped silently.

| slug | disposition |
|---|---|
| `doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_` | **Carried, not addressed.** This is the ceiling that killed Arm W. Addressing it means moving `performance_lb`/`alpha` or lifting the plant, and this round deliberately holds both so it stays comparable to the incumbent. Inputs for the re-derivation (saturated-run buffer distributions, and the fact that the gate's boundary statistic is the median, not p25) are recorded in the audit note for the next round. |
| `joint_target_runaway_is_not_a_sim_to_real_gap_both_sides_unbound` | **Resolved in fact; wiki page is stale.** The deploy-side reset asymmetry was fixed 2026-06-15 (`code/agent-jetson/robot/albc_rl/numpy_port/np_policy.py:218-220`, commit `b28648c`), 56 days before the page described it as open. The page's citation `np_policy.py:75,87` points at a pre-fix duplicate under `deploy/student_albc_260607/`. No training implication. Page should be closed after the board-clone check in the deploy chain confirms the board carries `b28648c`. |
| `sigma_decay_under_an_expanding_dr_curriculum_literature_verdict_` | **Closed for this round's purposes.** M2 already showed sigma trajectory is not what separates a saturating run from a failing one (Arm W vs reference matched within 0.5–2.6%, tolerance ±10%). The one remaining lever the page pointed at, `entropy_coef_per_dim` ×2, is refuted against its correct control. No config change. |
| `where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu` | **Executed this session (M3), result REJECT, with a stated weakness.** Quintile decomposition over `doraemon_state.pt` `buffer_xi`/`buffer_returns` for all 21 dims: Arm W's quintile means span ~11 points around its 241.28 mean with no dimension approaching the pre-registered "200 vs 250+" signature. Largest trends: `fault_severity` 246.03 → 236.96, `buoy_volume_scale` 235.25 → 246.41 (opposite sign). **Weakness to record**: the 2000-episode ring buffer is ~11 training iterations at 4096 envs, drawn while the curriculum was in contracting mode (−2), so the suspect upper range may be absent from the data that exonerates it; and marginal per-dimension tests cannot see a two-dimension interaction. No DR cap applied this round. |
| `the_c3_recipe_does_not_transfer_across_teachers_on_a_same_width_` | **Carried into the deploy chain — this is the one with a live consequence.** If the c3 distillation recipe does not transfer across teachers, then a winning R30/R31 cannot simply reuse the recipe that produced the incumbent's student. Mitigation: the incumbent-based pack is built first and is the shippable baseline; a replicate only swaps in after its own distillation is verified on the same gates, not assumed. |

## Predicted outcome

**Most likely: a null, and that is an acceptable result for this round.** Both replicates are
expected to land inside seed noise of the incumbent — 21/21 DORAEMON saturation by iteration
~7000 (the 4096 lineage's iteration-clocked saturation point), buffer-return p50 in the 255–261
band, and a best `none`-condition steady-state error near 0.50–0.51° (incumbent 0.5070°,
`trpo_hydrorc` 0.5067°, dgx16k 0.4968° at 4x envs). Nothing in this configuration is new, so
there is no mechanism for a large gain.

The one mechanism by which a replicate could genuinely beat the incumbent: the incumbent is the
tail of a 3-run resume chain, and a resumed policy can be stuck in a worse basin than a clean
from-scratch run of the same length reaches. If that is happening, R30 (same seed, same settings,
no resume) exposes it directly.

What the round delivers even on a full null:

1. A final artifact whose provenance is one config file rather than an unreconstructible
   `RESUME_SRC` chain.
2. The first seed-variance estimate for this plant generation — which converts every
   "A beats B" verdict in this campaign from n=1 vs n=1 into a statement with a dispersion.
3. A negative result worth recording: that the incumbent's numbers are reproducible from scratch,
   which is currently assumed and never tested.

Failure modes that would make the round uninformative, and their tells: a silent process death
(`teacher_final_dgx32k` was OS-killed at iteration ~287 of 5000 on 2026-08-04, cause never
established — watch DGX for a missing `model_N.pt` past its due time), or a launch that exits
rc=0 having trained nothing (the `CVD` trap). Both are caught by the artifact check in the
launch guards, not by the exit code.

## Selection

Three-way on the workstation, one `eval.py`, one anchor: incumbent `model_9998`, R30 best,
R31 best. Pre-registered before any result is read:

- Decide at `hard` and `ood` conditions, never at `none`.
- Per-env paired differences, not group means. Before reading any metric, confirm the 24
  `dr_*`/`fault*` arrays are elementwise identical across the compared runs (24/24).
- Quote `rms`/mean only. Never `peak` for cross-run comparison.
- Best-checkpoint tracking per run (DORAEMON authors' own prescription, arXiv:2311.01885 §5.2),
  not last-checkpoint.
- Filter eval directories by a batch-start-time cutoff; the eval tree contains prior-session
  leftovers at other anchors and seeds.

## Decisions for the user

- **[DECISION-REQUIRED: control_decimation]** — parked since 2026-06-29 with "resolve at robot
  bring-up" as its trigger. Bring-up is Thursday. Applying it now invalidates the anchor and makes
  this round incomparable; not applying it ships an unresolved sim-to-real timing gap. Recommend:
  do not apply, carry it as a known gap into the field test and log for it.
- **[DECISION-REQUIRED: latency_obs]** — user direction of 2026-07-20 that latency be in the final
  training config. Still blocked on a missing instrument. Recommend: explicit defer, recorded here
  so it is not silently dropped a third time.
