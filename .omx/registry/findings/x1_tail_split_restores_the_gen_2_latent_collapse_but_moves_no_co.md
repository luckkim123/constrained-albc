---
title: "X1 tail-split restores the gen-2 latent collapse but moves NO control metric: latent reconstruction and closed-loop dispersion are decoupled"
tags: ["obs4", "student", "latent", "delivery", "distillation"]
created: 2026-08-04T06:37:32.467729
updated: 2026-08-04T09:36:41.244318
sources: []
links: ["feedback_derive_a_metrics_healthy_target.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
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

---

## Update (2026-08-04T06:43:29.103612)

SELF-CORRECTION, same day (2026-08-04), before this page was used for anything. The DECOUPLED framing above is WRONG and is retracted. The numbers stand; the interpretation does not.

The error was reading a delta in R2 as if it were a delta in latent error. Decomposing X1 vs Phase E at hard:
  - dR2 = +0.1689, of which 85% is genuine numerator (error) reduction and 15% is denominator drift (sumVar 0.5766 -> 0.5927).
  - The same change expressed in the units that couple to control is a 6.69% reduction in latent RMSE (sqrt(0.5544/0.6367) = 0.9331). R2 sits near zero here, so a modest error change swings the ratio a long way; the ratio exaggerates the practical size of the improvement.

Now price that against the campaigns OWN measured exchange rate (C1-latsens, probe next-20260729-180058, wiki the_frozen_actor_s_sensitivity_to_latent_error_is_strongly_level): at hard, injecting k=0.5 (half the students existing per-dim latent RMSE, in its own shape) moved att_norm ss_error 0.6496 -> 1.0728, i.e. +0.4232 deg. Scaling linearly in the small-perturbation regime, a 6.69%-equivalent move is worth about 0.057 deg.

The decision floor is 0.10 deg. So a sub-floor control result is EXACTLY what the measured coupling predicts for a latent improvement this size. The null is expected and carries NO information about whether latent quality drives control - it is not a counterexample to the coupling, it is consistent with it. Calling it decoupling inverted the meaning of the campaigns own sensitivity measurement.

WHAT ACTUALLY HOLDS:
1. Delivery path owns the gen-2 latent collapse (H2 confirmed) - unchanged, the R2/sumMSE evidence is untouched by this correction.
2. The control null is uninformative, not evidence against the latent lever. To clear the 0.10 deg floor at hard you need roughly a 12% latent-RMSE reduction, and appreciably more to be worth an arm; X1 delivered 6.7%.
3. The program decision is UNCHANGED - the obs76 line still shows no measurable better student - but it rests on the teacher-advantage-does-not-distill evidence and on X1 vs C3 being a trade (-0.118 deg hard mean REAL against +0.604 deg hard roll dispersion REAL), NOT on any decoupling claim.
4. Reporting rule this earns: never state a latent result as an R2 delta alone. Convert to RMSE and price it through the measured deg-per-unit sensitivity at that DR level BEFORE claiming a control implication either way. See [[feedback-derive-a-metrics-healthy-target]] for the sibling trap on the same metric.

---

## Update (2026-08-04T09:36:41.244318)

CAVEAT on the correction above (added 2026-08-04 after cross-checking the campaign owners independent report diagnose-20260804-154122, whose verdict matches this one). The 0.057 deg figure is a MED-confidence estimate, not a measurement, and must never be quoted as one:
  - C1-latsens measured a NONLINEAR curve whose smallest point is k=0.5; pricing a 6.69% move is a roughly 7x extrapolation below anything measured.
  - It was measured on a DIFFERENT arm (A0g), not on this teacher or this student.
  - An injected random perturbation of the latent is not the same object as a structured reduction in reconstruction error; the sensitivity to one need not equal the sensitivity to the other.
The load-bearing claim survives all three - the predicted effect is far enough under the 0.10 deg floor that no plausible correction lifts it above - but the correct sentence is "this null is uninformative", not "the expected gain was 0.057 deg".

MECHANISM (from the owners report, and it strengthens the H2 verdict): the improvement is covariate shift, NOT fitting capacity. X1s TRAINING-side latent loss is 4.3% WORSE than the baselines (0.004236 vs 0.004062) while its CLOSED-LOOP latent error is 12.9% better, and the train-to-in-loop gap narrows at every level (9.7x -> 3.2x at none, 17.4x -> 14.5x at hard). Folding the four channels into policy_obs subjects them to the teachers FROZEN normalizer statistics, so the further the closed-loop distribution drifts from the one those statistics were fitted on, the more the channels misrepresent themselves. Tail-split removes that dependence. The gap narrows but does NOT close at hard, so covariate shift remains open as a campaign-level problem.

INSTRUMENT NOISE bound, also from that report: re-evaluating the SAME checkpoint under two builds moves hard aggregate latent R2 by 0.0266 and none by 0.2190. The +0.169 hard result clears its own instrument noise by ~6x; any none-level aggregate claim is inside the noise and must not be made.
