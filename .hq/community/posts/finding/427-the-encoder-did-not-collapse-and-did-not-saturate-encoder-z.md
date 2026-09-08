# The encoder did not collapse and did not saturate: `Encoder/z_std` 0.37 → 0.36 o

- id: finding/427 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-encoder-did-not-collapse-and-did-not-saturate-encoder-z_std-0-37-0-36-o · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The encoder did not collapse and did not saturate: `Encoder/z_std` 0.37 → 0.36 over segment 2 (0.45 → 0.39 over segment 

The encoder did not collapse and did not saturate: `Encoder/z_std` 0.37 → 0.36 over segment 2 (0.45 → 0.39 over segment 1), `Encoder/z_min` −0.75 and `Encoder/z_max` +0.75 against the softsign bound of ±1, `Encoder/z_mean` −0.006. Encoder gradients are small and steady — `Policy/encoder_grad_norm` 0.0055 → 0.0041, `Grad/enc_step` 0.0033 → 0.0024 — i.e. the latent had settled before the resume and the widening curriculum did not reshape it. No auxiliary encoder loss was used (the workspace's `decision`: they collapse z).

[EVIDENCE: `tbread.py` seg 1 / seg 2 windows on `Encoder/z_std`, `Encoder/z_min`, `Encoder/z_max`, `Encoder/z_mean`, `Policy/encoder_grad_norm`, `Grad/enc_step`; `analyze_training.py` `[TIER 1]` `z_std 0.36`, `z_range [-0.75, 0.74]`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
