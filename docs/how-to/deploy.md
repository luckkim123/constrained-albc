# Deploy — Model Export

> **Status**: superseded 2026-07-12. The procedure this page used to describe is dead —
> it targeted a project and task that no longer exist. See
> [deploy-pack-export.md](deploy-pack-export.md) for the current, verified procedure.

## What changed

This page previously walked through a manual `torch.save(export_bundle, ...)` export for the
`constrained_full_albc` project / `Isaac-FullDOF-TRPO-v0` task — neither exists in the current
codebase (`grep` for both returns zero hits). It also flagged an open problem: the actor
couldn't run without the encoder's privileged-obs latent `z`, and proposed building a
student/adapter module (HORA/RMA Phase 2) as unfinished future work.

That adapter is now built. `constrained_albc/envs/main/student/` trains a TCN (or GRU) encoder
that consumes a rolling window of the same 69D policy observation the teacher's actor sees and
reproduces the teacher's 9D latent `z` — no privileged obs needed at deployment. The export
mechanism is `constrained_albc/deploy/` (`spec.py`/`engine.py`/`golden.py`/`pack.py`), driven by
`scripts/export_deploy.py`, with a CPU-golden self-check and MANIFEST sha256 verification built
in. Full command, contracts, and the Mac/agent-jetson handoff steps are in
[deploy-pack-export.md](deploy-pack-export.md) — not duplicated here.

## Dims and architecture

Exact obs/action/latent dimensions and the encoder/actor/critic wiring are reference-SSOT:
[observation-space.md](../reference/observation-space.md),
[main-network-architecture.md](../reference/main-network-architecture.md).

## Real-hardware integration

Obs-pipeline reconstruction, sim-vs-real gap analysis, and the staged rollout checklist are
covered in [sim-to-real.md](sim-to-real.md) (§7 Real Robot Deployment Checklist). The board-side
inference code runs in the separate `agent-jetson` repo, outside this repo's scope.
