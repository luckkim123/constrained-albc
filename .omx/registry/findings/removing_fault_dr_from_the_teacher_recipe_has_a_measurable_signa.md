---
title: "Removing fault-DR from the teacher recipe has a measurable signature on the HEALTHY eval too: better nominal steady state, much worse hard-DR tail, and a wider thruster_util margin"
tags: []
created: 2026-08-03T19:54:01.455891
updated: 2026-08-03T19:54:01.455891
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# Removing fault-DR from the teacher recipe has a measurable signature on the HEALTHY eval too: better nominal steady state, much worse hard-DR tail, and a wider thruster_util margin

## Measurement

An accidental A/B: obs4 Phase D attempt 1 trained the same recipe with `fault.enable: false`
while its baseline E-int trained with it `true`. Both were evaluated with `eval.py static`,
64 envs, `fault_injection=False` in both npz files -- so the EVAL plant is identical and only the
TRAINING plant differs. The obs width also differs (72 vs 76), so this is a signature to
recognise, not an isolated effect.

| quantity | E-int (fault-DR on) | attempt 1 (fault-DR off) |
|:--|--:|--:|
| att_norm `ss_error` none (deg) | 0.5246 | 0.4455 |
| att_norm `ss_error` hard (deg) | 0.7189 | 1.0201 |
| att_norm `ss_error_std` none (deg) | 0.1975 | 0.0551 |
| att_norm `ss_error_std` hard (deg) | 1.2791 | 2.7643 |
| none -> hard `ss_error` ratio | 1.37x | 2.29x |
| none -> hard `ss_error_std` ratio | 6.5x | 50.2x |
| `Constraint/margin/thruster_util` | 7.17 (JC/dk 0.821) | 8.51 (JC/dk 0.787) |
| `Loss/value_function` | 0.50622 | 0.35931 |
| `DORAEMON/success_rate` | 0.81044 | 0.91889 |

## Reading

The fault-free policy is BETTER at nominal and much worse at the DR corner. That is consistent
with the 2026-07-27 adoption record, which found fault-DR arms beat the fault-free anchor on
healthy att_norm ss_error and named heavy-tail removal as the mechanism -- here the healthy
hard-DR spread doubles without it.

The thruster_util margin is the cleanest corroborator and is mechanistic rather than statistical:
a policy that never loses a thruster does not have to over-drive the survivors, so it sits
further from its budget (margin 8.51 vs 7.17). The adoption page records the same effect in the
opposite direction ("Arm A's margin is HALVED because a fault-blind policy must over-drive the
survivors").

`DORAEMON/mean/fault_severity` still expanded to 11.3% of range with fault injection disabled,
because `albc_env.py:1652` gates the whole fault-sampling block on `cfg.fault.enable` while the
curriculum keeps widening the dimension regardless. A fault_severity curriculum that is
advancing is therefore NOT evidence that faults are being injected -- check `cfg.fault.enable`
in the recorded config.

Confidence is MEDIUM: single seed per side, and the obs-width difference is not controlled. The
controlled version is attempt 2 (`trpo_obs76fault_s30_260804_043926`).

