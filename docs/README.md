# constrained-albc Documentation

Documentation for the constrained full-DOF ALBC research stack. Organized
[Diátaxis](https://diataxis.fr/)-style by reader intent.

| Section | Intent | Start here when… |
|---|---|---|
| [Getting started](#getting-started) | orientation | you're new to the repo |
| [explanation/](#explanation--understanding) | understanding ("why") | you want to know how/why the system works |
| [how-to/](#how-to--tasks) | tasks ("how do I…") | you have a job to do |
| [reference/](#reference--lookup) | lookup | you need a specific fact or past result |

## Getting started

- [`../README.md`](../README.md) — repo overview, registered tasks, quickstart
- [`installation.md`](installation.md) — three-layer install (isaaclab → marinelab → constrained-albc)
- [`architecture.md`](architecture.md) — package layout + the RSL-RL fork dependency

## explanation/ — understanding

| Doc | Topic |
|---|---|
| [system-overview](explanation/system-overview.md) | the robot, control problem, action/obs spaces, algorithm |
| [dynamics](explanation/dynamics.md) | ALBC dynamics, added-mass coupling, adaptive M |
| [reward-design](explanation/reward-design.md) | Gaussian tracking + PBRS + penalty design |
| [constraint-theory](explanation/constraint-theory.md) | NORBC theory ↔ ConstraintTRPO/IPO alignment |
| [tdc-control-law](explanation/tdc-control-law.md) | roll/pitch TDC derivation (DLS IK, anti-windup) |
| [tdc-literature](explanation/tdc-literature.md) | Time-Delay Control literature survey |
| [dr-strategies-survey](explanation/dr-strategies-survey.md) | DR strategies survey (ADR, DORAEMON, RMA, HIM) |

## how-to/ — tasks

| Doc | Task |
|---|---|
| [deploy](how-to/deploy.md) | export & deploy a trained policy (obs pipeline, EmpNorm recal) |
| [domain-randomization](how-to/domain-randomization.md) | configure DORAEMON DR (categories, parameters) |
| [sim-to-real](how-to/sim-to-real.md) | sim-to-real gap (actuator, sensor, hydrodynamics) |
| [physics-tuning](how-to/physics-tuning.md) | PhysX stability (effort_limit, added mass, damping) |

## reference/ — lookup

| Doc | Use |
|---|---|
| [experiments-index.json](reference/experiments-index.json) | machine-readable lookup: `settled_decisions` (key-value) + per-run records with verdicts |
| [experiments-archive.md](reference/experiments-archive.md) | experiment campaign rounds 1-8 + root-cause investigations (what changed → result → verdict) |
| [design-history.md](reference/design-history.md) | design/plan timeline (2026-02 ~ 03) → what maps to current code |
| [debug-history.md](reference/debug-history.md) | resolved bugs, TDC gain tuning, code review/cleanup logs |

> **Currency note.** This documentation was consolidated 2026-05-25 from the former
> `isaaclab/docs/hero/` tree. Deprecated material (HORA/RMA pipeline, 2-DOF `hero_agent`
> envs, abandoned RL-TDC / SAC-MPC paths) was removed. Verified facts (e.g. **87D obs /
> 24D privileged**) come from current code; older docs that conflicted were corrected.
> Historical experiment/changelog detail is compressed into `reference/` for lookup,
> not maintained as living docs.
