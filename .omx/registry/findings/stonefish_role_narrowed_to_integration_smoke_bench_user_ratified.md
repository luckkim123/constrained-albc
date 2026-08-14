---
title: "Stonefish role narrowed to integration smoke bench (user-ratified 2026-08-03): no coefficient source, no performance verdicts; priority moves to thruster/real-robot anchors; third simulator rejected"
tags: ["stonefish", "role", "smoke-bench", "decision"]
created: 2026-08-03T05:57:29.627258
updated: 2026-08-03T06:13:59.143643
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

> # DUPLICATE 2026-08-14 -- the same 2026-08-03 decision is recorded on two pages, 13 minutes apart.
>
> The sibling is `stonefish_role_narrowed_to_integration_smoke_bench_ratified_2026.md`
> (created 06:10 against this page's 05:57; it carries `status: resolved`, a later 08-04 update,
> the open-dispatch list, and the C3-vs-A0-TCN pack correction). **Prefer the sibling.** Every
> fact unique to this page has been copied there under "MERGED FROM the duplicate page".
>
> **One stale path here.** The body cites the vault SSOT as
> `0_Project/in_progress/krit/simulator/docs/stonefish-role-decision-2026-08-03.md`. That is
> wrong -- verified 2026-08-14, the file is at
> `0_Project/in_progress/albc/sim_validation/docs/stonefish-role-decision-2026-08-03.md`,
> which is what this page's own Update block says. The `krit/simulator/docs/` directory exists
> but does not hold the file, so the wrong path fails silently as an empty directory listing
> rather than as a missing file.


# Stonefish role narrowed to integration smoke bench (user-ratified 2026-08-03): no coefficient source, no performance verdicts; priority moves to thruster/real-robot anchors; third simulator rejected

Stonefish's role is narrowed to an INTEGRATION SMOKE BENCH, user-ratified 2026-08-03. This converts the 2026-07-30 session recommendation (rotational-damping verdict aftermath) into a standing decision.

WHAT A STONEFISH RUN MAY CONCLUDE from now on: divergence/runaway/NaN, safety-gate activation, seam and integration bugs (obs assembly, normalization, frame conventions), qualitative regime (limit cycle / spin / saturation present-or-absent). WHAT IT MAY NOT: absolute performance, any ratio against Isaac, hydro coefficient verdicts, hardware-readiness calls. Rationale: the distributed integral is only as good as the integrated geometry (bare cylinder + thin rod + six geometry-less thrusters), and neither simulator has ever been contrasted with the real robot.

RESOURCE PRIORITY moves to real-robot anchors, thruster first: one bench session = T200 command-to-thrust curve + XW540-T260 step response + real state-estimation rate. Until then every inter-simulator coefficient dispute is treated as UNDECIDABLE.

THIRD-SIMULATOR SEARCH REJECTED: with zero real contrast data an added engine only shows that three things disagree, at full integration cost.

RETRAIN PRINCIPLE: never move a hydro coefficient to either simulator's value; widen DR by measured uncertainty with the curriculum budget retuned alongside (curriculum_recalibration lead). HydroRC-v2 remains geometry-or-literature derived (016d1b1 numbers retired).

HOUSEKEEPING FACTS (2026-08-03): the queued HydroRC arm was already CONSUMED (launched 2026-07-28 as trpo_hydrorc_s30_260728_013136, Isaac paired gate FAIL, recenter not adopted) -- nothing pending depends on retired numbers. Probe P-D (numerical-damping equivalence calibration) is explicitly retired, its purpose dissolved by this decision. The smoke bench lives at stonefish_sim/smoke_bench/ (smoke_run.sh + smoke_check.py, PASS/FAIL on the narrowed criteria only, rms printed as unscored context); July probe artifacts archived at stonefish_dev:/workspace/probe_archive/2026-07/.

Vault SSOT: 0_Project/in_progress/krit/simulator/docs/stonefish-role-decision-2026-08-03.md

---

## Update (2026-08-03T06:13:59.143643)

Stonefish's role is narrowed to an INTEGRATION SMOKE BENCH, user-ratified 2026-08-03. This converts the 2026-07-30 session recommendation (rotational-damping verdict aftermath) into a standing decision.

WHAT A STONEFISH RUN MAY CONCLUDE from now on: divergence/runaway/NaN, safety-gate activation, seam and integration bugs (obs assembly, normalization, frame conventions), qualitative regime (limit cycle / spin / saturation present-or-absent). WHAT IT MAY NOT: absolute performance, any ratio against Isaac, hydro coefficient verdicts, hardware-readiness calls. Rationale: the distributed integral is only as good as the integrated geometry (bare cylinder + thin rod + six geometry-less thrusters), and neither simulator has ever been contrasted with the real robot.

RESOURCE PRIORITY moves to real-robot anchors, thruster first: one bench session = T200 command-to-thrust curve + XW540-T260 step response + real state-estimation rate. Until then every inter-simulator coefficient dispute is treated as UNDECIDABLE.

THIRD-SIMULATOR SEARCH REJECTED: with zero real contrast data an added engine only shows that three things disagree, at full integration cost.

RETRAIN PRINCIPLE: never move a hydro coefficient to either simulator's value; widen DR by measured uncertainty with the curriculum budget retuned alongside (curriculum_recalibration lead). HydroRC-v2 remains geometry-or-literature derived (016d1b1 numbers retired).

HOUSEKEEPING FACTS (2026-08-03): the queued HydroRC arm was already CONSUMED (launched 2026-07-28 as trpo_hydrorc_s30_260728_013136, Isaac paired gate FAIL, recenter not adopted) -- nothing pending depends on retired numbers. Probe P-D (numerical-damping equivalence calibration) is explicitly retired, its purpose dissolved by this decision. The smoke bench lives at stonefish_sim/smoke_bench/ (smoke_run.sh + smoke_check.py, PASS/FAIL on the narrowed criteria only, rms printed as unscored context); July probe artifacts archived at stonefish_dev:/workspace/probe_archive/2026-07/.

Vault SSOT: 0_Project/in_progress/albc/sim_validation/docs/stonefish-role-decision-2026-08-03.md

