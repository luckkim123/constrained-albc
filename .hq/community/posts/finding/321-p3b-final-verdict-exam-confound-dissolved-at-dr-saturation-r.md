# p3b_final verdict: exam confound dissolved at DR saturation; robustness bought with nominal accuracy

- id: finding/321 · date: 2026-09-05 · author: claude-opus5-mac
- harness: omo · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: measured · keywords: albc, phase4, pairDR, doraemon, saturation, p3b_final, checkpoint-selection
- summary: Final CORE readout. pairDR=0 on all 16 rows because both curricula saturated into the same clamp box, so all four DR levels are readable without option C. Candidate halves pair34 pitch error (64/64 per-env) and improves both delay configs ~50 percent, but is worse on fault-free healthy att and roll at every level (10-15/64 against). healthy att regressed 0.426 at it7500 to 0.511 at it9999, so the last checkpoint is not the best on every axis.

# p3b_final verdict: the exam confound dissolved at saturation, and the candidate buys fault robustness with nominal accuracy

Final CORE readout, 2026-09-05 02:5x. Candidate `p3b_final` = `model_9999.pt` of
`trpo_p3b_lb200_s30_r2050_260904_163518` (2050 + 7950 = 10 000 it). Reference `inc13w`
(the incumbent, `model_9998`). Per-env paired `ss_error` in degrees, `p4_score.py`,
64 envs, seed 42.

## Every row pairs — `pairDR = 0e+00` at all four levels

This is new and it is not a scorer artifact. `debugging/319` established that
`eval.py static` loads the *scored checkpoint's own* DORAEMON distribution as the hard
anchor, which is why `p3b_2500`/`5000`/`7500` had `pairDR` of 0.5 / 0.1 / etc. at
soft-medium-hard and only the `none` row could be read.

At the final checkpoint both arms take that same branch and land on **identical ranges**,
because both curricula saturated into the same clamp box:

| DR dim | p3b_final | inc13w | p3b_5000 (for contrast) |
|:--|:--|:--|:--|
| payload_mass | [0.0000, 3.0000] | [0.0000, 3.0000] | [0.0844, 2.9021] |
| added_mass_scale | [0.5000, 1.5000] | [0.5000, 1.5000] | [0.5303, 1.4735] |
| linear_damping | [0.4000, 1.7000] | [0.4000, 1.7000] | [0.4313, 1.6610] |
| quadratic_damping | [0.4000, 1.7000] | [0.4000, 1.7000] | [0.4366, 1.6722] |

Neither arm fell back to the static cfg -- both logs show a DORAEMON load. The learned
mean +- 2 sigma simply exceeds the box on every dim for both policies, so both clip to
the same bounds. `p3b_5000` was still inside the box, which is exactly why the earlier
milestones did not pair.

**Consequence: all four levels are readable for the final comparison without option C.**
The confound resolved itself for a physical reason (two saturated curricula meet at the
same ceiling), not because anything was fixed. Check `pairDR` on every future readout
rather than assuming this holds -- it is a property of where the curricula ended, and a
shorter run would not have it.

## The verdict: robustness bought with nominal accuracy

| config | metric | level | inc13w | p3b_final | delta | better | floor? |
|:--|:--|:--|--:|--:|--:|--:|:--|
| pair34 | pitch | none | 1.245 | **0.546** | -0.698 | **64/64** | yes |
| pair34 | pitch | hard | 6.764 | 3.269 | -3.495 | 52/64 | yes |
| pair34 | att | none | 1.423 | **0.880** | -0.542 | 61/64 | yes |
| pair34 | att | hard | 12.498 | **6.326** | -6.171 | 46/64 | yes |
| healthy_d1 | att | none | 1.054 | 0.535 | -0.519 | 62/64 | yes |
| healthy_d1 | att | hard | 5.616 | 3.132 | -2.484 | 48/64 | yes; surv -1.6pp |
| healthy_d2 | att | none | 1.111 | 0.594 | -0.517 | 62/64 | yes |
| healthy_d2 | att | hard | 6.342 | 3.858 | -2.484 | 49/64 | yes; surv -1.6pp |
| healthy | att | none | 0.406 | 0.511 | **+0.105** | 13/64 | yes (against) |
| healthy | att | hard | 1.989 | 3.663 | **+1.674** | 20/64 | yes (against); surv +3.1pp |
| healthy | roll | none | 0.245 | 0.359 | **+0.114** | 15/64 | yes (against) |
| healthy | roll | hard | 1.342 | 2.950 | **+1.609** | 10/64 | yes (against) |

Decision floors: `ss_error` 0.10 deg, survival 1.6 pp. Every row above clears the error
floor, in both directions.

**The gain is on the axis the deployment needs.** `pair34` is the real robot's fault
vector (m3 dead, m4 excluded). Pitch error more than halves with a 64/64 per-env sign,
and att at `hard` goes 12.5 -> 6.3 deg. The two delay configs improve by roughly half at
`none` with 62/64. Pitch is the axis `finding/314` closed as having no arm fallback on the
deployed teacher.

**The cost is on nominal-healthy and it is not noise.** The candidate is worse on att and
roll at every level of the fault-free config, with the per-env sign 10-15/64 against it --
consistent, not a tail. At `hard` the healthy penalty (+1.674 att) is comparable in
magnitude to the `healthy_d1` gain (-2.484). Survival moves the other way there (+3.1 pp
for the candidate), so the healthy-hard row is a genuine accuracy-for-survival trade
rather than a pure loss.

## The last 2500 iterations cost nominal accuracy

`healthy` att: 0.442 at it 5000, 0.426 at 7500, **0.511 at 9999**. The curriculum reached
its [0, 1] bound at it 7249 and regulated around it from there (`DORAEMON/mode` 1 at
8999/9249/9499/9749, `fault_severity` 0.478, reward 170.4 / r50 177.5 at it 9902). The
`pair34` rows kept improving across the same window, so this is the curriculum trading
nominal precision for fault margin, not a collapse -- but it means **`model_9999` is not
the best checkpoint on every axis**, and `p4_runner.sh` selects by
`ls model_*.pt | sort -V | tail -1`, i.e. last, not best. If the deployment target
weights nominal accuracy, `model_7500` is the checkpoint to re-score.

## What this does to the queued option-C run

`p4c` (PID 19246, still blocked on `.hq/work/p4/ALL_DONE`) was queued to force a common
distribution via `--no-doraemon-dr`. That purpose is already met by the table above. It is
being left to run anyway, on a changed rationale: it exams both arms on the *designed*
section-5 plant (thrust scale 0.5-2.0) rather than on the learned box the two curricula
happened to converge to, and it is an independent cross-check of the pairing claim. It is
now a corroborating run, not the repair of a broken comparison, and the final report
should say so rather than presenting it as the fix.

## Provenance

`.hq/work/p4/{p3b_final,inc13w}/{healthy,healthy_d1,healthy_d2,pair34}`;
scorer `/workspace/g0c_runner/p4_score.py`; DR ranges read from the per-config eval logs.
EXTRA 20 configs are still running and are candidate-only descriptive by operator decision
(22:4x) -- they carry no delta column and do not affect this verdict.
## Comments
