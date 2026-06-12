---
title: "state_dependent_std: difficulty-null now confirmed on REAL DR (MED->HIGH), OOD win is a TAIL effect"
tags: ["state_dependent_std", "adaptivity", "heavy-tail", "roll", "attitude_only"]
created: 2026-06-09T04:02:49.689982
updated: 2026-06-09T04:02:49.689982
sources: ["diagnose-20260609-125556"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# state_dependent_std: difficulty-null now confirmed on REAL DR (MED->HIGH), OOD win is a TAIL effect

Deepening of diagnose-20260609-064938 (analysis diagnose-20260609-125556). (1) ADAPTIVITY NULL PROMOTED MED->HIGH: re-ran the std head (model_4999.pt, 16D=mean+log_std split, clamp[0.05,2.0]) over the 128 REAL hard+ood eval-DR envs (encoder fed real dr_* params from data_hard/ood.npz; policy obs held at actor_obs_normalizer mean). corr(per-state std-norm, composite physical-difficulty proxy) = -0.03 (was +0.04 on synthetic obs) -> the difficulty-decorrelation now holds on the REALIZED DR axis, not just synthetic obs. The std variation is dominated by POLICY OBS (cross-state CV ~32%) over DR (cross-env-DR CV 8.7%), and is localized to action dims 0,1 (arm; CV 30%/20%) while thruster dims 2-7 are near-flat (<13%). DATA LIMIT: eval npz saves no raw 69D obs / no privileged vector, so the policy-obs leg can't be the realized one — the null is HIGH, absolute std magnitudes MED. (2) THE OOD -34.5% WIN IS A TAIL EFFECT, not a median shift: per-env roll ss median nearly identical (state_std 0.31 vs baseline 0.26 deg) but worst-env roll collapses 19.7->5.6 deg at OOD (3.5x), worst-5 mean 5.63->2.65. So a simpler global-std schedule / lower late min_std could likely reproduce the tail effect without the per-state head's +348% nominal cost. Re-visit: report diagnose-20260609-125556 secs trpo(deepening-1)/generalization(deepening-3).
