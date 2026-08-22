# Handoff — dgx-final-teacher (live state, written 2026-08-09 16:25 KST)

Paste-as-is resume note. Everything needed to continue is here or produced by the commands below.
Plan SSOT is `PLAN.md` beside this file (`omx program-lint` clean). This file is the OPERATIONAL
state: what is running, what was already verified, what fires next.

## Objective (carried from PLAN.md, verbatim)

> "다음 실험을 dgx에서 진행할껀데, num envs나 max iter 같은 경우는 늘리기는 하되
> claude의 판단에 맡기는거야. num envs가 3만이 과하다 하면 줄여도 괜찮고, max iter도
> 마찬가지로 20,000 정도가 과하다 하면 낮춰도 괜찮아. 어쨌든 중요한건 **최고의 성능이
> 나오도록 학습**할 수 있게 하면 되고, **관련된 결합 파라미터도 파악해서 수정**하는거지.
> marinelab에 여러 실험 기록이 있으니 그걸 참고하고. **이 한번을 마지막이라고 생각하고
> 꼼꼼하게 분석 및 조사 후 계획**을 세우도록 하고, 지금 현재 완료된 dgx 실험의 결과도
> 포함해서 분석하도록 말이야."

## Machines — read this before any command

| name | what it is | how to reach |
|:--|:--|:--|
| workstation | `ksm-MS-7E01`, RTX 4070 + 4060. Arm W runs here. The **adoptable** machine. | `ssh ksm-ubuntu 'docker exec marinelab-isaaclab bash -lc "cd /workspace/constrained-albc && <cmd>"'` |
| DGX | `seungmin-dev`, GB10. Arm D would run here. | `ssh ksm-nas` **from the Mac only** — the workstation cannot resolve `ksm-nas` |

`omx` works ONLY inside the marinelab container. Repo is `/workspace/constrained-albc` in-container,
`~/workspace/1_code/5_marinelab_ws/constrained-albc` on the workstation host.

## RUNNING NOW — Arm W

| field | value |
|:--|:--|
| run_id | `trpo_rampw_kl006_s30_260809_161913` |
| campaign | `teacher_final_ramp` (wandb project = same string) |
| started | 2026-08-09 16:19:13 KST |
| config | 4096 envs, `kl_ub` **0.06**, `step_interval` 250, `max_iterations` 20000, seed 30, from scratch |
| measured | **3.30 s/iter** (faster than the 4.19 budgeted) -> ETA ~18.8 h, finish ~2026-08-10 11:05 KST |
| sha | constrained-albc `8a41029`, marinelab `a1d8b2f`, training code tree verified clean |
| stdout log | `/workspace/constrained-albc/.omx/scratch/armW_launch.log` |
| run dir | `logs/rsl_rl/albc_trpo_teacher/teacher_final_ramp/trpo_rampw_kl006_s30_260809_161913/` (also `.../latest`) |

**G1 PASSED — do not re-verify.** Read from the dumped `params/env.yaml` + `agent.yaml`:
`fault.enable: true`, `kl_ub: 0.06`, `performance_lb: 250.0`, `step_interval: 250`,
`observation_space: 72`, `use_bias_ema_obs: true`, `use_extra_policy_obs: false`,
`use_privileged_fault_obs: false`, `max_thrust_scale (0.85, 1.15)`,
`thrust_coefficient_scale (0.7, 1.3)`, `num_envs: 4096`, `max_iterations: 20000`, `seed: 30`.

### Gates for Arm W (in firing order)

1. **~iteration 500** (~30 min in): abort if `DORAEMON/kl_step` is not reaching the new cap **0.06**
   on accepted updates while `mode <= -2`; or `success_rate` pinned > 0.95 or < 0.5; or any dim
   already Beta(1,1); or NaN in metric lines. Scan `kl_step > 0` over ALL steps — it is written 0 on
   every non-boundary iteration, so a fixed-stride sample reads 0 everywhere and looks like "no
   expansions".
2. **Saturation, expected ~iteration 14,750** (59 boundaries x 250 at `kl_ub` 0.06 against the
   3.5209 KL distance measured on Run A). Confirm 21/21 Beta(1,1) in `doraemon_state.pt` and
   `kl_step` -> 0. **Not saturated by 17,000 = the budget arithmetic is wrong -> report, do not kill.**
3. **Inert-gate watch, the risk direction is INVERTED for this arm.** A slower ramp keeps
   `success_rate` HIGHER, so the danger is the 0.95 inert ceiling, not the alpha 0.5 floor. Healthy
   at saturation on this plant under the FAST ramp is 0.62-0.70; this arm should settle above that.
   Sustained > 0.95 means `performance_lb` = 250 has stopped constraining anything -> kill, keep the
   best checkpoint, report.

## NEXT ACTION — Arm D probe (blocked on a measurement, not on time)

Arm D is queued pending-approval and **must not launch until its exploration probe passes.**

The probe's target is Arm W's own sigma trajectory, which becomes readable ~1 h after Arm W's start
(1100 iterations x 3.30 s), i.e. from **~17:20 KST 2026-08-09**. Read it with:

```bash
# from the Mac, on the workstation container
D=logs/rsl_rl/albc_trpo_teacher/teacher_final_ramp/latest/train
# window-mean Policy/mean_noise_std over iterations 400-600 and 900-1100
```

Reference values already measured on 4096 (`trpo_hydrorc_s30`, current plant): **0.1851** at 400-600,
**0.1376** at 900-1100. The 16384 default reads 0.1307 / 0.1024 (-29% / -26%).

Probe = 16384 envs, ~1100 iterations, default logger (NOT `--logger off`: the sigma read needs the TB event file), on the DGX, with
`agent.algorithm.entropy_coef_per_dim` scaled by k. Try **k = 2** first (a sqrt(4) noise-scale
heuristic — flagged as a heuristic, the literature behind it excludes trust-region methods); if sigma
is still low, k = 3. Cost 5.5 h each at 18.07 s/iter measured; the 400-600 window lands at ~3.0 h, so an early verdict is possible without waiting for 1100.

**If no k restores the trajectory, Arm D is NOT launched.** A treatment that does not take cannot
discriminate, and 50 h is not spent on it.

Verify the Hydra list-override parses into a tuple with a 50-iteration smoke BEFORE the probe:
`agent.algorithm.entropy_coef_per_dim='[0.02,0.02,0.002,0.002,0.002,0.002,0.002,0.002]'`. If it does
not, make the change as a commit on a tagged branch instead — the protocol this project already
requires (clean tree, tagged branch, sha in manifest).

Arm D full config (queued): 16384 envs, `kl_ub` 0.12 unchanged, `step_interval` 250,
`max_iterations` 10000, seed 30, `entropy_coef_per_dim` x k, `env.fault.enable=True`.
Campaign `teacher_final_entcomp`. Expected saturation ~7,250 (measured on the 16k run).
During the run watch `Loss/cost_value` against the 4096 reference at matched iterations — it ended
+29% and diverging in the 16k run; if it repeats, `num_mini_batches` 4 -> 16 is the pre-registered
follow-up, NOT a mid-run change.

## Judgment rule — how this round ends

The incumbent is **`teacher_iter_budget/trpo_iterbudget_s30_260805_012813/train/model_9998.pt`**,
promoted by the G0 gate today. Any new checkpoint must beat it, or the incumbent ships.

1. **Selection pass, `none` only, per arm.** Arm W: 15,000 / 16,000 / 17,000 / 18,000 / 19,000 /
   20,000. Arm D: 7,500 / 8,000 / 9,000 / 10,000. All `--seed 42` so per-env differencing applies.
2. **Finalist pass.** Best per arm + `model_9998`, re-scored **in ONE batch, on ONE machine (the
   workstation), under ONE saturated anchor** via `--doraemon-dr-from`, at `none` + `hard` + `ood`.
   The anchor used today is
   `experiments/.../teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/train` (21/21 Beta(1,1)).
   **Select at `hard`/`ood`, not at `none`** — the `none` ranking dissolves there (t = +7.53 -> +0.63).
3. **Overfit check.** Winner and runner-up re-scored at `--seed 43`. Ranking flips = exam-specific.
4. Verify pairing (24/24 `dr_*`/`fault*` arrays elementwise identical) BEFORE reading any metric.

Eval invocation form (verified today):

```bash
TERM=xterm /workspace/isaaclab/isaaclab.sh -p constrained_albc/analysis/eval.py static \
  --checkpoint <experiments path>/train/model_<N>.pt \
  --num_envs 64 --seed 42 --headless --ood --doraemon-dr-from <ANCHOR train dir>
```

Checkpoint MUST go through the `experiments/.../train/` symlink and `--output_dir` must be omitted,
or the eval scatters outside `experiments/<run_id>/eval/`.

## Traps this session already hit — do not rediscover

- `python` is not on PATH in a non-interactive container shell. Use
  `TERM=xterm /workspace/isaaclab/isaaclab.sh -p <script>`; plain `python` gives rc=127 instantly.
- `--doraemon-dr-from` reads **TB event-file `DORAEMON/mean/*` scalars**, not `doraemon_state.pt`, so
  it must point at the `train/` dir. It also expects a directory and raises if missing.
- **`none`-invariance holds within a machine, not across machines.** The same checkpoint moved -4% on
  `none` when re-scored on a different GPU, while a same-machine control reproduced exactly. Never
  compare a recorded score from one machine to a fresh score from another; re-score both.
- Anchor asymmetry is invisible in `summary.json` — it shows up only in the `dr_*` draw spans of the
  npz. Two runs can both print "hard" and be graded on different boxes.
- `pgrep -f "eval.py static"` over ssh matches the ssh command line itself. Judge completion by
  `summary.json`, or poll the PID.

## Open, needing the user

1. **Commit branch.** Every new artifact is untracked on `exp/koopman-marine-obs`, which carries
   another session's uncommitted work: `.omx/programs/dgx-final-teacher/`,
   `.omx/campaigns/teacher_final_{ramp,entcomp}/`, `.omx/runs/trpo_{rampw_kl006_s30,entcomp_s30}/`,
   plus 4 new wiki pages. Needs a decision: main, or this branch.
2. **D5 — the only question that can raise the ceiling.** How much do the T200 command-to-thrust
   bench and the XW540-T260 step response actually cost? Half a day makes them the highest-value
   action available and they should precede any further training. Days, or no rig, and the DR box
   stays frozen and the plan's Option A stands.
3. Arm D launch approval, after its probe passes.

## Recorded status of this plant (launch ack, per the open-actionable ledger)

Both arms are **pre-vertical-TAM** (verified today: `config.py:93` Fz row is still
`(0,0,0,0,1,1)` — the real robot is one motor with dual-ESC wiring), **pre-IMU-45deg-offset**, and
**pre-plant-batch-v2** (four Isaac corrections batched behind the T200/XW540 benches). `omx
queue-launch` did not refuse because those items read `status: resolved`, which in this project means
"moved to the hardware queue", NOT "applied in code".

## Monitoring (armed 2026-08-09 16:28 KST)

A `Monitor` task polls Arm W every 120 s from the Mac and emits an event only on things
that change what to do next. Probe script: `/workspace/constrained-albc/.omx/scratch/dgx-final-teacher-analysis-scripts/armw_probe.sh` in the container
(host `~/workspace/1_code/5_marinelab_ws/armw_probe.sh`, one line `IT=<n> ERR=<n> ALIVE=<n>`).

| event | meaning |
|:--|:--|
| `ARM W GATE 1 ready` (it >= 500) | run the gate-1 checks below |
| `ARM W SIGMA READ ready` (it >= 1100) | Arm D probe target is now readable |
| `ARM W SATURATION window` (it >= 14750) | check 21/21 Beta(1,1) |
| `ARM W STALLED` | iteration frozen 10 min while process alive |
| `ARM W DIED` / `ARM W COMPLETE` | process gone; distinguished by whether it >= 19990 |
| `PROBE-FAIL x3` | cannot reach the container — run state UNKNOWN, check manually |

`ALIVE` uses `pgrep -cf 'scripts/[t]rain.py'` — the bracket is what stops pgrep from
matching its own command line (the trap recorded below). It reads 3 normally
(`isaaclab.sh` wrapper, `python.sh`, the trainer); any value > 0 means alive.

Re-arm after a session restart by re-running the same `Monitor` command; the probe script
is already deployed and needs no redeployment.

## Plant identity verified — Arm W vs the incumbent (2026-08-09 16:36 KST)

Arm W runs on `exp/koopman-marine-obs` (`8a41029`), which carries another session's work:
**257 files, +45,849 lines** against `main` (`1062dc2`, which is what the DGX has). That is a
live risk to the head-to-head — a final deliverable trained on a plant nobody else measured
would be uncomparable to `model_9998`. It is now closed, with evidence.

**Config check.** Flat key-by-key comparison of Arm W's dumped `params/env.yaml` against the
incumbent run's `config/env.yaml`
(`teacher_iter_budget/trpo_iterbudget_s30_260805_012813`), excluding pickled buffers and the
intended knobs: **367 keys compared, 1 differs** — `koopman_module_path`, absent in the
incumbent and empty in Arm W, i.e. a new field that is off. Script kept at
`/workspace/constrained-albc/scripts/plantdiff.py` (takes two globs, prints only the differing keys).

**Code-path check.** Config parity does not prove code parity, so `git diff --numstat` over
`envs/main` + `envs/_core`: every teacher-path file is a **pure addition** except
`albc_env.py`, which has 3 deletions. All three are cosmetic — two single-line imports
rewritten as parenthesized multi-line imports, and one f-string inside a `ValueError`
message. No always-on teacher code changed.

**Conclusion.** Arm W's plant == the incumbent's plant, and `main` (the DGX) differs from
Arm W only by dormant additions, so Arm D is comparable to both. **Do not re-open this.**

Do NOT use `teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136` as the plant reference —
it predates the 2026-07-30 retraction and still carries `added_mass` heave `8.0`, since
reverted to `1.0`. Comparing against it manufactures a plant difference that is not there.

## Arm D blocker cleared — Hydra list-override parses (2026-08-09 16:40 KST)

The pre-registered blocker on the Arm D probe is closed. On the DGX, `exit=0`, and the dumped
`params/agent.yaml` reads:

```yaml
entropy_coef_per_dim: !!python/tuple
- 0.02
- 0.02
- 0.002        # x6
```

So `agent.algorithm.entropy_coef_per_dim='[0.02,0.02,0.002,0.002,0.002,0.002,0.002,0.002]'`
reaches the config as a tuple with the k=2 values. **No commit and no tagged branch are needed**
— the probe uses the CLI override directly. Smoke was 64 envs / 3 iterations / no logger, left
at `logs/rsl_rl/albc_trpo_teacher/_smoke_hydra/` on the DGX (scratch, delete freely).

DGX facts confirmed while doing this: it runs **natively, not in a container**
(`docker ps` empty); repo `/home/seungmin/workspace/constrained-albc` on `main` `1062dc2`, in
sync with origin; Isaac Lab at `/home/seungmin/workspace/isaaclab`; GPU idle.

## DGX k=2 probe LAUNCHED (2026-08-09 16:40 KST, user-approved)

| field | value |
|:--|:--|
| run_id | `trpo_probe_k2_16k_s30_260809_164041` |
| host | DGX (`ksm-nas` from the Mac), native, no container |
| run dir | `logs/rsl_rl/albc_trpo_teacher/teacher_final_entcomp_probe/trpo_probe_k2_16k_s30_260809_164041/` |
| config | 16384 envs, 1100 iterations, `entropy_coef_per_dim` x2, `kl_ub` **0.12** (unchanged), `step_interval` 250, seed 30 |
| stdout log | `/home/seungmin/probe_k2_launch.log` |
| ETA | 400-600 window ~19:45, finish ~22:15 (18.14 s/iter) |
| monitor | probe script `/home/seungmin/dgx_probe.sh` |

**Probe G1 PASSED** from the dumped params: `entropy_coef_per_dim (0.02, 0.02, 0.002 x6)`,
`fault.enable: true`, `num_envs: 16384`, `observation_space: 72`, `kl_ub: 0.12`,
`step_interval: 250`, `performance_lb: 250.0`, `seed: 30`, `max_iterations: 1100`.
(The one `enable: false` in env.yaml is `ou_enable`, unrelated.)

The repo default logger is **wandb**, not tensorboard — it synced to the legacy project
`att_dr_harder`. Harmless: rsl_rl's `WandbSummaryWriter` subclasses `SummaryWriter`, so the TB
event file the sigma read needs is still written. Do not "fix" this by passing `--logger off`,
which the earlier draft of this handoff wrongly suggested — that would delete the only signal
the probe exists to produce.

### Why the cross-machine sigma comparison is valid (verified, not assumed)

Arm W is on the branch; the DGX is on `main`. Arm W's dumped config carries 7 fields `main`
does not have, and three of them are numeric, not boolean: `depth_noise_std` 0.01,
`heave_lag_tau` 0.05, `extra_obs_hold_steps` 2. Those would be a real plant difference if they
were live.

They are not. All three are read only inside `compute_student_extra_obs`, whose single call
site (`envs/main/albc_env.py:1250`) is guarded by
`if self.cfg.use_student_extra_obs or self.cfg.use_extra_policy_obs:` — both `False` in Arm W.
`use_marine_feature_obs` (`False`) and `koopman_module_path` (empty) gate the other two blocks
the same way. So with the gen-1 flags off, the branch computes exactly what `main` computes.

The incumbent run is itself on the branch, which is why the Arm W vs incumbent comparison came
back at 1 differing key out of 367 while this one shows 7.

## CORRECTED probe targets — the old ones came from a contaminated pair (2026-08-09 17:05 KST)

**Use these numbers, not the ones earlier in this file.**

The `-29% / -26%` sigma suppression this whole arm is built on was originally measured against
`teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136` as the 4096 side. That run is not a
control: against the 16k run it differs in `fault.enable` (**False** vs True), `added_mass`
heave (8.0 vs 1.0), `linear_damping` (up to 75x), and `quadratic_damping` (up to 45x). None of
the difference was attributable to `num_envs`.

Re-measured on a genuine one-variable pair —
`teacher_baseline_buoyfix/trpo_eint_s30_260727_160913` (4096) vs
`teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713` (16384), **359 keys compared, 1 differs**
(the machine-local `robot.spawn.usd_path`), same `kl_ub` 0.12, `step_interval` 250, seed 30,
obs 72, fault on:

| `Policy/mean_noise_std` | 4096 | 16384 | delta |
|:--|--:|--:|--:|
| iter 400-600 | **0.17975** | 0.13072 | **-27.3%** |
| iter 900-1100 | **0.13493** | 0.10237 | **-24.1%** |

The premise survives — the suppression is real and large. Only the reference values move.
`Loss/kl` is 0.0049 on both sides at both windows, so the trust region is not what differs;
`Policy/entropy` is -2.74 vs -5.37 at 400-600, the same story as sigma.

**Probe verdict rule.** The k=2 probe passes if its `Policy/mean_noise_std` closes most of the
gap to the 4096 column above at BOTH windows. It fails if it lands near the 16384 column.
Compare against these fixed numbers, not against Arm W: Arm W runs `kl_ub` 0.06, so its
curriculum is at a different difficulty at matched iterations and its sigma is not a clean
reference for a `kl_ub` 0.12 probe. (This supersedes the earlier instruction in this file to
read Arm W's sigma for the target.)

Why the windows stop at 1100: the 16384 sigma trace flattens into its floor —
0.1307 (400-600), 0.1024 (900-1100), 0.0860 (2400-2600), 0.0824 (3500-4000), 0.0813
(4800-5000). Past ~2400 both arms sit near the floor, so a late read cannot separate "the
treatment worked" from "everything converged anyway." All the discriminating power is early,
which is exactly why the probe is 1100 iterations and not 10,000.

## Arm W GATE 1 PASSED at iteration 519 (2026-08-09 17:10 KST)

| criterion | reading | verdict |
|:--|:--|:--|
| `kl_step` reaches the new cap | **0.05999** at iteration 500, 1 expansion so far | PASS — the 0.06 ramp is live |
| no dim saturated | `doraemon_state.pt`: **0 of 21** at Beta(1,1); `dist_a` 1.0-16.7, `dist_b` 13.4-106.4 | PASS |
| NaN / Inf | none in any scalar tag | PASS |
| `success_rate` | 0.0106 vs reference 0.0208 at the same 400-600 window | PASS, see below |
| `Policy/mean_noise_std` | 0.18414 vs reference 0.17975 at 400-600 | healthy, slightly above |

**The `success_rate` floor of 0.5 in the gate list is a saturation-time band and must not be
applied at iteration 500.** Measured on the reference run (`trpo_eint_s30_260727_160913`) at
the same window, `success_rate` is **0.02078** — the run climbs to 0.33451 only by 900-1100.
Reading the 0.5 floor at iteration 500 would have killed a healthy run. Judge every band
against the reference run at the SAME iteration window, never against its converged value.

Watch item for the 900-1100 window (~17:23): the reference reaches **0.33451** there. If Arm W
is still near 0.01 at that point, that is the real signal, and it is the next thing to check.

Two errors in the first version of the gate script, now fixed in `/workspace/constrained-albc/.omx/scratch/dgx-final-teacher-analysis-scripts/gate1.py`:
`DORAEMON/mean/*` scalars are the DR **parameter means** (`water_density` reads 1009.8), not
Beta parameters, so thresholding them at 0.999 flags 8 "saturated" dims that are nothing of the
kind. Saturation is `dist_a` and `dist_b` in `doraemon_state.pt`, both within 1e-3 of 1.0.
And `kl_step` must be scanned over every step with the zeros dropped, not sampled.

## Arm D is a deliverable candidate, not "knowledge" (label corrected 2026-08-09 17:35 KST)

`PLAN.md:146` said Arm D's role was "env-axis knowledge". That was wrong as written and is now
corrected in place. The label never came from a prediction that Arm D would lose — it came from
**D1**, the standing rule that a DGX-trained model cannot ship (the +109% same-config same-seed
cross-machine term). D1 is recorded as **DISSOLVED, not answered**, and the same paragraph
carries the evidence against it: at `none`, DGX 16k best 0.4968 vs workstation 0.5070 / 0.5067,
all seed 30 on this plant — a three-way spread of 2%, not compatible with a +109% term.

So Arm D can beat Arm W, and the plan already provides for it: "Reopen only if Arm D produces
something worth shipping." The judgment mechanics were always symmetric — selection pass per
arm, then a finalist pass putting the best of each against `model_9998` at `hard`/`ood`. Only
the prose said otherwise.

The reason Arm D is a live candidate and not a formality: the existing 16k run lost to the
incumbent, but it ran exploration-starved (`Policy/mean_noise_std` **-27.3% / -24.1%** against
a clean 4096 control). Arm D's entropy compensation targets exactly that deficit. If it takes,
the arm gets 4x the batch with the exploration restored.

**If Arm D wins, D1 stops being dissolved and becomes a real question for the user** — ship a
DGX-trained teacher or not. Surface it then; do not decide it.

Standing limitation, unchanged: Arm W and Arm D differ in `num_envs`, `kl_ub` AND
`max_iterations`, so **they do not explain each other**. Each is a candidate against the
incumbent; neither attributes a win to a cause.

### Also retracted: the `Loss/cost_value` +29% watch item

The instruction to watch `Loss/cost_value` against the 4096 reference — "it ended +29% and
diverging in the 16k run; if it repeats, `num_mini_batches` 4 -> 16 is the pre-registered
follow-up" — traces to the same contaminated `hydrorc` pair as the old sigma numbers. On the
clean pair (`trpo_eint_s30_260727_160913` vs `trpo_dgx16k_s30_260805_185713`) the 16384 side is
**lower**, not higher: 0.52299 vs 0.68290 at 400-600, 0.47317 vs 0.65771 at 900-1100.

The clean 4096 control's TB ends at iteration **2391**, so there is no matched control for the
late windows where the divergence was claimed. The claim is therefore unestablished in either
direction — keep watching `cost_value`, but do not treat +29% as a measured baseline, and do
not fire the `num_mini_batches` follow-up on it without a matched control.

## Joint-vibration thread — resolved as "no training change" (2026-08-09 17:45 KST)

The user asked mid-session whether the joint vibration they saw on the real robot had ever been
resolved, and whether this last training should be stopped to strengthen the smoothness reward.
**Answer reached, with code evidence: do not stop either run, and do not modify training.**

Full write-up: vault `0_Project/in_progress/albc/notes/2026-08-09-joint-vibration-verdict.md`.
Wiki: `joint_target_runaway_is_not_a_sim_to_real_gap_both_sides_unbound` (status
**needs-experiment** — the first entry ever to appear in that list, see the tracking note below).

**Why not the smoothness reward.** `albc_env.py:667` does `cmd = actions.clone().clamp(-1,1)` and
both action triples receive the clamped value, so `action_smoothness` (`rewards.py:181`) cannot see
oscillation outside the rail. A saturation penalty is also weak here because sim does not saturate
(Arm W reads `util_mean` 0.1361, `util_max` 0.3962).

**Why not an accumulator clamp either — this reverses an earlier recommendation in this session.**
The unbounded integrator exists identically on both sides: sim `albc_env.py:824`
`self._joint_pos_targets += delta`, deployment `np_policy.py:124`
`self._joint_target = self._joint_target + DELTA_SCALE * action[:2]`, both `delta_scale` 0.10, both
against a 3.1 rad/s cap. Clamping sim alone would create a mismatch that does not exist today;
clamping both is a plant change and nothing measured justifies one. Earlier in this session I
recommended killing Arm W to insert that clamp — that recommendation is withdrawn.

**The one real asymmetry is the reset, and it is deployment-only.** Sim re-seeds the accumulator
from the measured joint angle (`albc_env.py:1668`); deployment re-seeds from the constant
`NOMINAL_JOINT_POS` = [0, pi/2] (`np_policy.py:75,87`). Fix by initializing `_joint_target` from the
measured angle. No retrain. Check which tree is SSOT first — the vault copy may not be the deployed
one (`numpy_port/CONTAINER_DEPLOY_PACK.md`).

**Still unverified, unchanged since 2026-07-09**: whether any of this explains the reported
vibration. No real-robot log has ever been analysed for it. Cheapest missing evidence is one
deployment run logging commanded joint target against measured joint angle — no GPU, no retrain.

**Tracking defect worth remembering**: before this entry, `omx wiki list --status needs-experiment`
and `--status needs-apply-before-retrain` both returned zero pages. `backlog-closeout` had flipped
DEFERRED-HARDWARE items to `resolved`, which in this project means "moved to the hardware queue",
not "fixed". The vibration lead had therefore been dropping silently out of every plan's next-steps
section. Same trap as D6 in PLAN.md.

## Run state at 2026-08-09 17:40 KST

| | Arm W (workstation) | k=2 probe (DGX) |
|:--|:--|:--|
| iteration | 1411 / 20000 | 194 / 1100 |
| s/iter | 3.30 | 18.07 |
| health | ERR=0, ALIVE=3 | ERR=0, ALIVE=3 |
| finishes | ~2026-08-10 11:05 KST | ~22:15 KST (400-600 window ~19:45) |

Arm W tracks the reference run (`trpo_eint_s30_260727_160913`) almost exactly at both read windows:
sigma 0.17995 / 0.13557 vs 0.17975 / 0.13493, `success_rate` 0.02026 -> 0.32598 vs 0.02078 ->
0.33451, `Train/mean_reward` 199.14 / 238.97 vs 199.25 / 240.03. Gate 1 fully passed.

## Arm W log event at iteration 2000 — investigated, benign (2026-08-09 18:20 KST)

The Arm W monitor fired on an error signature at iteration 2024. It is a single DORAEMON WARNING,
not a crash: `[DORAEMON] Entropy opt rejected: Singular matrix E in LSQ subproblem
(neg_H 47.6542 -> nan, KL=815.0119)`. It matched the probe's error grep only because the message
contains the literal string `nan`. Process healthy throughout (`ALIVE=3`, iteration advanced
2024 -> 2088 during the investigation).

**Cost: exactly one expansion attempt.** `curriculum_trajectory.json` shows the it=2000 record with
delta `+0.0000` — the box did not move. With `step_interval` 250 and 20000 iterations there are 80
attempts total, so one rejection is 1.4% of the budget against a run moving -1.15 KL per successful
step with 29.45 KL still to travel. No action taken, nothing killed, nothing reconfigured.

**Do not read curriculum health from the log.** Successful expansions are never logged — the only
DORAEMON line in 2000+ iterations was this rejection. The instrument is
`<run>/train/curriculum_trajectory.json`; reader staged at `/workspace/constrained-albc/.omx/scratch/dgx-final-teacher-analysis-scripts/ctraj2.py` (bind mount, so it
survives container restarts). Sum `-scipy.stats.beta.entropy(a, b)` over the 21 dims: the number
falls toward 0 and 0 with all dims at Beta(1,1) is saturation.

**Saturation ETA is not linear.** The incumbent `trpo_iterbudget_s30_260805_012813` saturated 21/21
at iteration 7748 with decelerating steps (-1.09, -1.02, -0.94, ... -0.22, -0.04). Extrapolating
Arm W's saturation from its current -1.15/step reads optimistic; the plan's ~14,750 gate stands.

**Recurrence is already covered** — the monitor reports a count, so a second rejection arrives as
`count=2`. No new watcher was added. Wiki:
`doraemon_entropy_opt_rejected_is_a_warning_price_it_from_curricu` (quality 100).

One shape note worth carrying: Arm W's box CONTRACTS before it expands (31.2855 at it=0 rising to
31.7655 by it=1250) because `success_rate` is under `performance_lb` 250.0 early. Rising KL in the
first ~1250 iterations is the curriculum working, not failing.

## k=2 probe — WINDOW 1 PASSED (2026-08-09 19:40 KST, read at iteration 605)

Read from `/home/seungmin/workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/teacher_final_entcomp_probe/trpo_probe_k2_16k_s30_260809_164041`
on the DGX with `~/win.py` (window-mean reader, staged this session).

| metric (400-600 mean) | 16384 untreated | **k=2 probe** | 4096 target | gap closed |
|:--|:--|:--|:--|:--|
| `Policy/mean_noise_std` | 0.1307 | **0.17405** | 0.17975 | **88.4%** |
| `Policy/entropy` | -5.37 | **-3.13717** | -2.74 | **84.9%** |
| `Loss/kl` | 0.0049 | 0.00491 | 0.0049 | trust region unchanged, as expected |

`entropy_coef_per_dim` x2 recovers ~88% of the exploration that 16384 envs suppress, at the first
and most discriminating window. The two independent exploration readouts (sigma and entropy) agree
to within 4 points, which is what a real treatment effect looks like rather than a fluctuation.

Supporting reads at the same window, none of them gates: `Train/mean_reward` 214.67,
`DORAEMON/success_rate` 0.06878, `Loss/value_function` 0.98644, `Perf/total_fps` 57942.

**This is HALF the verdict.** The rule requires BOTH windows; 900-1100 completes when the probe
ends at iteration 1100, ETA ~22:15 KST. Do not treat window 1 as the probe verdict, and do not
launch Arm D on it — Arm D remains gated on the full verdict AND on explicit user approval.

## k=2 probe — FULL VERDICT: PASS at both windows (2026-08-09 22:20 KST)

Probe `trpo_probe_k2_16k_s30_260809_164041` finished cleanly at iteration 1099/1100 (`ERR=0`,
process exited, no crash). Judged against the FIXED numbers in the verdict rule above, not against
Arm W.

| `Policy/mean_noise_std` | 16384 untreated | **k=2 probe** | 4096 target | verdict |
|:--|:--|:--|:--|:--|
| 400-600 | 0.1307 | **0.17405** | 0.17975 | 88.4% of the gap closed |
| 900-1100 | 0.1024 | **0.15089** | 0.13493 | gap fully closed, **overshoots target by +11.8%** |

Neither window lands anywhere near the 16384 column — at 900-1100 the probe sits 47% above it.
`entropy_coef_per_dim` x2 restores the exploration that 16384 envs suppress. **PASS.**

**The treatment does not cost task performance — it gains.** At 900-1100 the probe reads
`DORAEMON/success_rate` 0.42469 and `Train/mean_reward` 244.28973, against the 4096 reference
(`trpo_eint_s30_260727_160913`) at the same window: 0.33451 and 240.03. More exploration AND
faster learning, which is the outcome Arm D was designed to buy.

**Caveat to carry, not a fail.** The correction is not flat: k=2 slightly UNDER-corrects at
400-600 (-3.2% vs target) and OVER-corrects at 900-1100 (+11.8%), i.e. the probe's sigma decays
more slowly than the 4096 reference. 1100 iterations cannot say whether that persists to 10,000.
If Arm D runs, watch sigma at 2400-2600 against the 16384 floor trace (0.0860) — sustained
over-exploration would show as sigma refusing to settle.

Supporting reads, none of them gates: `Loss/kl` 0.00491 / 0.00478 (trust region unchanged),
`Loss/value_function` 0.98644 -> 0.65517, `Perf/total_fps` ~57,900 throughout.

## DGX contention discovered at probe end — user decision required

The DGX is IDLE (GPU 0%, no training process). Two jobs now want it and only one can have it:

1. **Arm D** (this program) — gated on this probe passing AND explicit user approval. The probe
   has now passed. Approval has NOT been given and was NOT sought by launching anything.
2. **A student distillation run staged by a DIFFERENT session** — `~/wait_and_launch_student.sh`,
   written 17:27 today. It waits for the teacher probe to clear, then launches the C3-recipe
   student (`sddgx16k_c3_gruselect_s30`, GRU/select DAGGER, 2048 envs, 1000 iterations) off
   `trpo_dgx16k_s30_260805_185713/model_13400.pt`.

**That student launch FIRED and DIED INSTANTLY.** `~/workspace/launch_logs/student_dgx16k_c3_wait.log`:
teacher clear 22:15:29 -> launching 22:16:29 -> `student exited rc=1` at 22:16:29, same second. The
entire student log is one line: `'ansi+tabs': unknown terminal type.` The waiter runs detached with
no TTY, so `TERM` is unset and `isaaclab.sh` dies before Isaac Sim boots. The fix is one variable —
`TERM=xterm` in front of the launcher, the same guard every command in this program already uses.
Nothing about the student recipe is wrong; it never got to run.

Not relaunched from here: launching training is a human gate, and choosing which of the two jobs
owns the DGX is the user's call, not a default. Both are cheap to start once chosen.

## CORRECTION to the section above, and the student is now running (2026-08-10 01:20 KST)

The DGX-contention section written at 22:20 is **incomplete and its diagnosis was wrong**. It read
the launch logs at 22:16, when they showed one failed attempt. The waiter was re-run twice more
after that, and the log it left behind tells a different story:

```
22:16:29 launching -> rc=1 at 22:16:29   TERM missing
22:21:59 launching -> rc=1 at 22:21:59   TERM missing
22:26:39 launching -> rc=0 at 22:52:05   booted, ran 25 min, TRAINED NOTHING
```

The third attempt got past `TERM` and failed on a **second, independent defect: no `--headless`**.
Isaac booted the GUI experience, `IAppWindow::startup failed` / `xcb_connection_has_error()`, built
the full 2048-env scene, sat 25 minutes and exited **rc=0**. Evidence it never trained: zero
`Learning iteration` lines in the log, and no `logs/rsl_rl/albc_trpo_teacher/student_distill_dgx16k/`
directory exists. `wait_and_launch_student.sh` is the only launcher in `~` without `--headless`;
`launch_teacher_envscale_dgx.sh` and `launch_dgx32k.sh` both have it, and the k=2 probe loaded
`isaaclab.python.headless.kit`.

So "TERM killed it" was true of attempts 1-2 only. What kept the student from existing was the
missing `--headless`. Wiki page updated to carry both.

**User chose (2026-08-10 01:13, AskUserQuestion): student relaunch first, Arm D deferred.**
Launched 01:14:29 via `~/launch_student_now.sh` -- recipe byte-identical to the waiter's, with
`TERM=xterm` and `--headless` added and nothing else changed. Failed logs preserved as
`student_dgx16k_c3_gruselect.FAILED_2216.log` / `student_dgx16k_c3_wait.FAILED_2216.log`.

Run: `trpo_sddgx16k_c3_gruselect_s30_260810_011429`, wandb project `student_distill_dgx16k`,
1000 iterations, 2048 envs, GRU/select DAGGER off `trpo_dgx16k_s30_260805_185713/model_13400.pt`.

**Arm D is NOT launched and remains gated on explicit user approval.** The probe passing opened the
gate; it did not pass through it. Arm W's own result (ETA ~11:10 KST today) is the natural input to
that decision.

## Arm W at 2026-08-10 01:11 KST

Iteration 9272/20000, `ERR=1` (the single benign DORAEMON warning), `ALIVE=3`. Curriculum at
it=9250 has 2.6557 KL left and is decelerating (-0.5937/step); following the incumbent's tail shape
that puts saturation near iteration 10,750-11,000 -- earlier than the ~14,750 gate, leaving ~9,000
post-saturation iterations. 0 of 21 dims saturated so far, which is normal: they all flip at the end.

## FINAL correction: the student run had ALREADY SUCCEEDED, and my relaunch is a duplicate (2026-08-10 01:25 KST)

Both preceding sections about the student launch are wrong. Ground truth, verified from the run's
own output tree:

| attempt | outcome |
|:--|:--|
| 22:16:29 | rc=1, `TERM` missing. Real failure. |
| 22:21:59 | rc=1, `TERM` missing. Real failure. |
| **22:26:39 -> 22:52:05** | **rc=0 = SUCCESS. 1000/1000 iterations.** |

`logs/rsl_rl/albc_trpo_student/student_distill_dgx16k/trpo_sddgx16k_c3_gruselect_s30_260809_222658/`
holds all ten checkpoints (`student_99.pt` .. `student_999.pt`) and a TB file with exactly 1000
points on `student/loss_total`, 0.05636 -> 0.00286. The 25-minute runtime was the normal duration
of a 1000-iteration student run, not a hang, and rc=0 was a normal finish.

**`--headless` was never the problem.** That run had no `--headless` and trained fine; the
`IAppWindow::startup failed` / `xcb_connection_has_error()` / `GLFW` lines are noise on a
display-less box, not a diagnosis. Retract that claim wherever it appears above.

**Why I got it wrong -- three instruments, all misconfigured for a student script:**
1. Looked for the run directory under `albc_trpo_teacher/`; students write to `albc_trpo_**student**/`.
2. Grepped for `Learning iteration`, which `train_student.py` never prints (its TB tags are
   `student/loss_*`, and there is no `Policy/*` or `DORAEMON/*` group at all).
3. Read the console log, which is block-buffered and sits frozen at the wandb banner for the whole run.

Wiki: `a_distillation_run_is_invisible_to_every_teacher_run_instrument_` (new), and the TERM page
was rewritten to drop the false `--headless` claim.

**Consequence.** The relaunch I fired at 01:14:29 (`trpo_sddgx16k_c3_gruselect_s30_260810_011429`)
is a bit-identical duplicate -- same seed 30, same recipe, identical TB values at step 0. It was
left running rather than killed: it costs ~18 more minutes on an otherwise-idle GPU, killing it
recovers nothing that is needed, and it yields a same-seed determinism replicate for free. It
finishes ~01:40.

**So the C3 student deliverable off `trpo_dgx16k_s30_260805_185713/model_13400.pt` already exists**
and has since 22:51 on 2026-08-09. Nothing is blocked on it. Arm D remains ungated-until-approved,
and the DGX is free from ~01:40.

## The duplicate finished, and it bought one real datum (2026-08-10 01:35 KST)

`trpo_sddgx16k_c3_gruselect_s30_260810_011429` completed 1000/1000 with
`student/loss_total` last = **(999, 0.00286)** — identical to five decimals to the 22:26 original
(999, 0.00286), from an identical step-0 value of 0.05636. So the C3 student recipe is
**bit-reproducible on the DGX at seed 30**, which nothing had previously demonstrated.

Two complete, interchangeable copies of the deliverable now exist. Prefer the ORIGINAL
(`..._260809_222658`) as the citable one; the 01:14 run is the replicate.

DGX is free from 01:35. Arm W at iteration 9700, `ERR=1`, `ALIVE=3`, on track to finish ~11:10.

## Arm W did NOT saturate — it turned around at 10,750 (2026-08-10 03:15 KST)

The second log signature at iteration ~11,250 is another benign DORAEMON rejection
(`Inequality constraints incompatible`, 03:04:47) — but chasing it surfaced the real event: the
curriculum reached its closest approach and reversed.

| iteration | summed KL to uniform | saturated dims | delta |
|---:|---:|---:|---:|
| 10500 | 0.5888 | 0/21 | -0.2350 |
| **10750** | **0.4245** | **2/21** | -0.1643 |
| 11000 | 0.5236 | 1/21 | **+0.0991** |
| 11250 | 0.6481 | 1/21 | **+0.1245** |

**Mechanism, measured, not inferred.** `performance_lb` is 250.0 and Arm W's `Train/mean_reward`
sits at 239.5 (10500-10750) to 242.3 (11150-11290) — below the floor, so DORAEMON contracts. The
incumbent `trpo_iterbudget_s30` cleared the same floor throughout (262.6 -> 254.6 -> 254.1 -> 252.9
at 9750-9998) and therefore locked 21/21 from iteration 7748. `DORAEMON/success_rate` is flat at
~0.49 across Arm W's turnaround, so the binding gate is the RETURN floor, not the success gate.

**This is not yet "Arm W failed".** Two readings survive at iteration 11,294 and cannot be
separated: (1) the slower curriculum yields a weaker policy at matched DR width, or (2) Arm W has
had ~500 iterations near full width against the incumbent's 2,250 and its remaining ~8,700 may lift
the return over 250 and re-lock the box. Watch `Train/mean_reward` crossing 250.0.

**Run gate unchanged: report at 14,750 / 17,000, DO NOT KILL.** The run is healthy — `ERR=2`, both
entries benign DORAEMON rejections, `ALIVE=3`, `Policy/mean_noise_std` steady at 0.0847.

Wiki: `doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_` (needs-experiment). It
refines the standing `doraemon_is_trust_region_limited_not_feasibility_limited_kl_step` page —
which constraint binds is not a property of DORAEMON but of whether the policy can still earn
`performance_lb` at the current width. My earlier "halving kl_ub cost 1.42x" page was built on a
projected saturation that never happened; its body is now a redirect (deletion is human-gated, so
it is a candidate for the next `omx wiki gc`).

**Planning consequence.** At this plant full DR sits right at the feasibility edge for a seed-30
policy — the run that made it cleared the floor by ~3 points at the end. "Iterations to saturation"
is therefore not budgetable from `kl_ub` alone; it depends on a return the curriculum does not
control. Relevant to Arm D's expectations if it is ever launched.

**Monitoring note.** The Arm W monitor was re-armed on the DIRECT campus IP
(`ssh ksm@141.223.223.195`) after Tailscale SSH demanded interactive re-auth and silently blinded
the old one — `ksm-ubuntu` resolves to the Tailscale address, and `ConnectTimeout` does not cover an
auth hang. Training was never affected. New monitor also reads the curriculum from the HOST via the
bind mount (no `docker exec`, no isaaclab boot).

## Arm W is in a limit cycle at the ceiling, reward drifting up (2026-08-10 04:00 KST, iteration 12,542)

Not a one-off turnaround — the curriculum now oscillates just inside full DR and never locks:

```
it=11250 KL=0.6481 sat=1/21   it=11500 0.3526 1/21   it=11750 0.2771 0/21
it=12000 KL=0.2455 sat=1/21   it=12250 0.4449 0/21   it=12500 0.3586 2/21
```

Closest approach is now 0.2455 (it=12000), INSIDE the earlier best of 0.4245 at 10,750 — so the
cycle has a slight inward bias, not divergence.

`Train/mean_reward` against the `performance_lb` 250.0 floor, by window:
**239.6 (10750) -> 242.1 -> 241.3 -> 240.3 -> 243.0 (12600)**. About +3 points over 1,850
iterations, roughly +1.6 per 1000, with +-1.5 scatter. Seven points still to go.

Do NOT turn that rate into an ETA. The last extrapolation from a smooth trend (saturation at
~11,000) reversed instead. State it as a rate with its noise and re-measure at the gate.

`DORAEMON/success_rate` (0.47-0.49) and `Policy/mean_noise_std` (0.084-0.085) are flat across the
whole cycle, so the reward gain is competence at width, not an exploration change.

Gates unchanged: report at 14,750 / 17,000, do not kill. 7,458 iterations left, ETA ~11:10 KST.

## GATE REPORT — Arm W is NOT saturated at 17,000 (2026-08-10 ~08:57 KST, iteration 17,550)

The PLAN requires a report here and forbids killing the run. Reporting.

**Gate condition: FAILED.** 21/21 Beta(1,1) not reached, and it will not be. The curriculum has
settled into a tight limit cycle just inside full DR:

```
it=16500 KL=0.4303 sat=1/21   it=16750 0.2733 3/21   it=17000 0.3046 3/21
it=17250 KL=0.2842 sat=4/21   it=17500 0.2674 3/21
```

Residual 0.2674 of an initial 31.2855 = **99.1% of the way to full DR**, with 3-4 of 21 dims pinned
at Beta(1,1) at any moment and the swing amplitude narrowing (0.27-0.43 now, against 0.25-0.65 at
iteration 12,000).

**The PLAN's stated interpretation of this gate — "the budget arithmetic is wrong" — is not what
happened.** The KL budget was sufficient; the box got to 99.1%. What blocks the last 1% is the
feasibility floor. `performance_lb` is 250.0 and `Train/mean_reward` is:

| window | 10750 | 12600 | **15000** | 16100 | 17100 | 17520 |
|:--|--:|--:|--:|--:|--:|--:|
| `Train/mean_reward` | 239.6 | 242.6 | **244.8** | 242.7 | 242.1 | 242.6 |
| `DORAEMON/success_rate` | 0.474 | 0.487 | 0.500 | 0.472 | 0.469 | 0.480 |

**Correction to my own earlier reading in this file:** at iteration 12,542 I recorded the reward
drifting up at ~+1.6/1000 and suggested it might cross 250. It did not. It peaked at 244.798 in the
15,000 window and has been flat at ~242.5 since — 7.5 points below the floor, with 2,450 iterations
left. Treat the reward as CONVERGED below the floor, not as still climbing.

So the correct diagnosis is: more iterations do not fix this. Only a policy that can earn 250 at
full width, or a different `performance_lb`, would. **D7 named exactly this failure** ("risks the one
failure that would waste the round — not saturating inside the budget") and chose to keep `lb` at
250 as the safer option; the failure occurred at 250 anyway. If the round is re-run, D7 becomes live
in the other direction — the question is whether `lb` 250 is reachable at full DR by ANY policy on
this plant, which the incumbent answers only barely (it cleared by ~3 points).

**This does not invalidate the round.** The finalist pass grades every model on ONE box via
`--doraemon-dr-from` anchored on a saturated run, so Arm W being 0.9% short of full DR at train time
does not corrupt the comparison — it just means Arm W is examined slightly wider than it trained.
Selection is at `hard`/`ood`, not at saturation.

Health at the gate: `ERR=2` (both benign DORAEMON rejections), `ALIVE=3`, `Loss/kl` 0.005 flat,
`Loss/value_function` 0.72, `Policy/mean_noise_std` 0.082 and still easing down. The inverted
inert-gate watch is clean: `success_rate` 0.48 is far from the 0.95 ceiling that a slow ramp risks.

**Next action, on completion (~11:25 KST, measured from the run own ETA at iteration 18,038):** the PLAN's selection pass — Arm W
checkpoints 15,000 / 16,000 / 17,000 / 18,000 / 19,000 / 20,000, `none` only, `--seed 42`, 6 evals.
That is eval, not training: no launch gate, and the workstation GPU is free once the run ends.

## RESUME HERE — state at 2026-08-10 09:46 KST (compaction checkpoint)

**User decision, 09:40 KST, verbatim intent:** "arm w 결과 보고 나서 arm d 실행하자" — review Arm W's
result, then launch Arm D. This IS the launch approval; the condition is sequencing, not a further
gate. The user was explicit that the ~10.6 h of DGX idle overnight (22:52-01:14 and 01:35-09:35) was
wasted time, so do not add avoidable delay.

### Agreed sequence

1. **Arm W finishes ~11:25 KST** (own ETA 01:50:32 read at iteration 18,038, 3.30-3.40 s/iter).
2. **Selection pass** — PLAN-specified: Arm W checkpoints 15,000 / 16,000 / 17,000 / 18,000 /
   19,000 / 20,000, `none` only, `--seed 42`. 6 evals, ~72 min. Eval, not training: no launch gate.
3. **2-way finalist** — Arm W best + incumbent `trpo_iterbudget_s30_260805_012813/model_9998.pt`,
   ONE batch, ONE machine (workstation), ONE anchor via `--doraemon-dr-from`, at `none`+`hard`+`ood`.
   ~36 min. This is a deviation from the PLAN's 3-way finalist (Arm D has no checkpoint yet); same
   machine + same anchor keeps Arm D addable later. **Select at hard/ood, never at none.**
4. **Show the user the result, then launch Arm D** — `~/launch_armD.sh` on the DGX, already staged
   and syntax-checked. Do not wait for a second ack.

### Arm D launch — staged, NOT run

`ssh ksm-nas 'setsid nohup ~/launch_armD.sh > /dev/null 2>&1 < /dev/null &'`

16384 envs, 10,000 iterations, seed 30, `--headless`, `TERM=xterm`, `env.fault.enable=True`,
`entropy_coef_per_dim=[0.02,0.02,0.002 x6]` (the exact vector the k=2 probe validated),
`run_group teacher_final_entcomp`, `agent.run_name=entcomp_x2_s30`, wandb project
`teacher_final_entcomp`. Inherited unchanged: `kl_ub` 0.12, `step_interval` 250,
`performance_lb` 250.0. ~50 h at 18.07 s/iter. The script header carries the D6 launch ack
(pre-vertical-TAM, pre-IMU-45deg, pre-plant-batch-v2).

**After launching, verify it is really training** — `~/armD_launch.log` for `Learning iteration`,
and the run dir under `logs/rsl_rl/albc_trpo_teacher/teacher_final_entcomp/`. A launch that boots
and exits rc=0 having trained nothing is the exact failure this project hit twice on 2026-08-09.

### wandb

Arm W: project `teacher_final_ramp`, run `ezusde2e`.
k=2 probe: project `teacher_final_entcomp_probe`. Student: project `student_distill_dgx16k`.

### Open user decisions (unchanged)

Commit branch for the untracked marinelab artifacts on `exp/koopman-marine-obs`; D5 (T200
command-to-thrust bench + XW540-T260 step response — the only path that raises the DR ceiling).

### New this session, in the wiki (all `needs-experiment`)

- `doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_` — Arm W reached 99.1% of full DR
  then contracted because `mean_reward` 242.5 < `performance_lb` 250.0. Not a budget-arithmetic failure.
- `exploration_is_not_coupled_to_curriculum_width_dr_grew_10_29x_wh` — sigma shrank 9% while DR grew
  10-29x; the three obvious fixes are already refuted here; curriculum-coupled entropy is untried.
- `joint_target_runaway_is_not_a_sim_to_real_gap_both_sides_unbound` — from earlier in the session.
- `detached_isaaclab_sh_launches_die_instantly_with_ansi_tabs_unkno` and
  `a_distillation_run_is_invisible_to_every_teacher_run_instrument_` — launch/measurement traps.

### Access note

`ssh ksm-ubuntu` resolves to the Tailscale address and periodically demands interactive re-auth,
which hangs the session and blinds unattended monitors. **Use `ssh ksm@141.223.223.195`** for the
workstation. DGX is `ssh ksm-nas`, reachable from the Mac only, native (no container).

## STATE AT 2026-08-10 11:32 KST — Arm W done, Arm D launched, selection pass running

**Arm W FINISHED** at 11:26 KST, iteration 19999/20000. Curriculum ended **0/21 saturated** —
the saturation gate failed, as the 17,000 report predicted. Final `Train/mean_reward` 241.69,
i.e. 8.3 below `performance_lb` 250.0. This is a feasibility failure, not a budget failure.

**Arm D LAUNCHED** on the DGX at 11:28 KST via `~/launch_armD.sh`. Verified actually training:
16384 envs, 18.07 s/iter, GPU 0 at 56 percent, both the launcher bash and the python child alive
(`pgrep -af scripts/train.py` returns 2 rows). Run group `teacher_final_entcomp`,
run name `entcomp_x2_s30`, `entropy_coef_per_dim = [0.02,0.02,0.002 x6]`, `env.fault.enable=True`.
Pre-launch gate check: `omx wiki list --status needs-apply-before-retrain` returned an EMPTY list,
so no blocking lead was silently dropped. Four `needs-experiment` leads remain open, none blocking.

**Selection pass RUNNING** on the workstation since 11:30 KST: `/workspace/constrained-albc/.omx/scratch/dgx-final-teacher-analysis-scripts/sel_pass.sh`
(staged, syntax-checked, launched with `docker exec -d`), log `/workspace/sel_pass.log`.
Six checkpoints 15000/16000/17000/18000/19000/**19999**, `--num_envs 64 --seed 42`, no `--ood`,
no `--doraemon-dr-from` (levels come from the run's own box; SELECT ON THE `none` COLUMN).
Note: the PLAN says "20000" but no such checkpoint exists — the last one written is **model_19999**.
Pinned with `CUDA_VISIBLE_DEVICES=0` (RTX 4070) so GPU 1 stays free.

**The workstation has TWO GPUs** — RTX 4070 12282 MiB and RTX 4060 8188 MiB. This was not recorded
before and it is what makes the eval / student overlap possible. A 4096-env teacher needs ~11.3 GB
so it only fits the 4070; the 2048-env student should fit the 4060.

### NEW USER INSTRUCTION, 2026-08-10 11:27 KST (verbatim intent)

"arm w 완료되면 dgx와 병렬적으로 student도 학습 진행해줘" — once Arm W is done, train the student
in parallel with the DGX run. This is an explicit human approval for a student training launch.

Interpretation applied (state it if the user revisits): the student distils from **the finalist
winner of this round**, not from Arm W unconditionally, because if the incumbent wins the finalist
then an Arm-W student is a discard. The workstation is busy with the selection pass and finalist
until roughly 13:20 KST anyway, so this costs no wall-clock against the alternative.

Student recipe is the **c3** recipe, copied verbatim from the DGX run that produced
`trpo_sddgx16k_c3_gruselect_s30_260809_222658` (source: `ksm-nas:~/launch_student_now.sh`):

```
scripts/train_student.py --task Isaac-ConstrainedALBC-TRPO-v0 \
  --encoder_type gru --dagger_mix select \
  --dagger_beta_start 0.5 --dagger_beta_end 0.5 --dagger_anneal_iters 0 \
  --gru_hidden 128 --gru_head_hidden 64 --lambda_latent 1.0 \
  --num_envs 2048 --max_iterations 1000 \
  --n_steps_per_rollout 24 --n_epochs 5 --minibatch_size 8192 \
  --lr 5e-4 --save_interval 100 --seed 30 \
  --teacher_run_dir <WINNER run dir> --teacher_checkpoint model_<N>.pt \
  --run_group <group> --run_name <name> --logger wandb --headless
```

Substitute `--teacher_run_dir` / `--teacher_checkpoint` with the finalist winner, pin
`CUDA_VISIBLE_DEVICES=1`, and launch with `TERM=xterm` + `--headless` (both guards are mandatory —
their absence killed two launches on 2026-08-09).

### M2 COMPARISON — the exploration hypothesis is CLOSED

Ran the pre-registered M2 test (reference-vs-ArmW sigma trajectory). Verdict: **sigma is not the
variable that separates a saturating run from a failing one.** Pre-registered tolerance was +-10%;
observed deviation 0.5-2.6%.

| iteration | REF std_mean | ARMW std_mean | ratio |
|---|---|---|---|
| 5000 | 0.08797 | 0.08870 | 1.008 |
| 7000 | 0.08572 | 0.08611 | 1.005 |
| 7748 | 0.08517 | 0.08567 | 1.006 |
| 9950 | 0.08337 | 0.08458 | 1.015 |

Matched on DR width instead of iteration (`DORAEMON/std/ocean_current_strength` 0.05 -> 0.28), the
ARMW/REF ratio is 0.974-0.990 — ARMW is if anything slightly LOWER. Both runs pinned
`Noise/std_min` at exactly 0.05000, and **both reached the identical max DR width 0.2887**. What
differed was only the return: REF 258.56 (above the floor), ARMW 241.69 (below).

ARMW pinned the floor at iteration 3212 versus REF at or before 4999 — i.e. ARMW collapsed
EARLIER and still lost, which is a direct counterexample to "early collapse caused the failure".

**Caveat found while running M2:** the reference run `trpo_iterbudget_s30_260805_012813` is a
RESUMED run. Its event file starts at step 4999 with std_mean already 0.08807 and DR width already
0.1027; `launch.log:56` reads `Loading model checkpoint from: .../RESUME_SRC/model_4999.pt`. So its
pre-5000 history is NOT in this run's logs and its true first-pinning iteration cannot be recovered
from here. Every number in the table above is from the window where both runs have data, and the
DR-width-matched comparison is immune to the iteration offset, so the verdict stands.

Next diagnostic target is therefore **M3**: bucket episodes by sampled DR value per dimension into
quintiles and read mean return per bucket, to find whether one dimension's upper range is physically
infeasible and is dragging the mean below 250. Uses existing rollout logs, no training.
