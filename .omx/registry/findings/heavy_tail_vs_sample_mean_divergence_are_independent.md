---
title: "heavy-tail vs sample-mean divergence are independent"
tags: ["heavy-tail", "divergence", "eval", "procedure"]
created: 2026-06-02T08:08:22.048876
updated: 2026-06-02T08:08:22.048876
sources: []
links: []
category: debugging
confidence: high
schemaVersion: 1
---

# heavy-tail vs sample-mean divergence are independent

Conclusion: heavy-tail (extreme outlier envs in per-env distribution) and sample-mean divergence (median-att env trajectory deviating from mean) are INDEPENDENT failure modes — never infer one from the other. Procedure: mean+std alone cannot judge either; run analyze.py eval_dr which separates them — heavy-tail via ss_max>>ss_mean / %env peak>th, divergence via MAE/Linf + sample rank%, root cause via per-env axis Pearson rho (rho~0 = different env subsets fail on different axes = divergence). Evidence (re-visit pointer): 03-analysis-quality.md 'Heavy-tail vs Sample-mean Divergence' + example r9_tightrates SOFT vx MAE=0.059 rank=97%. Do NOT call large mean+std 'heavy-tail' without analyze.py eval_dr.
