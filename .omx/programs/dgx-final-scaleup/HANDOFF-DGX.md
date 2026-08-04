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
- Expected steady-state: ~34.7 s/iter → 5000 iters ≈ 48.2 h.
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
  --num_envs 32768 --max_iterations 5000 --headless \
  --run_group teacher_final_dgx32k \
  --logger wandb --log_project_name teacher_final_dgx32k \
  env.fault.enable=True \
  agent.run_name=dgx32k_s30
```

- **`env.fault.enable=True` is REQUIRED and is not optional polish.** `FaultInjectionCfg.enable`
  defaults to `False` in code (`envs/main/config.py`, `ALBCEnvCfg.fault = FaultInjectionCfg()`), and
  `train.py` exposes no fault flag — so without this Hydra override the env comes up fault-DISABLED
  and fails the `fault.enable | true` row of the Step 1 table. The E-int final teacher and the
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

## Step 5 — crash handling

A relaunch mints a NEW run id — never resume by editing Hydra `agent.resume` or a group-path
`load_run` (both fail silently). The working protocol:

```bash
# inside the NEW run dir's parent, point RESUME_SRC at the crashed run:
ln -s <crashed_run_dir> RESUME_SRC
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 32768 --headless \
  --resume --load_run RESUME_SRC --checkpoint model_<last>.pt \
  --max_iterations <5000 minus completed iters> \
  --run_group teacher_final_dgx32k --logger wandb --log_project_name teacher_final_dgx32k \
  agent.run_name=dgx32k_s30_resume
```
Pick `model_<last>.pt` by NUMERIC sort (`ls model_*.pt | sort -t_ -k2 -n | tail -1`) — alphabetical
sort has destroyed final checkpoints before. Record both run ids and the stitch point in your report.

## Step 6 — after the run

1. Verify `model_4999.pt` exists (numeric sort), plus `doraemon_state.pt` and the wandb dir.
2. Do NOT delete or trim anything.
3. Sync back to the workstation (the workstation runs the paired eval under its shared-DR
   protocol): the full `logs/rsl_rl/albc_trpo_teacher/teacher_final_dgx32k/<run_id>/` dir and the
   `experiments/` mirror entry. If you eval locally, use exactly
   `eval.py static --seed 42 --num_envs 64 --headless` with the checkpoint path THROUGH the
   run's `train` symlink, and NEVER pass `--output_dir`.

## Step 7 — report back (measurements only)

- run_id, sha, exit code, wall-clock, s/iter curve summary, `free -m` peak;
- abort-gate readings at 500/1000/2500/5000 (the tag list above);
- final DORAEMON state: per-dim Beta a/b, achieved expansion count vs the reachable 20,
  final success_rate;
- checkpoint inventory (numeric sort) + doraemon_state.pt + wandb sync status;
- any deviation from this document, however small.

No adoption language: the standing rule says a DGX-trained teacher is not the shipped final model
(cross-machine +109% term); this run is scale exploration unless the workstation side says
otherwise.
