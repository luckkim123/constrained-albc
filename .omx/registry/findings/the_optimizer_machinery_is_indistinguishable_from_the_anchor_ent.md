---
title: "The optimizer MACHINERY is indistinguishable from the anchor — entropy, sigma, f"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-23T07:42:43.865902
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# The optimizer MACHINERY is indistinguishable from the anchor — entropy, sigma, f

The optimizer MACHINERY is indistinguishable from the anchor — entropy, sigma, floor, line-search success, KL and step sizes all match within ~2.2%, so no part of the failure is an optimisation artifact.

[EVIDENCE: TB last-200-iter means for Policy/entropy, mean_noise_std, Noise/std_min, line_search_success, Loss/kl, Grad/actor_step, Grad/sigma_step]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md

---

## Update (2026-07-22T01:58:11.799085)

The optimizer machinery is indistinguishable from the anchor: entropy, sigma floor, KL, step sizes and line-search success all match within seed-scale, so the run is a clean optimisation with no artifact. | tag                  | A5      | anchor  | delta% | |----------------------|---------|---------|--------| | Policy/entropy       | -8.8081 | -9.0644 | +2.8%  | | Policy/mean_noise_std| 0.0905  | 0.0861  | +5.1%  | | Noise/std_min        | 0.0500  | 0.0500  | 0.0%   | | Loss/kl              | 0.0050  | 0.0050  | -0.3%  | | Grad/actor_step      | 0.0145  | 0.0157  | -7.3%  | | Grad/sigma_step      | 0.0005  | 0.0005  | -6.6%  | | line_search_success  | 1.0000  | 1.0000  | 0.0%   |

[EVIDENCE: TB last-200-iter means]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

The optimizer machinery is indistinguishable from the anchor: entropy, sigma floor, KL, step sizes and line-search success all match within seed-scale, so the run is a clean optimisation with no artifact. | tag                  | A5      | anchor  | delta% | |----------------------|---------|---------|--------| | Policy/entropy       | -8.8081 | -9.0644 | +2.8%  | | Policy/mean_noise_std| 0.0905  | 0.0861  | +5.1%  | | Noise/std_min        | 0.0500  | 0.0500  | 0.0%   | | Loss/kl              | 0.0050  | 0.0050  | -0.3%  | | Grad/actor_step      | 0.0145  | 0.0157  | -7.3%  | | Grad/sigma_step      | 0.0005  | 0.0005  | -6.6%  | | line_search_success  | 1.0000  | 1.0000  | 0.0%   |

[EVIDENCE: TB last-200-iter means]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T07:42:43.865902)

2026-07-23 curation: attempted recategorize session-log -> pattern (durable negative-control claim: optimizer machinery -- entropy, sigma, KL, step-size, line-search -- is clean and indistinguishable across all posttam ablation arms A4 and A5; never the failure mechanism). Recurs across 2 independent runs, no existing pattern page covers it.
