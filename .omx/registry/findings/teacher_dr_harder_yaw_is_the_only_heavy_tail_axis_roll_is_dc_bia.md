---
title: "teacher dr_harder: yaw is the ONLY heavy-tail axis, roll is DC-bias"
tags: ["teacher", "yaw", "roll", "heavy-tail", "eval_dr"]
created: 2026-06-06T09:44:04.865862
updated: 2026-06-07T17:15:00.000000
sources: ["diagnose-20260606-183657", "diagnose-20260606-194621"]
links: ["teacher_hard_dr_cv_explodes_without_heavy_tail_dc_bias_dispersio.md", "constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md"]
category: pattern
confidence: high
schemaVersion: 1
---

# teacher dr_harder: yaw is the ONLY heavy-tail axis, roll is DC-bias

Teacher baseline (trpo_main_teacher_260525_232805) eval_dr static, 64 env, verified from heavy_tail.json pct_peak_gt_thresh: roll and pitch have ZERO heavy-tail at EVERY DR level (0.00% env peak>20deg). The ONLY heavy-tailed axis is YAW: soft 4.69% / medium 18.75% / hard 14.06% of envs over threshold. CORRECTS an earlier note that attributed medium/hard heavy-tail to roll -- it is yaw. Roll has the largest absolute ss_error (1.10deg at hard, CV 265%) but peak_max=11.36deg (under the 20deg bound) => its high CV is DC-bias env-dispersion, NOT a tail. Mechanism for yaw tail: yaw SS jitter (std) climbs 12x from ~0.0001 (none) to 0.0012 rad/s (hard) -- AC oscillation, not DC error, pushes worst envs over threshold (summary_yaw.png SS Jitter panel). Survival 100% all levels all axes, so yaw tail is an accuracy/oscillation issue not a stability one. Training-side: both yaw constraints satisfied with 0 violation, so the yaw eval weakness is NOT a training constraint violation. CORRECTION (2026-06-07): an earlier version of this note read yaw_rate ABSOLUTE margin=8.62 as "largest of 10 = most slack" and cumul_yaw margin=1.00 -- that is the un-normalized-margin trap. Normalized by budget (J_C/d_k, d_k=budget*100), yaw_rate is MID at 0.138 and cumul_yaw is fully INERT at 0.000; the absolute 8.62 just reflects yaw_rate's larger budget (d_k=10), not more headroom. Either way both hold 0 violation, so the conclusion (yaw weakness != constraint violation) stands. See [[constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli]] for why absolute margin must never be read directly. cf [[teacher_hard_dr_cv_explodes_without_heavy_tail_dc_bias_dispersio]].
