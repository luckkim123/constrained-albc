# constrained-albc Documentation

Documentation for the constrained ALBC (arm-equipped underwater vehicle) RL stack.
Organized [Diátaxis](https://diataxis.fr/)-style by reader intent. English-only
(the former `*.ko.md` translations and `*.pdf` renders were removed 2026-07-12).

| Section | Intent | Start here when... |
|---|---|---|
| [Getting oriented](#getting-oriented) | orientation | you're new to the repo |
| [tutorials/](#tutorials--learning) | learning | you want a guided first run |
| [how-to/](#how-to--tasks) | tasks ("how do I...") | you have a job to do |
| [reference/](#reference--lookup) | lookup | you need a specific fact or past result |
| [explanation/](#explanation--understanding) | understanding ("why") | you want to know how/why the system works |

## Getting oriented

- [`../README.md`](../README.md) — repo overview, registered tasks, quickstart
- [`installation.md`](installation.md) — three-layer install (isaaclab -> marinelab -> constrained-albc) + task-registration verify snippet
- [`architecture.md`](architecture.md) — package layout, registered-task table, stock RSL-RL dependency notes

## tutorials/ — learning

| Doc | Topic |
|---|---|
| [getting-started](tutorials/getting-started.md) | first walkthrough: install check, smoke-train, locate output, eval, read plots |

## how-to/ — tasks

| Doc | Task |
|---|---|
| [deploy-pack-export](how-to/deploy-pack-export.md) | produce a self-verifying teacher+student deploy pack via `export_deploy.py` (current export procedure) |
| [deploy](how-to/deploy.md) | superseded pointer page — old FullDOF export is dead; redirects to `deploy-pack-export.md` |
| [domain-randomization](how-to/domain-randomization.md) | enable/disable DR, work with the DORAEMON curriculum, add a new DR parameter |
| [run-on-dgx](how-to/run-on-dgx.md) | run a campaign stage on the NVIDIA DGX: three-repo sync, launch conventions, why the split is safe, how results come back |
| [sim-to-real](how-to/sim-to-real.md) | sim-to-real gap analysis (actuator, sensor, hydrodynamics) and deployment strategy |

## reference/ — lookup

| Doc | Use |
|---|---|
| [task-reference](reference/task-reference.md) | all 7 registered task IDs — env package, obs/privileged/action dims, typical launch command (SSOT for task ID enumeration) |
| [teacher-campaign-plan](reference/teacher-campaign-plan.md) | consolidated teacher-campaign plan + status (SSOT): canonical experiment ids, legacy-name mapping, disk-derived status, remaining work + GPU budget |
| [observation-space](reference/observation-space.md) | `envs/main` 69D obs / 28D privileged obs breakdown, proprioception history, encoder consumption |
| [action-pipeline](reference/action-pipeline.md) | `envs/main` action path: policy output -> clamps -> arm delta-PD + 6-thruster TAM wrench |
| [command-and-task](reference/command-and-task.md) | `envs/main` command/goal side: attitude+yaw-rate sampling, tracking error, reward consumption |
| [main-network-architecture](reference/main-network-architecture.md) | `envs/main` encoder/actor/critic architecture and dims |
| [reward](reference/reward.md) | `envs/main` reward system: tracking kernel, six weighted terms, error buffers, dt-scaling |
| [constraints](reference/constraints.md) | `envs/main` 10 IPO constraints (5 probabilistic + 5 average), config + ConstraintTRPO consumption |
| [exploration-and-noise](reference/exploration-and-noise.md) | `envs/main` action-noise (`log_std`), post-update clamp, entropy bonus, entropy collapse under ConstraintTRPO |
| [domain-randomization-and-doraemon](reference/domain-randomization-and-doraemon.md) | `envs/main` DR system: 20-param DORAEMON curriculum, `DomainRandomizationCfg`, sampling/scheduler wiring, eval-side fixed DR |
| [glossary](reference/glossary.md) | alphabetized term list, each entry linked to its owning reference page |
| [experiments-archive](reference/experiments-archive.md) | ARCHIVE — experiment campaign rounds (2026-04-04 ~ 04-18) + root-cause investigations |
| [design-history](reference/design-history.md) | ARCHIVE — design/plan document timeline (2026-02 ~ 03) mapped to current code |
| [debug-history](reference/debug-history.md) | ARCHIVE — resolved bugs, TDC gain tuning, code review/cleanup logs |

## explanation/ — understanding

| Doc | Topic |
|---|---|
| [system-overview](explanation/system-overview.md) | conceptual overview of the default task: robot, control problem, obs/action spaces, algorithm |
| [dynamics](explanation/dynamics.md) | ALBC dynamics, added-mass coupling derivation, inertia-variation/TDC stability |
| [physics-tuning](explanation/physics-tuning.md) | PhysX stability rationale (effort_limit, added mass, damping) |
| [reward-design](explanation/reward-design.md) | rationale for the `envs/main` reward shape (why, not values -- values live in `reference/reward.md`) |
| [constraint-theory](explanation/constraint-theory.md) | NORBC Constrained RL theory vs. ConstraintTRPO/IPO/cost-GAE/barrier implementation |
| [dr-strategies-survey](explanation/dr-strategies-survey.md) | literature survey of DR-handling strategies (curriculum, privileged info, contrastive) |
| [tdc-control-law](explanation/tdc-control-law.md) | roll/pitch TDC derivation (DLS IK, anti-windup) |
| [tdc-literature](explanation/tdc-literature.md) | Time-Delay Control literature survey |
| [run-id-tree-design](explanation/run-id-tree-design.md) | design of the unified `run_id` tree (`experiments/<run_id>/` manifest + `train` symlink) spanning training/eval/config |

> **Currency note.** Reference pages under `reference/{action-pipeline,command-and-task,
> constraints,domain-randomization-and-doraemon,exploration-and-noise,
> main-network-architecture,observation-space}.md` are verified against commit `c5a8a08`
> and describe the **default** task `Isaac-ConstrainedALBC-TRPO-v0` (`envs/main`,
> 69D obs / 28D privileged / 8D action). The **legacy** full-DOF variants
> (`envs/full_dof`, 87D obs / 24D privileged) are out of scope for those pages -- see
> [`task-reference.md`](reference/task-reference.md) for the full task table. Archive
> pages (`experiments-archive.md`, `design-history.md`, `debug-history.md`) predate the
> `envs/main` split and are historical narrative, not maintained as living reference.
