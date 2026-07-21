# How to run a campaign stage on the NVIDIA DGX

This repo's experiment campaigns are split across two machines: the local workstation
(RTX 4070 + RTX 4060) and a separate NVIDIA DGX. This page is the runbook for the DGX
side — what to sync, how to launch, and how results come back.

It assumes the campaign conventions in
[`../reference/experiment-conventions.md`](../reference/experiment-conventions.md) and
the omx wiki (`omx wiki query --root <repo>`); this page only covers what is
DGX-specific.

## When to use this

The division of labour is by CAMPAIGN STAGE, not by convenience:

| Where | What runs there | Why |
|---|---|---|
| local workstation | Stage A — cheap single-variable mechanism probes at `num_envs=4096`, 5000-8000 iters | one run ≈ 4.5 h; the sequential run → eval → analyze cycle keeps both GPUs busy |
| DGX | the scale-up arm first; other stages only if the benchmark below justifies it | its advantage is MEMORY, not parallelism — see the hardware note |

### Hardware note — know what this machine actually is (added 2026-07-21)

The DGX in question reports `GPU 0: NVIDIA GB10` and `nproc = 20`. That is a
**single-GPU, 20-core Grace-Blackwell desktop machine, not a multi-GPU DGX server**, and
two consequences follow that invalidate the obvious assumptions:

- **No run-level parallelism.** One GPU means one training run at a time, the same as the
  workstation. Any plan that plays several arms concurrently does not apply here.
- **It may be SLOWER per run, not faster.** The workstation has 28 available cores against
  this machine's 20, and Isaac Sim's `num_envs=4096` physics stepping is CPU-heavy. Do not
  assume a speedup — measure it (Step 0 below). The workstation reference is **3.3 s/iter
  at 4096 envs**.

The genuine advantage is the large unified memory, which is what a `num_envs` scale-up
needs. So this machine earns its place on the scale-up arm; for ordinary 5000-iter probes,
whether it is worth using at all is an empirical question the benchmark answers.

## Step 0 — verify this machine can run the stack AT ALL, then benchmark it

Do this before any campaign work. The Grace CPU is ARM (`aarch64`), and Isaac Sim's
platform support there is not something to assume:

```bash
uname -m                                    # expect aarch64
ls -d /isaac-sim && /isaac-sim/python.sh -c "import isaacsim, torch; print(torch.cuda.is_available())"
free -g                                     # unified memory actually available
```

If the import or the CUDA check fails, **stop** — training cannot run here and the campaign
stays on the workstation. Report the failure rather than working around it.

If it passes, measure throughput before planning anything around this machine:

```bash
cd <path>/constrained-albc
CUDA_VISIBLE_DEVICES=0 /isaac-sim/python.sh scripts/train.py \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --num_envs 4096 --max_iterations 200 \
    --run_group bench_spark --log_project_name bench_spark \
    --headless agent.run_name=bench 2>&1 | tail -5
```

Report the s/iter against the workstation's 3.3 s/iter at the same `num_envs`. That number,
not an assumption about the hardware tier, decides what this machine is given.

**The split is methodologically safe only because Stage B re-anchors.** A policy trained
on one GPU does not reproduce bit-for-bit on another (floating-point nondeterminism
changes the sampled trajectories even at a fixed seed), so a cross-machine comparison
carries a hardware confound on top of whatever variable is under test. Stage B's first
run is a RE-BASELINE: it retrains the anchor on the new plant with the Stage-A adopted
bundle. Every later Stage-B comparison is then made against an anchor produced on the
SAME machine, and the hardware term cancels.

**Rule that follows from this — do not break it:** never compare a DGX run's numbers
directly against a workstation run's numbers as if the difference were caused by the
variable under test. Cross-machine numbers may be quoted for orientation only, and must
be labelled as such. If a genuine cross-machine comparison is ever needed, re-run the
comparator on the same machine.

## Step 1 — sync the three repos

The stack is three independently versioned repos and the install order is strict.
The DGX copy is usually behind, so start every campaign session with a sync.

```bash
# base layer (clean upstream fork -- normally already in sync)
git -C <path>/isaaclab pull --ff-only

# overlay 1: marine physics + assets (Git LFS!)
git -C <path>/marinelab pull --ff-only
git -C <path>/marinelab lfs pull          # meshes are LFS pointers otherwise

# overlay 2: the main project
git -C <path>/constrained-albc pull --ff-only
```

Then re-run the editable installs for the two overlays. A `git pull` alone does NOT
update an editable install when packages, entry points, or namespace layout changed:

```bash
cd <path>/marinelab        && pip install -e .
cd <path>/constrained-albc && pip install -e .
```

**Check out the exact commit the campaign stage is anchored to.** Every campaign stage
names a baseline tag; ask for it rather than assuming `main` is right:

```bash
git -C <path>/constrained-albc fetch --tags
git -C <path>/constrained-albc log --oneline --decorate -5
```

## Step 2 — verify the environment before launching anything

A stale install fails as a confusing mid-run error, so fail fast instead:

```bash
cd <path>/constrained-albc
python -c "
import gymnasium as gym, constrained_albc
ids = sorted(k for k in gym.registry if 'ConstrainedALBC' in k)
print(len(ids), 'tasks registered'); print('\n'.join(ids))
"
nvidia-smi --query-gpu=index,name,memory.total --format=csv
```

Expect 7 registered `Isaac-ConstrainedALBC-*` task ids. If the count is short, the
editable install did not take — redo Step 1.

> **Interpreter gotcha.** Every script runs through the Isaac Sim interpreter. Inside the
> overlay repos a PATH `python` wrapper normally handles this, but in a non-interactive
> shell (an agent session, a `nohup` job, a cron) that wrapper may be absent and a bare
> `python` exits 127. Call `/isaac-sim/python.sh` explicitly when in doubt, or use
> `./isaaclab.sh -p` from inside `isaaclab/`.

## Step 3 — launch

Launch conventions are identical to the workstation; only `num_envs` and the device list
differ. Pin the GPU explicitly so a training run and an eval can overlap.

```bash
cd <path>/constrained-albc
CUDA_VISIBLE_DEVICES=0 nohup python scripts/train.py \
    --task Isaac-ConstrainedALBC-TRPO-v0 \
    --num_envs <N> --max_iterations <M> \
    --run_group <purpose> \
    --logger wandb --log_project_name <purpose> \
    --headless \
    agent.run_name=<tag> \
    > logs_queue/<tag>_<YYMMDD>.log 2>&1 &
```

Non-negotiables, all of which the campaign conventions already require:

- `agent.run_name=<tag>` is **mandatory** — without it `make_run_id` emits a tag-less
  run id, which violates the naming convention.
- `--run_group` and `--log_project_name` take the **same** string: the experiment
  PURPOSE. One purpose = one group folder = one wandb project, so every run of that
  purpose is comparable in one workspace.
- The run id is minted at train time and will not match any id reserved in advance;
  read it from the `Exact experiment name requested from command line:` line.
- One variable per run, on its own `exp/<topic>` branch, with a `baseline-<YYMMDD>-<topic>`
  annotated tag on the branch point. `main` stays the verified original.

**Scale-up runs are multi-knob by nature.** Raising `num_envs` changes the effective
batch size and therefore the optimisation dynamics, so a scale-up run is a
CHARACTERISATION, not a single-variable probe. Report it as such; do not use it to
adopt or reject a mechanism.

## Step 4 — after the run

Same order as the workstation cycle:

1. **Manipulation check first.** Confirm the intervention actually took effect
   (`.omx/profile/analyze_training.py <run>/train --tier 3 --deep`, plus whatever
   run-specific check the probe pre-registered). If it failed, the run does not
   discriminate — stop and report; do not read the eval as a verdict.
2. **Eval** with `constrained_albc/analysis/eval.py static`, pointing `--checkpoint` at
   the path **through the `experiments/<run_id>/train/` symlink**, and **without**
   `--output_dir`. Both are required for the output to land in
   `experiments/<run_id>/eval/<mode>_<ts>/`; a `logs/…` path or an explicit
   `--output_dir` silently scatters the artifacts elsewhere.
3. **Analyze** with the omx `exp-analyze` skill, which writes the canonical
   `report.md` into `experiments/<run_id>/analysis/<analysis_id>/`.
4. **Verdict at the `none` DR level only.** Each run's learned DR box differs, so the
   soft/medium/hard rows are not comparable across runs unless a shared exam was run
   via `--doraemon-dr-from`.

## Step 5 — return the results

Two channels, because the two kinds of output are tracked differently:

| What | How it comes back |
|---|---|
| heavy run data — checkpoints, TB event files, eval `.npz`, plots | `experiments/` and `logs/` are **gitignored**. Copy them back with `rsync -av --progress` into the same relative paths so the `experiments/<run_id>/train` symlink resolves. |
| knowledge — omx wiki pages, run ledger | `.omx/registry/` and `.omx/runs/` **are** tracked. Commit and push them; the workstation picks them up with `git pull`. |
| code changes | the `exp/<topic>` branch plus its `baseline-*` tag; push both. |

Keep the run-id directory names byte-identical when copying — the analysis tooling
resolves runs by id and the `train` symlink is relative.

## Appendix — starting prompt for an agent session on the DGX

Paste this into a fresh Claude Code session started in the `constrained-albc` repo on
the DGX, filling the bracketed fields:

```text
You are running experiments for the constrained-albc UUV RL campaign on an NVIDIA DGX.
The workstation half of this campaign runs elsewhere; you own the DGX half.

FIRST, read these in order and follow them:
  docs/how-to/run-on-dgx.md          (this runbook -- sync, launch, eval, return path)
  .claude/rules/                      (behavioral rules: 01-critical .. 04-isaaclab-gotchas)
  omx wiki query --root . "<the topic of the run you are about to do>"

STATE YOU ARE GIVEN:
  campaign stage        : [Stage B / scale-up arm / joint1 arm]
  anchored at           : [commit or tag]
  purpose (group+project): [purpose string]
  run to launch         : [id from the campaign plan, e.g. B1a]
  the ONE variable      : [exact config field and old -> new value]
  pre-registered band   : [primary metric + adopt threshold + cost guard + kill criterion]

DO:
  0. FIRST, runbook Step 0: confirm the stack runs on this machine at all (aarch64 +
     Isaac Sim import + CUDA), then run the 200-iteration benchmark and report s/iter
     against the workstation's 3.3 s/iter at 4096 envs. If Step 0 fails, STOP and report
     -- do not work around it, and do not launch a campaign run.
  1. Sync all three repos and re-run the editable installs (runbook Step 1), then verify
     7 tasks register (Step 2). Report the versions you ended up on.
  2. Create the baseline tag and the exp/<topic> branch, make the single-variable change,
     commit it with the rationale, and only then launch.
  3. Launch per runbook Step 3, confirm it reached "Learning iteration 3/", and report the
     real run id.
  4. When it finishes: manipulation check FIRST, then eval, then exp-analyze, then judge
     against the PRE-REGISTERED band at the `none` level.
  5. Write the result into the omx wiki (close the lead with the outcome, not just a
     label), record keep/discard with `omx run-record`, and commit .omx/.

DO NOT:
  - compare a DGX number against a workstation number as if the delta were caused by the
    variable under test -- different GPUs do not reproduce bit-for-bit;
  - change the verdict band after seeing results;
  - hand-edit report.md or omx wiki pages (both have gated write paths);
  - `git push` without being asked;
  - use `git add -A` (stage explicit paths -- other sessions may be staging concurrently).

Report back: the run id, the manipulation-check outcome, the verdict against the band,
and the rsync path where the run artifacts are waiting.
```
