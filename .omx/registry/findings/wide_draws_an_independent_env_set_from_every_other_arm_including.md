---
title: "WIDE draws an independent env set from every other arm, including B2 whose recip"
tags: ["auto-captured", "trpo_sdeint_b2wide_gru256_s30_260803_231320"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:16:03.279468
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# WIDE draws an independent env set from every other arm, including B2 whose recip

WIDE draws an independent env set from every other arm, including B2 whose recipe it shares except for the hidden width, so the difference sd 0.0533 applies rather than any paired estimate.

[EVIDENCE: `dr_*` arrays across the four `data_hard.npz` files; `gru_hidden` changes the parameter count and therefore the torch RNG stream, which is why an arm that touches no env cfg still desynchronises the env draws]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-03T15:16:03.279468)

WIDE draws an independent env set from every other arm, including B2 whose recipe it shares except for the hidden width, so the difference sd 0.0533 applies rather than any paired estimate.

[EVIDENCE: `dr_*` arrays across the four `data_hard.npz` files; `gru_hidden` changes the parameter count and therefore the torch RNG stream, which is why an arm that touches no env cfg still desynchronises the env draws]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
