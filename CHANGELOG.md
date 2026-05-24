# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-25

### Added

- Initial extraction from the isaaclab monorepo with full git history (`git filter-repo`).
- `constrained_full_albc` environment: ConstraintTRPO + IPO + asymmetric encoder,
  DORAEMON adaptive DR curriculum, 6-DOF full-DOF ALBC for underwater vehicles.
- `constrained_full_albc_tdc` environment: TDC (Time-Delay Controller) variant with
  kinematics, TDC, and thruster-PD controllers.
- Student distillation pipeline (TCN / GRU) under `envs/constrained_full_albc/student/`:
  collector, runner, models, teacher, eval.
- Analysis tooling under `constrained_albc/analysis/`: `eval_dr` (4 DR modes: static,
  periodic, segmented, sudden), `eval_student`, `analyze`, `compare`, `monitor`,
  `encoder_tools`.
- Launcher scripts under `scripts/`: `launch_student_tcn.sh`, `launch_student_gru.sh`,
  `launch_students_sequential.sh`, `run_student_evals.sh`, `train_student.py`.
- Six registered Isaac Lab task IDs: `Isaac-FullDOF-TRPO-v0` (main),
  `Isaac-FullDOF-NoEncoder-v0`, `Isaac-FullDOF-PPO-v0`, `Isaac-FullDOF-TRPO-NoIPO-v0`,
  `Isaac-FullDOF-PPO-Enc-v0`, `Isaac-FullDOF-TDC-v0`.
- Depends on `marinelab` for shared marine physics and UUV assets (Hero Agent).
