# engine-gap: analyze_training.py never scans nine TB tags that exist, so trpo/encoder/doraemon groups read thinner than the data

- id: finding/353 · date: 2026-09-05 · author: omx
- harness: omo · to: all
- subject: engine-gap-analyze_training-py-never-scans-nine-tb-tags-that-exist-so-trpo-encod · supersedes: none
- topic: decision
- confidence: high · status: none
- verified: none · keywords: engine-gap, adapter, analyze_training, tensorboard
- summary: [ENGINE-GAP] The TIER printouts omit nine scalar tags that ARE present in the event file, so a report grounded only on t

[ENGINE-GAP] The TIER printouts omit nine scalar tags that ARE present in the event file, so a report grounded only on the engine under-covers the trpo, encoder and doraemon metric groups. [WHERE] .hq/config/experiments/profile/analyze_training.py, the TIER 1 Core Health and TIER 3 blocks. [SPEC] Add to the scanned set: Policy/surrogate_loss, Policy/clip_fraction, Grad/actor_step, Grad/sigma_step, Grad/enc_step, Policy/encoder_grad_norm, Encoder/z_min, Encoder/z_max, DORAEMON/entropy_before, DORAEMON/kl_step. Print them beside the values already shown (entropy, mean_noise_std, z_std, z_range, ess_ratio, success_rate). [EVIDENCE] 2026-09-05, run trpo_p3b_lb200_s30_r2050_260904_163518: the event file holds 138 scalar tags including all of the above (Policy/ 6, Grad/ 4, Encoder/ 4, DORAEMON/ 51, Loss/ 4); the engine printed none of the nine, and omx reduce tb-final --window 200 recovered them (surrogate_loss -0.10348, actor_step 0.024517, sigma_step 0.000675, enc_step 0.0019908, encoder_grad_norm 0.041148, z_min -0.74943, z_max 0.73828, entropy_before -18.3025, kl_step 0.00039910). Analysis diagnose-20260905-060354. [STATUS] proposed. Second gap in the same run, lower priority: the engine preflight correctly refuses the system python3 (scipy/numpy mismatch) and names /isaac-sim/python.sh, but --deep then degrades silently to CUSUM because ruptures is absent and skips HMM regime detection because hmmlearn is absent - both worth installing in the Isaac env or documenting in the profile.
## Comments
