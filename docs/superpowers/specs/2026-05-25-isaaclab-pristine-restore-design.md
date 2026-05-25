# isaaclab Pristine Restore + Overlay-Owned Train Entry — Design

**Date:** 2026-05-25
**Status:** Approved (brainstorming complete)
**Scope:** Two repos — `isaaclab` (remove our scripts/ contamination) and
`constrained-albc` (own the train entry point).

## Problem

After the 3-repo split ([repo-3split](../../../../isaaclab/docs/superpowers/specs/2026-05-25-repo-3split-design.md)),
a smoke-test train run (`Isaac-FullDOF-TRPO-v0 --num_envs 4 --livestream 2`) revealed
that `isaaclab` is **not** the pristine upstream fork it was supposed to be.

A full audit against `upstream/main` (merge-base `cbf51abb`) found that we directly
modified 15 files since the fork base. The contamination splits into two failure modes:

1. **gym.register self-register gap** (already understood, launcher import-hook handles
   it): upstream `train.py` imports only `isaaclab_tasks`, so overlay envs never register.
2. **isaaclab `scripts/` carry our code** (this design): `train.py` / `play.py` carry a
   hardcoded `_RUNNER_MAP` pointing at the old `isaaclab_tasks.direct.constrained_full_albc`
   namespace, which no longer exists after the split → `ModuleNotFoundError` at runner
   creation, even though the env was created successfully.

## "Pristine" — settled definition

`feedback-isaaclab-pristine` says "zero of our code in isaaclab." But the split design
(`constrained-albc/docs/architecture.md`) explicitly documents `isaaclab_rl` and the
`rsl_rl` package as **intentionally forked** (custom `weight_decay`, `state_dependent_std`,
encoder ctor kwargs). These two statements conflict.

**Resolution (user-confirmed 2026-05-25): "pristine" applies to `scripts/` only.**

- `scripts/` (train/play/demos) → restored to upstream, zero of our code.
- `source/isaaclab_rl` + forked `rsl_rl` package → remain a documented, intentional fork.
  This matches `architecture.md` and the project CLAUDE.md note ("isaaclab_rl retains
  state_dependent_std/weight_decay cfg fields — constrained-albc depends on them").

**Restore baseline = the fork point (`cbf51abb`), NOT current `upstream/main`
(learned during execution).** Our `isaaclab_rl` is an OLD fork; `upstream/main` has since
added symbols our fork lacks (e.g. `handle_deprecated_rsl_rl_cfg`). Restoring `scripts/`
from `upstream/main` makes even stock `Isaac-Cartpole-v0` fail at import
(`ImportError: cannot import name 'handle_deprecated_rsl_rl_cfg'`). The pristine baseline
must be the upstream tree contemporaneous with our `isaaclab_rl` — i.e. the merge-base
`cbf51abb` (equivalently, what a fresh clone at our fork point would contain). So:
`git checkout cbf51abb -- scripts/...`, not `git checkout upstream/main -- ...`.
"Pristine" = our-code-free AND compatible with our forked `isaaclab_rl`, not
"byte-identical to today's upstream/main".

### Audit verdict (merge-base `cbf51abb` .. HEAD)

| File | Action | Rationale |
|---|---|---|
| `scripts/reinforcement_learning/rsl_rl/train.py` | restore upstream | `_RUNNER_MAP` contamination; overlay launcher replaces it |
| `scripts/reinforcement_learning/rsl_rl/play.py` | restore upstream | +383 lines contamination (same `_RUNNER_MAP` + FullDOF CLI args + encoder export branch) |
| `scripts/reinforcement_learning/rsl_rl/play_student.py` | restore (delete from isaaclab) | our new file; play entry deferred (YAGNI) |
| `scripts/demos/*.py` (9 files) | **delete** | hero/full_dof debug scripts, never isaaclab demos; recoverable from git history |
| `source/isaaclab_tasks/.../direct/__init__.py` | restore upstream | accidental `import gymnasium as gym` deletion |
| `source/isaaclab_rl/.../rsl_rl/rl_cfg.py` (`weight_decay`) | **keep** | documented intentional fork; overlay depends on it (`TypeError` otherwise) |
| forked `rsl_rl` package (actor_critic/ppo kwargs) | **keep** | documented intentional fork |

Note: `state_dependent_std` is NOT our contamination — upstream/main added it
independently (rl_cfg.py:88,371). Only `weight_decay` is ours, and it is intentional.

## Why overlay owns the train entry (not a runpy delegation)

The first launcher delegated to upstream `train.py` via `runpy` + an import-hook. That
solved registration but **cannot solve runner dispatch**: upstream `train.py` hardcodes
exactly two runner classes (`OnPolicyRunner`, `DistillationRunner`) and raises
`ValueError` on anything else. Our envs use **two distinct custom runners**:

- `Isaac-FullDOF-TRPO-v0` → `class_name="FullDOFConstraintEncoderRunner"` → `ConstraintEncoderRunner`
- ablations → `class_name="OnPolicyDoraemonRunner"` → `OnPolicyDoraemonRunner`

Aliasing both onto the single `"OnPolicyRunner"` branch loses the distinction. The honest
structure is: **the overlay owns its train entry point** and contains its own runner
dispatch map. This is the real meaning of "isaaclab pristine."

### Runner signature compatibility (verified 2026-05-25)

Both custom runners are drop-in `OnPolicyRunner` subclasses:
- `ConstraintEncoderRunner.__init__(self, env, train_cfg, log_dir=None, device="cpu")`
  — matches upstream's `OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=..., device=...)`.
- `OnPolicyDoraemonRunner` has no `__init__` override (inherits `OnPolicyRunner`).

So the overlay launcher can instantiate them with the same positional call upstream uses.

## Design: overlay-owned `constrained-albc/scripts/train.py`

The launcher replicates upstream `train.py`'s `main()` body (≈90 lines: CLI override,
seed, log_dir, `gym.make`, video wrap, `RslRlVecEnvWrapper`, checkpoint resume, dump,
`runner.learn`). The **only** divergence from upstream is the runner-dispatch block,
which the overlay owns:

```python
_RUNNER_MAP = {
    "FullDOFConstraintEncoderRunner": ConstraintEncoderRunner,
    "OnPolicyDoraemonRunner": OnPolicyDoraemonRunner,
}
runner_cls = _RUNNER_MAP.get(agent_cfg.class_name)
if runner_cls is not None:
    runner = runner_cls(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
elif agent_cfg.class_name == "OnPolicyRunner":
    runner = OnPolicyRunner(...)
elif agent_cfg.class_name == "DistillationRunner":
    runner = DistillationRunner(...)
else:
    raise ValueError(...)
```

Registration: keep the existing one-shot `builtins.__import__` hook so `constrained_albc`
is imported when `isaaclab_tasks` is imported (post-AppLauncher, so `pxr` exists) — this
triggers `gym.register()` for the overlay envs. The launcher still uses the upstream
`AppLauncher`/argparse boilerplate from upstream train.py (replicated, not delegated).

**Drift control:** the launcher's docstring states "main() body replicated from
upstream/main `scripts/reinforcement_learning/rsl_rl/train.py`" so future upstream rebases
can diff against it. The replicated section is a stable, rarely-changed part of upstream.

**Caveat — target our forked isaaclab_rl, not upstream/main (learned during execution):**
the replicated main() must use only symbols our INSTALLED (forked) `isaaclab_rl` exports,
not whatever upstream/main's train.py imports. Our fork sits at merge-base `cbf51abb`, which
predates upstream/main's `handle_deprecated_rsl_rl_cfg` helper — that symbol does not exist
in our `isaaclab_rl.rsl_rl`. The launcher therefore drops both the
`handle_deprecated_rsl_rl_cfg` import and its call (our agent cfgs need no deprecation shim).
Rule of thumb: when replicating upstream main(), reconcile imports against
`git show HEAD:source/isaaclab_rl/.../rsl_rl/__init__.py`, not against upstream/main.

### Components

- `constrained-albc/scripts/train.py` — full overlay train entry (replaces the thin
  runpy launcher). Imports custom runners directly, owns `_RUNNER_MAP`, keeps import-hook
  for registration.
- `isaaclab/scripts/reinforcement_learning/rsl_rl/train.py` — restored to upstream/main.
- `isaaclab/scripts/reinforcement_learning/rsl_rl/play.py` — restored to upstream/main.
- `isaaclab/scripts/reinforcement_learning/rsl_rl/play_student.py` — deleted.
- `isaaclab/scripts/demos/*.py` (9) — deleted.
- `isaaclab/source/isaaclab_tasks/.../direct/__init__.py` — restored to upstream/main.

### Play entry — deferred (YAGNI)

`play.py` is restored to upstream; FullDOF play is NOT re-created. Rationale: project rules
(`03-analysis-quality.md`, `feedback-eval-fulldof`) mandate `eval_dr.py static` as the
canonical Full-DOF evaluation tool, and `eval_dr.py` boots its own AppLauncher + registers
the overlay independently of `play.py`. A FullDOF play launcher will be added to the
overlay only when livestream visualization is actually needed.

## Verification

1. After restore: `cd isaaclab && git diff upstream/main HEAD -- scripts/` shows **zero**
   of our scripts/ lines (only legitimate upstream-version diffs, ideally none in the RL
   scripts). Specifically `_RUNNER_MAP` / `constrained_full_albc` strings are gone from
   `scripts/`.
2. Overlay launcher smoke: `cd isaaclab && ./isaaclab.sh -p
   /workspace/constrained-albc/scripts/train.py --task Isaac-FullDOF-TRPO-v0
   --num_envs 4 --headless` reaches **"Learning iteration 0"** (env created, runner built,
   first rollout). Headless for the verification run (faster; livestream is a separate
   manual concern).
3. `source/isaaclab_rl` `weight_decay` field still present (overlay cfg construction does
   not raise `TypeError`).

## Out of scope

- Touching the forked `rsl_rl` package or `isaaclab_rl` cfg fields (intentional fork).
- Re-creating FullDOF `play.py` (deferred).
- The `marinelab` overlay (its BlueROV envs register fine; not implicated here).
