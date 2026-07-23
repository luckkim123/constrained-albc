---
title: "roll transient is WORST at none DR and improves monotonically as DR hardens (inverted, both runs)"
tags: ["roll", "overshoot", "transient", "dr-scaling", "os_env_mean", "open-lead"]
created: 2026-07-21T07:58:14.787774
updated: 2026-07-23T07:42:45.252377
sources: ["diagnose-20260721-164331"]
links: ["eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-experiment
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
