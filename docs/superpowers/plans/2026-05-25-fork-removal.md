# isaaclab + rsl_rl Fork Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `isaaclab` source/ and the bundled `rsl_rl` package byte-stock, removing all of our forks, while keeping the main TRPO pipeline and the PPO ablations working.

**Architecture:** The main TRPO pipeline (`ConstraintTRPO` standalone + custom `ActorCriticEncoder`) depends on zero fork code, verified by code-grep. So we (1) back up then reinstall stock `rsl-rl-lib==3.1.2`, (2) restore two isaaclab source files to the fork point `cbf51abb`, (3) verify the PPO ablation cfg still constructs against stock PPO, and (4) correct the now-false fork claims in the overlay docs. Verification is smoke-gate based (train reaches "Learning iteration 0"), not unit tests — the change is configuration/dependency, not new code.

**Tech Stack:** Isaac Lab v2.3.0 (merge-base `cbf51abb`), Isaac Sim 5.1.0 bundled Python 3.11, rsl-rl-lib 3.1.2, RSL-RL `OnPolicyRunner`, gym registration via `import constrained_albc`.

**Critical facts (verified 2026-05-25, do not re-derive):**
- isaaclab source/ fork = 2 files: `rl_cfg.py` (+7 lines `weight_decay`), `urdf_converter.py` (-1 blank line). `git diff cbf51abb..HEAD --stat -- source/` shows exactly these.
- `state_dependent_std` is STOCK (present at merge-base `rl_cfg.py:34`); our cfgs never set it. NOT a fork. Docs that call it a fork are WRONG.
- rsl_rl fork = `algorithms/ppo.py` ONLY (all other modules byte-identical to stock 3.1.2). Adds 6 ctor kwargs + 199-line `_update_encoder_ppo()`.
- Main TRPO bypasses rsl_rl.PPO. PPO ablation (`Isaac-FullDOF-PPO-Enc-v0`, `Isaac-FullDOF-PPO-v0`) uses stock `rsl_rl.PPO` (`class_name="PPO"`), has NO encoder params, never sets `weight_decay`/fork kwargs.
- Stock PPO 3.1.2 ctor accepts NONE of: `weight_decay`, `encoder_grad_scale`, `use_encoder_update`, `min_lr`, `max_lr`, `reward_scale`.
- No training is running (verified ps + nvidia-smi). Do NOT start a training run during this work (`feedback-no-install-swap`).

**Paths:**
- isaaclab repo: `/workspace/isaaclab` (git, upstream remote present, merge-base `cbf51abb`)
- constrained-albc repo: `/workspace/constrained-albc` (git)
- rsl_rl site-package: `/isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl`
- Python interpreter: `/isaac-sim/python.sh` (or PATH `python` wrapper)

---

## File Structure

| File | Repo | Responsibility | Action |
|---|---|---|---|
| `docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak` | constrained-albc | Provenance backup of the forked ppo.py (restore path if regression) | create |
| `<site>/rsl_rl/algorithms/ppo.py` | (site-package) | PPO algorithm | reinstall stock |
| `source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py` | isaaclab | RSL-RL cfg dataclasses | restore merge-base |
| `source/isaaclab/isaaclab/sim/converters/urdf_converter.py` | isaaclab | URDF import | restore merge-base |
| `docs/architecture.md` | constrained-albc | Stack/dependency doc | correct fork claims |
| `docs/installation.md` | constrained-albc | Install doc | correct fork claims |

---

### Task 1: Back up the forked ppo.py before touching anything

**Files:**
- Create: `/workspace/constrained-albc/docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak`

- [ ] **Step 1: Copy the current forked ppo.py with a provenance header**

The backup is a plain `.bak` (not importable), so prepend a header comment, then the file body. Run:

```bash
SITE=/isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl/algorithms/ppo.py
DEST=/workspace/constrained-albc/docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak
{
  echo "# PROVENANCE BACKUP — forked rsl_rl/algorithms/ppo.py (rsl-rl-lib 3.1.2 base)"
  echo "# Removed 2026-05-25 (fork-removal-design.md). Stock 3.1.2 reinstalled in its place."
  echo "# Fork added: encoder_grad_scale/use_encoder_update/min_lr/max_lr/reward_scale/weight_decay"
  echo "# ctor kwargs + a 199-line _update_encoder_ppo() (HORA-style per-epoch LR + z-bounds)."
  echo "# The main TRPO pipeline never used this (ConstraintTRPO is standalone)."
  echo "# Restore ONLY if a removed-fork regression surfaces in a PPO-encoder ablation."
  echo "#"
  cat "$SITE"
} > "$DEST"
```

- [ ] **Step 2: Verify the backup is non-empty and contains the fork marker**

Run:
```bash
grep -c "_update_encoder_ppo" /workspace/constrained-albc/docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak
wc -l /workspace/constrained-albc/docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak
```
Expected: grep count >= 1 (method def present), line count > 600.

- [ ] **Step 3: Commit the backup**

```bash
cd /workspace/constrained-albc
git add docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak
git commit -m "chore: back up forked rsl_rl ppo.py before stock reinstall

Provenance copy of the forked algorithms/ppo.py (rsl-rl-lib 3.1.2 base) so the
exact fork can be restored if a regression surfaces. The main TRPO pipeline does
not use it; reinstalling stock 3.1.2 next.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Reinstall stock rsl-rl-lib 3.1.2 over the fork

**Files:**
- Modify (via pip, not editor): `/isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl/algorithms/ppo.py`

- [ ] **Step 1: Confirm no training process is running (gate before any install)**

Run:
```bash
ps aux | grep -E "train\.py|train_student" | grep -v grep || echo "NO_TRAINING"
```
Expected: prints `NO_TRAINING`. If any training process is listed, STOP — do not proceed (`feedback-no-install-swap`).

- [ ] **Step 2: Record the fork is present (pre-state)**

Run:
```bash
grep -c "_update_encoder_ppo" /isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl/algorithms/ppo.py
```
Expected: `1` (fork present before reinstall).

- [ ] **Step 3: Reinstall stock, dependencies untouched**

Run:
```bash
/isaac-sim/python.sh -m pip install rsl-rl-lib==3.1.2 --no-deps --force-reinstall
```
Expected: "Successfully installed rsl-rl-lib-3.1.2". The `--no-deps` keeps torch/numpy/etc untouched; `--force-reinstall` overwrites the forked files.

- [ ] **Step 4: Verify the fork is gone (post-state gate G1)**

Run:
```bash
/isaac-sim/python.sh -m pip show rsl-rl-lib | grep -E "Version|Location"
grep -c "_update_encoder_ppo" /isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl/algorithms/ppo.py || echo "0"
grep -c "encoder_grad_scale" /isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl/algorithms/ppo.py || echo "0"
```
Expected: Version 3.1.2; both grep counts `0` (fork symbols gone). No commit — site-package is not git-tracked; provenance is the backup from Task 1.

---

### Task 3: Restore the two isaaclab source files to the fork point

**Files:**
- Modify: `/workspace/isaaclab/source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py` (remove `weight_decay` +7)
- Modify: `/workspace/isaaclab/source/isaaclab/isaaclab/sim/converters/urdf_converter.py` (restore -1 blank line)

- [ ] **Step 1: Confirm exactly these two files differ from merge-base (pre-state)**

Run:
```bash
cd /workspace/isaaclab
git diff cbf51abb..HEAD --name-only -- source/
```
Expected: exactly two lines —
```
source/isaaclab/isaaclab/sim/converters/urdf_converter.py
source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py
```
If any other file appears, STOP and report (scope drift).

- [ ] **Step 2: Restore both files from merge-base**

Run:
```bash
cd /workspace/isaaclab
git checkout cbf51abb -- source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py
git checkout cbf51abb -- source/isaaclab/isaaclab/sim/converters/urdf_converter.py
```

- [ ] **Step 3: Verify isaaclab source is now pristine (gate G4)**

Run:
```bash
cd /workspace/isaaclab
git diff cbf51abb..HEAD --stat -- source/
grep -n "weight_decay" source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py || echo "NO_WEIGHT_DECAY"
grep -n "state_dependent_std" source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py | head -1
```
Expected: `git diff` stat is EMPTY (no source/ diff vs merge-base); `weight_decay` prints `NO_WEIGHT_DECAY` (removed); `state_dependent_std` still present at line 34 (it is stock, must remain).

- [ ] **Step 4: Commit the restore**

```bash
cd /workspace/isaaclab
git add source/isaaclab_rl/isaaclab_rl/rsl_rl/rl_cfg.py source/isaaclab/isaaclab/sim/converters/urdf_converter.py
git commit -m "revert: restore isaaclab source to fork-base (remove weight_decay fork)

Restore rl_cfg.py (drop our weight_decay field, +7) and urdf_converter.py (a
removed blank line) to merge-base cbf51abb. isaaclab source/ is now byte-pristine.
state_dependent_std is a stock field and stays. The PPO ablation never set
weight_decay, so dropping the inherited field is safe (verified next task).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Verify main TRPO + PPO ablation construct and train against stock (gates G2/G3/G5)

**Files:** none modified — this is the behavioral verification task. If a gate fails, the failure dictates a follow-up fix (see Step 5).

- [ ] **Step 1: Main TRPO smoke (gate G2)**

Run:
```bash
cd /workspace/constrained-albc
timeout 600 python scripts/train.py --task Isaac-FullDOF-TRPO-v0 --num_envs 4 --headless --max_iterations 1 2>&1 | tail -30
```
Expected: log shows `Using overlay runner ConstraintEncoderRunner` and reaches `Learning iteration 0/1` (or `1/1`), process exits without traceback. This proves stock rsl_rl + restored isaaclab still run the main pipeline.

- [ ] **Step 2: PPO ablation smoke (gate G3 — the decoupling check)**

Run:
```bash
cd /workspace/constrained-albc
timeout 600 python scripts/train.py --task Isaac-FullDOF-PPO-Enc-v0 --num_envs 4 --headless --max_iterations 1 2>&1 | tail -30
```
Expected: the PPO algorithm constructs and reaches `Learning iteration 0/1` with NO `TypeError: __init__() got an unexpected keyword argument 'weight_decay'` (or any fork kwarg). This proves the ablation cfg is stock-PPO compatible after the fork removal.

- [ ] **Step 3: Plain PPO ablation smoke (second ablation path)**

Run:
```bash
cd /workspace/constrained-albc
timeout 600 python scripts/train.py --task Isaac-FullDOF-PPO-v0 --num_envs 4 --headless --max_iterations 1 2>&1 | tail -30
```
Expected: same as Step 2 — constructs, iteration 0, no kwarg TypeError.

- [ ] **Step 4: Stock Cartpole regression (gate G5)**

Run:
```bash
cd /workspace/isaaclab
timeout 600 ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py --task Isaac-Cartpole-v0 --num_envs 4 --headless --max_iterations 1 2>&1 | tail -20
```
Expected: reaches `Learning iteration 0` with no import/ctor error — proves stock rsl_rl + pristine isaaclab did not regress unrelated tasks.

- [ ] **Step 5: If any ablation gate (Step 2/3) raised a kwarg TypeError, drop the offending field**

Only if a `TypeError: ... unexpected keyword argument '<kwarg>'` appears on PPO construction:
- Open `/workspace/constrained-albc/constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py`.
- Locate `_FullDOFPPOAlgorithmCfg` (around line 332). Remove any field named `<kwarg>` that stock PPO 3.1.2 does not accept (the stock ctor accepts only: `num_learning_epochs, num_mini_batches, clip_param, gamma, lam, value_loss_coef, entropy_coef, learning_rate, max_grad_norm, use_clipped_value_loss, schedule, desired_kl, normalize_advantage_per_mini_batch, rnd_cfg, symmetry_cfg`; plus `class_name` which the runner consumes, not PPO).
- Re-run Step 2/3 until clean.
- Note: based on the audit, `_FullDOFPPOAlgorithmCfg` sets none of the fork kwargs, so this step is expected to be a no-op. It exists only as the documented fix path if the audit missed something.

- [ ] **Step 6: No commit (no files changed unless Step 5 fired)**

If Step 5 changed `rsl_rl_ppo_cfg.py`, commit it:
```bash
cd /workspace/constrained-albc
git add constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py
git commit -m "fix(cfg): drop fork-only PPO kwarg from ablation cfg for stock rsl_rl

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```
Otherwise skip (verification-only task, nothing to commit).

---

### Task 5: Correct the false fork claims in the overlay docs

**Files:**
- Modify: `/workspace/constrained-albc/docs/architecture.md:8,45-78`
- Modify: `/workspace/constrained-albc/docs/installation.md:71-88`

- [ ] **Step 1: Read both fork-claim sections to get exact current wording**

Run:
```bash
sed -n '40,80p' /workspace/constrained-albc/docs/architecture.md
echo "===== installation ====="
sed -n '68,90p' /workspace/constrained-albc/docs/installation.md
```
(Read the actual lines before editing — wording may have shifted from the grep snapshot.)

- [ ] **Step 2: Rewrite architecture.md's RSL-RL section to state there is no fork**

In `docs/architecture.md`, replace the "forked RSL-RL stack" section (the block beginning around line 45 "constrained-albc depends on a **forked RSL-RL stack**" through the "A clean environment must install both forks" paragraph around line 78) with an accurate description. The new text must say:
- constrained-albc uses **stock `rsl-rl-lib==3.1.2`** and **stock `isaaclab_rl`** — no forks.
- The main TRPO pipeline does not subclass stock rsl_rl: `ConstraintTRPO` is a standalone algorithm and `ActorCriticEncoder(PolicyBase)` is a custom policy base, both injected into the runner namespace by the overlay.
- `state_dependent_std` is a STOCK `RslRlPpoActorCriticCfg` field (not used by our cfgs); `weight_decay` was a former fork field, now removed (the PPO ablation never set it).

Also fix line 8: change `RSL-RL fork, forked isaaclab_rl` to `stock RSL-RL, stock isaaclab_rl`.

Use this replacement for the section body (adapt surrounding markdown to match the file's heading style):
```markdown
## RSL-RL dependency (stock, no fork)

constrained-albc runs on **stock `rsl-rl-lib==3.1.2`** and **stock `isaaclab_rl`**.
There are no forks: a fresh-machine install is `pip install rsl-rl-lib==3.1.2` plus
the clean isaaclab fork-point checkout.

The main pipeline does not subclass stock rsl_rl. `Isaac-FullDOF-TRPO-v0` uses:
- `ConstraintTRPO` — a standalone algorithm (own `optim.Adam`), NOT an `rsl_rl.PPO`
  subclass. Injected into `rsl_rl.runners.on_policy_runner`'s namespace by the overlay
  runner so `OnPolicyRunner`'s `eval(class_name)` resolves it.
- `ActorCriticEncoder(PolicyBase)` — a custom policy base, NOT `rsl_rl.ActorCritic`.

The PPO ablations (`Isaac-FullDOF-PPO-v0`, `Isaac-FullDOF-PPO-Enc-v0`) use stock
`rsl_rl.PPO` with `class_name="PPO"`; they set only stock algorithm fields.

Notes on fields that previously looked fork-specific:
- `state_dependent_std` is a STOCK `RslRlPpoActorCriticCfg` field (present upstream at
  the fork point); our cfgs do not set it.
- `weight_decay` was a former local addition to `RslRlPpoAlgorithmCfg`; it has been
  removed. The PPO ablation never set it, so stock PPO (which lacks the kwarg) is
  fully compatible.
```

- [ ] **Step 3: Rewrite installation.md's "RSL-RL fork" section**

In `docs/installation.md`, replace the "## RSL-RL fork — critical dependency" section (lines ~71-88, the block with "A stock `rsl-rl-lib` from PyPI will fail at runtime" and the two numbered forks) with:
```markdown
## RSL-RL dependency (stock)

constrained-albc runs on **stock `rsl-rl-lib==3.1.2`** — no fork is required.

```bash
/isaac-sim/python.sh -m pip install rsl-rl-lib==3.1.2 --no-deps
```

`isaaclab_rl` is the clean isaaclab fork-point version (no local cfg fields added).
The main TRPO pipeline ships its own `ConstraintTRPO` algorithm and `ActorCriticEncoder`
policy (custom, injected into the runner namespace), so it does not depend on any
rsl_rl modification. See [`architecture.md`](architecture.md) → "RSL-RL dependency".
```

- [ ] **Step 4: Verify no stale fork claims remain**

Run:
```bash
grep -n -iE "forked rsl|rsl.rl fork|two forks|both forks|will fail at runtime" /workspace/constrained-albc/docs/architecture.md /workspace/constrained-albc/docs/installation.md || echo "NO_STALE_FORK_CLAIMS"
```
Expected: `NO_STALE_FORK_CLAIMS`.

- [ ] **Step 5: Commit the doc corrections**

```bash
cd /workspace/constrained-albc
git add docs/architecture.md docs/installation.md
git commit -m "docs: correct RSL-RL fork claims — stack is stock, no fork

Audit (2026-05-25) showed the 'forked RSL-RL stack' claim was false: the main TRPO
pipeline uses a standalone ConstraintTRPO + custom ActorCriticEncoder, depending on
zero rsl_rl modifications. state_dependent_std is a stock field; weight_decay (the
only real isaaclab_rl fork) is now removed. Docs now say: stock rsl-rl-lib 3.1.2,
stock isaaclab_rl, no fork.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- rsl_rl ppo.py → stock: Task 2 ✓ (backup Task 1)
- rl_cfg.py + urdf_converter.py → merge-base: Task 3 ✓
- ablation cfg decoupling verified: Task 4 Steps 2/3/5 ✓
- architecture.md / installation.md corrected: Task 5 ✓
- Gates G1 (Task 2 Step 4), G2/G3/G5 (Task 4), G4 (Task 3 Step 3) all mapped ✓
- R2 backup: Task 1 ✓; R3 no-install-swap: Task 2 Step 1 ✓

**Placeholder scan:** No TBD/TODO. Doc rewrites give full replacement text. Task 4 Step 5 is a conditional fix with the exact stock-ctor field allowlist, not a vague "handle errors."

**Consistency:** Task ids `Isaac-FullDOF-PPO-Enc-v0` / `Isaac-FullDOF-PPO-v0` match the registry (verified). Stock PPO ctor field list in Task 4 Step 5 matches the merge-base `RslRlPpoAlgorithmCfg` + stock PPO `__init__` (verified). Backup path consistent across Task 1 and the design doc.

**Note on test style:** No pytest tasks — this is a dependency/config change verified by train-smoke gates, consistent with the project's eval-by-running convention. Unit tests would require booting Isaac Sim and add no signal beyond the smoke gates.
