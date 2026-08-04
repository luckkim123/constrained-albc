---
title: "X1 tail-split restores the gen-2 latent collapse but moves NO control metric: latent reconstruction and closed-loop dispersion are decoupled"
tags: ["obs4", "student", "latent", "delivery", "distillation"]
created: 2026-08-04T06:37:32.467729
updated: 2026-08-04T06:37:32.467729
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: resolved
---

# X1 tail-split restores the gen-2 latent collapse but moves NO control metric: latent reconstruction and closed-loop dispersion are decoupled

X1-tailsplit (trpo_sdobs76_x1_tailsplit_s30_260804_151400) ran 2026-08-04 as the one-variable probe separating delivery path from teacher swap. Config parity verified: 40 recorded keys, exactly ONE differs from Phase E (extra_obs_from_policy_tail=True) plus run_name. Bite check done on the REAL obs76 teacher normalizer (not the synthetic unit-test one): tail channels mean=(-0.035,-0.024,9.032,0.690) std=(2.656,2.563,0.797,0.332) vs static scale (10,10,10,1), so z-score vs static-scale differ by 3.8x / 12.5x / 3.0x with a 0.90 DC offset left on the gravity-dominated accel-z channel. The injection bites.

RESULT (eval static_260804_152454, PAIRED with Phase E static_260804_145821 - 24/24 dr/fault keys identical at all 4 levels after the per-level reseed fix 9eac3a8):

Latent, aggregate R2 = 1 - sumMSE/sumVar (mandatory decomposition quoted):
  hard   X1 sumMSE 0.5544 sumVar 0.5927 R2 +0.0645  |  PhaseE 0.6367 / 0.5766 / -0.1044  -> delta +0.169
  medium X1 0.2550 / 0.3124 / +0.1838            |  PhaseE 0.3576 / 0.3160 / -0.1315
  soft   X1 0.1804 / 0.1723 / -0.0466            |  PhaseE 0.3426 / 0.1763 / -0.9436
  none   (excluded per pre-registration, degenerate denominator)
The pre-registered H2 threshold was delta > 2*sigma_diff = 0.107 at hard. Measured +0.169 CLEARS it, and hard sumMSE fell into the predicted 0.50-0.55 band at comparable sumVar (+2.8%). H2 (delivery path) CONFIRMED on the latent endpoint.

Control, paired, registered floors (ss_error 0.10 deg, ss_error_std 0.60 deg, survival 1.6 pp, n_gt20 15 envs):
  EVERY X1-vs-PhaseE control delta is BELOW FLOOR at every level. hard att ss_error +0.020, roll +0.015; hard att ss_error_std +0.309, roll +0.250; survival +1.562 pp (one env, below the 1.6 pp floor by design).

THE FINDING: the intervention that most improved latent reconstruction in this campaigns history (hard R2 -0.104 -> +0.065; none -1.799 -> +0.013) produced ZERO decision-grade control change, and its dispersion drifted the WRONG way (hard roll ss_error_std 2.880 -> 3.130 absolute). Latent-reconstruction quality and closed-loop control quality are DECOUPLED on this axis. Any future argument of the form "improve the students latent tracking and control will follow" now has a direct counterexample and needs its own evidence.

Survival endpoint reads the other way from R2: X1 lands at 1 death of 64 at hard, exactly matching its own obs76 teacher (also 1), while Phase E had 2. Per the pre-registrations own mapping this is the H1 (teacher lineage) side - but the +1.562 pp gain is below the registered floor, so it is directional context, not decision-grade.

VERDICT: MIXED per pre-registration - delivery path owns the latent collapse (H2), teacher lineage owns the death behaviour (H1), and NEITHER owns a control improvement. Adopt tail-split for any future gen-2 student (it is strictly better on latent at no control cost), but it does not make the obs76 line the better product.
