# configure_env_for_student disabled nothing: every student since 2026-04-21 rolled out on DORAEMON initial Beta (payload 1.5 kg, inertia 1.2, fault-free) and, for SimToReal, on the base thrust and delay ranges

- id: finding/381 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- topic: debugging
- confidence: high · status: resolved
- verified: none · keywords: configure_env_for_student, doraemon, initial-beta, runner-defect, simtoreal, thrust_coefficient_scale, control_delay_steps, student, distillation, plant-support, inc9998
- summary: The runner flips cfg.doraemon.enable after gym.make, which ALBCEnv reads once; the scheduler persisted frozen at Beta(concentration 30) around each nominal, so the student never saw payload 0 kg (5.6 sigma), water 1000 (3.7 sigma), a dead thruster or a delay, and the fresh DomainRandomizationCfg() reverted the section-5 thrust band and delay range. Patched in tree (drop _doraemon, keep task DR, env.yaml dump); HARD gate until R1 verifies.

**`configure_env_for_student` never disabled DORAEMON. Every student distilled through the runner since 2026-04-21 rolled out on the scheduler's INITIAL Beta -- payload 1.5 kg, inertia 1.2, water 1010, fault severity 0.01 (fault-free) -- while its teacher was graded on the full box; and for the SimToReal task the runner additionally reverted `thrust_coefficient_scale` (0.5, 2.0) -> (0.7, 1.3) and `control_delay_steps` (0, 3) -> (0, 0). Patched 2026-09-06 (uncommitted at post time); R1 verifies.**

**Defect 1 -- a flag read once.** `constrained_albc/envs/_core/student/runner.py:44-75` (called from `StudentRunner.__init__`, line 86, AFTER `gym.make`) sets `env_cfg.doraemon.enable = False` and logs "DORAEMON disabled". But `ALBCEnv._init_doraemon()` (`albc_env.py:582-619`) reads that flag exactly once during construction and builds `self._doraemon = DoraemonScheduler(...)`; every later use is `if self._doraemon is not None` (`albc_env.py:1420, 1622, 1723, 1863`) -- reset-time sampling of the 21 curriculum dims (1723-1727), fault severity (1775-1782), obs-noise scale (1741). Nothing re-reads the cfg. `train_student.py` never calls `_doraemon.step()` (that lives in `OnPolicyDoraemonRunner`, which the student path does not use) and never loads `doraemon_state.pt`. So the scheduler stayed at its constructor state for the whole distillation: `BetaDistribution(concentration=cfg.init_concentration=30)` centred on each `ParamSpec.nominal` (`marinelab/algorithms/doraemon.py:42, 118-144`), nominal = range midpoint except the four zero overrides (`envs/main/doraemon.py _NOMINAL_OVERRIDES`).

The plant the student actually saw, against the exam's `none` (true nominal, `dr_config.py:122-136`):

| dim | train centre +/- std | exam none | distance |
|:--|--:|--:|--:|
| payload_mass (kg) | 1.50 +/- 0.27 | 0.0 | 5.6 sigma |
| payload_cog_offset_z | -0.025 +/- 0.0045 | 0.0 | 5.6 sigma |
| water_density | 1010 +/- 2.7 | 1000 | 3.7 sigma |
| inertia_scale | 1.20 +/- 0.14 | 1.0 | 1.4 sigma |
| linear/quadratic_damping_scale | 1.05 +/- 0.12 | 1.0 | 0.4 sigma |
| fault_severity | 0.01 +/- 0.018 | 0 (healthy) / two dead (pair34) | fail_prob = severity x 0.30 <= ~0.015: dead thrusters essentially never sampled |
| obs_noise_scale, ocean_current, payload_xy_u | 0.01 +/- 0.018 | 0 | in support |

Calibration: the p3b teacher's own TB at its resume point (it 2050) shows `DORAEMON/mean/inertia_scale` 1.199 +/- 0.202 and `payload_mass` 1.487 +/- 0.386 -- the same centres, slightly widened -- and by it 7500 the teacher had expanded to 1.204 +/- 0.457 and 1.518 +/- 0.851 with fault severity 0.494 +/- 0.286. The exam's `hard` anchor is that final box (mean +/- 2 std, clamped). The student trained inside a narrow ball at the centre of a box its teacher was graded across, and at a corner (`none`) it never visited.

**Defect 2 -- the task's DR fields replaced.** The same function does `env_cfg.randomization = DomainRandomizationCfg()` (fresh base class from the variant package). For `ALBCSimToRealEnvCfg` that reverts the two section-5 randomization fields to the base defaults: `thrust_coefficient_scale` (0.7, 1.3) instead of (0.5, 2.0) and `control_delay_steps` (0, 0) instead of (0, 3) (`config.py:231, 263` vs `config_simtoreal.py`). The delay buffer is allocated at construction (cfg was (0,3) then) but every reset then draws lag 0. `thrust_coefficient = 13.0` lives in `env_cfg.thrusters` and survived. So option B (user, 2026-09-05: "the student rolls out on the section-5 plant") was silently defeated on two of its three randomized fields, and the exam's d1/d2 configs were, for the student, unseen.

**Dates.** `doraemon_cfg.enable = False` entered at beee560 (2026-04-21); the fresh-cfg substitution at 088809f (2026-06-08); the function moved to `_core` at a1360a7 (2026-07-13). Every student in this wiki -- buoyfix TCN, the student_distill_eint campaign (A0..C3), obs76 gen-2 and X1, dgx16k, student_final_round inc9998 (the DEPLOYED student) -- was distilled after 2026-04-21 through this path.

**What this re-frames (numbers stand, attributions do not).**
- finding/274 / decision/186 / finding/250 / finding/045 read the 10-19x train-to-in-loop latent gap and the 2.5-3.1 deg hard-roll dispersion band as "the distillation step's ceiling" and "DAgger covariate shift". The students' rollouts never covered the box their in-loop numbers were measured on; the shift was plant support before it was anything about DAgger. Whether the ceiling survives on the right plant is now an open question, not a closed one.
- The deployed inc9998 student never trained with a payload of 0 kg, a dead thruster, a delay, or water at 1000 kg/m3. It flew; that is a fact about robustness, not about the recipe. Its control exam on this protocol is `.hq/work/p4/sd_inc9998` (running).
- The 2026-09-05 HANDOFF line "train_student.py has no DORAEMON handling, so the distillation env starts the curriculum from its initial state" was right about the state and wrong about the implication drawn beside it ("fault exposure ~ severity 0.01 x p0 -- the same limit the incumbent had"): the limit is not a curriculum starting point, it is a frozen 30-concentration Beta on all 21 dims.

**Fix applied (tree, uncommitted at post time).** `configure_env_for_student` now sets `raw._doraemon = None` (the env then draws every DR dim uniformly from `cfg.randomization`; faults at `cfg.fault.thruster_fail_prob` with severity None -- the pre-curriculum path, `faults.py:54-69`), keeps `env_cfg.randomization` as the task defines it (`enable = True`), and prints one `[Student] DORAEMON scheduler dropped; DR = task cfg ...` line with the thrust band, delay range, payload range, inertia range and fault settings. `train_student.py` now writes `params/env.yaml` (Isaac `dump_yaml`) after the runner configures the env, which closes the "student has no env.yaml" hole of finding/352 for student launches. For the base task the kept cfg IS `DomainRandomizationCfg()`, so nothing changes there.

**Verification owed (R1 = `sd_p3b7500_c3_dr5_s30`, queued):** the `[Student]` line in `student_p3b_r1.log` showing (0.5, 2.0) / (0, 3) / fail_prob 0.3; `params/env.yaml` with `doraemon.enable: false` and those ranges; and on the exam, the healthy/none latent bias (finding/380 section 3) collapsing toward the training loss. Until then this page is a HARD gate: no student launch from a tree without the patch.

Evidence: `runner.py:44-75,86`; `albc_env.py:582-632,1420,1622,1723-1727,1741,1775-1782,1863`; `marinelab/algorithms/doraemon.py:32-49,115-145,365-367,773-825`; `envs/main/doraemon.py:40-96`; `config.py:231,263`; `config_simtoreal.py`; teacher TB `trpo_p3b_lb200_s30_r2050_260904_163518/events*` (`DORAEMON/mean|std/*` at it 2050 / 7500 / 9999); `git log -S`.
## Comments
- (2026-09-06, omx) 정정: R1 verified both owed items: params/env.yaml shows thrust (0.5,2.0) delay (0,3) fail_prob 0.3 doraemon false, and the 64-env shared latent bias^2 fell 0.033 -> 0.008 (finding/384). The runner fix is committed (4438492). The score gap is a different question, carried by finding/384.
