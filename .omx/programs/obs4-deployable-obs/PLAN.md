# OBS4 Program: +4 sensor channels — student validation first, then teacher obs76

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement Phase A task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking. Phases B-E are EXPERIMENT OPERATIONS: every training
> launch is HUMAN-GATED (`omx queue-launch`, never auto-fired), and each phase has an explicit
> user decision gate before the next.

> **Location note (2026-08-04).** This document moved here from
> `/workspace/.sp/plans/2026-08-03-obs4-student-then-teacher76-program.md` byte-identically.
> `.sp/` is superpowers scratch: gitignored, on a `/workspace` tree that is not a git repository
> at all, and explicitly "throwaway once the work lands" — the wrong home for a multi-phase
> program that outlives its runs and needs its progress tracked. Program state is now machine-
> readable via `omx program-status`. The same drift already cost one cleanup (the teacher
> `PLAN.md` header records consolidating 60 scattered `.sp/plans/` documents on 2026-07-23) and
> cost this program a stale run id that went unnoticed overnight.
>
> **Campaign membership.** `program.json` attaches the two campaigns this program owns outright:
> `teacher_obs76` (Phase D) and `student_distill_obs76` (Phase E). Phases B and C ran inside
> `student_distill_eint`, which belongs to the `teacher-final-closeout` program and is NOT
> re-attached here to avoid double ownership — its obs4 runs are
> `trpo_sdeint_b2_extraobs_s30_260803_215117`, `trpo_sdeint_b2ctl_dim0_s30_260803_220234` and
> `trpo_sdeint_b2wide_gru256_s30_260803_231320`.

---

## STATUS — read this first (2026-08-03)

**Phase A (tasks A1-A9) is COMPLETE, independently reviewed, and PUSHED.** Do not re-implement it.

| | |
|:--|:--|
| Branch | `exp/obs4-extraobs` @ `7c16b93`, 11 commits, pushed to origin |
| Baseline tag | `baseline-260803-obs4` (pushed) — the comparison anchor |
| `main` | untouched at `1062dc2` |
| Tests | 443 → **459 passed / 9 skipped** |
| Reviews | every task reviewed; 1 task-level fix round (A4); whole-branch review + 1 fix wave; re-review APPROVE |
| Ledger + reports | `constrained-albc/.superpowers/sdd/2026-08-03-obs4-student-then-teacher76-program/` |

**Phases B-E have NOT started. Every one of them gates on a human.** `omx queue-launch` queues;
it never fires. The tasks below are kept as the record of what was built and why — the sections
that still describe FUTURE work are Phase B onward, plus Task A9's recorded launch command,
which Phase B copies.

Corrections applied to this plan during execution are in the **Review log** at the bottom; the
task bodies already carry them inline. Two items still need a HUMAN decision before Phase B can
be proposed: the B2 pairing regime (Phase B step 4b) and the `--run_group` / purpose name.

---

**Goal:** Add 4 deployable sensor channels (IMU specific force 3D + pressure-derived heave rate
1D), validate them cheaply on the student encoder (~13 min run), and if they carry information,
retrain the teacher with policy_obs 72→76 and re-distill the student — the user-ratified
sequence of 2026-08-03.

**Architecture:** Gen-1 (Phases A-C) feeds the channels to the STUDENT ENCODER ONLY as an extra
KEY IN THE OBSERVATION DICT (`observations["student_extra"]`) — the frozen E-int teacher actor
(72D `policy_obs`) is untouched, so the validation is one-variable and cheap. Gen-2 (Phases D-E)
folds the same channels INTO `policy_obs` (72→76, the `apply_bias_ema_obs` materializer
precedent) and retrains teacher + student. The channel computation code (sensor models, cfg
knobs, reset handling) is shared between generations.

**Why the obs dict, not an env attribute (user decision 2026-08-03, revising the 07-30 spec):**
`RslRlVecEnvWrapper.step()` wraps the WHOLE `_get_observations()` dict into a TensorDict with no
key filtering (`isaaclab_rl/rsl_rl/vecenv_wrapper.py:156-164`), and the dict already carries a
non-standard `"privileged"` key — so a third conditional key rides the existing transport to both
consumers for free. The student runner reads `obs_next["student_extra"]` from the dict it already
receives; `StudentInLoopPolicy.__call__(obs_td)` reads `obs_td["student_extra"]` from the
tensordict it already receives. **eval.py's step loop needs ZERO edits**, no `env.unwrapped`
reach-through, and the "caller forgot to push the extra channels" failure class — which the
07-30 spec had to guard with a runtime `raise` — cannot occur by construction. One thing to
verify at implementation (A2 step 4): that gym's env checker does not reject the third key.

**Tech Stack:** Isaac Lab DirectRLEnv (`constrained-albc` overlay), ConstraintTRPO+IPO teacher,
GRU student distillation (`envs/_core/student/`), omx experiment harness, eval.py static.

**Decision provenance (2026-08-03, user):** (1) proceed student-first then teacher — ratified in
conversation; (2) do NOT wait for the plant-change batch (its gates are hardware bench sessions
with no booked date; the Stonefish role decision of 2026-08-03 declares coefficient disputes
UNDECIDABLE until that bench, so the batch timeline is open-ended); (3) this session plans only —
implementation happens in a NEW session; (4) C3 (GRU+select) is the adopted deployment student,
so the B2 arm builds on the C3 recipe.

## Global Constraints

- **NEVER auto-launch training.** Every `train.py` / `train_student.py` run goes through an omx
  proposal (`exp-design` → `omx proposal-lint` → independent `proposal-reviewer` agent) and
  `omx queue-launch`; a human approves each launch. Evals are launchable without a gate.
- **Plain `python` = exit 127 in Claude sessions.** Overlay repos: the PATH `python` wrapper
  (`exec /isaac-sim/python.sh`) works from a login shell but NOT in-session — use
  `/isaac-sim/python.sh` explicitly. Repo root for all commands: `/workspace/constrained-albc`.
- **Student training runs on GPU1** via `CUDA_VISIBLE_DEVICES=1` (StudentCfg.device is hardcoded
  `cuda:0`; masking is the mechanism). **Teacher training runs on GPU0** (paired comparisons vs
  E-int must be same-machine — machine isolation is +109% roll ss_error at same config+seed).
- **cuDNN: a TCN concern, NOT a GRU one.** CORRECTED 2026-08-03 during the A9 review, which
  verified from source that `StudentEncoderGRU` (`_core/student/models.py`) contains no
  `Conv1d` — only `StudentEncoderTCN` does. The `LD_LIBRARY_PATH` fix (Isaac's prebundled cu12
  cuDNN first, else conv1d fails and the step time blows up ~80x) exists for the TCN path; the
  `albc-cudnn-fix-is-a-library-path-not-a-package` memory says the same ("GRU never hit it").
  B2 and every other GRU arm therefore need NO cuDNN preamble, and the A9-verified launch
  command correctly omits it. Do not paste the export line in "just in case" — an unnecessary
  environment mutation in a recorded launch recipe is how a spurious variable enters a
  comparison.
- **run_id via `make_run_id`** (`<task_short>_<tag>_<ts>`, tag mandatory, label-before-date);
  `--run_group <purpose> --log_project_name <purpose>` use the SAME string.
- **One variable per run.** B2 changes ONLY the extra-obs flag vs C3's recipe. E-obs76 changes
  ONLY the obs width vs E-int's recipe.
- **Byte-parity acceptance gate before any B2 launch** (Task A8): one obs sequence through the
  training-collection path and the eval path must produce identical `l_hat`. This file class
  broke exactly this way on 2026-07-29 (`38d979e`): the eval wrapper re-implemented the forward
  and dropped normalization, corrupting every verdict. The metrics ARE the deliverable here.
- **`tests/` is the NO-ISAAC suite — never `from constrained_albc...` in a test.** That import
  triggers `constrained_albc/__init__` → `isaaclab.sim` → `pxr`, which is absent
  (VERIFIED 2026-08-03: `from isaaclab.utils.math import quat_rotate_inverse` dies with
  `ModuleNotFoundError: No module named 'pxr'` because `isaaclab/utils/__init__.py` does
  `from .mesh import *`). Load modules standalone instead, the way `tests/test_dagger_schedule.py`
  and `tests/test_student_eval_obs_width.py` already do:
  `importlib.util.spec_from_file_location(...)` + `sys.modules[spec.name] = mod`. VERIFIED
  2026-08-03 that `envs/main/mdp/observations.py` and `envs/_core/student/*.py` load this way.
- **`mdp/observations.py` must stay runtime-import-clean (torch only).** isaaclab appears there
  only under `TYPE_CHECKING` today, and that property is what makes the standalone test load
  above work. Do NOT add a runtime isaaclab import to it — not at module top, not lazily inside a
  function (the pxr failure above is at `isaaclab.utils` package init, so a deferred import fails
  identically). Any isaaclab math this module needs gets a torch-only local copy with a comment
  naming this constraint.
- **Commit per task** (git workflow rule 1), explicit paths only — never `git add -A`.
- **isaaclab/ stays pristine.** All changes live in `constrained-albc`.
- Results SSOT = experiments tree (`report.md` via exp-analyze); knowledge = omx wiki
  (`--root /workspace/constrained-albc`); no results in loose markdown.

## Phase map

| Phase | What | GPU cost | Gate before it |
|:--|:--|:--|:--|
| A | Implement channels + side-channel (8 tasks, TDD) | none | user already approved planning→impl handoff |
| B | B2 student arm: train + eval | ~13 min GPU1 + ~5 min eval | omx proposal + human launch approval |
| C | Analyze (exp-analyze) → GO/NO-GO on channels | none | — |
| D | E-obs76 teacher retrain (policy_obs 76) | ~5.8 h GPU0 | Phase C GO + human launch approval |
| E | Re-distill student (C3 recipe on new teacher) + eval | ~13 min GPU1 + eval | human launch approval |

NO-GO at C: stop after Phase B, drop the batch-v2 candidate 5 (wiki page
`plant_change_batch_v2_...`), record the null. Everything remains reversible: gen-1 flags
default OFF and are byte-identical when off.

---

## Phase A — Implementation (8 tasks)

### Task A1: Sensor-model cfg knobs + `compute_student_extra_obs`

**Files:**
- Modify: `constrained_albc/envs/main/config.py` (ALBCEnvCfg, near the joint1 experiment block ~line 654)
- Modify: `constrained_albc/envs/main/mdp/observations.py` (new function after `compute_policy_obs`)
- Test: `tests/test_student_extra_obs.py` (new)

**Interfaces:**
- Produces: `compute_student_extra_obs(env, robot) -> torch.Tensor` of shape `(num_envs, 4)`;
  cfg fields `use_student_extra_obs: bool`, `depth_noise_std: float`, `heave_lag_tau: float`,
  `accel_noise_std: float`. Consumed by Task A2 (env) and, in spirit, Phase D.

- [ ] **Step 1: add cfg fields** to `ALBCEnvCfg` (config.py, after the joint1 block):

```python
    # --- student-extra-obs experiment (E1/B2, off by default = byte-identical) ---
    # 4 deployable sensor channels for the STUDENT ENCODER side-channel: IMU specific
    # force (3D, gravity included -- what the hardware outputs) + pressure-derived heave
    # rate (1D). Gen-1 (validation): side-channel only, policy_obs stays 72D and the
    # frozen teacher actor never sees these. Gen-2 (teacher obs76) folds them into
    # policy_obs via a materializer (Phase D of the 2026-08-03 obs4 program plan).
    use_student_extra_obs: bool = False
    # Sensor-model calibration knobs -- real hardware needs tuning a minimal model
    # cannot see. Values are STARTING points, not measurements.
    depth_noise_std: float = 0.01   # m; pressure-sensor depth resolution (~1 cm)
    heave_lag_tau: float = 0.05     # s; first-order sensor lag
    accel_noise_std: float = 0.0    # m/s^2; additive white noise on specific force
    # Zero-order hold: how many 50 Hz control ticks one sensor sample is held for.
    # The real bus is SLOWER than sim -- /hero_agent/sensors (attitude + gyro + DEPTH,
    # i.e. every channel these 4 are derived from) publishes at <= ~25 Hz: agent.ino's
    # main loop is a 4-phase state machine with delay(9) per phase and publishes only
    # in the last phase, so the period is >= 36 ms against a 20 ms control tick.
    # 2 => 25 Hz. Refreshing these channels every tick would train the student on a
    # signal the robot cannot deliver -- the same defect class as feeding it
    # root_lin_vel_b[2] (see compute_student_extra_obs' docstring).
    # CALIBRATION KNOB, not a measurement: the exact rate is recoverable in a minute
    # from any real bag -- the firmware ships its own loop count as loop_speed in the
    # DEPTH field, so the true value is loop_speed/4. Re-set this once that bag exists.
    extra_obs_hold_steps: int = 2   # 1 = no hold (50 Hz, NOT deployable today)
```

- [ ] **Step 2: re-verify the Isaac Lab APIs this rests on at head.** VERIFIED 2026-08-03 during
plan review; re-run because the point of the step is drift detection:

```bash
grep -n "def body_lin_acc_w" /workspace/isaaclab/source/isaaclab/isaaclab/assets/articulation/articulation_data.py
grep -n "def step_dt" /workspace/isaaclab/source/isaaclab/isaaclab/envs/direct_rl_env.py
grep -n "def quat_apply_inverse" /workspace/isaaclab/source/isaaclab/isaaclab/utils/math.py
```

Found 2026-08-03: `body_lin_acc_w` (articulation_data.py:1086) is an alias of
`body_com_lin_acc_w`, which is `get_link_accelerations()` from PhysX (real link accelerations,
timestamp-cached) — good. `step_dt` on DirectRLEnv:266 — good.

**Do NOT use `quat_rotate_inverse`.** Two independent reasons found at review:
(a) it is DEPRECATED since Isaac Lab v2.1.0 — it logs a warning on EVERY call and just delegates
to `quat_apply_inverse` (math.py:707-725), so calling it per step would spam the log;
(b) it is unimportable here anyway — see the Global Constraint above (`isaaclab.utils` init
pulls `pxr`). The 2026-07-30 spec's grep checked `def quat_rotate_inverse` and PASSED, which is
exactly why a name-exists grep is not an API check.

- [ ] **Step 3: write the function** in `mdp/observations.py`, with a torch-only local rotation
helper. No new imports at all — the module keeps `torch` as its only runtime import:

```python
def _quat_apply_inverse(quat: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Rotate ``vec`` (x,y,z) by the inverse of ``quat`` (w,x,y,z). World -> body.

    Local torch-only copy of isaaclab.utils.math.quat_apply_inverse (math.py:650-668,
    same arithmetic, same order). Copied rather than imported because this module must
    stay importable without Isaac: `isaaclab.utils.__init__` does `from .mesh import *`
    which needs `pxr`, so the no-Isaac test suite (tests/conftest.py) could not load
    this file at all. Do not "clean this up" into an import.
    """
    shape = vec.shape
    quat = quat.reshape(-1, 4)
    vec = vec.reshape(-1, 3)
    xyz = quat[:, 1:]
    t = xyz.cross(vec, dim=-1) * 2
    return (vec - quat[:, 0:1] * t + xyz.cross(t, dim=-1)).view(shape)


def compute_student_extra_obs(
    env: ALBCEnv,
    robot: Articulation,
) -> torch.Tensor:
    """4 deployable extra channels for the student encoder (E1/B2 side-channel).

        [0:3] IMU specific force, body frame, gravity INCLUDED (hardware convention):
              a_imu_b = R_wb^T (a_w - g_w),   g_w = (0, 0, -9.81)
        [3]   pressure-derived heave rate: d(depth_meas)/dt through a first-order LPF.
              depth_meas = -z_w + N(0, depth_noise_std); NEVER root_lin_vel_b[2] --
              ground truth would hand the student a signal the robot cannot produce.

    Gen-1: NOT part of policy_obs; the frozen teacher actor never sees these. The env
    publishes the return value as observations["student_extra"]. State buffers
    (_depth_meas_prev, _heave_rate_filt, _extra_reset_pending) live on env and are
    reset in _reset_idx; the pending mask suppresses the post-reset spike.

    CALL EXACTLY ONCE PER ENV STEP -- it advances a differentiator and an LPF. The only
    call site is ALBCEnv._get_observations (gen-1) or the policy_obs concat (gen-2),
    which DirectRLEnv invokes once per step and once per reset.
    """
    # --- zero-order hold at the sensor rate (see cfg.extra_obs_hold_steps) ---
    # Between publishes the real policy re-reads the last sample, so do the same here.
    # The sensor model below advances ONLY on a sample boundary, and its dt is the
    # SENSOR period, not the control tick.
    hold = max(1, int(env.cfg.extra_obs_hold_steps))
    env._extra_tick += 1
    if env._extra_tick < hold:
        return env._student_extra_held
    env._extra_tick = 0
    sensor_dt = hold * env.step_dt

    lin_acc_w = robot.data.body_lin_acc_w[:, 0, :]  # root body, world frame
    spec_force_w = lin_acc_w - env._gravity_w  # (N,3) - (3,) broadcast
    a_imu_b = _quat_apply_inverse(robot.data.root_quat_w, spec_force_w)
    if env.cfg.accel_noise_std > 0.0:
        a_imu_b = a_imu_b + env.cfg.accel_noise_std * torch.randn_like(a_imu_b)

    depth_meas = -robot.data.root_pos_w[:, 2]
    if env.cfg.depth_noise_std > 0.0:
        depth_meas = depth_meas + env.cfg.depth_noise_std * torch.randn_like(depth_meas)
    # Post-reset envs: re-anchor the differentiator so heave_raw = 0 (no spike).
    pending = env._extra_reset_pending
    if pending.any():
        env._depth_meas_prev[pending] = depth_meas[pending]
        env._extra_reset_pending[pending] = False
    heave_raw = (depth_meas - env._depth_meas_prev) / sensor_dt
    env._depth_meas_prev = depth_meas
    alpha = sensor_dt / (env.cfg.heave_lag_tau + sensor_dt)
    env._heave_rate_filt = env._heave_rate_filt + alpha * (heave_raw - env._heave_rate_filt)

    env._student_extra_held = torch.cat([a_imu_b, env._heave_rate_filt.unsqueeze(-1)], dim=-1)
    return env._student_extra_held
```

**Note on `depth_noise_std` at 25 Hz:** differentiating a 1 cm-resolution depth over a 40 ms
sensor period puts ~0.25 m/s of noise on `heave_raw` against a signal of order 1 m/s. That is
what `heave_lag_tau` is for and it is why the LPF is not optional — but it also means the heave
channel's usable SNR is a real quantity the B2 bite check (Phase B step 5) should report, not
assume.

- [ ] **Step 4: write the sim-free unit test** for the LPF/reset logic (the only branchy part).
Tiny fake env/robot (plain namespaces with tensors). **Load `observations.py` standalone** —
`from constrained_albc...` would pull `pxr` (Global Constraints). VERIFIED 2026-08-03 that this
loader works and exposes the module's functions:

```python
import importlib.util
import sys
import types
from pathlib import Path

import torch

_OBS_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc" / "envs" / "main" / "mdp" / "observations.py"
)


def _load_observations():
    """Standalone module load -- bypasses constrained_albc/__init__ -> isaaclab.sim -> pxr.
    Same pattern as tests/test_dagger_schedule.py. Works because observations.py's only
    runtime import is torch (isaaclab is TYPE_CHECKING-only there); keep it that way.
    """
    spec = importlib.util.spec_from_file_location("albc_observations_standalone", _OBS_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _fake_env(n=4, dt=0.02, tau=0.05, depth_noise=0.0, hold=1):
    env = types.SimpleNamespace()
    env.cfg = types.SimpleNamespace(
        accel_noise_std=0.0, depth_noise_std=depth_noise, heave_lag_tau=tau,
        extra_obs_hold_steps=hold,
    )
    env.step_dt = dt
    env.device = "cpu"
    env._gravity_w = torch.tensor([0.0, 0.0, -9.81])
    env._depth_meas_prev = torch.zeros(n)
    env._heave_rate_filt = torch.zeros(n)
    env._extra_reset_pending = torch.ones(n, dtype=torch.bool)
    env._extra_tick = 0
    env._student_extra_held = torch.zeros(n, 4)
    return env


def _robot(n=4, depth=5.0):
    return types.SimpleNamespace(data=types.SimpleNamespace(
        body_lin_acc_w=torch.zeros(n, 1, 3),
        root_quat_w=torch.tensor([[1.0, 0, 0, 0]] * n),
        root_pos_w=torch.tensor([[0.0, 0.0, -depth]] * n),
    ))

def test_heave_lpf_no_reset_spike():
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env()
    robot = types.SimpleNamespace(data=types.SimpleNamespace(
        body_lin_acc_w=torch.zeros(4, 1, 3),
        root_quat_w=torch.tensor([[1.0, 0, 0, 0]] * 4),
        root_pos_w=torch.tensor([[0.0, 0.0, -5.0]] * 4),  # depth 5 m
    ))
    out = compute_student_extra_obs(env, robot)
    # First call after reset: differentiator re-anchored, heave rate must be ~0,
    # NOT depth/dt (= 250 m/s spike).
    assert out.shape == (4, 4)
    assert torch.allclose(out[:, 3], torch.zeros(4), atol=1e-6)
    # Constant depth afterwards -> heave stays 0; specific force = -g rotated = (0,0,9.81)
    out2 = compute_student_extra_obs(env, robot)
    assert torch.allclose(out2[:, 3], torch.zeros(4), atol=1e-6)
    assert torch.allclose(out2[:, 2], torch.full((4,), 9.81), atol=1e-4)

def test_heave_lpf_tracks_descent():
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env()
    depth = 5.0
    for _ in range(60):
        out = compute_student_extra_obs(env, _robot(depth=depth))
        depth += 0.02  # descending 1 m/s at dt=0.02
    # LPF settled: heave rate ~= +1.0 m/s (depth increasing)
    assert torch.allclose(out[:, 3], torch.full((4,), 1.0), atol=0.05)


def test_zero_order_hold_serves_stale_sample_and_uses_sensor_dt():
    """hold=2 (25 Hz): the vector must repeat on odd ticks, and the differentiator
    must divide by the SENSOR period (2*step_dt), not the control tick -- dividing by
    step_dt would report 2 m/s for a 1 m/s descent."""
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env(hold=2)
    depth, seen = 5.0, []
    for _ in range(120):
        seen.append(compute_student_extra_obs(env, _robot(depth=depth)).clone())
        depth += 0.02  # still 1 m/s of true descent per 0.02 s control tick
    # Held: every refresh is followed by one repeat of the identical vector.
    assert torch.equal(seen[-1], seen[-2]) or torch.equal(seen[-2], seen[-3])
    n_distinct = sum(1 for a, b in zip(seen[1:], seen[:-1]) if not torch.equal(a, b))
    assert n_distinct <= len(seen) // 2, f"refreshed too often: {n_distinct} of {len(seen)}"
    # Settled magnitude is still the TRUE 1 m/s -- proves sensor_dt, not step_dt.
    assert torch.allclose(seen[-1][:, 3], torch.full((4,), 1.0), atol=0.05)
```

Identity quaternion makes `_quat_apply_inverse` a no-op, so the specific-force assertion reads
the gravity convention directly. If the standalone load ever fails, the cause is a new runtime
import in `observations.py` — fix that, do not stub around it.

- [ ] **Step 5: run the test**

```bash
cd /workspace/constrained-albc && /isaac-sim/python.sh -m pytest tests/test_student_extra_obs.py -v
```

Expected: PASS (3 tests: no-reset-spike, tracks-descent, zero-order-hold). If the Isaac import
chain fires, the cause is a new runtime import in `observations.py` — fix that, not the test.

- [ ] **Step 6: commit**

```bash
git add constrained_albc/envs/main/config.py constrained_albc/envs/main/mdp/observations.py tests/test_student_extra_obs.py
git commit -m "feat(obs4): sensor-model cfg knobs + compute_student_extra_obs (E1/B2 gen-1)"
```

### Task A2: Env buffers, per-step compute, reset handling

**Files:**
- Modify: `constrained_albc/envs/main/albc_env.py` — buffer allocation near `_bias_ema`
  (~line 386), compute in `_get_observations` (before the `observations` dict return,
  ~line 1152), reset in `_reset_idx` (near `self._bias_ema[env_ids] = 0.0`, ~line 1650)

**Interfaces:**
- Produces: `observations["student_extra"]` `(num_envs, 4)`, present ONLY when
  `cfg.use_student_extra_obs`. Flows unmodified through `RslRlVecEnvWrapper` (verified: it
  TensorDict-wraps the whole dict, no key filter) to Task A5 (runner) and A6 (eval).
  When the flag is off the key is absent and the dict is byte-identical to today.

- [ ] **Step 1: allocate buffers** in `__init__` next to `_bias_ema` (line 386):

```python
        # E1/B2 student-extra channel state (gen-1: published as observations["student_extra"],
        # NOT part of policy_obs). Allocated unconditionally -- three small dead buffers when the
        # flag is off, which keeps _reset_idx branch-free.
        self._gravity_w = torch.tensor([0.0, 0.0, -9.81], device=self.device)
        self._depth_meas_prev = torch.zeros(self.num_envs, device=self.device)
        self._heave_rate_filt = torch.zeros(self.num_envs, device=self.device)
        self._extra_reset_pending = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        # Zero-order-hold state: one global tick counter (one robot, one sensor bus) plus
        # the held sample the policy re-reads between publishes.
        self._extra_tick = 0
        self._student_extra_held = torch.zeros(self.num_envs, 4, device=self.device)
```

- [ ] **Step 2: publish the key** in `_get_observations`, at the `observations = {"policy": policy_obs}`
line (1152):

```python
        observations = {"policy": policy_obs}
        # E1/B2: publish the 4 extra student channels as their own obs key. NOT appended to
        # policy_obs in gen-1, so the frozen teacher actor's 72D input is untouched. The key
        # rides RslRlVecEnvWrapper's TensorDict straight to the student runner and to
        # StudentInLoopPolicy -- no env.unwrapped reach-through anywhere.
        if self.cfg.use_student_extra_obs:
            observations["student_extra"] = compute_student_extra_obs(self, self._robot)
```

(add `compute_student_extra_obs` to the existing `from .mdp.observations import ...` at line 45)

- [ ] **Step 3: reset handling** in `_reset_idx` next to `self._bias_ema[env_ids] = 0.0` (line 1650):

```python
        self._heave_rate_filt[env_ids] = 0.0
        self._extra_reset_pending[env_ids] = True
        self._student_extra_held[env_ids] = 0.0
```

(Zeroing the held sample matches how every other per-env buffer here is reset, e.g. `_bias_ema`.
A reset env therefore reads zeros for at most `hold - 1` ticks before the next sample boundary
refills it; `_extra_reset_pending` guarantees that first real sample carries no spike.
`_depth_meas_prev` is deliberately NOT reset — `_extra_reset_pending` re-anchors it on the next
obs call, which is what makes heave_raw exactly 0 on the first post-reset step.)

- [ ] **Step 4: OFF-path regression + ON-path smoke.** Two distinct checks; the second is the one
that retires the open question about the third obs key.

```bash
cd /workspace/constrained-albc && /isaac-sim/python.sh -m pytest tests/ -q 2>&1 | tail -5
```
Expected: existing suite PASS unchanged (flag defaults False → obs dict identical).

Then a ~20-step ON-path smoke on a handful of envs (`use_student_extra_obs=True`, 4 envs,
headless) asserting: (a) `gym.make` + `RslRlVecEnvWrapper` accept the third key without an env
checker complaint, (b) `obs_td["student_extra"]` has shape `(4, 4)`, (c) channel [2] sits near
+9.81 while roughly level and channels are NOT all-identical across steps.

**RESOLVED 2026-08-03 (commit `4bdcfa8`)** — the smoke ran for real on GPU0 and all three
checks passed: the third key is accepted by `gym.make` + `RslRlVecEnvWrapper`, shape `(4,4)`,
channel [2] = 9.810 at the first real sample, ZOH pairs visible. **The env-attribute +
`policy.extra` push fallback from the 2026-07-30 spec is dead — do not revisit it.**
(Observed while doing so: env construction makes one warm-up `_get_observations()` call, so the
hold phase is offset from a step counter. Harmless — a real sensor bus is asynchronous to the
control loop anyway, and the reset-pending flag still re-anchors the differentiator.)

- [ ] **Step 5: commit**

```bash
git add constrained_albc/envs/main/albc_env.py
git commit -m "feat(obs4): env side-channel buffers + per-step compute + reset (gen-1)"
```

### Task A3: Student config + GRU model input widening

**Files:**
- Modify: `constrained_albc/envs/_core/student/config.py` (StudentCfg)
- Modify: `constrained_albc/envs/_core/student/models.py` (StudentEncoderGRU)
- Test: extend `tests/test_student_extra_obs.py`

**Interfaces:**
- Produces: `StudentCfg.extra_obs_dim: int = 0`, `StudentCfg.extra_obs_scale: tuple`,
  GRU `input_size = policy_obs_dim + extra_obs_dim`. Consumed by A4/A5/A6.

**Deliberate simplification (mark it in code):** the side channel is implemented for the GRU
path ONLY. The adopted student (A0g/C3) and the B2 recipe are GRU; the TCN path would need
flat-buffer and ring widening for an architecture the campaign no longer advances. TCN +
extra_obs_dim>0 must raise a named error, not silently ignore.

- [ ] **Step 1: StudentCfg fields** (config.py, after the GRU block ~line 60):

```python
    # E1/B2 extra sensor channels (gen-1 side-channel). 0 = off (default recipe).
    # simplified: GRU-only -- TCN would need flat_buf/ring widening for a retired
    # architecture; extend if a TCN arm ever needs the channels.
    extra_obs_dim: int = 0
    # Static per-channel scales (divide before the encoder): IMU specific force ~ +-15
    # m/s^2 -> /10; heave rate ~ +-1 m/s -> /1. Static (not a running normalizer) so the
    # board runtime can replicate normalization from constants; calibration knobs, tune
    # against real sensor ranges at bring-up.
    extra_obs_scale: tuple[float, ...] = (10.0, 10.0, 10.0, 1.0)
```

- [ ] **Step 2: widen the GRU input** (models.py `StudentEncoderGRU.__init__`):

```python
        extra = getattr(cfg, "extra_obs_dim", 0)
        self.gru = nn.GRU(
            input_size=cfg.policy_obs_dim + extra,
            hidden_size=cfg.gru_hidden,
            num_layers=cfg.gru_layers,
            batch_first=True,
        )
```

and in `make_student_encoder`:

```python
    if getattr(cfg, "extra_obs_dim", 0) > 0 and cfg.encoder_type != "gru":
        raise ValueError(
            "extra_obs_dim > 0 is implemented for the GRU student only "
            "(TCN flat-buf/ring were deliberately not widened -- see StudentCfg)"
        )
```

- [ ] **Step 3: test** — GRU builds at 76 and forwards. Add the standalone loader for the
`_core/student` package to the same test file (copy `_load_student_models` from
`tests/test_student_eval_obs_width.py:38-66` — it registers empty parent packages so the
modules' `from .config import StudentCfg` resolves; that is the repo's established pattern and
these three files copy it from each other rather than sharing a conftest helper):

```python
_STUDENT_DIR = (
    Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "_core" / "student"
)


def _load_student(*module_names):
    """Exec _core/student modules by path without importing constrained_albc.
    Verbatim shape of tests/test_student_eval_obs_width.py::_load_student_models."""
    for pkg in ("constrained_albc", "constrained_albc.envs",
                "constrained_albc.envs._core", "constrained_albc.envs._core.student"):
        if pkg not in sys.modules:
            m = types.ModuleType(pkg)
            m.__path__ = []
            sys.modules[pkg] = m
    out = []
    for name in module_names:
        full = f"constrained_albc.envs._core.student.{name}"
        spec = importlib.util.spec_from_file_location(full, _STUDENT_DIR / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "constrained_albc.envs._core.student"
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
        out.append(mod)
    return out


def test_gru_input_widening():
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    cfg.encoder_type = "gru"
    cfg.policy_obs_dim = 72
    cfg.extra_obs_dim = 4
    enc = models_mod.make_student_encoder(cfg)
    z, h = enc(torch.zeros(2, 5, 76))
    assert z.shape == (2, 5, 9)


def test_tcn_extra_rejected():
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg(); cfg.encoder_type = "tcn"; cfg.extra_obs_dim = 4
    with pytest.raises(ValueError, match="GRU student only"):
        models_mod.make_student_encoder(cfg)
```

- [ ] **Step 4: run + commit**

```bash
/isaac-sim/python.sh -m pytest tests/test_student_extra_obs.py -v
git add constrained_albc/envs/_core/student/config.py constrained_albc/envs/_core/student/models.py tests/test_student_extra_obs.py
git commit -m "feat(obs4): StudentCfg extra_obs_dim + GRU input widening (GRU-only, TCN rejected)"
```

### Task A4: Collector — store extra channels

**Files:**
- Modify: `constrained_albc/envs/_core/student/collector.py`

**Interfaces:**
- Produces: `RolloutBuffer.add(..., extra: torch.Tensor | None)`;
  `RolloutBatch.extra_seq: torch.Tensor | None` `(envs, T, extra_dim)` on the GRU minibatch
  path. Consumed by A5. TCN path never sees extra (guarded off in A3).

- [ ] **Step 1: buffer + add.** In `__init__`, after `done_flat`:

```python
        self.extra_dim = getattr(cfg, "extra_obs_dim", 0)
        self.extra_flat = (
            torch.zeros(self.n_steps, self.num_envs, self.extra_dim, device=device)
            if self.extra_dim > 0 else None
        )
```

`add()` signature gains `extra: torch.Tensor | None = None`; store before `step_idx += 1`:

```python
        if self.extra_flat is not None:
            assert extra is not None, "extra_obs_dim > 0 but no extra passed to buffer.add"
            self.extra_flat[self.step_idx] = extra
```

- [ ] **Step 2: RolloutBatch field + GRU minibatch.** Add `extra_seq: torch.Tensor | None = None`
to `RolloutBatch` — it is a dataclass whose first six fields have NO defaults, so the new field
must be declared after them (put it next to `env_idx`, which is already defaulted).
In `iter_minibatches_gru`, alongside `obs_seq`:

```python
                    extra_seq=(self.extra_flat[:T, idx].transpose(0, 1)
                               if self.extra_flat is not None else None),
```

- [ ] **Step 3: test** (pure-torch): fill a 2-step buffer with extra, check `extra_seq` shape and
env-major ordering matches `obs_seq` (same `idx` slice, same transpose).

```python
def test_collector_extra_roundtrip():
    cfg_mod, coll_mod = _load_student("config", "collector")
    cfg = cfg_mod.StudentCfg(); cfg.encoder_type = "gru"; cfg.extra_obs_dim = 4
    cfg.num_envs = 3; cfg.n_steps_per_rollout = 2; cfg.minibatch_size = 6
    buf = coll_mod.RolloutBuffer(cfg, torch.device("cpu"))
    for t in range(2):
        buf.add(torch.full((3, cfg.policy_obs_dim), float(t)),
                torch.zeros(3, cfg.privileged_dim), torch.zeros(3, 9),
                torch.zeros(3, 8), torch.zeros(3, dtype=torch.bool),
                extra=torch.full((3, 4), 10.0 + t))
    (batch,) = buf.iter_minibatches_gru()
    assert batch.extra_seq.shape == (3, 2, 4)
    assert torch.allclose(batch.extra_seq[:, 0], torch.full((3, 4), 10.0))
    assert torch.allclose(batch.obs_seq[:, 1, 0], torch.ones(3))
```

- [ ] **Step 4: run + commit**

```bash
/isaac-sim/python.sh -m pytest tests/test_student_extra_obs.py -v
git add constrained_albc/envs/_core/student/collector.py tests/test_student_extra_obs.py
git commit -m "feat(obs4): collector stores extra channels on the GRU path"
```

### Task A5: Runner — collect, train, and DAgger with extra channels

**Files:**
- Modify: `constrained_albc/envs/_core/student/runner.py` — rollout loop (198-236),
  `_dagger_action` (238-275), `_compute_loss_gru` (292-308), **the end-of-rollout hidden
  recompute in `learn()` (386-396)**, `learn()`'s initial reset (321-328), and `__init__`
  (`self.obs_normalizer` is set at line 106).

**Interfaces:**
- Consumes: `obs_td["student_extra"]` from the env (A2), `buffer.add(extra=...)` +
  `batch.extra_seq` (A4).
- Produces: a module-level `student_input(obs_n, extra, scale)` in `_core/student/models.py`
  (NOT a runner method — A8 requires `analysis/student_policy.py` to call the identical
  function, and importing a runner method there would drag the whole training stack into eval).

**FOUR forward sites, not two.** Plan review found the GRU encoder is fed in four places, and
the 2026-07-30 spec listed only two. Every one must use `student_input`, or the widened
`nn.GRU` (`input_size = policy_obs_dim + 4`) raises a shape error — site (c) is the one that
was missed and it fires at the END OF EVERY ITERATION, so a B2 run would die at iteration 0:

| # | Site | File:line | Feeds |
|:--|:--|:--|:--|
| a | DAgger collection | `runner.py:257-259` | stepwise, carried `self.gru_hidden` |
| b | Training loss | `runner.py:299-300` | whole-sequence, `h_in` |
| c | **End-of-rollout hidden recompute** | `runner.py:386-396` | whole-rollout, all envs, no_grad |
| d | Eval in-loop | `student_policy.py:185-187` | stepwise, carried `self.hidden` (Task A6) |

- [ ] **Step 1: the shared layout function.** In `_core/student/models.py` (module level, so
both the runner and `analysis/student_policy.py` import the same object):

```python
def student_input(
    obs_n: torch.Tensor, extra: torch.Tensor | None, scale: torch.Tensor | None
) -> torch.Tensor:
    """THE definition of the student encoder's input layout: [obs_n, extra / scale].

    Every encoder forward in the codebase -- DAgger collection, training loss,
    end-of-rollout hidden recompute, and eval in-loop inference -- calls this. Do not
    inline the concat at a call site: an eval-side copy of a training-side forward is
    exactly how 38d979e silently invalidated every in-loop verdict for two months.
    Shapes: obs_n (..., D), extra (..., E), scale (E,) -> (..., D + E).
    """
    if scale is None:
        return obs_n
    if extra is None:
        raise ValueError("student_input: extra_obs_dim > 0 but extra is None")
    return torch.cat([obs_n, extra / scale], dim=-1)
```

- [ ] **Step 2: scale tensor in runner `__init__`** (near line 106, where `obs_normalizer` is set):

```python
        self._extra_scale = (
            torch.tensor(cfg.extra_obs_scale[: cfg.extra_obs_dim], device=device)
            if cfg.extra_obs_dim > 0 else None
        )
```

- [ ] **Step 3: rollout loop reads the obs dict.** In `learn()` (line 323) the initial
`obs_td, _extras = self.env.reset()` already carries the key; in `_collect_rollout` the loop's
`obs_next, _rew, dones, extras = self.env.step(a_exec)` does too. Thread `extra` exactly as
`privileged` is threaded — same lifetime, same source, no `.clone()` needed and no
`env.unwrapped` access:

```python
            obs = obs_next["policy"]
            privileged = obs_next["privileged"]
            extra = obs_next.get("student_extra") if self.cfg.extra_obs_dim > 0 else None
```

`_collect_rollout` gains `extra` as a parameter and returns it alongside `(obs, privileged)`;
`learn()` seeds it from the reset tensordict and carries it across iterations, mirroring the
existing `obs, privileged = self._collect_rollout(obs, privileged, beta)` shape. `buffer.add`
gains `extra=extra` at line 206.

- [ ] **Step 4: sites (a), (b), (c).**

```python
        # (a) _dagger_action GRU branch (line 257) -- gains an `extra` parameter,
        #     passed from the call site at line 210.
            obs_n = self.obs_normalizer(obs)
            x = student_input(obs_n, extra, self._extra_scale)
            l_hat_seq, self.gru_hidden = self.student(x.unsqueeze(1), hidden=self.gru_hidden)

        # (b) _compute_loss_gru (line 299) -- after obs_seq_n is built
        x_seq = student_input(obs_seq_n, batch.extra_seq, self._extra_scale)
        l_hat_seq, _ = self.student(x_seq, hidden=h_in)

        # (c) learn() end-of-rollout hidden recompute (lines 390-394) -- THE MISSED SITE.
        #     obs_all is (E, T, D); the extra buffer must be sliced and transposed the
        #     same way, over ALL envs (this forward is not minibatched).
                    obs_all = self.buffer.obs_flat[:T_].transpose(0, 1)
                    obs_all_n = self.obs_normalizer(
                        obs_all.reshape(-1, D)
                    ).reshape(self.cfg.num_envs, T_, D)
                    extra_all = (
                        self.buffer.extra_flat[:T_].transpose(0, 1)
                        if self.buffer.extra_flat is not None else None
                    )
                    _, h_end = self.student(
                        student_input(obs_all_n, extra_all, self._extra_scale), hidden=h_start
                    )
```

Leave the hidden-threading logic around these lines untouched — only the tensor handed to
`self.student(...)` changes.

- [ ] **Step 5: run the sim-free student suite** plus the collector test:

```bash
/isaac-sim/python.sh -m pytest tests/ -q -k "student or dagger" 2>&1 | tail -5
```

Expected: PASS (extra defaults off → `student_input` returns `obs_n` unchanged, so every
existing path is byte-identical). Site (c) has no unit coverage; A8 step 2 covers the layout and
the Phase B smoke covers the shape.

- [ ] **Step 6: commit**

```bash
git add constrained_albc/envs/_core/student/runner.py
git commit -m "feat(obs4): runner threads extra channels through collect/DAgger/loss (one concat helper)"
```

### Task A6: Eval path — StudentInLoopPolicy + eval.py wiring

**Files:**
- Modify: `constrained_albc/analysis/student_policy.py` (`__init__` restore block 59-80,
  `__call__` GRU branch 183-188)
- Modify: `constrained_albc/analysis/eval.py` — **one env_cfg line in `run_static`**, NOT the
  step loop. (The 2026-07-30 spec called for a per-step push into the policy; the obs-dict
  transport removes it. Note the step loop is inside the SHARED `run_evaluation`, used by
  teacher mode too, so not touching it is also the safer diff.)

**Interfaces:**
- Consumes: `obs_td["student_extra"]` (A2) and `models.student_input` (A5) — the same function
  object the runner calls, so sites (a)-(d) cannot diverge.

- [ ] **Step 1: restore + guard widths.** In `StudentInLoopPolicy.__init__`, next to the existing
`policy_obs_dim` restore (line 60-61) and BEFORE the encoder is built. Keep the teacher guard on
OBS width only — obs width must still equal the teacher's; the ENCODER width is obs + extra:

```python
        for field in ("extra_obs_dim", "extra_obs_scale"):
            if field in saved_cfg:
                setattr(cfg, field, saved_cfg[field])
        # (existing line 62 guard, unchanged: cfg.policy_obs_dim vs self.teacher.obs_dim)
        if getattr(cfg, "extra_obs_dim", 0) > 0 and cfg.encoder_type != "gru":
            raise ValueError("extra channels are GRU-only (see StudentCfg)")
        self._extra_scale = (
            torch.tensor(cfg.extra_obs_scale[: cfg.extra_obs_dim], device=device)
            if getattr(cfg, "extra_obs_dim", 0) > 0 else None
        )
```

- [ ] **Step 2: `__call__` GRU branch** (line 184-187) — site (d) of the four:

```python
            obs_for_student = self.obs_normalizer(obs)
            if self._extra_scale is not None and "student_extra" not in obs_td:
                raise RuntimeError(
                    "student ckpt has extra_obs_dim > 0 but the env published no "
                    "'student_extra' obs key -- the eval env needs "
                    "use_student_extra_obs=True (run_static sets it from the ckpt)"
                )
            obs_seq = student_input(
                obs_for_student, obs_td.get("student_extra"), self._extra_scale
            ).unsqueeze(1)
```

The explicit `raise` rather than a zeros fallback is deliberate: zeros ARE a value, so a silent
fallback would produce a clean-looking eval measuring a different model input — the 38d979e
class. Note the guard can only fire on a genuine misconfiguration now, since nothing has to
remember to push anything per step.

- [ ] **Step 3: eval.py — set the env flag from the checkpoint, not from a CLI flag.** In
`run_static`, among the existing `env_cfg` mutations (lines 1055-1068, well before
`gym.make` at 1250):

```python
    # A student trained with the extra sensor channels needs the env to publish them.
    # Read it off the CHECKPOINT rather than adding a CLI flag: a flag can be forgotten,
    # and a forgotten flag would silently evaluate the student against an absent key.
    if is_student_mode:
        _sc = torch.load(args_cli.student_ckpt, map_location="cpu").get("cfg", {})
        if _sc.get("extra_obs_dim", 0) > 0:
            env_cfg.use_student_extra_obs = True
```

(`_save_checkpoint` stores `vars(self.cfg)`, so both new fields are in the blob — verified.)
Confirm `is_student_mode` is already in scope at that point (it is set at line 1079; if the
mutation block runs earlier, move this snippet just below line 1079, still before `gym.make`).

- [ ] **Step 4: run the existing eval-instrument guard test** (it protects this exact file):

```bash
/isaac-sim/python.sh -m pytest tests/test_student_eval_latent_instrument.py -v 2>&1 | tail -5
```

Expected: PASS unchanged (extra defaults off).

- [ ] **Step 5: commit**

```bash
git add constrained_albc/analysis/student_policy.py constrained_albc/analysis/eval.py
git commit -m "feat(obs4): eval-side extra-channel wiring with loud missing-input guards"
```

### Task A7: Export guard — refuse extra-obs students for now

**Files:**
- Modify: `constrained_albc/deploy/specs/student_gru.py` (`_assert_board_runnable`, ~line 72)
- Modify: `constrained_albc/deploy/specs/student_tcn.py` — **added 2026-08-03 from the A3
  review.** Both spec files construct `StudentEncoder{GRU,TCN}(cfg)` DIRECTLY
  (`student_gru.py:66`, `student_tcn.py:62`), bypassing `make_student_encoder` — so A3's
  GRU-only `ValueError` never fires on the deploy path. Guard BOTH, so the rejection covers
  the class rather than the one instance we happened to notice. (A TCN+extra checkpoint
  cannot be trained today, since the runner does go through `make_student_encoder`; guarding
  the TCN spec costs three lines and removes the reachability argument entirely.)
- Test: extend `tests/deploy/test_student_gru_spec.py` (it already has the gru_layers rejection
  test at line 82-83: `pytest.raises(ExportContractError, match="gru_layers")` against
  `StudentGRUSpec._assert_board_runnable(_cfg(gru_layers=2))` — mirror that shape exactly) AND
  `tests/deploy/test_student_tcn_spec.py` for the TCN counterpart.

Rationale: `npforward.py` and the pack normalization contract don't know the extra channels.
If B2 wins, gen-2 (teacher obs76) makes every width uniform again and the exporter needs no
special case; a gen-1 B2 student must not silently export a mispaired pack. Same failure class
as `deploy_export_was_tcn_only` (a VALID pack for the wrong thing).

- [ ] **Step 1: add the rejection**

```python
        if getattr(cfg, "extra_obs_dim", 0) > 0:
            raise ExportContractError(
                "student_gru: extra_obs_dim > 0 (E1/B2 gen-1 side-channel student). "
                "npforward has no extra-channel input or scaling contract; deploy support "
                "arrives with gen-2 (teacher obs76), where policy_obs itself is 76D."
            )
```

- [ ] **Step 2: test** (mirror the existing gru_layers rejection test shape), run
`tests/deploy/`, expect all pass + 1 new.

- [ ] **Step 3: commit**

```bash
git add constrained_albc/deploy/specs/student_gru.py tests/deploy/
git commit -m "guard(obs4): export refuses gen-1 extra-obs students with a named reason"
```

### Task A8: THE ACCEPTANCE GATE — train/eval byte-parity on `l_hat`

**Files:**
- Create: `tests/test_student_extra_parity.py`

This is the gate the 38d979e incident mandates. **Review finding: the 2026-07-30 spec's version
of this test was a tautology** — its "collection path" and "eval path" were two byte-identical
inlined loops in the test file, so `assert torch.equal(l_collect, l_eval)` compared one piece of
test code against itself and would have passed no matter what `runner.py` and
`student_policy.py` actually did. The spec's own fallback ("prefer the extraction") is the only
version that gates anything, so A5 step 1 makes `student_input` mandatory and this task asserts
**on the real source** that every forward routes through it.

- [ ] **Step 1: structural gate — every encoder forward routes through `student_input`.**
AST over the real files (precedent: `test_bias_ema_obs.py` check (2) and
`test_student_eval_obs_width.py` check (2) both assert against shipped source):

```python
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Per file: (functions that MUST route through student_input,
#            functions that call the encoder but legitimately must NOT).
# The second set is the TCN path. `_compute_loss_tcn` forwards the encoder and takes no
# extra channels by design (A3 rejects extra_obs_dim > 0 for non-GRU encoders), so it is
# an ALLOWED unrouted forward -- not a violation. `_dagger_action` holds BOTH branches,
# so it belongs in the routed set: its GRU branch must go through student_input.
# CORRECTED 2026-08-03: the first draft of this test omitted the TCN allowance and would
# have failed on correct code -- a gate that cries wolf gets deleted, which is worse than
# no gate. Verified against the code: runner.py has exactly 5 `self.student(` calls.
_SITES = {
    REPO / "constrained_albc" / "envs" / "_core" / "student" / "runner.py": (
        {"_dagger_action", "_compute_loss_gru", "learn"},   # sites (a) (b) (c)
        {"_compute_loss_tcn"},                              # TCN path, no extra by design
    ),
    REPO / "constrained_albc" / "analysis" / "student_policy.py": (
        {"__call__"},                                       # site (d)
        set(),
    ),
}


def _fns_calling_the_encoder(tree):
    """Function names containing a `self.student(...)` / `self.student(...)`-style call."""
    out = set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "student"):
                out.add(fn.name)
    return out


def _fns_calling_student_input(tree):
    out = set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "student_input":
                out.add(fn.name)
    return out


def test_every_encoder_forward_uses_the_shared_layout():
    for path, (must_route, allowed_unrouted) in _SITES.items():
        tree = ast.parse(path.read_text())
        forwards = _fns_calling_the_encoder(tree)
        routed = _fns_calling_student_input(tree)
        # (1) Catches a NEW forward added without anyone noticing -- the failure that
        #     would have let runner.py's end-of-rollout hidden recompute (site c) ship
        #     unwidened. A new function calling the encoder fails here until it is
        #     deliberately classified as routed or TCN-only.
        assert forwards == must_route | allowed_unrouted, (
            f"{path.name}: encoder forwards are {sorted(forwards)}, expected "
            f"{sorted(must_route | allowed_unrouted)}. A forward was added, removed, or "
            "renamed -- route it through student_input and update _SITES deliberately."
        )
        # (2) Every forward that is not on the TCN allowance must use the shared layout.
        assert must_route <= routed, (
            f"{path.name}: {sorted(must_route - routed)} call the encoder without student_input"
        )
```

Assertion (1) is the one with teeth over time: it fails on ANY change to the set of
encoder-calling functions, so a future forward cannot be added silently — someone has to
look at `_SITES` and decide which set it belongs in. Assertion (2) alone would pass if a
new unrouted forward appeared, since it only checks the names already listed.

- [ ] **Step 2: behavioral gate — layout + GRU stepwise/sequence equivalence.** Uses the REAL
`student_input` and the REAL encoder, loaded standalone (`_load_student` from A3):

```python
def test_stepwise_and_sequence_forwards_agree():
    torch.manual_seed(0)
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    cfg.encoder_type = "gru"
    cfg.policy_obs_dim = 6      # tiny for speed; the layout logic is width-agnostic
    cfg.extra_obs_dim = 4
    cfg.gru_hidden = 8
    cfg.gru_head_hidden = 4
    enc = models_mod.make_student_encoder(cfg)
    si = models_mod.student_input
    scale = torch.tensor(cfg.extra_obs_scale[: cfg.extra_obs_dim])
    T, B = 7, 3
    obs = torch.randn(B, T, cfg.policy_obs_dim)
    extra = torch.randn(B, T, cfg.extra_obs_dim)

    # stepwise + carried hidden == sites (a) and (d)
    h = enc.init_hidden(B, torch.device("cpu"))
    for t in range(T):
        l_step_seq, h = enc(si(obs[:, t], extra[:, t], scale).unsqueeze(1), hidden=h)

    # whole-sequence == sites (b) and (c)
    l_seq, _ = enc(si(obs, extra, scale), hidden=enc.init_hidden(B, torch.device("cpu")))

    assert torch.allclose(l_seq[:, -1], l_step_seq[:, -1], atol=1e-6), \
        "sequence forward and stepwise forward disagree -- hidden carry is broken"
    # extra_obs_dim == 0 must be byte-identical to no-extra (the OFF path every other arm uses)
    assert torch.equal(si(obs, extra, None), obs)


def test_layout_is_obs_then_scaled_extra():
    _, models_mod = _load_student("config", "models")
    obs = torch.zeros(2, 3)
    extra = torch.tensor([[10.0, 20.0], [30.0, 40.0]])
    scale = torch.tensor([10.0, 2.0])
    out = models_mod.student_input(obs, extra, scale)
    assert out.shape == (2, 5)
    assert torch.equal(out[:, :3], obs)                       # obs first, unscaled
    assert torch.allclose(out[:, 3:], torch.tensor([[1.0, 10.0], [3.0, 20.0]]))
```

- [ ] **Step 3: run everything + commit**

```bash
/isaac-sim/python.sh -m pytest tests/test_student_extra_obs.py tests/test_student_extra_parity.py tests/deploy -q 2>&1 | tail -5
git add tests/test_student_extra_parity.py
git commit -m "test(obs4): train/eval parity gate on the student input layout (38d979e class)"
```

### Task A9: Launch wiring — make the channels actually switchable

**Added 2026-08-03 from the A5 review.** A1-A8 build the machinery but nothing exposes it to
the launcher: `scripts/train_student.py:149-163` populates `StudentCfg` field-by-field from
explicit argparse flags, with NO generic passthrough and no `--extra_obs_dim`. VERIFIED by
grep — `train_student.py` contains zero `extra` hits. Without this task Phase B cannot launch:
`cfg.extra_obs_dim` would stay 0 and B2 would silently be a plain C3 re-run. That silent-null
outcome is exactly why this is a task and not a footnote.

**Files:**
- Modify: `constrained_albc/scripts/train_student.py` (argparse block ~lines 23-75, cfg
  population ~lines 149-163)
- Test: extend `tests/test_student_extra_obs.py`

- [ ] **Step 1: the flag.** Add `--extra_obs_dim` (int, default 0) next to the other StudentCfg
flags, and set `cfg.extra_obs_dim = args_cli.extra_obs_dim` in the same block as
`cfg.lambda_latent`. Default 0 keeps every existing recipe byte-identical.

- [ ] **Step 2: the cross-check — the load-bearing part.** `StudentCfg.extra_obs_dim` (student
side) and `ALBCEnvCfg.use_student_extra_obs` (env side) are independent switches. Either
mismatch is a silent-wrong-experiment:
  - `extra_obs_dim > 0` + env flag OFF → the env never publishes the key, the student trains on
    absent input. (Today this lands on `collector.py`'s assert — loud, but assert-dependent, so
    `python -O` would degrade it.)
  - `extra_obs_dim == 0` + env flag ON → the env computes the channels and nobody reads them.
    B2 would look like it ran with the intervention while actually being a C3 re-run. **This
    direction is completely silent today and is the one that would corrupt the verdict.**

  Raise a named `ValueError` naming BOTH flags and BOTH values when they disagree, in the
  hydra-configured function where `env_cfg` and `cfg` are both in scope, before the runner is
  built. Not a warning — a warning in a 13-minute run scrolls past unread.

- [ ] **Step 3: verify the env-side override actually reaches the cfg.** `use_student_extra_obs`
and `extra_obs_hold_steps` are `ALBCEnvCfg` fields, so they are set by hydra
(`env.use_student_extra_obs=True env.extra_obs_hold_steps=2` after the script's own args).
That is the standard Isaac Lab mechanism but it is NOT verified for this script — confirm it
empirically (a 2-iteration `--max_iterations 2 --num_envs 4` run, or a dry parse that prints
`env_cfg.use_student_extra_obs`) and record the EXACT working command line in the report. Phase
B step 2 copies that line verbatim, so an unverified invocation here becomes a failed launch there.

- [ ] **Step 4: test** the cross-check both ways (dim>0 + flag off, dim==0 + flag on) against the
real function if it is importable standalone, or against an AST/source assertion in the style of
`tests/test_bias_ema_obs.py` check (2) if importing pulls Isaac. Also assert the argparse default
is 0.

- [ ] **Step 5: commit**

```bash
git add scripts/train_student.py tests/test_student_extra_obs.py
git commit -m "feat(obs4): --extra_obs_dim launch flag + student/env two-flag cross-check"
```

**Phase A exit criteria:** all new tests + `tests/deploy` + `tests/test_student_eval_latent_instrument.py`
pass; `use_student_extra_obs=False` path byte-identical (existing suites green); **the exact B2
launch command line recorded and verified by A9 step 3**; commits pushed on user approval.

---

## Phase B — B2 arm: one launch, one eval (human-gated)

- [x] **Step 1: proposal — WRITTEN AND APPROVED 2026-08-03.** exp-design, `omx proposal-lint`
  ok:true, independent `proposal-reviewer` verdict **`approve`** after three `revise` rounds,
  recorded as campaign intent (`omx campaign-plan-add`, label `B2-extraobs`).
  Artifact: `experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_c3_gruselect_s30_260729_193732/proposals/next-20260803-184816.md`
  (`next-20260803-181559`, `-183000`, `-184040` were SUPERSEDED drafts, moved to
  `/workspace/.trash/b2-superseded-drafts-260803/` on 2026-08-03 so one experiment has one
  proposal; their defects are summarised in the surviving file's `supersedes` header. Three
  independent review rounds, each finding real defects in what the previous round introduced; do not
  read them as current. Two are instructive. Round 2: the round-1 *correction* repeated the very
  error it fixed, ranking latent dims by R² without inspecting the denominator — d6's R² is worst
  because its target variance is 2nd-smallest, its *error* is 2nd-lowest, and d2, called a
  "substantive failure", is the best-tracked dim of the nine. Round 3: the decision table guarded GO
  at 3.00σ and the other affirmative region at 0.93σ, so a true null produced an affirmative
  capacity-crowding claim 17.5% of the time against a 17.6% correct-null rate.)
  (label `B2-extraobs`). It is the authoritative document for this arm — diagnosis, pre-registered
  thresholds, recipe, validity gates, and the full backlog reconciliation are all there. Independent
  `proposal-reviewer` dispatched; a `revise` verdict means a NEW proposal id, never a hand-edit of
  the reviewed one.
  One framing correction the proposal carries and this plan predates: the recurring phrase
  "under-dispersion" is not itself a defect claim. The B1b correction proved
  `Var(l_hat)/Var(l_true) = R2` for a calibrated predictor, so a low ratio is REQUIRED of an honest
  weak predictor. The live quantity is R², i.e. how much of `l_true` is predictable at all — which
  is what makes this an observability probe.
  Original brief (superseded in detail by the proposal, kept for traceability):
  ONE variable (`extra_obs_dim 0 -> 4` + env `use_student_extra_obs=True`) against the C3
  recipe. Pre-registered hypotheses (from the 2026-07-30 spec + Phase 5 R² measurement):
  - H1 (channels informative): per-dim in-loop R² rises on the currently-negative dims
    (~~d2, d3, d4, d6, d7 at hard~~ — **WRONG, do not use**), and aggregate hard R² exceeds
    C3's +0.1108.
    **CORRECTED 2026-08-03 by direct recomputation** from `<C3 run>/eval/static_260729_194845/latent_hard.npz`
    (7751×64×9): the negative set is **{d2, d3, d4, d6, d8}**. **d7 is +0.119 — one of C3's
    BEST-tracked dims**, and d8 (-0.015) was missing. Both the total-variance and env-variance
    estimators return the identical set. Pre-registering on the old set would have scored the arm
    on a dimension that already works. Further: d3 (-0.011) and d8 (-0.015) are within rounding of
    zero, so the substantive failures are d2 (-0.064), d4 (-0.142), and above all **d6 (-0.432)**,
    which is 3x worse than the next-worst dim. The source report never named the dims — it says only
    "4/9 dims R²>0" — so this plan's set had no source at all.
  - H2 (channels carry nothing new): R² profile unchanged within seed noise; control deltas
    sub-floor (0.1 deg / 15 envs — `eval_decision_floors` wiki page is binding).
    **This H2 is not usable as written** (found in review): a "how many negative dims improved"
    count is a coin flip on an unpaired single-seed contrast, and "within seed noise" has no
    referent because this campaign has **no seed replicate anywhere**. The proposal replaces it
    with a four-region outcome space (GO / NO-GO / INCONCLUSIVE / WORSE-capacity-crowding) and
    states plainly that its thresholds are anchored to the between-arm span, not to a measured
    noise scale.
  - Exact numeric floors: set in the proposal, reviewed by the independent proposal-reviewer
    agent (`omx proposal-lint` first). A control-only improvement with unchanged R² FALSIFIES
    the observability mechanism even if att_norm moves.
- [ ] **Step 2: recipe** — **DONE 2026-08-03, and this bullet had two errors. The authoritative
  recipe now lives in the proposal** (`next-20260803-184816`, path under Step 1 above); read it
  there, not here. `DESIGN.md` does NOT carry a launch line and C3's `manifest.json` has an EMPTY
  `repro` field — the recipe was recovered from C3's own recorded wandb config,
  `<C3 run>/train/wandb/run-20260729_193734-3iw537gj/files/config.yaml`, which is the only surviving
  record of what C3 actually ran. Corrections found:
  - **`beta 1.0→0.0 anneal per C3` was WRONG.** C3 ran `dagger_beta_start=0.5`,
    `dagger_beta_end=0.5`, `dagger_anneal_iters=0` — a FIXED beta of 0.5, independently confirmed by
    C3's own bite check `dagger_teacher_frac = 0.500091`. Launching B2 with an anneal would have
    confounded the arm against its own baseline. This bullet fell into the trap its own last line
    warns about.
  - **`cuDNN LD_LIBRARY_PATH line` — BOTH sides of this were wrong, and the CORRECT answer is
    the opposite of what was recorded on 2026-08-03 morning.** The bullet contradicted this
    section's Global Constraints ("No cuDNN preamble"), and the resolution written then —
    "`StudentEncoderGRU` has no `Conv1d`, so the preamble is a TCN-only concern" — is a
    **non-sequitur**: `Conv1d` is not the only cuDNN consumer. `nn.GRU` calls
    `torch._cudnn_rnn_flatten_weight` inside `flatten_parameters()` on `.to(device)`.
    **MEASURED 2026-08-03 evening**: `eval.py static --encoder_type gru` dies at
    `student_policy.py:93` with `CUDNN_STATUS_NOT_INITIALIZED`, and completes with
    `LD_LIBRARY_PATH=/isaac-sim/exts/omni.isaac.ml_archive/pip_prebundle/nvidia/cudnn/lib:$LD_LIBRARY_PATH`.
    The asymmetry that hid it: `train_student.py` disables cuDNN by DEFAULT (line 145-146) as the
    workstation workaround, so TRAINING is safe without the preamble; `eval.py` has **no cuDNN
    handling at all**, so EVAL is not. Add the preamble to the EVAL step, not the training step.
  - Confirmed correct in this bullet: teacher
    `experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/train/model_4999.pt`,
    encoder gru 128/64/1, `dagger_mix=select`, `lambda_latent=1.0`, 2048 envs, 1000 iters, seed 30.
    Note gru 128/64/1 and `lambda_latent=1.0` are `StudentCfg` DEFAULTS — C3 did not pass them.
  - `--run_group student_distill_eint` (same purpose, same wandb project), tag `sdeint_b2_extraobs_s30`
  - NEW: the extra-obs flag TRIO — `StudentCfg.extra_obs_dim=4`, env `use_student_extra_obs=True`,
    and env `extra_obs_hold_steps=2` (25 Hz). State the hold value explicitly in the proposal:
    it is a property of the channel being tested, not a nuisance parameter, and a B2 run at
    hold=1 would test an undeliverable channel.

  **Verified invocation form (A9 step 3, 2026-08-03).** Only the SHAPE below is verified — a
  real 2-iteration run on GPU1 confirmed the three new flags reach their targets, and a
  negative control without the env overrides failed with the named cross-check `ValueError`.
  Take every OTHER flag (envs, iterations, seed, `dagger_mix`, `lambda_latent`, gru dims,
  `--run_group`, tag, wandb) verbatim from the campaign `DESIGN.md` C3 line — do NOT retype
  them from memory, and do NOT treat the smoke's `--num_envs 4 --max_iterations 2` as the
  recipe:

```bash
cd /workspace/isaaclab
CUDA_VISIBLE_DEVICES=1 ./isaaclab.sh -p /workspace/constrained-albc/scripts/train_student.py \
    --encoder_type gru \
    --teacher_run_dir /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/train \
    --teacher_checkpoint model_4999.pt \
    --extra_obs_dim 4 \
    <ALL OTHER FLAGS COPIED FROM THE C3 LINE IN DESIGN.md> \
    env.use_student_extra_obs=True env.extra_obs_hold_steps=2
```

  Note the hydra `env.*` overrides come LAST, after the script's own arguments. No cuDNN
  preamble on the TRAINING line (its default-off guard covers it) — but the EVAL step DOES need
  it; see the corrected Step 2 bullet above.
- [x] **PREREQUISITE B0 — DONE 2026-08-03, commit `d81e2fd`.** `eval.py` now records the extra
  channels to `student_extra_<level>.npz` plus a per-level `student_extra_summary_<level>.json`, and
  `summarize_student_extra` (pure numpy, `_eval_dr/metrics.py`) computes the four checks. Tests
  469 -> 473. Independently code reviewed; its one REQUEST-CHANGES finding (the heave noise floor
  was 1.985x too high) is fixed and the correction is carried into the proposal, which
  pre-registers a threshold on that number.
  **Instrument proven unperturbed, not asserted**: C3's eval re-run from the same checkpoint under
  the patched code reproduces `latent_{none,soft,medium,hard}.npz`, all four `data_*.npz` (40 arrays
  each), `summary.json` and `summary_latent.json` **bit-identically** to the stored 2026-07-29 run.
  (First comparison attempt reported a false FAIL on `data_hard.npz`: `time_to_failure` is all-NaN
  in both runs — all 64 envs survived — and `NaN == NaN` is False. The verdict script was the
  defect, not the code. Use `np.array_equal(..., equal_nan=True)`.)
- [ ] **Step 3: queue — the B0 blocker below is now CLEARED; what remains is the human gate.** The
  original blocker, kept for the record: a NEW blocking prerequisite **B0** was found
  during proposal review and must land first: `eval.py` records NO `student_extra` channels
  anywhere (only the `env_cfg` setup block at `eval.py:1103-1109`), so Step 5's bite check —
  the gate that exists to catch a silent no-op — cannot itself execute. Queueing an arm that
  cannot be graded would add a 13th item to a queue already holding 12 pending launches.
  B0 = add a `student_extra` capture beside the existing latent dump, with a definition of done
  that RE-RUNS C3's eval under the patched instrument and confirms `latent_hard.npz` is
  numerically unchanged (the contrast spans an instrument change; `38d979e` is what asserting
  instead of checking costs). Then: queue via `omx queue-launch` → WAIT for human approval → launch → watch
  (poll the PID, never a self-matching pgrep; bracket patterns `train[_]student`).
- [ ] **Step 4: eval** — `eval.py static` student mode, 64 envs, 4 DR levels, `--headless`,
  checkpoint via the `experiments/<run_id>/train/models/student_999.pt` symlink path (NEVER the
  logs/ path — paths.py `train`-segment rule). Verify the extra-channel env override assert
  fires correctly (Task A6 step 3) by checking the log for the guard.
- [ ] **Step 4b: state the pairing regime in the proposal.** Found by the whole-branch review
  2026-08-03: `depth_noise_std` defaults to 0.01 (> 0), so the channel computation draws
  `randn_like` every sensor sample from the SAME global generator the DR/fault sensor-noise
  layer uses. Those draws sit AFTER both policy-obs noise layers in `_get_observations`, so
  step 0 matches C3 exactly — but the stream shifts from step 1 on, and B2 and C3 then visit
  DIFFERENT states at the same seed. **B2 vs C3 is therefore a distribution-level comparison,
  not "the same trajectories plus four extra channels."** That is fine for a screening verdict
  and it is what the pre-registered floors are for; it is NOT fine to describe the arms as
  paired. Say which regime the proposal claims. If a genuinely paired comparison is wanted,
  `env.depth_noise_std=0` removes the only new RNG consumer — at the cost of an
  unrealistically clean heave channel, which weakens the deployability claim the channels
  exist to test. Do not silently pick; put the trade-off in the proposal and let the reviewer
  judge it.
- [ ] **Step 5: bite check** — an all-zeros channel is a silent no-op (E2-delay injector
  precedent). From the eval dump confirm all four: (a) nonzero, (b) time-varying, (c) channel
  [2] centred near +9.81 (gravity convention held), (d) **the zero-order hold is visibly there —
  consecutive samples repeat in pairs at `extra_obs_hold_steps=2`.** (d) is the new one: if the
  vector changes every tick, the hold silently did not apply and B2 measured a 50 Hz channel the
  robot cannot deliver, which would make a GO verdict false.
  Also report the heave channel's SNR (its std against the ~0.25 m/s differentiation noise a
  1 cm depth resolution puts on a 40 ms sensor period) — do not assume it is usable.

## Phase C — Analyze + GO/NO-GO (user gate)

- [ ] exp-analyze the B2 run vs A0g and C3 (P1 per-dim R² at none+hard is the primary read;
  report per the campaign's report grammar, `report-review` + `report-coverage`).
- [ ] Verdict per the proposal's pre-registered rule. Then STOP and present to the user:
  - H1 → recommend Phase D GO (and the batch-v2 candidate 5 gate is satisfied).
  - H2 → recommend stopping: drop batch-v2 candidate 5, close the wiki lead
    `c4b_dagger_correction...`'s observability angle as refuted-for-these-channels, record in
    the campaign ledger. The E1 idea dies cheaply; the teacher retrain never happens.

## Phase D — E-obs76 teacher retrain (human-gated, GPU0, ~5.8 h)

- [ ] **Step 1: gen-2 materializer** (config.py, mirror `apply_bias_ema_obs` exactly):

```python
def apply_extra_policy_obs(cfg) -> None:
    """Gen-2 (teacher obs76): fold the 4 E1/B2 channels INTO policy_obs, 72 -> 76.

    MUST be called from ALBCEnv.__init__ BEFORE super().__init__(), AFTER
    apply_bias_ema_obs (the width check below assumes the 69->72 bump already ran).
    Mutually exclusive with the gen-1 side channel.
    """
    if not cfg.use_extra_policy_obs:
        return
    if cfg.use_student_extra_obs:
        raise ValueError("use_extra_policy_obs (gen-2) and use_student_extra_obs (gen-1) are mutually exclusive")
    if cfg.observation_space != 72:
        raise ValueError(f"use_extra_policy_obs expects observation_space=72 pre-bump, got {cfg.observation_space}")
    cfg.observation_space += 4
    if cfg.observation_noise_model is not None:
        zeros4 = (0.0, 0.0, 0.0, 0.0)  # channels carry their OWN modeled noise (cfg knobs)
        noise_cfg = cfg.observation_noise_model.noise_cfg
        bias_cfg = cfg.observation_noise_model.bias_noise_cfg
        noise_cfg.std = tuple(noise_cfg.std) + zeros4
        bias_cfg.n_min = tuple(bias_cfg.n_min) + zeros4
        bias_cfg.n_max = tuple(bias_cfg.n_max) + zeros4
```

`_get_observations` appends after the bias_ema block (~line 1135):

```python
        if self.cfg.use_extra_policy_obs:
            policy_obs = torch.cat([policy_obs, compute_student_extra_obs(self, self._robot)], dim=-1)
```

Call site in `__init__` right after `apply_bias_ema_obs(cfg)` (line 111).

**Three more width-tracking sites in `albc_env.py`, all of which must gain the same `+4` branch:**

1. **The obs-width guard, lines 183-210** — added at review; the 2026-07-30 spec missed it.
   `expected_obs_dim` is built from `PROPRIO_DIM + history + integral_dims + (3 if
   use_bias_ema_obs)`, and raises `ValueError` when it disagrees with `cfg.observation_space`.
   Since `apply_extra_policy_obs` bumps `observation_space` to 76, this guard raises at env init
   unless it also adds 4 when `use_extra_policy_obs`. Loud, not silent — but it blocks Phase D
   at step 0, so wire it in the same commit.
2. **`_obs_noise_base_std`, ~line 442-474** — reconstructs the always-on noise std at the env's
   real width (69 or 72) because eval nulls `observation_noise_model`. Must reconstruct at 76.
3. **The second reconstruction at ~line 532** — same comment, same treatment.
   (grep `_fault_obs_base_std|_dr_obs_base_std` to find both.)

Mirror the `use_bias_ema_obs` handling at each site rather than inventing a new pattern, and add
a gen-2 case to `tests/test_bias_ema_obs.py`'s AST-extracted materializer check (check (2)) —
that test exec's the real `apply_bias_ema_obs` body in an isolated namespace and is the cheapest
place to pin `apply_extra_policy_obs`' arithmetic too.

Student side: gen-2 students train with `extra_obs_dim=0` (the 76D stream IS the obs); the
gen-1 obs key is not published (the two flags are mutually exclusive, enforced above).

- [ ] **Step 2: proposal + launch ack.** One variable vs E-int (obs width). Seed 30, 4096 envs,
  5000 iters, GPU0, workstation. NEW group/purpose (group == wandb project; propose
  `teacher_obs76`, CONFIRM THE NAME WITH THE USER before launch per the naming rule).
  **The launch ack MUST name the 6 open needs-apply-before-retrain leads** (buoy added mass,
  HydroRC 016d1b1 retirement, IMU 45° offset [user-deferred to bring-up], TAM moment-arm band,
  Stonefish rotational drag, TAM vertical single-motor) and state the deliberate call: this
  retrain runs on the SAME plant generation as E-int so the pair is one-variable; the plant-v2
  batch lands later for BOTH generations per the ratified 2026-08-03 Stonefish decision
  (coefficients move only on real-robot anchors; DR widening + curriculum recalibration, not
  nominal moves).
- [ ] **Step 3: verdict rule** (pre-register in the proposal): paired vs E-int on the standard
  floors — H1: no nominal-level floor regresses AND hard att_norm within floors → the new
  teacher is eligible; the real prize is Phase E's student. A teacher-side IMPROVEMENT is
  possible (actor gets acceleration feedback) but NOT required for GO to Phase E.

## Phase E — Re-distill + close (human-gated launch)

- [ ] Distill the C3 recipe (GRU+select, λ=1.0, `extra_obs_dim=0`) from the E-obs76 teacher,
  same group `student_distill_eint` continuation or the new teacher's purpose — decide with the
  user at launch; eval vs the new teacher AND vs old C3 (cross-teacher comparison is context,
  not verdict — different plant input widths).
- [ ] If adopted: export the new pack (`scripts/export_deploy_pack.py`; exporter reads dims from
  tensor shapes and is campaign-agnostic — obs 76 flows through; the A7 guard doesn't fire
  because gen-2 students have `extra_obs_dim=0`). The 2026-08-03 C3 pack
  (`pack_eint_c3_gru_260803_144925`) remains the fallback until then. Record adoption in wiki +
  ledger; notify the Stonefish smoke bench that the stress checkpoint should be swapped.

---

## Risk register

| Risk | Mitigation |
|:--|:--|
| Eval feeds different input than training (38d979e class) | Mandatory shared `models.student_input` (A5 s1) + A8 AST gate asserting all four forwards route through it + loud `raise` on a missing obs key (A6 s2) |
| A forward site added later without routing it | A8 step 1 pins the exact set of encoder-calling functions per file; a new one fails the test |
| Side channel silently zeros (E2-delay injector class) | Phase B step 5 bite check (a)-(d) on the eval dump |
| **Channel trained fresher than the robot can deliver** | `extra_obs_hold_steps=2` zero-order hold at the measured ≤25 Hz sensor bound + bite check (d) proving the hold applied |
| Post-reset heave spike poisons early-episode latents | `_extra_reset_pending` re-anchor (A1) + `test_heave_lpf_no_reset_spike` |
| Isaac API drift / deprecated API | A1 step 2 — and the local `_quat_apply_inverse` copy removes the dependency entirely (the spec's grep passed on a DEPRECATED function) |
| Gym env checker rejects the third obs key | A2 step 4 ON-path smoke; documented fallback to the env-attribute push (the only branch point in the plan) |
| Gen-1 student pack exported to the board | A7 export rejection with named reason |
| Teacher retrain wasted on uninformative channels | Phase B/C gate: 13-min experiment before the 5.8-h one |
| Wrong-machine comparison | GPU0/workstation pinned for Phase D (E-int pairing); GPU1 for students |
| Group/wandb scatter | new purpose name user-confirmed at Phase D launch; B2 stays in `student_distill_eint` |

## Backlog reconciliation (all 16 open leads, 2026-08-03)

**New evidence arriving 2026-08-03 (real-robot publish rates), affecting one lead and this
program's sensor model.** Measured from the robot repo at `@edd735c` (2026-07-05; re-verified
against remote head — files changed, rate structure did not):

| Stage | Rate | Basis |
|:--|:--|:--|
| attitude + gyro + depth (`/hero_agent/sensors`) | ≤ ~25 Hz | `agent.ino` main loop is a 4-phase state machine, `delay(9)` per phase, publishes only in the last phase → period ≥ 36 ms. Exact value is recoverable from any bag: firmware ships `loop_speed` in the DEPTH field, true rate = `loop_speed/4` |
| joint states (`/albc/joint_states`) | 10 Hz | Dynamixel node `LOOP_HZ = 10.0` |
| policy control loop | 50 Hz | `control_hz=50`, `CONTROL_DT=0.02` |

**The real robot is SLOWER than the simulator.** The deployed policy runs under zero-order hold:
attitude refreshed roughly every 2 control ticks, joints every 5. Three consequences:

1. **In scope, applied here:** the 4 new channels all derive from `/hero_agent/sensors`, so they
   inherit the ≤25 Hz bound → `extra_obs_hold_steps=2` (A1). Without it B2 would validate a
   50 Hz channel and a GO verdict would not transfer.
2. **Out of scope, and pre-existing:** the SAME gap applies to today's 72D `policy_obs` — the
   teacher trains on attitude fresher than 25 Hz and joints fresher than 10 Hz. This is a
   property of every run to date, not something this program introduces, and fixing it is a
   plant change. It sharpens the open lead `experiment_idea_latency_...` from "what rate?" to
   "how stale were obs at training vs deployment?", and it should be recorded on that wiki page
   rather than acted on here. Do NOT fold it into B2 — that would break one-variable.
3. **Retires a separate proposal:** Stonefish odom at 50 Hz is already faster than the real bus,
   so the "raise smoke bench to 100 Hz" idea is dead; the bench stays at 50 Hz, and the
   "50 Hz aliasing → +40% bias" observation reclassifies from sim artifact to a real deployment
   condition the policy must tolerate.

Side finding for the hardware session: the robot repo already ships `arm_step_response.py`
(XW540 step response) and `net_buoyancy.py`, so two of the three bench prerequisites named in
the blocking leads exist — only the T200 thrust curve remains unbuilt.

Carried by this program: `c4b_dagger_correction...` (B2 IS its observability angle — Phase C
closes or refutes it). Named in the Phase D launch ack (all 6 blocking):
`buoy_added_mass...`, `hydrorc_016d1b1...`, `imu_45deg_offset...` (user-deferred to bring-up),
`sim_hydro_nominal...` (TAM moment-arm band unsourced), `stonefish_rotational_drag...`,
`tam_vertical_single_motor...` — all deliberately NOT applied so the E-int pairing stays
one-variable; they ride the plant-v2 batch per the ratified real-anchor principle. Explicitly
deferred, unchanged reasons: `curriculum_recalibration...` (couples to plant-v2 DR widening),
`experiment_idea_latency...` (off-DORAEMON blocker), `hydrorc_is_half_recentered...` (probe
design undecided), `joint1_stage_1...` (needs an unlimited-joint1 checkpoint),
`reward_sigma...` R6 (batch-pass parked), `roll_transient...` (blocked on the deferred teacher
C3 ablation set — "after C3" ordering question still with the user), `stonefish_yaw_gap...`
(XW540 step response + T200 bench, hardware), `thruster_nonlinear_curve...` and
`thruster_static_gain...` (both wait on the T200 bench, which the ratified decision makes the
next hardware priority).

## Traceability to the user's brief (2026-08-03)

| User said | Where in this plan |
|:--|:--|
| "E-int에 추가하고 student도 새롭게 학습" | Phases D + E |
| Agreed sequence "구현 → student 검증 → teacher 재학습" | Phase map A→B/C→D |
| "이 세션에서는 구현하지 않는다, 계획만 세세하게" | This document; zero code changes made in the planning session |
| "구현은 새로운 세션에서" | Header handoff: subagent-driven-development / executing-plans in a fresh session |
| C3 채택 (2026-08-03) | B2/E recipes build on C3 (GRU+select); C3 pack stays fallback |
| C++ ONNX 후순위 | Untouched here; A7 keeps deploy honest meanwhile |
| "읽고 분석 및 검토 후 문제가 없으면 진행" (2026-08-03) | Review ran against the code before any implementation; 8 defects found and folded in (see below). Transport switched to the obs dict by user choice |
| 실제 로봇 rate 조사 결과 (2026-08-03) | `extra_obs_hold_steps=2` in A1/A2 + Phase B bite check (d); the pre-existing 72D staleness gap routed to the latency-DR lead, not to B2 |

## Review log (2026-08-03, against code at `1062dc2`)

Findings folded into the tasks above. Each was verified against the file, not inferred:

| # | Finding | Where fixed |
|:--|:--|:--|
| 1 | `runner.py:386-396` end-of-rollout hidden recompute is a FOURTH encoder forward; feeding it 72D into a 76-wide GRU raises at the end of iteration 0 | A5 site table + step 4(c), A8 step 1 |
| 2 | Every test snippet used `from constrained_albc...`, which pulls `pxr` — `tests/` is the no-Isaac suite | Global Constraints + A1 s4 / A3 s3 / A4 s3 / A8 loaders |
| 3 | A1 would have added the first runtime isaaclab import to `mdp/observations.py`, breaking the standalone load the tests need. `isaaclab.utils.__init__` → `mesh` → `pxr`, so a lazy import fails identically | Global Constraints + local `_quat_apply_inverse` |
| 4 | `quat_rotate_inverse` is DEPRECATED (v2.1.0, warns per call). The spec's `def quat_rotate_inverse` grep passed anyway — a name-exists grep is not an API check | A1 s2/s3 |
| 5 | A8's parity test compared two identical inlined loops in the test file — a tautology that passes regardless of the real code | A8 rewritten: AST gate on real source + behavioral gate |
| 6 | A6 targeted `policy_obj.cfg/.extra`, but eval's policy is `_InstrumentedStudentPolicy` (only `_s`, `reset`, `__call__`) | Moot under the obs-dict transport; A6 rewritten |
| 7 | A6 called for a "hydra override"; eval mutates `env_cfg` directly in `run_static` before `gym.make` | A6 s3, reads the flag off the checkpoint |
| 8 | Phase D missed the obs-width guard at `albc_env.py:183-210`, which raises before any of the sites the spec did list | Phase D s1, three-site list |

Verified-correct and left alone: all three Isaac APIs exist at head; `albc_env.py` anchors 386 /
1152 / 1650 / 111 / 1134 are exact; `apply_bias_ema_obs`'s noise-tuple pattern is copied
faithfully (including the `observation_noise_model is None` skip); the gravity convention gives
+9.81 on body z at rest; the backlog section's 16 leads match `omx wiki list` exactly.

## Handoff prompt for the implementation session (paste as-is)

> Read `/workspace/.sp/plans/2026-08-03-obs4-student-then-teacher76-program.md` and execute
> Phase A with superpowers:subagent-driven-development (one task per subagent, spec + quality
> review per task). Work in `/workspace/constrained-albc` on `main` (check
> `git status --short --branch` first; concurrent sessions may share the tree — stage explicit
> paths only). Phase A only; STOP at the Phase B proposal and ask the user before any launch.
> **This plan supersedes `/workspace/.sp/plans/2026-07-30-spec-e1-b2-student-extra-obs.md`
> wherever the two differ** — the spec's env-attribute transport, its `quat_rotate_inverse`
> import, its `from constrained_albc...` test imports, and its parity test are all superseded
> (see the Review log). Read the spec only for background on the sensor physics.
> Also read the omx wiki pages it cites
> (`omx wiki query --root /workspace/constrained-albc "student extra obs"`).
