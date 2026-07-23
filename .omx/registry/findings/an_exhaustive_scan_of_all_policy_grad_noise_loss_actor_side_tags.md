---
title: "An exhaustive scan of all Policy/Grad/Noise/Loss actor-side tags common to both "
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-23T02:21:27.244561
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# An exhaustive scan of all Policy/Grad/Noise/Loss actor-side tags common to both 

An exhaustive scan of all Policy/Grad/Noise/Loss actor-side tags common to both runs puts `Policy/surrogate_loss` as the largest RELATIVE move (-100.1%, -0.2005 vs -0.1002), NOT clip_fraction; both, however, ride near-zero bases, so neither is a regime change -- the surrogate objective is twice as negative but at |0.20|, and clip_fraction rose to 0.0087 (far below A4's 0.0151 saturation). | actor-side tag         | A5      | anchor  | delta%  | |------------------------|---------|---------|---------| | Policy/surrogate_loss  | -0.2005 | -0.1002 | -100.1% | | Grad/sigma_dir         | -0.0001 | -0.0001 | +20.2%  | | Policy/clip_fraction   | 0.0087  | 0.0078  | +12.6%  | | Grad/actor_step        | 0.0145  | 0.0157  | -7.3%   |

[EVIDENCE: TB last-200-iter means, exhaustive rank over all common Policy/Grad/Noise/Loss tags by |delta%|]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

An exhaustive scan of all Policy/Grad/Noise/Loss actor-side tags common to both runs puts `Policy/surrogate_loss` as the largest RELATIVE move (-100.1%, -0.2005 vs -0.1002), NOT clip_fraction; both, however, ride near-zero bases, so neither is a regime change -- the surrogate objective is twice as negative but at |0.20|, and clip_fraction rose to 0.0087 (far below A4's 0.0151 saturation). | actor-side tag         | A5      | anchor  | delta%  | |------------------------|---------|---------|---------| | Policy/surrogate_loss  | -0.2005 | -0.1002 | -100.1% | | Grad/sigma_dir         | -0.0001 | -0.0001 | +20.2%  | | Policy/clip_fraction   | 0.0087  | 0.0078  | +12.6%  | | Grad/actor_step        | 0.0145  | 0.0157  | -7.3%   |

[EVIDENCE: TB last-200-iter means, exhaustive rank over all common Policy/Grad/Noise/Loss tags by |delta%|]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
