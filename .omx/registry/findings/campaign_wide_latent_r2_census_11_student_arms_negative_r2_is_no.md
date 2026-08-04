---
title: "Campaign-wide latent R2 census (11 student arms): negative R2 is NOT the campaign norm, the gen-1 extra-obs arm is the best tracker, and the obs76 gen-2 student sits at the bottom while being the only arm that kills envs"
tags: []
created: 2026-08-04T05:07:09.465856
updated: 2026-08-04T05:07:09.465856
sources: []
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-experiment
---

# Campaign-wide latent R2 census (11 student arms): negative R2 is NOT the campaign norm, the gen-1 extra-obs arm is the best tracker, and the obs76 gen-2 student sits at the bottom while being the only arm that kills envs

Computed 2026-08-04 from every stored `latent_<level>.npz` in albc_trpo_student, per-dim
R2 = 1 - MSE/Var_total (the corrected metric; see the d4 page). Aggregate at hard, where the
denominator is well-conditioned -- the `none` aggregate stays uninterpretable for every arm
(per-dim Var_total spans 2 to 4 orders of magnitude there).

| arm | teacher | hard agg R2 | hard n_pos | hard survival |
|:--|:--|--:|--:|--:|
| B2-extraobs (gen-1 side channel) | E-int | +0.246 | 7/9 | 100% |
| B2wide-gru256 (GRU 256) | E-int | +0.230 | 7/9 | 100% |
| C3-gruselect | E-int | +0.111 | 4/9 | 100% |
| B2ctl-dim0 (B2's control) | E-int | +0.090 | 4/9 | 100% |
| C2-daggersel | E-int | +0.046 | 5/9 | 100% |
| A0-tcn | E-int | +0.001 | 4/9 | 100% |
| B1-lam4 | E-int | +0.001 | 4/9 | 100% |
| B1-lam0 | E-int | -0.039 | 4/9 | 100% |
| B4b-beta05 | E-int | -0.047 | 4/9 | 100% |
| A0g-gru | E-int | -0.089 | 4/9 | 100% |
| **E-obs76 (gen-2, Phase E)** | **obs76** | **-0.078** | **6/9** | **96.9%** |

THREE THINGS THIS SETTLES

1. A negative in-loop latent R2 is NOT a campaign law. It spans -0.089 to +0.246 at hard across
   eleven arms. Any statement of the form "the student latent is worse than a constant-mean
   predictor" is a per-arm result, never a standing property of the architecture.

2. The 4 deployable channels DID buy real latent fidelity when delivered gen-1 (as a side channel
   on the unchanged E-int teacher): B2-extraobs +0.246 against its own dim=0 control at +0.090.
   The recorded decomposition of that gap attributes ~60% (+0.093) to genuine error reduction and
   ~40% to denominator drift, so the real gain is smaller than the headline but nonzero. Extra
   ENCODER INPUT is therefore a live lever, contrary to any reading that only covariate shift matters.
   Widening the encoder (GRU 128 -> 256) buys a comparable amount (+0.230), so capacity is a second
   live lever.

3. The obs76 gen-2 student is the ONLY arm in the census that loses envs (2 of 64 at hard; every
   other arm holds 100%), and it sits near the bottom on hard R2 despite carrying the same four
   channels that made B2 the best arm. Its latent metric is measured against a DIFFERENT teacher, so
   this is not a clean head-to-head -- but the survival column is teacher-independent and the
   contrast stands on its own.

THE QUESTION THIS OPENS, which is now the program's sharpest: the same four channels, delivered two
ways, gave opposite results on the latent axis. Gen-1 = side channel into the student encoder only,
teacher untouched (B2, best in census). Gen-2 = folded into policy_obs 72->76 with the teacher
RETRAINED on them (Phase E, bottom of census, only arm with fatalities). Two mechanisms are
confounded in that contrast -- the delivery path AND the teacher swap -- and nothing currently
separates them. A gen-1 student distilled from the obs76 teacher, or a gen-2 student from a teacher
that was NOT retrained, would split them.

METHOD NOTE carried from the Phase E analysis: cross-arm R2 comparison within one teacher is sound
(shared latent target), but per-dim indices are NOT comparable across teachers (the encoder is
retrained from scratch and nothing pins dimension ordering), so only aggregate and count statements
survive a teacher swap. And the eval env draws differ between any two runs except at `none`, so an
R2 delta must be decomposed before it is quoted as an effect.

