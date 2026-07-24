---
title: "roll transient is WORST at none DR and improves monotonically as DR hardens (inverted, both runs)"
tags: ["roll", "overshoot", "transient", "dr-scaling", "os_env_mean", "open-lead"]
created: 2026-07-21T07:58:14.787774
updated: 2026-07-23T19:18:40.914973
sources: ["diagnose-20260721-164331", "next-20260724-033159", "static_260724_040413", "static_260723_091813"]
links: ["eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# roll transient is WORST at none DR and improves monotonically as DR hardens (inverted, both runs)


[FINDING] Roll transient overshoot is INVERTED against DR level: it is WORST on the nominal
plant and improves monotonically as DR hardens. This holds in both runs compared on
2026-07-21, so it is a property of the policy family, not of any one intervention.

| DR level | A3 roll os_env_mean | anchor roll os_env_mean |
|---|---|---|
| none | 21.486 | 17.022 |
| soft | 17.699 | 15.645 |
| medium | 15.579 | 14.394 |
| hard | 14.730 | 14.172 |

[EVIDENCE: summary.json roll/os_env_mean, all four DR levels, trpo_minstdthr008_260721_064149
eval static_260721_113503 and trpo_biasema_260715_142543 eval static_260716_160156; analysis
diagnose-20260721-164331 §generalization]
[CONFIDENCE: HIGH]

[FINDING] This is counter-intuitive and currently UNEXPLAINED. The naive expectation is that a
harder plant produces a worse transient; the data says the opposite for roll specifically
(pitch os_env_mean is nearly flat across levels, 12.9 -> 10.3 for A3). Any mechanism proposed
must explain why the axis-specific inversion exists on roll and not pitch.
[EVIDENCE: same source, pitch os_env_mean none 12.873 / soft 11.858 / medium 11.114 / hard 10.304]
[CONFIDENCE: HIGH]

[FINDING] Candidate mechanisms NOT yet discriminated (this is the open work, not a conclusion):
(a) eval-protocol artifact — `eval.py static` grades each run on its own learned DR box, so the
`none` level may not be the "easiest" exam in the sense assumed (see
[[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]]);
(b) the policy is trained overwhelmingly on randomized plants and the nominal plant is
effectively an out-of-distribution corner of its own training distribution;
(c) a roll-specific coupling — roll/yaw per-env rho is strongly negative at `none` (-0.562 A3,
-0.947 anchor) and decays to ~0 at `hard`, so whatever couples the two axes is itself
DR-dependent.
[EVIDENCE: analyze.py eval_dr AXIS DECORRELATION blocks, roll_yaw column, all four levels, both
runs; analysis diagnose-20260721-164331 §heavy-tail]
[CONFIDENCE: MED]

STATUS: needs-experiment. No exploration-side lever addresses this — A3 raised sigma and made
the `none` transient WORSE, which is consistent with (b) but does not prove it. The cheapest
next probe is a zero-GPU one: check hypothesis (a) first by reading what DR box `eval.py static`
actually applies at the `none` level for these two checkpoints, before any training run is spent.

---

## Update (2026-07-23T07:42:45.252377)

2026-07-23 curation: status set to needs-experiment -- matches the body's STATUS line and open-lead tag, making this open lead queryable structurally via `omx wiki list --status needs-experiment`.

---

## Update (2026-07-23T19:18:40.914973)

[FINDING] E1/RT-a probe (proposal next-20260724-033159) RESOLVES exam-artifact hypothesis (a):
REJECTED. Re-evaluating the SAME anchor s30 checkpoint (model_4999) under the WIDEST legal exam
(--doraemon-dr-from trpo_biasema_extend8k_260716_162849, terminal DORAEMON = Beta(1,1) on all 20
params = full config box) did NOT lift any randomized level to >= the fixed none. The none-worst
inversion survives the widest exam, so it is NOT an artifact of each run grading itself on its own
lenient learned DR box.

| DR level | own-box roll os_env_mean (pp) | full-box roll os_env_mean (pp) | delta |
|---|---|---|---|
| none   | 13.545 | 13.217 | fixed physics; -0.33 = eval noise |
| soft   | 11.770 | 11.672 | -0.10 |
| medium | 12.201 | 11.355 | -0.85 |
| hard   | 11.872 | 12.979 | +1.11 |

[EVIDENCE: roll os_env_mean per level, own-box eval/static_260723_091813 vs shared-full-box
eval/static_260724_040413 of trpo_buoyanchor_s30_260722_134743, both 64 env cuda:1, code-exec read
2026-07-24]
[CONFIDENCE: HIGH]

[FINDING] Mechanism (b) nominal=OOD-corner is supported in DIRECTION but WEAK in magnitude, so the
lead is PARKED and no training is warranted. none stays the numerically worst level under the full
box, but the margin is only 0.24 pp over full-box hard (which rose +1.11 pp toward none, the only
level that moved materially) and 1.5-1.9 pp over soft/medium. The 0.24 pp none-vs-hard gap is INSIDE
the demonstrated eval noise: none itself moved 0.33 pp (os) and 14->12 (n_gt20) between two
fixed-physics runs, so none and full-box-hard are statistically indistinguishable. Robust none-worst
holds only vs soft/medium (~0.5 deg at 0.30 deg/pp). Below any defensible floor, so the H2-branch
training follow-up (a nominal-sampling DORAEMON floor) is DECLINED on magnitude; do not spend a run.

[EVIDENCE: same two summaries; none-level run-to-run wobble os 13.545->13.217, n_gt20 14->12,
us_env_mean 0.477->0.713, all at fixed nominal physics, so eval is not bit-reproducible (audit 11.2
determinism claim is too strong); pre-registered thresholds H1>=none and clean-H2 margin>=1.0 pp from
proposal next-20260724-033159]
[CONFIDENCE: HIGH]

STATUS: resolved (2026-07-24, E1/RT-a). Probe RAN; hypothesis (a) rejected, (b) real-but-sub-floor.
No training implication. Practical note for all future per-level roll readings: nominal (none) is a
real ~0.5 deg OOD-corner residual vs soft/medium, indistinguishable from full-box hard; treat
sub-1.0 pp per-level os differences as eval noise.

