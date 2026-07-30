---
title: "Fault-DR training reduces m4-dead attitude degradation by 4-12x versus the ancho"
tags: ["auto-captured"]
created: 2026-07-27T05:49:10.587769
updated: 2026-07-30T03:49:47.548469
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md"]
links: []
category: session-log
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Fault-DR training reduces m4-dead attitude degradation by 4-12x versus the ancho

Fault-DR training reduces m4-dead attitude degradation by 4-12x versus the anchor and eliminates the fault-induced terminations entirely, with `soft` the one level where the anchor was already benign so the improvement there is only 1.2-2.5x.

[EVIDENCE: summary.json paired healthy/dead — att_norm delta anchor 1.805 / 0.282 / 1.818 / 3.472 vs Arm A 0.285 / 0.241 / 0.251 / 0.432 and Arm B 0.148 / 0.113 / 0.149 / 0.669 (none/soft/medium/hard); yaw `ss_error` delta anchor 0.092-0.168 rad/s (18-34% of the 0.5 rad/s command) vs both arms 0.019-0.030 rad/s (4-6%); survival anchor -6.25 / 0.00 / -4.69 / -7.81 pp vs both arms 0.00 pp at all four levels]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-30T03:49:47.548469)

[CORRECTION 2026-07-30 -- THIS PAGE'S HEADLINE NUMBER IS WRONG. The correct range is
5-12x, not 4-12x.] Written here rather than only in the survivor because this page is
queued to be folded into
fault_dr_training_reduces_m4_dead_attitude_degradation_by_5_12x_.md, and the omx merge
appends source bodies verbatim -- so without this note the wrong figure would travel
into the survivor unchallenged.

Independently recomputed from the six eval summary.json files (anchor
trpo_buoyanchor_s30_260722_134743, Arm A trpo_faultdr_agnostic_s30_260725_183121, Arm B
trpo_faultdr_priv_s30_260725_232149; healthy vs m4-dead static evals). Delta =
dead att_norm ss_error minus healthy, then ratio anchor/arm per DR level, with soft
excluded exactly as the source report carves it out (soft is the anchor-already-benign
case, separately 1.2-2.5x):
  none    anchor/ArmA 6.329   anchor/ArmB 12.217
  medium  anchor/ArmA 7.245   anchor/ArmB 12.170
  hard    anchor/ArmA 8.033   anchor/ArmB  5.192
Min 5.192, max 12.217. NO ratio anywhere in the data lies between 4 and 5, so 4-12x has
no basis in the numbers.

PROVENANCE OF THE ERROR (not a recompute, no data changed): three same-day reports on
one run pair. diagnose-20260727-132857 said 5-12x; diagnose-20260727-134730 rewrote it
and introduced 4-12x; diagnose-20260727-140324 is a direct edit of that draft -- its
heading still reads diagnose-20260727-134730 -- and silently changed 4-12x back to
5-12x without listing the fix in its own revision note. The [EVIDENCE] blocks of both
wiki pages are byte-identical, so this is a mis-transcribed range in one intermediate
write-up, not a legitimately changed measurement.

The ratio is unit-invariant (same field divided by itself), so the deg-vs-percent label
trap does not affect this figure either way.

