---
title: "Every 5000-iteration teacher on the buoyfix plant stops at ~65 percent of its DR curriculum, so the declared DR box is NOT the box it trained against"
tags: ["doraemon", "curriculum", "saturation", "dr-box", "fault_severity", "ocean_current", "obs_noise", "teacher", "e-int", "dgx", "beta", "kl_budget"]
created: 2026-08-04T21:38:53.586268
updated: 2026-08-04T21:38:53.586268
sources: ["trpo_iterbudget_s30_260805_012813", "trpo_eint_s30_rs2350_260727_195102", "doraemon_state.pt"]
links: ["curriculum_recalibration_protocol_widening_the_dr_box_requires_r.md", "doraemon_is_trust_region_limited_not_feasibility_limited_kl_step.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Every 5000-iteration teacher on the buoyfix plant stops at ~65 percent of its DR curriculum, so the declared DR box is NOT the box it trained against

# Every 5000-iteration teacher on the buoyfix plant stops at ~65 percent of its DR curriculum, so the declared DR box is NOT the box it trained against

Measured 2026-08-05 from `doraemon_state.pt` directly (dist_a/dist_b), not inferred from a metric.

E-int (`trpo_eint_s30_rs2350_260727_195102`) is the shipped teacher, the DGX flagship's baseline, and
the source policy for every student in `student_distill_eint`. At its final iteration 5000 it had
**0 of 21 DORAEMON dims at Beta(1,1)** and had spent **2.2800** of the **3.5209** total KL budget its
own box requires -- 65 %. The box reaches Beta(1,1) on all 21 dims only at **iteration 7748**,
measured by resuming that exact checkpoint to 9998 (`trpo_iterbudget_s30_260805_012813`).

The four dims whose nominal is 0 -- the curriculum starts them "off" and expands outward -- were the
least expanded. For Beta(1, b) the mean is 1/(1+b):

| dim | Beta at iteration 5000 | mean, as a fraction of declared range |
|:--|:--|:--|
| payload_cog_offset_xy_u | (1.000, 7.288) | 0.121 |
| ocean_current_strength | (1.000, 7.670) | 0.115 |
| obs_noise_scale | (1.000, 7.918) | 0.112 |
| fault_severity | (1.000, 10.099) | 0.090 |

The other 17 dims sat near Beta(2.2, 2.2) -- symmetric and unimodal, well short of uniform.

## What this does and does not invalidate

**It does NOT invalidate teacher-vs-teacher comparisons at 5000 iterations.** Every such run stops at
about the same budget fraction, so the arms saw comparable exams and the relative verdicts stand.

**It DOES mean the absolute difficulty was lower than the config declares.** A run launched with
`fault.enable=True` experienced a mean fault severity of about 9 % of the declared range, not a
uniform draw over it. Any statement of the form "the teacher is robust to the declared DR box" is
unsupported at 5000 iterations -- it is robust to a partially expanded subset of it. This matters
most for the fault, ocean-current, and observation-noise claims, which are exactly the four dims
least expanded.

**It changes what a longer run buys.** Below saturation, `max_iterations` is a DR-WIDTH treatment,
not extra optimization; above it, the reverse. The 20000-iteration DGX flagship is the first run on
this plant that trains against the fully expanded box at all, and it spends about 12250 of its
iterations there.

## How to check any run in one command

Read the run's own `doraemon_state.pt` and count dims at Beta(1,1). Do not infer saturation from
`DORAEMON/entropy_before` alone, and do not infer it from a quiet `DORAEMON/kl_step` stretch: that
tag is written as 0.0 on every non-boundary iteration, and on a resumed chain the boundary phase
shifts by one iteration per resume (250-multiples, then ...499, then ...248), so a fixed-stride
sample reads 0 everywhere. Scan all steps for `kl_step > 0`, and treat a silent stretch as
saturation only once a whole `step_interval` boundary has been missed.

Protocol and budget arithmetic:
[[curriculum_recalibration_protocol_widening_the_dr_box_requires_r]].
Why the trust region rather than feasibility paces this:
[[doraemon_is_trust_region_limited_not_feasibility_limited_kl_step]].

