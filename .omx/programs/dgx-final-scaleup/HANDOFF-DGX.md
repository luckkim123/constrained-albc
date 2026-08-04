# DGX handoff — ALBC final-teacher scale run (paste as-is into the DGX-side session)

You are the DGX-side session for the `dgx-final-scaleup` program of the constrained-albc project.
This document is self-contained: everything you need is here or produced by the commands below.
It carries the defaults `num_envs 32768, obs72 plant, current plant, purpose teacher_final_dgx32k,
seed 30`; **the act of sending you this document IS the workstation-side human approval of exactly
those defaults** (the workstation user answers PLAN §8 Q1/Q2/Q6 by choosing to send it — if you
received this some other way, STOP and ask). If any step below fails its check, STOP and report —
do not improvise a different run.

Evidence status as of 2026-08-04: all four pre-launch gates are closed, and the obs72 default is
settled on paired metrics (the obs76 teacher is genuinely better in isolation, but none of that
advantage survives distillation to a student — PLAN §1). Nothing in this document is awaiting a
further experiment.

## Hard rules

1. Launch EXACTLY ONE training run, the one specified in Step 3. No other training or eval
   launches without a new human approval.
2. Change NOTHING except `num_envs`. Every "scale-up companion" change was tested and rejected on
   record: kl_ub-up is known-bad (E1), iteration-extension is net-negative twice (extend8k,
   moreiters), performance_lb re-derivation belongs to the next purpose, DR-box widening is
   blocked pending measured hardware bounds, entropy/min_std changes were a 5/5 zero-adoption
   sweep, num_mini_batches stays 4. If you think a knob needs to differ, that is a STOP-and-report,
   not a judgment call.
3. `isaaclab/` is a pristine fork — never commit or write project files into it.
4. All numbers you report are single-seed screening on a non-reference machine (a +109%
   cross-machine isolation term is on record). Report measurements, never adoption conclusions.

## Machine specifics (GB10, verified on record)

- No Docker; Isaac Sim is a source build. Launcher: `TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p`
  (raw python lacks numpy; missing TERM kills the launcher over SSH with "unknown terminal type").
- Single GPU — do NOT set `CUDA_VISIBLE_DEVICES`.
- Unified 121.7 GB memory: `nvidia-smi` reports Memory-Usage "Not Supported". Monitor with
  `free -m` and `nvidia-smi --query-compute-apps=pid,used_memory`. Measured peak at 32768 envs:
  83.2 GB; treat sustained > 100 GB as an abort signal.
- Expected steady-state: ~34.7 s/iter → **20000 iters ≈ 192.9 h ≈ 8.0 days**. That figure is a CAP,
  not a fixed commitment: Step 4b's periodic eval + stop rule can end the run earlier (48.2 h at
  5000, 96.5 h at 10000, 144.7 h at 15000) with no loss, because every earlier checkpoint is on disk.
  Plan for exclusive occupancy of about a week and make sure nothing else needs the GPU.
- cuDNN: the container-side cu13-vs-cu128 conv1d bug does NOT exist on DGX, but verify once before
  trusting any conv path: `python -c "import torch; print(torch.backends.cudnn.version())"` via the
  isaaclab launcher and record the value.

## Step 0 — sync and provenance (blocking)

```bash
git -C ~/workspace/constrained-albc pull --ff-only     # workstation has pushed main first
git -C ~/workspace/marinelab pull --ff-only
git -C ~/workspace/constrained-albc status --short --branch   # MUST be clean, on main
git -C ~/workspace/constrained-albc rev-parse --short HEAD    # record this sha in your report
```
If the tree is dirty or a pull fails, STOP and report. A dirty launch already voided one 4.9 h
run in this project.

## Step 1 — expected plant (verify BEFORE burning GPU time)

The run must train the gen-1 final-teacher recipe (E-int lineage, obs72, current plant). After
Hydra dumps the run's `env.yaml`/`agent.yaml` (they appear in the run's log dir at startup),
verify EVERY row of this table against the dumped values. One mismatched row = kill the run,
report the diff. Do not trust branch topology — experiment branches have deliberately reverted
adopted values before; only the dumped config counts.

| Key | Expected |
|:--|:--|
| observation width (env.yaml observation_space) | 72 (NOT 76; `use_extra_policy_obs` false/absent) |
| fault.enable | true |
| fault.thruster_fail_prob / thruster_health_range | 0.1 / (0.0, 0.5) |
| fault.use_privileged_fault_obs | false |
| max_thrust_scale DR band | (0.85, 1.15) |
| doraemon: enable / kl_ub / performance_lb / step_interval | true / 0.12 / 250.0 / 250 |
| doraemon alpha / buffer_size / min_episodes | 0.5 / 2000 / 200 |
| DR box (spot-check) | added_mass_scale (0.5,1.5), damping (0.4,1.7), inertia (0.4,2.0), volume/body_mass/buoy (0.75,1.25), water_density (995,1025), payload_mass (0,3), thrust_coefficient_scale (0.7,1.3) |
| agent: num_steps_per_env / max_kl / cg_iters / num_mini_batches / num_learning_epochs | 64 / 0.005 / 10 / 4 / 5 |
| agent: value_lr / max_grad_norm / init_noise_std | 1e-3 / 1.0 / 0.7 |
| agent: min_std_per_dim / entropy_coef_per_dim | (0.10, 0.10, 0.05 x6) / (0.01, 0.01, 0.001 x6) |
| encoder | hidden [256,128,64], latent 9, elu, output_norm true, privileged_dim 28 |
| seed | 30 |
| save_interval | 50 |
| num_envs | 32768 |
| max_iterations | 20000 (the Step 3 command's value; a shorter value means the wrong run) |
| resume | false |

Note: `policy_obs_dim=69` in agent.yaml is a stale static default — the runtime truth is
env.yaml's observation_space. Do not flag 69-vs-72 as a mismatch.

## Step 2 — memory/throughput sanity (optional but cheap)

If you want a pre-flight, a 50-iter smoke at 32768 envs with `--logger` disabled is acceptable
(record s/iter and `free -m` peak, then kill). Do NOT reuse its run dir for the flagship.

## Step 3 — launch

```bash
cd ~/workspace/constrained-albc
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 \
  --num_envs 32768 --max_iterations 20000 --headless \
  --run_group teacher_final_dgx32k \
  --logger wandb --log_project_name teacher_final_dgx32k \
  env.fault.enable=True \
  agent.run_name=dgx32k_s30
```

- **`env.fault.enable=True` is REQUIRED and is not optional polish.** `FaultInjectionCfg.enable`
  defaults to `False` in code (`envs/main/config.py`, `ALBCEnvCfg.fault = FaultInjectionCfg()`), so
  without it the env comes up fault-DISABLED and fails the `fault.enable | true` row of the Step 1
  table. (`train.py` also has a `--fault` store_true flag that sets the same field; either works.
  Use the Hydra override above — it is the string on record for the runs this one must match.)
  The E-int final teacher and the
  Phase D obs76 teacher were both launched with exactly this override; omitting it is the same diff
  that voided a 4.9 h run and made `trpo_obs76_s30_260803_233239` VOID. Step 1 will catch it, but
  only after the env has been built — verify the dumped `env.yaml` rather than assuming.
- run_id is minted at train time by make_run_id (`trpo_dgx32k_s30_<ts>`); record the actual id
  from the created log dir immediately — every watcher/report keys on it.
- `--run_group` and `--log_project_name` carry the SAME string (group = wandb project = purpose).
- Run it inside tmux/nohup so SSH drops don't kill it; capture stdout to the run's `launch.log`.
- Watcher discipline: poll the training PID (a pgrep pattern can self-match), and scope any NaN
  grep to metric lines only.

## Step 4 — iteration-500 abort gate (~4.8 h in)

By iteration 500 two DORAEMON updates have occurred. Read these TB tags (names verified against a
real event file): `DORAEMON/kl_step`, `DORAEMON/success_rate`, `DORAEMON/mode`,
`DORAEMON/ess_ratio`, `Policy/entropy`, `Policy/mean_noise_std`, `Loss/kl`,
`Policy/line_search_success`, `Loss/value_function`, `Loss/cost_value`,
`Constraint/barrier_penalty`.

KILL the run and report if ANY of:
- `DORAEMON/kl_step` shows no accepted widening move (≈0 on both updates) AND `DORAEMON/mode` <= -2;
- `DORAEMON/success_rate` pinned > 0.95 (inert gate) or < 0.5 (infeasible) sustained;
- any DR dim already at Beta(1,1) (premature saturation);
- sustained s/iter > 40, or `free -m` used > 100 GB;
- NaN in metric lines.
Healthy expectations: success_rate ≈ 0.75–0.90 (anchor measured 0.815 at lb=250),
kl_step at the 0.12 cap on accepted updates, `DORAEMON/ess_ratio` HIGHER than workstation runs
(buffer window narrows ~11 → ~1.4 iters at 32768 envs — expected, not an anomaly).

Repeat a lighter look at ~iter 1000 and ~2500 (checkpoints land every 50 iters ≈ 29 min).

### Step 4b — the two gates that matter for a 20000-iteration run

This run is 20000 iterations (192.9 h ≈ 8.0 days). The curriculum is expected to finish expanding
around iteration 6750, so roughly two thirds of the run trains on a frozen, fully-expanded DR box.
That regime has never been run at this length — these two gates are what make it safe.

**Gate A — saturation checkpoint (~iter 6750–7000).** Confirm `DORAEMON/kl_step` has gone to 0 and
that `doraemon_state.pt` reads Beta(1,1) on every dim (`torch.load`, keys `dist_a`/`dist_b`).
- Saturated MUCH earlier than ~6500: the budget arithmetic is wrong — report, do not kill.
- NOT saturated by ~iter 9000: expansion attrition is worse at 32768 envs than on record
  (`DORAEMON/mode = -3` fires in 4/4 recorded runs) — report.

**Gate B — inert-gate watch, at every eval point below.** `DORAEMON/success_rate` sustained > 0.95
is the recorded inert-gate failure class: `performance_lb=250` has stopped constraining anything
and the rest of the run is unguarded. The reference teacher already sits at 0.814 against
`alpha=0.5`, so there is not much slack. If it pins > 0.95, STOP and report before continuing.

**Periodic eval + stop rule (this is what bounds the 8 days).** Evaluate at iterations
5000 / 7500 / 10000 / 12500 / 15000 / 17500 / 20000 (~9 min each at 64 envs) and track `none`-level
`att_norm ss_error` from each eval's `summary.json`. **Two consecutive eval points worse than the
running best = stop the run and keep the best checkpoint.** Stopping early costs nothing: the better
checkpoint is already on disk, and the run's earlier iterations are identical to a shorter run
(`max_iterations` is consumed only as the loop counter).

**Fair-exam rule — do not skip this.** `eval.py static` defaults `--doraemon-dr` to True, which
grades each checkpoint on the DR box THAT checkpoint learned. Checkpoints from different iterations
therefore sit at different curriculum widths and their soft/medium/hard numbers are NOT comparable
to each other. Compare only on `none`, or re-evaluate every checkpoint under
`--doraemon-dr-from <one fixed run dir>` so they all take the identical exam.

## Step 5 — crash handling

A relaunch mints a NEW run id — never resume by editing Hydra `agent.resume` or a group-path
`load_run` (both fail silently). The working protocol:

```bash
# inside the NEW run dir's parent, point RESUME_SRC at the crashed run:
ln -s <crashed_run_dir> RESUME_SRC
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 32768 --headless \
  --resume --load_run RESUME_SRC --checkpoint model_<last>.pt \
  --max_iterations <20000 minus completed iters> \
  --run_group teacher_final_dgx32k --logger wandb --log_project_name teacher_final_dgx32k \
  agent.run_name=dgx32k_s30_resume
```
Pick `model_<last>.pt` by NUMERIC sort (`ls model_*.pt | sort -t_ -k2 -n | tail -1`) — alphabetical
sort has destroyed final checkpoints before. Record both run ids and the stitch point in your report.

## Step 6 — after the run

1. Verify the LAST checkpoint exists by NUMERIC sort (`model_19999.pt` for a full run, or whatever
   the stop rule left), plus `doraemon_state.pt` and the wandb dir.
2. Do NOT delete or trim anything — all ~400 checkpoints (5.9 MB each, ~2.4 GB total) are the
   dose-response series and are the main deliverable alongside the final model.
3. Sync back to the workstation (the workstation runs the paired eval under its shared-DR
   protocol): the full `logs/rsl_rl/albc_trpo_teacher/teacher_final_dgx32k/<run_id>/` dir and the
   `experiments/` mirror entry. If you eval locally, use exactly
   `eval.py static --seed 42 --num_envs 64 --headless` with the checkpoint path THROUGH the
   run's `train` symlink, and NEVER pass `--output_dir`.
   Note: the workstation's eval carries a cross-run pairing fix (per-level reseed) that landed
   after this repo state was branched; a local eval on an older `eval.py` will NOT be paired with
   the workstation's reference evals. Report your local numbers as indicative only.

## Step 7 — report back (measurements only)

- run_id, sha, exit code, wall-clock, s/iter curve summary, `free -m` peak;
- abort-gate readings at 500/1000/2500, then Gate A (saturation, ~6750) and Gate B (inert-gate
  watch) at every eval point;
- **the dose-response table** — for each eval point (5000/7500/10000/12500/15000/17500/20000, or
  wherever the stop rule fired): iteration, `none`-level `att_norm ss_error`, `roll ss_error`,
  `roll os_env_mean`, `n_gt20`, `survival_pct`, and which checkpoint you judged best. This table is
  the run's primary scientific output — it is the first iteration-budget curve ever measured on
  this plant;
- final DORAEMON state: per-dim Beta a/b, the iteration at which the box saturated, achieved
  expansion count (nonzero `DORAEMON/kl_step` entries — NOT the number of scheduled boundaries),
  and final success_rate;
- checkpoint inventory (numeric sort) + doraemon_state.pt + wandb sync status;
- any deviation from this document, however small.

No adoption language: the standing rule says a DGX-trained teacher is not the shipped final model
(cross-machine +109% term); this run is scale exploration unless the workstation side says
otherwise.
