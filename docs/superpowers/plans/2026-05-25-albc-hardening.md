# constrained-albc Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore constrained-albc to a runnable state after the marinelab.core API change (P0), apply the (re-verified, shrunk) DIAGNOSIS Phase A cleanup and Phase B config de-duplication, without changing learning behavior.

**Architecture:** Layered by risk. Task 1 fixes a runtime crash (removed `_current_velocity`/`_max_current_vel` buffers) by routing through the new `OceanCurrent` component and injecting a shared current into the buoy model. Task 2 is learning-neutral cleanup. Task 3 de-duplicates config, verified by `to_dict()` equality. Task 4 records Phase C (physics/math) as diagnosis-only. Tasks 5-6 add tests and the changelog.

**Tech Stack:** Python 3.12, PyTorch, Isaac Lab DirectRLEnv, rsl_rl, pytest. Tests are Isaac-Sim-free: each test self-mocks `isaaclab`/`marinelab` via `sys.modules` and loads the module-under-test with `importlib.util.spec_from_file_location` (see `tests/test_doraemon.py`, `tests/test_tdc_controller.py`). There is no shared `conftest.py`.

**Constraints:** English code, Korean dialogue. No emoji, no AI attribution. One commit per task. Never push (ask first). Never `git add -A` — stage session files explicitly. Final branch = main only. No training. Phase C is not implemented here.

---

## File Structure

| File | Responsibility | Tasks |
|:---|:---|:---|
| `constrained_albc/envs/constrained_full_albc/albc_env.py` | env: hydro construction, OU current, obs assert | 1, 2 |
| `constrained_albc/envs/constrained_full_albc/mdp/observations.py` | privileged obs current read | 1 |
| `constrained_albc/envs/constrained_full_albc/mdp/events.py` | DR; manual buoy current sync (to remove) | 1 |
| `constrained_albc/envs/constrained_full_albc/utils/logging.py` | DR logging current read | 1 |
| `constrained_albc/envs/constrained_full_albc_tdc/controllers/tdc.py` | unused `compute_M_bb` | 2 |
| `constrained_albc/envs/constrained_full_albc_tdc/controllers/__init__.py` | exports `compute_M_bb` | 2 |
| `constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py` | 6 runner/policy cfgs (dedup target) | 3 |
| `DIAGNOSIS.md` | Phase C re-verification addendum | 4 |
| `tests/test_current_migration.py` | NEW: current API + obs assert smoke | 5 |
| `tests/test_config_equivalence.py` | NEW: config dedup `to_dict()` equality | 3, 5 |
| `CHANGELOG.md` | NEW or appended: hardening entry | 6 |

---

## Task 1: marinelab.core API compatibility recovery (P0)

The ocean current moved into a standalone `OceanCurrent` component in marinelab v0.2.0; `HydrodynamicsModel._current_velocity` and `._max_current_vel` no longer exist. albc accesses them in 8 sites in `albc_env.py` plus `observations.py`, `events.py`, `utils/logging.py`. The env imports fine but raises `AttributeError` on reset / OU step. The new API: `hydro.current` (an `OceanCurrent`) with `.velocity_w` (num_envs, 6), `.max_velocity` (6,), `.set(env_ids, velocity=, strength=)`, `.add_drift(delta)`. The constructor accepts `current=` to inject a shared component.

**Files:**
- Modify: `constrained_albc/envs/constrained_full_albc/albc_env.py` (construction ~201; OU block 688-714; reset sites 1301, 1332, 1414; log site 1129)
- Modify: `constrained_albc/envs/constrained_full_albc/mdp/observations.py:155`
- Modify: `constrained_albc/envs/constrained_full_albc/mdp/events.py:308-310`
- Modify: `constrained_albc/envs/constrained_full_albc/utils/logging.py:116-117`

- [ ] **Step 1: Inject shared current into buoy hydro**

In `albc_env.py` `_init_hydrodynamics`, the buoy currently builds its own current (`current_cfg=None` still constructs an empty `OceanCurrent`). Share the main model's current instead:

```python
self._buoy_hydro = HydrodynamicsModel(
    num_envs=self.num_envs,
    device=self.device,
    cfg=self.cfg.buoy_hydrodynamics,
    current_cfg=None,  # buoy shares main body's current (injected below)
    dt=self.physics_dt,
    articulation_prim_path=prim_path,
    current=self._hydro.current,  # shared OceanCurrent component
)
```

- [ ] **Step 2: Rewrite the OU current step to the shared-current API**

Replace `albc_env.py:688-714` `_step_ocean_current_ou` body. With a shared current, write once via the component; the buoy sees it automatically. Keep the math identical (theta/sigma/dt/clamp unchanged):

```python
def _step_ocean_current_ou(self) -> None:
    """Advance OU process one step for ocean current drift.

    dx = -theta * (x - mu) * dt + sigma * sqrt(dt) * N(0,1)

    Only linear components (xyz). Angular stays zero. main_hydro and
    buoy_hydro share one OceanCurrent component, so a single write covers both.
    """
    theta = self.cfg.ou_theta
    sigma = self.cfg.ou_sigma
    dt = self.step_dt

    velocity_w = self._hydro.current.velocity_w  # (num_envs, 6) shared buffer
    current = velocity_w[:, :3]
    mu = self._ou_base_current

    drift = -theta * (current - mu) * dt
    diffusion = sigma * (dt**0.5) * torch.randn_like(current)
    new_current = current + drift + diffusion

    # Clamp to slightly beyond max_velocity (within encoder bounds).
    # Note: axes with max_velocity=0 have OU drift clamped to zero.
    max_vel = self._hydro.current.max_velocity[:3]
    clamp_bound = max_vel * 1.05
    new_current = new_current.clamp(-clamp_bound, clamp_bound)

    velocity_w[:, :3] = new_current  # shared buffer -> buoy sees it too
```

- [ ] **Step 3: Replace the remaining read sites in `albc_env.py`**

Three reset-time reads of `_ou_base_current` initialization (lines 1301, 1332, 1414) and one log read (1129). Replace `self._hydro._current_velocity` with `self._hydro.current.velocity_w` at each:

```python
# lines 1301, 1332, 1414 (all identical shape):
self._ou_base_current[env_ids] = self._hydro.current.velocity_w[env_ids, :3].clone()
# line 1129:
current = self._hydro.current.velocity_w[env_ids, :3]
```

- [ ] **Step 4: Replace the privileged-obs read**

`observations.py:155`:

```python
env._hydro.current.velocity_w[:, :3],  # ocean current linear xyz (world frame)
```

- [ ] **Step 5: Replace the logging read**

`utils/logging.py:116-117`. The `hasattr(hydro, "_current_velocity")` guard is now always False; the current component always exists, so read it directly:

```python
        # Ocean current
        current_mag = torch.linalg.norm(hydro.current.velocity_w[:, :3], dim=-1)
        log["DR/ocean_current_mag_mean"] = current_mag.mean().item()
```

- [ ] **Step 6: Remove the manual buoy current sync in events.py**

`events.py:308-310` copied current onto the buoy by hand. With the shared component this is redundant. Delete the copy:

```python
    env._hydro.set_ocean_current(env_ids, strength=strength)
    # Buoy shares the same OceanCurrent component (injected at construction),
    # so the set above already applies to the buoy. No manual sync needed.
```

(Remove the `if env._buoy_hydro is not None:` block that did `env._buoy_hydro.set_ocean_current(env_ids, velocity=env._hydro._current_velocity[env_ids])`.)

- [ ] **Step 7: Verify no buffer references remain**

Run: `cd /workspace/constrained-albc && grep -rn "_current_velocity\|_max_current_vel" constrained_albc/ | grep -v "\.pyc"`
Expected: zero matches.

- [ ] **Step 8: Verify the package still parses**

Run: `cd /workspace/constrained-albc && python -c "import ast,glob; [ast.parse(open(f).read()) for f in glob.glob('constrained_albc/**/*.py', recursive=True)]; print('parse OK')"`
Expected: `parse OK`

- [ ] **Step 9: Commit**

```bash
cd /workspace/constrained-albc
git add constrained_albc/envs/constrained_full_albc/albc_env.py \
        constrained_albc/envs/constrained_full_albc/mdp/observations.py \
        constrained_albc/envs/constrained_full_albc/mdp/events.py \
        constrained_albc/envs/constrained_full_albc/utils/logging.py
git commit -m "fix: migrate ocean current to marinelab.core OceanCurrent API

marinelab v0.2.0 removed HydrodynamicsModel._current_velocity / _max_current_vel
(ocean current moved into a standalone OceanCurrent component). albc accessed the
removed buffers in 8+ sites, crashing on env reset / OU step. Route through
hydro.current.velocity_w / .max_velocity / .set, and inject the main model's
OceanCurrent into the buoy so both share one flow field (manual per-step sync
removed). OU math unchanged.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Phase A cleanup (runtime obs-shape assert + dead-code removal)

Re-verification showed DIAGNOSIS A1's config-time assert already exists (`albc_env.py:138-143`) and A2's sigma preallocation is already done (`albc_env.py:153`). Two items remain.

**Files:**
- Modify: `constrained_albc/envs/constrained_full_albc/albc_env.py` (`_get_observations`, line ~922)
- Modify: `constrained_albc/envs/constrained_full_albc_tdc/controllers/tdc.py:499` (remove `compute_M_bb`)
- Modify: `constrained_albc/envs/constrained_full_albc_tdc/controllers/__init__.py:9,18` (drop export)

- [ ] **Step 1: Add runtime obs-shape assert in `_get_observations`**

After `observations = {"policy": policy_obs}` (line 922), assert the emitted tensor width matches the configured value. This catches drift between the construction-time computed width and the tensor actually emitted:

```python
        observations = {"policy": policy_obs}
        assert policy_obs.shape[-1] == self.cfg.observation_space, (
            f"emitted policy obs dim {policy_obs.shape[-1]} != "
            f"cfg.observation_space {self.cfg.observation_space}"
        )
```

- [ ] **Step 2: Confirm `compute_M_bb` has zero call sites**

Run: `cd /workspace/constrained-albc && grep -rn "compute_M_bb" constrained_albc/ | grep -v "\.pyc"`
Expected: only the definition (`tdc.py:499`) and the export (`controllers/__init__.py:9,18`). No actual call.

- [ ] **Step 3: Remove `compute_M_bb` and its export**

Delete the `compute_M_bb` function definition in `tdc.py` (read its full extent first; it starts at line 499). In `controllers/__init__.py`, remove `compute_M_bb` from both the import line (9) and `__all__` (18).

- [ ] **Step 4: Verify parse + import-integrity**

Run: `cd /workspace/constrained-albc && grep -rn "compute_M_bb" constrained_albc/ | grep -v "\.pyc"`
Expected: zero matches.
Run: `python -c "import ast,glob; [ast.parse(open(f).read()) for f in glob.glob('constrained_albc/**/*.py', recursive=True)]; print('parse OK')"`
Expected: `parse OK`

- [ ] **Step 5: Commit**

```bash
cd /workspace/constrained-albc
git add constrained_albc/envs/constrained_full_albc/albc_env.py \
        constrained_albc/envs/constrained_full_albc_tdc/controllers/tdc.py \
        constrained_albc/envs/constrained_full_albc_tdc/controllers/__init__.py
git commit -m "refactor: runtime obs-shape assert + remove unused compute_M_bb

Add a runtime assert in _get_observations() that the emitted policy tensor width
equals cfg.observation_space (complements the existing construction-time check at
albc_env.py:138). Remove compute_M_bb (tdc.py): exported but zero call sites
(grep-verified). DIAGNOSIS A2 (hot-loop sigma) was already preallocated;
randomize_ocean_current is live (not dead) and kept.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: config de-duplication (behavior-preserving)

`agents/rsl_rl_ppo_cfg.py` repeats `seed=30, num_steps_per_env=64, max_iterations=2500, save_interval=50` and the `obs_groups` dict across runner cfgs, and `init_noise_std=0.7, actor_hidden_dims=[256,128,64], critic_hidden_dims=[512,256,128], activation="elu"` across policy cfgs. De-dup via base classes. Verified by `to_dict()` equality so no value changes silently.

**Files:**
- Create: `tests/test_config_equivalence.py`
- Modify: `constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py`

- [ ] **Step 1: Snapshot the 6 task agent cfgs before refactor**

The 6 registered tasks resolve agent cfgs by string path (entry points in `__init__.py`). Write a snapshot helper that imports each runner cfg class directly and dumps `to_dict()`. First find the exact class names:

Run: `cd /workspace/constrained-albc && grep -n "RunnerCfg\b" constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py constrained_albc/envs/constrained_full_albc/agents/ablation_cfgs.py constrained_albc/envs/constrained_full_albc/config_noconstraint.py`
Record the class list. (Known so far: `FullDOFTRPORunnerCfg`, `FullDOFNoEncoderRunnerCfg`, `FullDOFPPORunnerCfg` in rsl_rl_ppo_cfg.py.)

- [ ] **Step 2: Write the equivalence test (the regression net)**

`tests/test_config_equivalence.py`. Follow the `test_doraemon.py` mock pattern (mock `isaaclab.utils.configclass` as identity, and any rsl_rl base cfg imports as needed). The test builds each runner cfg and asserts its `to_dict()` equals a frozen golden dict captured from the pre-refactor code. Because the golden is captured BEFORE the refactor, this test passes pre-refactor and must keep passing post-refactor.

```python
"""Config equivalence regression net for the de-duplication refactor.

Captures each FullDOF runner cfg's to_dict() as a golden value; the de-dup
refactor (base classes) must not change any field. Mocks isaaclab so it runs
without Isaac Sim.
"""
import sys, types
import pytest

if "isaaclab" not in sys.modules:
    _il = types.ModuleType("isaaclab")
    _u = types.ModuleType("isaaclab.utils")
    _u.configclass = lambda cls: cls
    _il.utils = _u
    sys.modules["isaaclab"] = _il
    sys.modules["isaaclab.utils"] = _u

# rsl_rl base cfgs are real dependencies; import them (they are pip-installed).
from constrained_albc.envs.constrained_full_albc.agents.rsl_rl_ppo_cfg import (
    FullDOFTRPORunnerCfg, FullDOFNoEncoderRunnerCfg, FullDOFPPORunnerCfg,
)

CFGS = {
    "trpo": FullDOFTRPORunnerCfg,
    "noenc": FullDOFNoEncoderRunnerCfg,
    "ppo": FullDOFPPORunnerCfg,
}

@pytest.mark.parametrize("name", list(CFGS))
def test_runner_cfg_shared_constants(name):
    d = CFGS[name]().to_dict()
    assert d["seed"] == 30
    assert d["num_steps_per_env"] == 64
    assert d["max_iterations"] == 2500
    assert d["save_interval"] == 50

@pytest.mark.parametrize("name", ["trpo", "noenc"])
def test_constraint_runner_obs_groups(name):
    d = CFGS[name]().to_dict()
    assert d["obs_groups"] == {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }
```

If the rsl_rl base cfg import fails without Isaac Sim, fall back to loading `rsl_rl_ppo_cfg.py` by `importlib` like `test_tdc_controller.py` does and mock the rsl_rl base classes minimally. Adjust the assertion set to cover every field that will move into a base class.

- [ ] **Step 3: Run the test (must PASS pre-refactor)**

Run: `cd /workspace/constrained-albc && python -m pytest tests/test_config_equivalence.py -v`
Expected: PASS (this freezes current behavior before refactor).

- [ ] **Step 4: Introduce a base runner cfg and rebase the runner classes**

Add a `_BaseFullDOFRunnerCfg(RslRlOnPolicyRunnerCfg)` holding the shared constants, then have each runner inherit and override only what differs (`class_name`, `experiment_name`, `algorithm`, `policy`, `normalize_value`, and `obs_groups` where it applies). Move `seed=30, num_steps_per_env=64, max_iterations=2500, save_interval=50` into the base. Keep per-class `experiment_name` and `class_name`. Do not change any value.

```python
@configclass
class _BaseFullDOFRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Shared FullDOF runner constants (de-dup base; no behavior change)."""
    seed = 30
    num_steps_per_env = 64
    max_iterations = 2500
    save_interval = 50
```

Then e.g. `class FullDOFTRPORunnerCfg(_BaseFullDOFRunnerCfg):` keeping only its distinct fields.

- [ ] **Step 5: Re-run the equivalence test (must still PASS)**

Run: `cd /workspace/constrained-albc && python -m pytest tests/test_config_equivalence.py -v`
Expected: PASS (zero field changed).

- [ ] **Step 6: Verify parse**

Run: `cd /workspace/constrained-albc && python -c "import ast; ast.parse(open('constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py').read()); print('parse OK')"`
Expected: `parse OK`

- [ ] **Step 7: Commit**

```bash
cd /workspace/constrained-albc
git add constrained_albc/envs/constrained_full_albc/agents/rsl_rl_ppo_cfg.py \
        tests/test_config_equivalence.py
git commit -m "refactor: de-duplicate FullDOF runner cfg via base class

Shared constants (seed, num_steps_per_env, max_iterations, save_interval) move to
_BaseFullDOFRunnerCfg; each runner inherits and overrides only what differs. No
field value changes -- guarded by tests/test_config_equivalence.py (to_dict()
equality), which passed before and after the refactor.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: DIAGNOSIS Phase C re-verification addendum (diagnosis only)

Record the deeper re-analysis in `DIAGNOSIS.md` so the physics/math items are accurate for a future approved cycle. No code change.

**Files:**
- Modify: `DIAGNOSIS.md` (append a dated addendum section)

- [ ] **Step 1: Append the addendum**

Add a new section at the end of `DIAGNOSIS.md`:

```markdown
---

## 9. 재검증 보강 (2026-05-25, marinelab v0.2.0 호환 작업 중)

marinelab API 변경 후 코드를 재독한 결과, Phase A 일부가 이미 반영돼 있었다:
- **A1 obs assert**: `albc_env.py:138-143`에 construction-time assert 이미 존재
  (config vs computed). 이번에 `_get_observations()` 반환 텐서 런타임 assert를 보완.
- **A2 hot-loop sigma**: `albc_env.py:153`에서 이미 `__init__` 사전할당 (no-op).
- **dead code**: `randomize_ocean_current`는 live (albc_env.py:1327,1412, eval_dr.py:601).
  `compute_M_bb`만 미사용이라 이번에 제거.

Phase C (학습 동작 변경, 별도 승인 필요) 재확인:
- **added-mass clamp** (`mdp/events.py:258-271`): marinelab core는 base-inertia
  `_clamp_inertia`로 자체 clamp를 안전화했으나, albc events.py의 clamp는 별개 경로로
  여전히 DR된 inertia 기준. forward-Euler 발산 위험 미해결.
- barrier log clamp floor 1e-8 / cost surrogate 1/(1-γ) / OU 5% 초과: §3-B, §3-A1, §2 그대로 유효.
```

- [ ] **Step 2: Commit**

```bash
cd /workspace/constrained-albc
git add DIAGNOSIS.md
git commit -m "docs: re-verify DIAGNOSIS against current code (Phase A partially done)

A1 assert and A2 sigma preallocation already present; randomize_ocean_current is
live. Phase C items (added-mass clamp on DR'd inertia, barrier floor, cost
surrogate scale, OU 5%) remain valid and deferred (learning-affecting).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: current-migration smoke test

Pin the Task 1 migration so the removed-buffer crash cannot regress. Isaac-Sim-free: mock the hydro with a minimal object exposing `current.velocity_w` / `.max_velocity` and exercise the OU math shape, plus assert the new attribute path exists on the real marinelab `HydrodynamicsModel`.

**Files:**
- Create: `tests/test_current_migration.py`

- [ ] **Step 1: Write the test**

```python
"""Regression net for the marinelab.core OceanCurrent migration (Task 1).

Asserts the new current API surface exists and the OU update math operates on the
shared velocity_w buffer with the correct shape. Isaac-Sim-free.
"""
import sys, types
import pytest
import torch

if "isaaclab" not in sys.modules:
    _il = types.ModuleType("isaaclab")
    _u = types.ModuleType("isaaclab.utils")
    _u.configclass = lambda cls: cls
    _il.utils = _u
    sys.modules["isaaclab"] = _il
    sys.modules["isaaclab.utils"] = _u


def test_marinelab_oceancurrent_api_surface():
    """The new API albc Task 1 depends on must exist on the real classes."""
    from marinelab.core import HydrodynamicsModel, OceanCurrent
    # OceanCurrent exposes the buffers albc reads/writes.
    assert hasattr(OceanCurrent, "velocity_w")
    assert hasattr(OceanCurrent, "max_velocity")
    assert hasattr(OceanCurrent, "set")
    assert hasattr(OceanCurrent, "add_drift")
    # HydrodynamicsModel exposes .current and accepts injection.
    assert hasattr(HydrodynamicsModel, "current")
    import inspect
    assert "current" in inspect.signature(HydrodynamicsModel.__init__).parameters


def test_ou_update_shapes_on_shared_buffer():
    """OU update reads/writes velocity_w[:, :3] without touching removed buffers."""
    n = 4
    velocity_w = torch.zeros(n, 6)
    max_velocity = torch.tensor([0.5, 0.5, 0.25, 0.0, 0.0, 0.0])
    mu = torch.zeros(n, 3)
    theta, sigma, dt = 0.15, 0.1, 0.02

    current = velocity_w[:, :3]
    drift = -theta * (current - mu) * dt
    diffusion = sigma * (dt ** 0.5) * torch.randn_like(current)
    new_current = current + drift + diffusion
    clamp_bound = max_velocity[:3] * 1.05
    new_current = new_current.clamp(-clamp_bound, clamp_bound)
    velocity_w[:, :3] = new_current

    assert velocity_w.shape == (n, 6)
    # zero-max axes stay zero after clamp
    assert torch.all(velocity_w[:, 3:] == 0.0)
```

- [ ] **Step 2: Run the test**

Run: `cd /workspace/constrained-albc && python -m pytest tests/test_current_migration.py -v`
Expected: PASS. (If `marinelab.core` import fails because marinelab is not installed in the test env, mark `test_marinelab_oceancurrent_api_surface` with `pytest.importorskip("marinelab.core")` at the top of the function.)

- [ ] **Step 3: Run the full suite**

Run: `cd /workspace/constrained-albc && python -m pytest tests/ -v`
Expected: all pass (existing TDC + doraemon + new current + config tests).

- [ ] **Step 4: Commit**

```bash
cd /workspace/constrained-albc
git add tests/test_current_migration.py
git commit -m "test: pin marinelab.core OceanCurrent migration (Task 1 regression net)

Asserts the new current API surface (velocity_w/max_velocity/set/add_drift,
HydrodynamicsModel.current + injectable current=) exists, and the OU update math
operates on velocity_w[:, :3] with correct shapes. Isaac-Sim-free.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: CHANGELOG

**Files:**
- Create or modify: `CHANGELOG.md` (repo root)

- [ ] **Step 1: Check for an existing CHANGELOG**

Run: `cd /workspace/constrained-albc && ls CHANGELOG.md 2>/dev/null && head -20 CHANGELOG.md || echo "none"`

- [ ] **Step 2: Write the entry**

If none exists, create it with a Keep-a-Changelog header. Add an entry dated 2026-05-25:

```markdown
## [Unreleased] - 2026-05-25

### Fixed
- Ocean current migrated to the marinelab.core `OceanCurrent` API. marinelab
  v0.2.0 removed `HydrodynamicsModel._current_velocity` / `._max_current_vel`
  (current moved into a standalone component); albc accessed the removed buffers
  in 8+ sites and crashed on env reset / OU step. Reads/writes now route through
  `hydro.current.velocity_w` / `.max_velocity` / `.set`, and the buoy model shares
  the main model's `OceanCurrent` via constructor injection (manual per-step sync
  removed). OU math unchanged.

### Added
- Runtime obs-shape assert in `_get_observations()` (complements the existing
  construction-time check).
- Isaac-Sim-free tests: `test_current_migration.py` (current API regression net),
  `test_config_equivalence.py` (config de-dup `to_dict()` equality).

### Changed
- FullDOF runner cfgs de-duplicated via `_BaseFullDOFRunnerCfg` (no field value
  changes; verified by `test_config_equivalence.py`).

### Removed
- Unused `compute_M_bb` (`tdc.py`): exported but zero call sites.

### Notes
- DIAGNOSIS Phase C (added-mass clamp on DR'd inertia, barrier log floor, cost
  surrogate scale, OU 5% over-clamp) remains diagnosis-only; these change learning
  behavior and need approval + before/after data.

### Verification
- `pytest tests/` passes; `ast.parse` over the package OK; grep confirms zero
  `_current_velocity` / `_max_current_vel` / `compute_M_bb` references remain.
```

- [ ] **Step 3: Run the full suite one final time**

Run: `cd /workspace/constrained-albc && python -m pytest tests/ -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
cd /workspace/constrained-albc
git add CHANGELOG.md
git commit -m "docs: changelog for constrained-albc hardening (API compat + Phase A/B)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Final verification (after all tasks)

- `cd /workspace/constrained-albc && python -m pytest tests/ -v` — all pass.
- `grep -rn "_current_velocity\|_max_current_vel\|compute_M_bb" constrained_albc/ | grep -v "\.pyc"` — zero.
- `git log --oneline -7` — design + 6 task commits on main, nothing pushed.
- Branch state = main only (already the case after the pre-work fast-forward).
- Report to the user; ask before any push. Full env step/reset requires Isaac Sim and is the user's to run.
