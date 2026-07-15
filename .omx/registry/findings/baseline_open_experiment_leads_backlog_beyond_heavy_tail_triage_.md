---
title: "Baseline open experiment-leads backlog (beyond heavy-tail): triage by value x launchability with blockers"
tags: ["backlog", "experiment-roster", "next-experiment", "heavy-tail", "doraemon-per-axis-gate", "command-box", "tam-dr", "sim-to-real", "triage", "teacher-baseline", "doraemon", "performance_lb", "exploration"]
created: 2026-07-14T07:57:24.357274
updated: 2026-07-15T04:54:42.574431
sources: ["diagnose-20260713-081707", "diagnose-20260715-133249"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: needs-experiment
---

# Baseline open experiment-leads backlog (beyond heavy-tail): triage by value x launchability with blockers

Consolidated index of the baseline's open experiment leads that are NOT the hard-DR roll heavy-tail
(the one weakness the p7_tail campaign targeted). Created because these WERE surfaced by the p7-planning
broad audit (recorded in DESIGN.p7_tail.md "Post-audit gaps", 2026-07-13) but were then DROPPED from the
campaign README's "미해결/다음" summary, which flattened the picture to "유일한 약점 = heavy-tail". This page
is the searchable backlog so a broad query reliably surfaces the full experiment roster, not just the
heavy-tail thread. Reference baseline: trpo_baseline_260713_031325 (consolidated main 7ac39c8).

## Triage: experiment value x launchable-now, with blocker

| Lead | Value | Launchable now? | Blocker / prerequisite | Priority |
|---|---|---|---|---|
| Eval command-box extension (static eval steps only to ATT_AMP=15 deg while trained box = +-30 deg -> inner half only) | HIGH — corrects tail MEASUREMENT itself | YES, zero-GPU, no retrain (re-eval existing checkpoints over full box) | none | 1 (nearly free) |
| DORAEMON per-axis success-gate (single binding axis=roll drives a GLOBAL min-gate freezing ALL strong-axis DR widening; set_axis_gate/_AXIS_PARAM_GATE do NOT exist) | HIGH — DIRECT structural fix for the e1 stall; unblocks the whole class of reward-costly probes | NO | engine code in marinelab/algorithms/doraemon.py | 2 (max structural lever) |
| performance_lb recalibration (lb=250 sits on baseline return ~247 -> ANY intervention costing ~10% return stalls the curriculum; e1 proved it) | MED-HIGH | partial (after measurement) | measure delayed-nominal return first; decide relative vs absolute lb | 2 (paired with per-axis gate) |
| Latency as a DORAEMON _PARAM_DEFS dim (e1 redesign; ties to real-robot vibration channel B) | MED-HIGH | NO | engine code (make control_delay a curriculum dim) | 3 |
| TAM / max_thrust DR band (the ONLY axis with NO DR at all; a wrong TAM is a systematic bias hitting all envs identically; onboard IMU+pressure, no load cell -> CANNOT be measured) | HIGH (deployment) | NO | source a physically-defensible numeric band from spec/literature (not measurable) | 3 (design-first) |
| thruster nonlinear curve ON (real T200 deadband + signed-square that multiplicative DR can NEVER reproduce) | conditional | NO | bench-measure real command->thrust first; an unverified curve manufactures a new sim-to-real gap | wait (measure before enabling) |
| hydro nominal measurement/anchoring (sim nominal is ANALYTICAL not measured; the "low-damping envs are hard" tail story rests on a possibly mis-anchored nominal) | MED | NO | tank free-decay protocol; and free-decay is non-separable (GM/I/A lumped) so only partial | wait |
| state_dependent_std, z-conditioned variant (feed DR-carrying encoder latent to the std head) | MED | NO | eval npz must log raw obs std (engine gap); premise weakened since baseline already converges to tight std 0.109 | parked, re-rank after tail probes |
| constraint inert-2 loosening ablation (rp_vel_settling + manipulability are the ONLY 2 genuinely inert of 10; other 8 shaped early training) | LOW | YES (budgets x100 on those 2) | none | low (deprioritized; slack is healthy complementary slackness, not a defect) |

## Not experiments (recorded so they are not mistaken for launchable probes)

- Real-robot vibration channel PICK (A obs-noise / B latency / D control-rate): needs REAL FFT logs to choose the channel; cannot design the training experiment without them.
- Real-robot vibration channel C (clamp-saturation blind spot): ALREADY largely closed by data, not a new experiment — baseline clip_fraction=0.0048 (P4 logging) means |a|>=1 saturation is ~0, so the smoothness-reward blind-spot is an unlikely vibration cause (rules/03: evidence over guess).
- arm step-response ID (Dynamixel bus telemetry), net buoyancy (pressure): MEASUREMENTS, not RL experiments; the only sim-to-real targets actually reachable with the current sensor suite.

## Movable-now recommendation

Of everything above, only two are both high-value and unblocked today: (1) command-box extension eval (zero-GPU; without it the whole heavy-tail success/failure judgment is made on the inner half of the trained envelope), and (2) DORAEMON per-axis gate / lb recalibration (engine code, but it unblocks every future return-costly probe that currently stalls like e1). The sim-to-real gaps (TAM DR, thruster curve, hydro) may matter MORE than heavy-tail for real deployment but are design-first / measurement-gated, not launchable now. Formalize any chosen lead through exp-design (single variable, H1/H2 discriminator, human-gated launch); do NOT auto-launch.

---

## Update (2026-07-14T09:56:26.815912)

Flagged needs-experiment 2026-07-14: this is the open experiment-leads backlog (command-box eval, DORAEMON per-axis gate, latency-as-DR-dim, state_std z-cond, etc.). Soft actionable -- every next-experiment/summary pass must enumerate these leads (omx wiki list --status needs-experiment) and carry or explicitly defer them, so the heavy-tail-flatten drop cannot recur.

---

## Update (2026-07-15T04:54:42.574431)

## Update (2026-07-15): two leads dispositioned + a NEW lead surfaced

- **Eval command-box extension (Priority 1): DONE** this session (commit 8c07584 — ATT_AMP 15->30 deg, YAW_RATE 0.25->0.5; eval box now matches trained +-30 deg box). Lead closed.
- **performance_lb recalibration (Priority 2): DONE** via probe trpo_perflb200_260715_023744 (analysis diagnose-20260715-133249). Result: lowering performance_lb 250->200 UN-STALLS the curriculum (mode -2->0, success 0.407->0.712, ess 0.414->0.754, DR widens) — confirms the 'lb sits on baseline return, so any return-costly intervention stalls' diagnosis. **DECISION: adopt performance_lb=200 as the standing setting.** Lead closed.
- **NEW lead surfaced (was hidden behind the stall): exploration-machinery collapse.** The SAME probe proved the actor entropy/noise_std collapse (entropy ~-7.8, noise_std pinned near min_std=0.05 floor) is CAUSALLY INDEPENDENT of the DORAEMON gate — its trajectory is near-identical (max dev 0.18 entropy / 0.003 noise_std) whether the curriculum stalls or not. So neither performance_lb NOR the DORAEMON per-axis gate will fix exploration. The next exploration lever must target the actor noise/entropy machinery directly: min_std (0.05 floor), entropy_coef (0.003), or the noise parameterization / entropy schedule. See finding 'performance_lb (DORAEMON gate) is causally independent of the actor exploration collapse'.

STILL OPEN (unchanged): DORAEMON per-axis success-gate (max structural lever, blocked on marinelab/algorithms/doraemon.py engine code) — note it addresses per-axis DR WIDENING, NOT the exploration collapse above; latency-as-DR-dim (engine code); TAM/max_thrust DR band (design-first, needs-apply-before-retrain); thruster nonlinear curve (measure-first); hydro nominal anchoring (measure-first); state_std z-conditioned (parked); constraint inert-2 (low).
