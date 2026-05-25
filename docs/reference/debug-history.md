# Debug & Tuning History

Backup lookup of resolved bugs, gain-tuning results, and cleanup records. Source logs
used deprecated `hero_agent` / `HeroAgent*` / `AdaptRunner` naming, but the substantive
TDC controller fixes apply to the **current** `controllers/tdc.py` / `kinematics.py`
and remain relevant for `Isaac-FullDOF-TDC-v0`. Deprecated-only items are flagged ⚠.

---

## TDC controller tuning (2026-02-05 ~ 02-11)

The path from a 36-combo gain sweep to a converging controller.

- **36-combo Kp×Kd sweep** → 31/36 worse than initial error; chronic workspace
  saturation (WS util 2.5-3.0×). Best gains alone got only 6.1° improvement.
- **TDE term isolation** → both TDE terms (Λ·p_EE delayed, −M̂·ν̇) diverge; PD-only and
  ΔT_b both converge → divergence is from TDE terms, not PD.
- **Root cause = 3 reinforcing mechanisms:** Λ attitude-dependence (positive feedback);
  finite-diff amplification (1/dt=100× → M̂·ν̇ exceeds 12.2 Nm authority); violated
  H_t≈H_{t−L} assumption (arm-body coupling).
- **Attempts 1-8 (all failed):** H_hat EMA → 50° stagnation (filter biases ΔT_b
  cancellation); filter-off 100Hz → diverge (noisy ν̇); 200Hz → diverge; anti-windup TDE →
  diverge; ν̇ EMA α=0.05 → oscillation (Λ·p_EE still dominates); M̂=0.5 raise → worse
  (scales M̂·ν̇). **Param tuning alone is a dead end.**
- **Attempt 9 — BREAKTHROUGH:** `m_hat=(0.15,0.15)`, `Kp=40`, `Kd=12`,
  `tde_saturation=5.0 Nm` → converges roll ±13°, pitch 2.5° in 10s. TDE capped so PD
  is primary.
- **Structural changes after tuning:** sign fix on Λ/T_b; removed workspace clamp;
  introduced **DLS IK (Yoshikawa adaptive)**; then **removed TDE saturation** (DLS IK
  naturally limits p_EE); `control_decimation=4` (50Hz, matches C++ ref); joint PD
  Kp=200/Kd=10; payload on gripper body; privileged obs 22D→24D.
- **Current config:** `m_hat=(0.15,0.16)`, `kp=40`, `kd=12`, `dls_lambda_damping=0.01`,
  `ik_dls_lambda=0.15`, `nu_dot_ema_alpha=0.05`, `h=0.18`, `max_joint_velocity=3.0`.
  `tde_saturation` / `workspace_radius` / `h_hat_filter_alpha` all **REMOVED**.
- **Key lessons:** actuator authority gates TDC feasibility (TDE needed 30-50 Nm vs 12.2
  available); never filter H_hat/U_hat containing T_b (filter ν̇ only); DLS IK replaced
  TDE saturation as the structural fix.

## TDC bug archive (2026-02-05 ~ 02-10)

- **Bug 1 — ΔT_b sign flipped:** `t_b_current - t_b_delayed` → `t_b_delayed - t_b_current`.
- **Bug 2 — p_EE history off-by-one:** moved `_update_tde_history` from start to end of
  `compute()`; `delayed_idx (idx−delay)` → `(idx−delay+1)` so p_EE/omega/lf align to same
  timestep.
- **Lambda_inv DLS:** replaced `1/lf` with adaptive DLS `dls_factor = lf/(lf²+λ²)`,
  `λ²=25·(1−lf/F_bu)`; exact at 0°, no saturation at 80°, p_EE→0 at 89°;
  `dls_lambda_max=5.0`, per-env `_lf_max` from `set_buoyancy_force()`.
- **Inertia fixes:** main body (0.071,0.071,0.031)→(0.0994,0.0994,0.0372) [URDF R=0.09,
  L=0.325]; buoy (0.0023…)→(0.00278,0.00278,0.00336) [R=0.085, H=0.118].
- **default_m_hat fix:** (1.0,1.0)→(0.14,0.15); old value ~7× overestimate caused
  workspace saturation from step 1.
- **Encoder index fix:** M_hat read from `z[:2]` (wrong) → `z[3:5]` (roll/pitch in 6-DOF
  convention).
- ⚠ **Invalid conclusions caveat:** numerical TDE-divergence analyses in deleted notes
  06/07 were done WITH the Λ/T_b sign bugs and pre-DLS — those numbers are INVALID. Only
  conceptual frames survive (G_loop structure, sim-to-real stiff-PD vs actuator-bandwidth,
  small-angle approx confirmed NOT the cause).

## Code review (2026-02-23 ~ 03-05)

- Full review 2026-03-05 (27 files): 0 HIGH, 2 MEDIUM fixed, 4 LOW no-fix.
- **Fix 1:** config.py hardcoded `3.14`/`1.5708` → `math.pi` constants.
- **Fix 2:** base_env.py EMA warm-start used pre-reset velocity → set to `0.0`.
- **Verified correct (no change):** TDC math (Λ signs, TDE formula, anti-windup, EMA),
  DLS IK convergence, proprio ring buffer (torch.roll), encoder+adaptation, runners
  (encoder LR cosine decay, ckpt migration), rewards (PBRS Ng 1999, added-mass stability
  clamp), DORAEMON (Beta-dist entropy max matches ICLR 2024).
- ⚠ **Deleted deprecated code:** `unified_tdc_env.py`, `single_phase_runner.py`,
  `ppo_aux_mhat.py`, `adapt_tdc_env.py`, ActorCriticEncoderTDC/-Adapt + cfgs;
  whole `hero_agent_mpc/` package (SAC-MPC concluded). `encoder_tdc_env.py` kept as
  unregistered reference.

## Code simplification (2026-03-05)

~7,700 lines / 27 files. No architecture changes; all steps `ruff`-verified.

- **Step 1:** dead code — `_cumulative_effort` buffer, `HeroAgentEnvWindow` class, MPC
  docstring refs, 8 `__pycache__` dirs.
- **Step 2:** unused rewards — deleted `action_rate_penalty()`,
  `angular_velocity_penalty()` (+ cfg fields).
- **Step 3:** dedup `_update_perturbation()` → `_apply_perturbation_cycle()` helper.
- **Step 4:** noise config — `_iter_noise_params()` iterator collapses 4-nested loops.
- **Step 5:** DR factory — `_apply_xyz_offset_with_doraemon()` helper (XY uniform + Z
  DORAEMON).
- **Step 6:** full `ruff check`+`format` clean, F401 clean.
- **Step 7:** removed stale MPC docstring + duplicate parent-equal overrides;
  `tdc.py` `_set_param()` + `_zero_buffers` loop refactors. (Pre-existing double
  `_compute_M_true` call deferred.)
