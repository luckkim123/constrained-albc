---
title: "The row-1 leak is quantifiable and does not change the verdict: A1's terminal wi"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The row-1 leak is quantifiable and does not change the verdict: A1's terminal wi

The row-1 leak is quantifiable and does not change the verdict: A1's terminal width sits 0.66 nats wider than the 5k reference and 3.84 nats narrower than extend8k — about 15% of the 4.5-nat separation the H1/H2 discrimination rests on. Because the outcome landed OUTSIDE both poles (30.5% vs 17% / 25-27%), no plausible reading of that 15% moves it back into a pole. This is a size argument, not a calibrated conversion: no measured mapping from entropy-nats of width to percentage-points of overshoot exists, so the step from 'the leak is 15% of the separation' to 'the leak cannot flip the verdict' is an inference.

[EVIDENCE: terminal `DORAEMON/entropy_before` — A1 -22.043, ref5k -22.702, extend8k -18.201; achieved nonzero `kl_step` — A1 19, ref5k 18, extend8k 26]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md

---

## Update (2026-07-21T10:26:11.609658)

The row-1 leak is quantifiable and does not change the verdict: A1's terminal width sits 0.66 nats wider than the 5k reference and 3.84 nats narrower than extend8k — about 15% of the 4.5-nat separation the H1/H2 discrimination rests on. Because the outcome landed OUTSIDE both poles (30.5% vs 17% / 25-27%), no plausible reading of that 15% moves it back into a pole. This is a size argument, not a calibrated conversion: no measured mapping from entropy-nats of width to percentage-points of overshoot exists, so the step from 'the leak is 15% of the separation' to 'the leak cannot flip the verdict' is an inference.

[EVIDENCE: terminal `DORAEMON/entropy_before` — A1 -22.043, ref5k -22.702, extend8k -18.201; achieved nonzero `kl_step` — A1 19, ref5k 18, extend8k 26]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
