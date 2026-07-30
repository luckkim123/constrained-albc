---
title: "TRPO optimizer health carries the in-family signature unchanged: Policy/entropy "
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-30T03:54:24.726456
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# TRPO optimizer health carries the in-family signature unchanged: Policy/entropy 

TRPO optimizer health carries the in-family signature unchanged: Policy/entropy -8.76 vs -8.95 (collapsed in both — the known family-wide trait, not run-specific), Policy/mean_noise_std 0.0914 vs 0.0881, Policy/line_search_success 1.00 vs 1.00, Loss/kl 0.00503 vs 0.00496 (vs max_kl 0.005 config), Policy/surrogate_loss -0.1034 vs -0.1025, Grad/actor_step 0.0171 vs 0.0229, Grad/sigma_step 0.00064 vs 0.00084.

[EVIDENCE: tb_final.py final-window means, tags Policy/entropy Policy/mean_noise_std Policy/line_search_success Loss/kl Policy/surrogate_loss Grad/actor_step Grad/sigma_step, both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

TRPO optimizer health carries the in-family signature unchanged: Policy/entropy -8.76 vs -8.95 (collapsed in both — the known family-wide trait, not run-specific), Policy/mean_noise_std 0.0914 vs 0.0881, Policy/line_search_success 1.00 vs 1.00, Loss/kl 0.00503 vs 0.00496 (vs max_kl 0.005 config), Policy/surrogate_loss -0.1034 vs -0.1025, Grad/actor_step 0.0171 vs 0.0229, Grad/sigma_step 0.00064 vs 0.00084.

[EVIDENCE: tb_final.py final-window means, tags Policy/entropy Policy/mean_noise_std Policy/line_search_success Loss/kl Policy/surrogate_loss Grad/actor_step Grad/sigma_step, both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

TRPO optimizer health carries the in-family signature unchanged: Policy/entropy -8.76 vs -8.95 (collapsed in both — the known family-wide trait, not run-specific), Policy/mean_noise_std 0.0914 vs 0.0881, Policy/line_search_success 1.00 vs 1.00, Loss/kl 0.00503 vs 0.00496 (vs max_kl 0.005 config), Policy/surrogate_loss -0.1034 vs -0.1025, Grad/actor_step 0.0171 vs 0.0229, Grad/sigma_step 0.00064 vs 0.00084.

[EVIDENCE: tb_final.py final-window means, tags Policy/entropy Policy/mean_noise_std Policy/line_search_success Loss/kl Policy/surrogate_loss Grad/actor_step Grad/sigma_step, both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md

---

## Merged from trpo_health_carries_the_in_family_signature_unchanged_by_the_ban.md (2026-07-30T03:54:24.726456)

# TRPO health carries the in-family signature, unchanged by the band: entropy COLL

TRPO health carries the in-family signature, unchanged by the band: entropy COLLAPSED and noise_std at the floor in BOTH runs, line_search_success 1.00, kl at its 0.01 cap — the known Z1/A2 family behaviour, not a B0c effect. | metric | anchor | B0c | |---|---|---| | entropy | -8.93 (COLLAPSED) | -8.80 (COLLAPSED) | | noise_std | 0.09 (LOW) | 0.09 (LOW) | | line_search_success | 1.00 | 1.00 | | kl | 0.01 | 0.01 |

[EVIDENCE: engine TIER 1 Core Health, both runs; wiki april_2026_entropy_collapse (Z1) and the A2 entcoefzero verdict]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

TRPO health carries the in-family signature, unchanged by the band: entropy COLLAPSED and noise_std at the floor in BOTH runs, line_search_success 1.00, kl at its 0.01 cap — the known Z1/A2 family behaviour, not a B0c effect. | metric | anchor | B0c | |---|---|---| | entropy | -8.93 (COLLAPSED) | -8.80 (COLLAPSED) | | noise_std | 0.09 (LOW) | 0.09 (LOW) | | line_search_success | 1.00 | 1.00 | | kl | 0.01 | 0.01 |

[EVIDENCE: engine TIER 1 Core Health, both runs; wiki april_2026_entropy_collapse (Z1) and the A2 entcoefzero verdict]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
