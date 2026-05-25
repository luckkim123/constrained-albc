# constrained-albc Hardening — Design

> Created 2026-05-25. Mirror of the marinelab v0.2.0 framework-ization: cleanup,
> bug fixes, physics-correctness review, plus compatibility with the new
> `marinelab.core` API. `DIAGNOSIS.md` is the reference; this design records a
> deeper re-analysis verified against current code.

**Goal:** Restore constrained-albc to a runnable state after the `marinelab.core`
API change (P0), then apply DIAGNOSIS Phase A (low-risk cleanup) and Phase B
(config de-duplication). Do not change learning behavior.

**Architecture:** Changes are layered by risk. (1) Compatibility recovery resolves
a runtime crash, so it is first. (2) Phase A is learning-neutral safe cleanup.
(3) Config de-dup is verified deterministically by `to_dict()` equality. Every
change is gated on behavior preservation. Phase C (physics/math) is diagnosis-only
this cycle — it changes learning behavior and needs user approval plus before/after
data per `feedback_no_unauthorized_changes` and `feedback_training_control`.

**Tech stack:** Python 3.12, PyTorch, Isaac Lab DirectRLEnv, rsl_rl, pytest
(Isaac-Sim-free harness via `tests/conftest.py` with real quaternion math).

---

## Deep re-analysis vs DIAGNOSIS (what changed)

DIAGNOSIS was written before the marinelab v0.2.0 API change, so it does not cover
the single most important issue:

**P0 — `marinelab.core` API incompatibility = runtime crash.** The ocean current
moved into a standalone `OceanCurrent` component (marinelab Task 3); the
`HydrodynamicsModel._current_velocity` and `._max_current_vel` buffers were
removed. constrained-albc still accesses them in 9 places (read and write), so the
environment imports fine but raises `AttributeError` on reset / OU current update.

Verified against marinelab `core/hydrodynamics.py` and `core/ocean_current.py`:

| albc access (current) | marinelab.core status | new path |
|:---|:---|:---|
| `_hydro._current_velocity[:, :3]` (read, several sites) | removed | `_hydro.current.velocity_w[:, :3]` |
| `_hydro._max_current_vel[:3]` | removed | `_hydro.current.max_velocity[:3]` |
| `_hydro._current_velocity[...] = v` (write) | removed | `_hydro.current.set(...)` / `add_drift(...)` |
| `_buoy_hydro._current_velocity[ids] = ...` (manual sync) | removed | inject shared `current=` at construction |
| `hasattr(hydro, "_current_velocity")` | always `False` now | use `hydro.current.velocity_w` |
| `_hydro.apply_added_mass` (property) | present | unchanged |
| `_hydro.rigid_body_inertia` (property) | present | unchanged |
| `_thruster.randomize_parameters(...)` | present | unchanged (memory concern rejected) |

marinelab `HydrodynamicsModel.__init__` now accepts `current: OceanCurrent | None`
for dependency injection, so the two hydro instances can share one current field
and the manual per-step buffer copy becomes unnecessary.

**DIAGNOSIS physics items, re-verified:**
- Added-mass clamp (DIAGNOSIS §2): marinelab core added a base-inertia `_clamp_inertia`
  buffer that fixes this on the marinelab side, but albc's own clamp in
  `mdp/events.py:258-271` is a separate code path and still clamps against the
  DR'd inertia. The DIAGNOSIS concern is real for albc → Phase C (learning-affecting).
- `ThrusterModel.randomize_parameters` exists in marinelab.core → not broken
  (the memory/DIAGNOSIS worry that DR would crash on a missing method is rejected).

---

## Section 1 — marinelab.core API compatibility recovery (P0, behavior-preserving)

Most important and highest-risk. The environment crashes on reset / OU step today.

Changes:
1. **Inject shared current** — after constructing `_hydro`, pass its `OceanCurrent`
   to `_buoy_hydro` via `current=self._hydro.current`. Both models then read the
   same flow field.
2. **Replace reads** `_hydro._current_velocity[:, :3]` → `_hydro.current.velocity_w[:, :3]`
   at every site (`albc_env.py`, `mdp/observations.py`, `utils/logging.py`).
3. **Replace `_max_current_vel`** → `_hydro.current.max_velocity` (`albc_env.py`).
4. **Replace OU write** (`albc_env.py` OU update): with a shared current, update
   the field once via the `OceanCurrent` API (`set` / `add_drift`) instead of
   writing the private buffer on both models.
5. **Remove manual sync** in `mdp/events.py:308-310` (made redundant by injection).

Verification: import-integrity sweep — zero remaining `_current_velocity` /
`_max_current_vel` references in albc. Isaac-Sim-free smoke test exercising the
current API path with a mock hydro (no `AttributeError`). Full env step requires
Isaac Sim and is run by the user.

## Section 2 — Phase A: low-risk cleanup (learning-neutral)

Re-verification against current code shrank this phase: two DIAGNOSIS A-items are
already done.

- **A1 (obs-dim assert) — already present at construction.** `albc_env.py:138-143`
  already raises when `cfg.observation_space != computed obs dim`. The remaining
  gap is that this is a *config-time* check against a computed width, not a
  *runtime* check on the tensor actually emitted by `_get_observations()`. The only
  worthwhile addition is a runtime assert on the returned `policy` tensor shape.
- **A2 (hot-loop sigma) — already preallocated.** `albc_env.py:153` builds
  `self._integral_gate_sigmas` once in `__init__` (comment: "Avoids re-allocating
  ... every step"). No-op; nothing to do.
- **A3 (analysis MetricsConfig) — deferred** with the eval_dr split.

Actual Phase A work:
1. **runtime obs-shape assert** — at the end of `_get_observations()`, assert the
   emitted `policy` tensor's last dim equals `self.cfg.observation_space`.
2. **dead-code removal** — `compute_M_bb()` (`tdc.py:499`) is exported but has zero
   call sites (verified). Remove it and drop the export, recording the grep in the
   commit. NOTE: `randomize_ocean_current` is NOT dead — it is called at
   `albc_env.py:1327,1412` and `eval_dr.py:601`; do not remove it.

Verification: pytest passes; the runtime assert accepts valid obs and rejects a
mismatched width (unit test); dead-code grep evidence in the commit message.

## Section 3 — Phase B: config de-duplication (behavior-preserving, `to_dict()` equality)

`rsl_rl_ppo_cfg.py` / `agents/ablation_cfgs.py` / `config_noconstraint.py` duplicate
`seed=30, num_steps_per_env=64, max_iterations=2500` (100%) and 25-40% of policy/algo
cfg across 9 classes.

Changes: define `_Base*Cfg` baselines; each of the 6 task cfgs inherits and overrides
only. Intentional per-ablation differences stay as explicit overrides.

`feedback_fork_not_inherit` note: that rule forbids subclassing for large *env*
feature variants (copy-the-folder). Removing duplicate scalar config values is
ordinary dedup, not a feature fork — but no value may change during dedup.

Verification (deterministic, no checkpoint / no Isaac Sim): snapshot all 6 task
`agent_cfg.to_dict()` before refactor; after each change, diff must be empty. Any
field difference fails immediately. TDD: snapshot first, verify zero diff per step
(`feedback_verify_before_commit`).

## Section 4 — Phase C items: diagnosis only (no code change)

Recorded in `DIAGNOSIS.md` with a "re-verified 2026-05-25" addendum; not modified
this cycle. Each needs user approval + before/after data.

1. Added-mass clamp against DR'd inertia (`mdp/events.py:258-271`) — forward-Euler
   divergence risk; marinelab core fixed its own path but albc's is separate.
2. Barrier log clamp floor `1e-8` (`constraint_trpo.py:464`) — gradient ~1e8 on
   constraint violation.
3. Cost surrogate `1/(1-γ)` scale (`constraint_trpo.py:462`) — NORBC formula
   consistency unconfirmed (possible double application); needs paper/author check.
4. OU current exceeds `max_velocity` by 5% (`albc_env.py`, `clamp_bound = max_vel*1.05`)
   — may shift encoder input distribution; comment if intentional.

## Section 5 — Tests & verification strategy

Follow the marinelab Isaac-Sim-free pytest pattern.
- Existing: `tests/test_tdc_controller.py`, `tests/test_doraemon.py`.
- Add: (a) obs-dim assert unit test, (b) current API migration smoke (mock hydro
  exposing `current.velocity_w`), (c) config dedup equality test (`to_dict` diff).
- Full env step/reset needs Isaac Sim → run by the user. This work guarantees code
  consistency, import-integrity, and pytest.

## Task order & commit protocol

One commit per task. Never push (ask first). Korean dialogue / English code. No
emoji, no AI attribution. Never `git add -A` (parallel sessions) — stage session
files explicitly. Final branch state = main only.

1. marinelab.core compatibility recovery (P0)
2. Phase A cleanup
3. config de-duplication
4. DIAGNOSIS Phase C re-verification addendum
5. test additions
6. CHANGELOG
