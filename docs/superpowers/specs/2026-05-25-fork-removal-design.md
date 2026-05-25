# isaaclab + rsl_rl Fork 완전 제거 — Design

**Date:** 2026-05-25
**Status:** Approved (brainstorming complete)
**Scope:** Three repos/packages — `isaaclab` source/ (2 files), the `rsl_rl`
site-package (1 file), and `constrained-albc` (1 ablation cfg + 2 docs).

## Problem

The 3-repo split documented `isaaclab_rl` + the `rsl_rl` package as "intentional
forks." A code-grep audit (2026-05-25) found the forks are **mostly dead** for the
main pipeline: `Isaac-FullDOF-TRPO-v0` uses a standalone `ConstraintTRPO` (NOT a
stock-PPO subclass) and a custom `ActorCriticEncoder(PolicyBase)` (NOT a stock
rsl_rl class). The forks survive only as a documented dependency the main pipeline
never exercises. The user asked to remove the fork so isaaclab/rsl_rl are byte-stock.

## Ground truth (verified 2026-05-25, code-grep + stock diff)

**isaaclab `source/` fork = 2 files, both trivial:**
- `source/isaaclab_rl/.../rsl_rl/rl_cfg.py`: `+7` lines — `weight_decay: float = 0.0`
  field added to `RslRlPpoAlgorithmCfg`.
- `source/isaaclab/.../sim/converters/urdf_converter.py`: `-1` line — a blank line
  removed. Meaningless whitespace.
- (`git diff cbf51abb..HEAD --stat -- source/` shows exactly these two.)

**rsl_rl site-package fork = 1 file (`algorithms/ppo.py`), substantial:**
- Installed at `/isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl`, version
  3.1.2, NOT an editable install.
- Diff vs stock `rsl-rl-lib==3.1.2`: ONLY `ppo.py` differs (all other modules are
  byte-identical). Added: 6 ctor kwargs (`min_lr`, `max_lr`, `encoder_grad_scale`,
  `use_encoder_update`, `reward_scale`, `weight_decay`), encoder-detection logic,
  reward scaling, and a 199-line `_update_encoder_ppo()` method (HORA-style per-epoch
  LR + mu/sigma refresh + z-bounds loss + encoder grad scaling).
- `state_dependent_std` is a **stock** 3.1.2 feature (in `actor_critic.py`), NOT a
  fork addition — the prior analysis was wrong on this point.

**Dependency verdict (the critical fact):**
- Main TRPO pipeline depends on ZERO fork modifications. `ConstraintTRPO` is
  `class ConstraintTRPO:` (standalone, own `optim.Adam`); `ActorCriticEncoder(PolicyBase)`
  is a custom base. The runner `ConstraintEncoderRunner(OnPolicyRunner)` subclasses
  rsl_rl's runner but the algorithm is fully custom.
- The PPO-Enc / PPO ablations use stock `rsl_rl.PPO` (`class_name="PPO"`,
  policy `class_name="ActorCritic"`). `_FullDOFPPOAlgorithmCfg(RslRlPpoAlgorithmCfg)`
  inherits `weight_decay` but **never sets** it (stays 0.0 default) and never sets the
  fork kwargs. The ablation policy has **no encoder params**, so the fork's
  `_has_encoder_params` is False and `_update_encoder_ppo()` is never entered.
- The fork's only live surface is therefore: (a) the inherited `weight_decay=0.0` field
  on the ablation cfg, and (b) `min_lr`/`max_lr`/`reward_scale` defaults that stock PPO
  lacks — but the ablation passes none of them, so swapping to stock changes nothing the
  ablation actually exercises.

**Version compat:** our isaaclab_rl is at merge-base `cbf51abb` and its
`isaaclab_rl/rsl_rl/__init__.py` does NOT export `handle_deprecated_rsl_rl_cfg`
(that's a newer upstream symbol). Stock `rsl_rl.PPO.__init__` (3.1.2) accepts none of
the fork kwargs (`weight_decay`/`encoder_grad_scale`/`use_encoder_update`/`min_lr`/
`max_lr`/`reward_scale`) — confirmed from the downloaded stock wheel.

## Scope

| Target | Current | Action |
|---|---|---|
| rsl_rl `ppo.py` (site-package) | fork (encoder kwargs + `_update_encoder_ppo` + reward_scale + min/max_lr) | reinstall stock `rsl-rl-lib==3.1.2 --no-deps --force-reinstall` |
| isaaclab `rl_cfg.py` | fork: `weight_decay` +7 | restore to merge-base `cbf51abb` |
| isaaclab `urdf_converter.py` | fork: -1 blank line | restore to merge-base `cbf51abb` |
| `_FullDOFPPOAlgorithmCfg` | `RslRlPpoAlgorithmCfg` subclass | keep subclass but ensure it never carries `weight_decay` to stock PPO — restored stock parent has no `weight_decay`, so the inherited field disappears cleanly; cfg sets only stock fields (no code change needed beyond verifying construction). Per `fork-not-inherit`, the cfg already enumerates its own fields explicitly. |
| architecture.md / installation.md | "rsl_rl/isaaclab_rl fork required" | correct to "stock rsl-rl-lib==3.1.2, no fork" |

### Ablation cfg decoupling (user-confirmed: "explicit self-copy")

The user chose explicit self-copy over silent inheritance (`fork-not-inherit` rule).
Concretely: after restoring `rl_cfg.py` to merge-base, stock `RslRlPpoAlgorithmCfg`
has NO `weight_decay` field. `_FullDOFPPOAlgorithmCfg` already enumerates every field
it uses (`num_learning_epochs`, `learning_rate`, `schedule`, ... `clip_param`) and
never sets `weight_decay`, so the inherited field simply vanishes — the cfg's
to_dict() will no longer contain `weight_decay`, matching stock PPO's ctor exactly.
No field needs adding; the task is to VERIFY (G3 smoke) that the ablation cfg
constructs and trains against stock PPO with zero `TypeError`. If a `TypeError` on an
unexpected kwarg appears, the fix is to drop that kwarg from the cfg (it was a
fork-only field).

## Data flow (why it is safe)

`OnPolicyDoraemonRunner(OnPolicyRunner)` builds PPO from
`agent_cfg.to_dict()["algorithm"]`. Stock PPO 3.1.2 raises on unknown kwargs, so the
ablation cfg must contain only stock fields. Restoring `rl_cfg.py` to merge-base
removes the one non-stock field (`weight_decay`) from the inheritance chain, so the
ablation cfg becomes stock-compatible automatically. The main TRPO pipeline bypasses
rsl_rl.PPO entirely (`ConstraintTRPO` standalone), so it is unaffected by the swap.

## Verification (gates, run in order)

| Gate | Command | Expected |
|---|---|---|
| G1 stock installed | `pip show rsl-rl-lib` + `grep -c _update_encoder_ppo <site>/rsl_rl/algorithms/ppo.py` | version 3.1.2; grep count 0 |
| G2 main TRPO smoke | `cd /workspace/constrained-albc && python scripts/train.py --task Isaac-FullDOF-TRPO-v0 --num_envs 4 --headless --max_iterations 1` | "Learning iteration 0" reached, exit 0 |
| G3 PPO ablation smoke | same launcher, `--task <PPO ablation task id> --num_envs 4 --headless --max_iterations 1` | cfg constructs, iteration 0, NO TypeError on PPO ctor |
| G4 isaaclab pristine | `cd /workspace/isaaclab && git diff cbf51abb..HEAD --stat -- source/` | empty (both files restored) |
| G5 stock regression | `Isaac-Cartpole-v0` via isaaclab train.py, `--num_envs 4 --headless --max_iterations 1` | iteration 0, no import/ctor error |

The exact PPO ablation task id is resolved at plan time from the gym registry
(`constrained_albc` registers NoEncoder/PPO/TRPO-NoIPO/PPO-Enc/TDC variants).

## Risks and mitigations

- **R1 reinstall breaks deps:** use `--no-deps` so only `rsl_rl` is touched;
  `--force-reinstall` to overwrite the fork in place.
- **R2 past ablation runs irreproducible:** they might have depended on the fork's
  `_update_encoder_ppo`. Investigation shows the ablation policy has no encoder params
  so the path was never entered, but as a safety net, **back up the current forked
  `ppo.py`** to `constrained-albc/docs/reference/rsl_rl_ppo_fork_3.1.2.py.bak` (a plain
  copy, not a package) before reinstalling, with a header comment noting provenance and
  why it was removed. This lets us restore the exact fork if a regression surfaces.
- **R3 no-install-swap rule:** verified no training process is running (ps + nvidia-smi).
  Do NOT start any training run during this work. Respect `feedback-no-install-swap`.

## Out of scope

- Main TRPO algorithm / policy code (`ConstraintTRPO`, `ActorCriticEncoder`) — untouched.
- marinelab and other overlays.
- isaaclab `scripts/` — already pristine (prior session).
- isaaclab `docs/hero/` removal — separate isaaclab-side change, not part of this.
