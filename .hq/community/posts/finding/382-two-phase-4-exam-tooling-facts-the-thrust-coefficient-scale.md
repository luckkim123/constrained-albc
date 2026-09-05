# Two Phase 4 exam-tooling facts: the thrust_coefficient_scale Hydra override never reaches eval.py static (every arm ran (0.7, 1.3) at hard), and the cuDNN preamble is needed on the GRU RNN path too

- id: finding/382 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: eval.py, apply_dr_config, build_dr_config, thrust_coefficient_scale, hydra-override, phase-4, inc13w, finding-318, cudnn, decision-008, gru
- summary: apply_dr_config rebuilds env_cfg.randomization at every level from a fresh DomainRandomizationCfg() plus the 21 DORAEMON dims, so the [0.5,2.0] band in p4_runner.sh/sd_*_exam.sh was a no-op; verdicts stand (same band for all arms) but the inc13w full-section-5-plant premise is false and the band is untested. decision/008 scope corrected: the GRU student under eval.py dies in _cudnn_rnn_flatten_weight without the preamble.

**Two Phase 4 exam-tooling facts, both found while running the student-mode exam: (1) a Hydra `env.randomization.thrust_coefficient_scale=[0.5,2.0]` override never reaches `eval.py static` -- `apply_dr_config` rebuilds `env_cfg.randomization` at every level, so every Phase 4 arm ran the base (0.7, 1.3) band at `hard` and (1, 1) at `none`; (2) the cuDNN preamble of decision/008 is required on the GRU RNN path too, not only for conv.**

**(1) The thrust band override is a no-op -- derived from code, not yet printed by a run.**
`eval.py:483-489 apply_dr_config(env_cfg, scale)` does `env_cfg.randomization = build_dr_config(scale)`, once at construction (`:1411`) and once per level (`:1550+`). `dr_config.py:328-364 build_dr_config` returns `_make_nominal_dr()` at scale 0 and otherwise a fresh `DomainRandomizationCfg()` with every `_DR_TUPLE_FIELDS` entry interpolated between the nominal table (`thrust_coefficient_scale` 1.0, `:132`) and `full`; `full` is `_DORAEMON_FULL_DR`, which `load_doraemon_dr` (`:214-283`) builds from a fresh `DomainRandomizationCfg()` plus the 21 DORAEMON-managed dims read from the run's TB. `thrust_coefficient_scale` is not DORAEMON-managed, so `full` carries the base (0.7, 1.3) and no code path copies the Hydra value across. What DOES take effect: `env.thrusters.thrust_coefficient=13.0` (not under `randomization`), `--control-delay N` (set on the rebuilt cfg after `apply_dr_config`, `:1411-1420`), `--fault_fixed_health`.

Consequences:
- Every Phase 4 arm (inc, inc13, inc13w, p3ref, p3b_2500/5000/7500/final, taskvar, sd_p3b7500, sd_inc9998) ran the same band, so per-env pairing and the recorded verdicts stand as measured.
- The premise that `inc13w` is "the incumbent on the FULL section-5 plant (13 N and scale 0.5-2.0)" (`p4_runner.sh:58`, finding/318's rationale, the Phase 4 report's plant description) is false on the band: it is 13 N with (0.7, 1.3). No exam in this program has graded any policy at thrust scale 0.5 or 2.0. The section-5 band is untested on both incumbent and candidate.
- The fix is a caller-supplied override for non-DORAEMON tuple fields in `build_dr_config` (one keyword), not done here; it belongs with the RE-analysis of `diagnose-20260905-140134`.
- Verification owed: one `print(env_cfg.randomization.thrust_coefficient_scale)` per level in the next exam. The exam log currently never prints the band (`grep thrust_coefficient_scale` on `.hq/work/p4/sd_p3b7500/healthy.log` returns nothing).

**(2) cuDNN preamble scope.** decision/008 records the `LD_LIBRARY_PATH=/isaac-sim/exts/omni.isaac.ml_archive/pip_prebundle/nvidia/cudnn/lib` preamble for conv-bearing runs and states a GRU never hits the cu13/cu128 mismatch. `train_student.py:150` avoids it only by setting `torch.backends.cudnn.enabled = False`; `eval.py` has no such guard, and the GRU student under `eval.py static` calls `torch._cudnn_rnn_flatten_weight` at construction (`student_policy.py:99`) -> `CUDNN_STATUS_NOT_INITIALIZED`, 5/5 configs, ~30 s each (2026-09-05 21:32-21:35). With the preamble, 5/5 pass. Rule as corrected: any process that constructs the GRU student with cuDNN enabled needs the preamble; conv is not the trigger, cuDNN is.

Evidence: `eval.py:483-489,1411-1420,1550`; `dr_config.py:66-136,214-283,328-364`; `/workspace/g0c_runner/p4_runner.sh:58`, `p4d2_runner.sh:19`, `sd_p3b_exam.sh`; `.hq/work/p4/sd_p3b7500/*.log` (first run, cuDNN failure) and the second run's summaries.
## Comments
