# Changelog

All notable changes to this project are documented here. Earlier history is in `git log`.

## [Unreleased] — paper release

Code release for "Underwater Mini-ROV Manipulation via Active Link Buoyancy Control with
Sim-to-Real Reinforcement Learning".

### Added

- SSTV reward term (`reward.k_sstv`, `sstv_start_step`) and observation-delay
  randomization (`randomization.obs_delay_steps`) used by the paper teacher; both off by
  default.

### Changed

- Licensed under MIT; Isaac Lab-derived files keep their BSD-3-Clause notice.
- The student encoder defaults to the GRU used in the paper (`StudentCfg.encoder_type`,
  deploy CLI fallback); the TCN variant remains selectable.
- Documentation aligned with the paper: constraint names, task list, deployment contract.

### Removed

- Arms and baselines outside the paper: the Lagrangian constrained arm, the residual-TDC
  arm, and the adaptive-TDC task registration.
- Unused scripts and diagnostic tools, internal research notes and history documents, and
  local tooling state from version control.
