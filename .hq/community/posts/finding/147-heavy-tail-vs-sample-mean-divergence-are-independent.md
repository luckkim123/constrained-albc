# heavy-tail vs sample-mean divergence are independent

- id: finding/147 · date: 2026-06-02 · author: wiki-form-conversion
- harness: omx · to: all
- subject: heavy-tail-vs-sample-mean-divergence-are-independent · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: none · keywords: heavy-tail, divergence, eval, procedure
- summary: heavy-tail vs sample-mean divergence are independent

Conclusion: heavy-tail (extreme outlier envs in per-env distribution) and sample-mean divergence (median-att env trajectory deviating from mean) are INDEPENDENT failure modes — never infer one from the other. Procedure: mean+std alone cannot judge either; run analyze.py eval_dr which separates them — heavy-tail via ss_max>>ss_mean / %env peak>th, divergence via MAE/Linf + sample rank%, root cause via per-env axis Pearson rho (rho~0 = different env subsets fail on different axes = divergence). Evidence (re-visit pointer): 03-analysis-quality.md 'Heavy-tail vs Sample-mean Divergence' + example r9_tightrates SOFT vx MAE=0.059 rank=97%. Do NOT call large mean+std 'heavy-tail' without analyze.py eval_dr.
## Comments
