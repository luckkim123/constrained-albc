# Docker daemon restart killed Phase 3b at 2100 it; the resume failed twice silently before working (agent.resume overwritten, load_run cannot reach a run_group path)

- id: finding/317 · date: 2026-09-04 · author: claude-opus-5
- project: constrained-albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: none · keywords: resume, checkpoint, doraemon-state, run_group, docker-restart, phase3b
- summary: Host docker daemon restarted 15:56 and killed p3b training at ~2100 it plus the Phase 4 runner. Resume trap 1: cli_args.py:76 always overwrites agent_cfg.resume from args_cli (store_true, never None), so a Hydra agent.resume=true is discarded and training silently restarts at 0 while load_run/load_checkpoint still appear in agent.yaml. Trap 2: get_checkpoint_path regex-matches only names one level under the experiment dir (parse_cfg.py:194), so a --run_group nested run is unreachable; fixed with a symlink at the experiment root. Resume verified complete: DORAEMON curriculum restored (TB opens at severity 0.0230, the pre-crash value) via the doraemon_state.pt sidecar, env config identical in 338 of 339 keys. Residue: p3b history now spans two run dirs.

## What happened

The host's docker daemon restarted at 2026-09-04 15:56:09 KST (`systemctl show docker --property=ActiveEnterTimestamp`; host uptime 21 days, so no reboot). Every container on the machine came back up, and the two jobs running inside `marinelab-isaaclab` died with them: Phase 3b training at ~2 100 iterations, and the Phase 4 exam runner mid-`inc/m4`. The container's `sshd` went with it too — expected, since the entrypoint bootstrap is still not in effect.

The resume then failed **twice, silently**, before working. Both failures produced a running process and no error that named the real cause. Recording them because the next resume will meet the same two.

## Trap 1 — `agent.resume=true` as a Hydra override is always discarded

`cli_args.py:76` reads

```python
if args_cli.resume is not None:
    agent_cfg.resume = args_cli.resume
```

and `--resume` is declared `action="store_true", default=False` (`cli_args.py:30`), so `args_cli.resume` is **never** `None`. The assignment therefore fires on every run and overwrites whatever Hydra put there. `--load_run` and `--checkpoint` default to `None`, so *their* Hydra overrides survive — which is what makes this look correct:

```
$ grep resume params/agent.yaml
resume: false
load_run: retrain_simtoreal_p3/trpo_p3b_lb200_s30_260904_134536
load_checkpoint: model_2050.pt
```

The checkpoint path is recorded, `resume` is not, and training starts at iteration 0 with no warning. Caught at iteration ~50 by the log line `Learning iteration 0/7950`; that scratch run is quarantined as `SCRATCH_fromzero_162821_delete_me`.

**Fix:** pass `--resume` as a train.py CLI flag. Keep `load_run`/`load_checkpoint` as Hydra overrides or use `--load_run`/`--checkpoint`; either works.

## Trap 2 — `load_run` cannot name a `--run_group` nested path

`get_checkpoint_path` matches the run directory with

```python
runs = [... for run in os.scandir(log_path) if run.is_dir() and re.match(run_dir, run.name)]
```

(`parse_cfg.py:194`) — `run.name` is a **single directory name one level under** `logs/rsl_rl/<experiment_name>/`. Any run launched with `--run_group` lives one level deeper, so no `load_run` string can reach it and the call raises

```
ValueError: No runs present in the directory: '.../albc_trpo_teacher'
             match: 'retrain_simtoreal_p3/trpo_p3b_lb200_s30_260904_134536'
```

This one at least fails loudly, but it fails *after* Isaac Sim has started, so it costs a minute per attempt and buries the traceback under kit warnings.

**Fix used:** a symlink at the experiment root, then `agent.load_run=<symlink name>`.

```bash
cd logs/rsl_rl/albc_trpo_teacher
ln -sfn retrain_simtoreal_p3/trpo_p3b_lb200_s30_260904_134536 RESUME_p3b_2050
```

`run.is_dir()` follows symlinks, so it matches. The link is read only at startup and is safe to leave or remove afterwards.

## What the resume actually restored (verified, not assumed)

| state | restored | evidence |
|:--|:--|:--|
| policy / value / cost-critic weights | yes | `model_state_dict`, 43 keys including `cost_critic.{0,2,4,6}.{weight,bias}` |
| optimizer | yes | `optimizer_state_dict` present, `load_optimizer` defaults True |
| iteration counter | yes | `Learning iteration 2050/10000` (rsl_rl `tot_iter = start_iter + num_learning_iterations`, `on_policy_runner.py:97`) |
| **DORAEMON curriculum** | **yes** | new run's TB opens at step 2050 with `DORAEMON/mean/fault_severity` **0.0230**, the pre-crash value; a reset would read 0.0100 |
| env config | yes | both `params/env.yaml` parsed and flattened: 339 keys, exactly one differs (`log_dir`) |

The curriculum restore works because `ConstraintEncoderRunner.save` writes a `doraemon_state.pt` sidecar beside each checkpoint and `load` feeds it back through `load_state_dict` (`constraint_encoder_runner.py:293` and `:311`). Note the sidecar is **one file per run directory, overwritten every save** — it matches the *latest* checkpoint only, so resuming from any earlier checkpoint would silently pair the wrong curriculum state with the weights.

Two things the docstring implies are saved but are not, and neither matters here: "adaptive entropy state" has no `_save_aux_state` call, and `entropy_coef` is a static config field (`constraint_trpo.py:106`), not adapted state; the IPO barrier has no learned dual variable, and `_last_barrier_penalty` is recomputed inside each update (`constraint_trpo.py:485`).

Sanity check on the outcome: 64 iterations after the resume the run reads reward 238.3 and success 0.94, against 234.2 / 0.880 immediately before the crash.

## Cost and the one residue

Nothing was lost. The two failed attempts cost about 10 minutes of wall clock and the GPU sat idle from 15:56 to 16:35.

The residue is that **p3b's history is now split across two run directories** — `trpo_p3b_lb200_s30_260904_134536` holds iterations 0–2050 and `trpo_p3b_lb200_s30_r2050_260904_163518` holds 2050–10000, each with its own TB event file and its own `curriculum_trajectory.json`. Any full-history plot must stitch them. This is not new: the incumbent `trpo_iterbudget_s30_260805_012813` has exactly this property, and its TB holds only the resumed segment (steps ≥ 5248), which is why the first-500-iteration reference was unavailable for the G0-C readout.

A side effect worth naming: the first failed attempt's wrapper reached its `touch $M/P3B_DONE` line on exit, and the Phase 4 runner — which polls for that marker — took it as "training finished" and began scoring `model_2050.pt` into `p3b_final/`. Caught within one config; the marker and the `p3b_final/` directory were removed and the runner restarted. A done-marker written by a wrapper's exit path, rather than by the job succeeding, is a false signal to anything watching it.
## Comments
