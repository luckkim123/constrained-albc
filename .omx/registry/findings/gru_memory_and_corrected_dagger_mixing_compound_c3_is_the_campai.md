---
title: "GRU memory and corrected DAgger mixing COMPOUND: C3 is the campaign's best latent tracker at every level and the first student to beat the teacher by a decision-grade margin"
tags: ["student", "distillation", "dagger", "gru", "albc", "compound", "teacher-comparison", "c3"]
created: 2026-07-29T11:46:10.396683
updated: 2026-08-03T05:50:03.314927
sources: ["diagnose-20260729-200134"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# GRU memory and corrected DAgger mixing COMPOUND: C3 is the campaign's best latent tracker at every level and the first student to beat the teacher by a decision-grade margin

Campaign `student_distill_eint` ran six arms before this one and adopted exactly one intervention per
axis: A0g's GRU encoder (the only arm to clear the control floor) and C2's corrected DAgger mixing
(policy SELECTION instead of action blending). C3 (`trpo_sdeint_c3_gruselect_s30_260729_193732`,
analysis diagnose-20260729-200134) combines them.

## They compound, they do not trade off

| in-loop latent MSE | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| A0 (TCN, beta 1) | 0.032975 | 0.030741 | 0.040636 | 0.068041 |
| A0g (GRU, beta 1) | 0.030400 | 0.025430 | 0.049167 | 0.074132 |
| C2 (TCN, select) | 0.031748 | 0.028085 | 0.041338 | 0.065192 |
| C3 (GRU, select) | 0.023550 | 0.016285 | 0.033686 | 0.060606 |

C3 is best at EVERY level (-22.5 / -36.0 / -31.5 / -18.2% against A0g). Each intervention beat its own
baseline alone, and the combination beats both. This was predicted from C2's per-axis split: C2 owned
roll, A0g owned pitch, so they were not redundant.

## First decision-grade student-over-teacher result in the campaign

| att_norm ss_error, deg (floor 0.1) | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| teacher E-int | 0.5246 | 0.4690 | 0.4662 | 0.7189 |
| A0g (adopted) | 0.5139 | 0.4510 | 0.5177 | 0.6496 |
| C3 | 0.5469 | 0.4618 | 0.5182 | 0.5652 |
| C3 - teacher | +0.0224 | -0.0072 | +0.0520 | -0.1537 |

The hard margin over the teacher, 0.1537 deg, clears the floor; A0g's was 0.0693 and did not. Both axes
carry it -- roll 0.4469 and pitch 0.2540 at hard are each campaign-lowest AND below the teacher's
0.5999 / 0.2803. Hard dispersion (att_norm CV 132.4%) and jitter (0.1877 deg) are also campaign-lowest
and better than the teacher's 177.9% / 0.2337. Survival 100% everywhere. Cheapest arm too, 0.0824 s/iter.

## But against the ADOPTED arm it is hard-only

C3 - A0g = +0.0331 / +0.0108 / +0.0004 / -0.0844 deg, every delta sub-floor, and C3's none- and
medium-level dispersion are the campaign's worst (CV 53.5% and 108.8%). So on the literal adoption rule
C3 does not displace A0g. Whether it should is a deployment question: hard DR is the only regime where
the sensitivity probe showed latent fidelity reaches control at all, and C3 dominates there on mean,
dispersion, jitter and both axes.

## Why this arm is also a methodology result

TWO earlier findings from the same day were load-bearing here, and without either one the campaign would
have drawn the wrong conclusion.

1. THE RATIO-VS-R2 CORRECTION SAVED THIS ARM. C3 has the campaign's LOWEST latent ratio at every level
   (0.2725 / 0.3954 / 0.2780 / 0.2983) and its HIGHEST collapse count at `none` (3 of 9 dims under the
   0.1 threshold). Read against the old target of 1, C3 is the worst arm in the campaign and would have
   been rejected. Read against R2 -- which the law of total variance shows is the ratio's real target --
   it is the best:

   | at hard | ratio | aggregate R2 | ratio - R2 |
   |:--|--:|--:|--:|
   | A0g | 0.3443 | -0.0887 | 0.433 |
   | C2 | 0.4822 | +0.0459 | 0.436 |
   | C3 | 0.2983 | +0.1108 | 0.188 |

   Lowest ratio, highest R2, smallest gap to the calibrated identity: most accurate AND best calibrated.
   A lower ratio alongside a lower MSE is the shrinkage an MSE-optimal predictor performs when the target
   is only partly identifiable.

2. THE SENSITIVITY CURVE IS NOW QUANTITATIVELY VALIDATED. The C1-latsens probe measured the frozen
   actor's hard-level sensitivity at 1.070 deg per unit of latent perturbation, independently, on A0g.
   Applied to C3's measured hard latent improvement (about -0.076 in perturbation-norm units) it predicts
   ~0.081 deg; the observed C3 - A0g hard gain is 0.0844 deg, within 4%. The same calculation missed C2
   by 5x. The difference is that C3's improvement landed at the sensitive level and C2's did not -- which
   is exactly where a local slope should and should not be expected to hold.

## Operational notes

- The GRU branch of `_dagger_action` had NEVER executed before this run (A0g was beta=1 so the function
  was never called; B4b and C2 were TCN). Verified before launch that `gru_hidden` (collection-time) and
  `train_hidden` (training-time, threaded across BPTT chunks) are separately allocated so they cannot
  alias. It worked first try; bite check `student/dagger_teacher_frac` = 0.500091.
- C3's OPEN-LOOP `loss_latent` is the campaign's WORST (0.004924 vs A0g's 0.003521) while its in-loop
  tracking is the best. Do not judge these arms on open-loop loss: DAgger trains on a harder distribution
  by construction, and C2 already established that the mixing mechanisms separate only in-loop.

---

## Update (2026-08-03T05:50:03.314927)

## ADOPTION DECISION 2026-08-03: C3 ADOPTED as the deployment student (supersedes the A0g-only adoption)

User delegated the open gate-1 call ("do as recommended") and the recommendation was C3, on the
deployment-regime argument this page left open: the operating target is open water with real plant
mismatch (6 needs-apply-before-retrain leads still open), which sits closer to hard DR than to none,
and hard is the ONLY level where C1-latsens showed latent fidelity reaching control (sensitivity
1.070 deg/unit vs 0.027-0.214 elsewhere). C3 dominates hard on mean, dispersion, jitter and both
axes, and is the only decision-grade student-over-teacher arm (-0.1537 deg vs the 0.1 floor).

Caveats carried with the decision, not hidden: vs A0g the win is hard-only (all other deltas
sub-floor) and C3's none/medium dispersion is campaign-worst; n=1 seed screening. The decision is
cheaply reversible - both packs exist on disk.

Executed: deploy pack exported 2026-08-03 at
deploy/student_distill_eint/pack_eint_c3_gru_260803_144925 (same teacher model_4999.pt from
trpo_eint_s30_rs2350_260727_195102, same attitude_only_5000 batch, device cpu). Parity self-close
CLOSED: gru_latent_max_err 1.04e-07, gru_hidden_max_err 1.79e-07, teacher_act_max_err 5.96e-07 at
atol 1e-5. The A0g pack (pack_eint_a0g_gru_260730_134104) is RETAINED as the fallback checkpoint.

Consistency note: the next student arm (E1/B2) already builds on the GRU+select recipe, so the
campaign lineage and the deployed checkpoint now agree.

