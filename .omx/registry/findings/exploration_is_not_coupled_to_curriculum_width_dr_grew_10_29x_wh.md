---
title: "Exploration is not coupled to curriculum width: DR grew 10-29x while sigma shrank 9 percent, and the three obvious fixes are already refuted here"
tags: ["albc", "entropy", "exploration", "noise_std", "doraemon", "curriculum", "entropy_coef", "min_std", "arm-w", "open-question", "m2"]
created: 2026-08-10T00:46:40.833126
updated: 2026-08-10T02:34:41.921119
sources: []
links: ["april_2026_entropy_collapse_campaign_machinery_bug_solved_conver.md", "ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder.md", "doraemon_over_widens_then_oscillates_when_a_converged_teacher_is.md", "doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: resolved
---

# Exploration is not coupled to curriculum width: DR grew 10-29x while sigma shrank 9 percent, and the three obvious fixes are already refuted here

Actor exploration in this project is **not coupled to curriculum difficulty in any way**. Nothing in
the architecture raises sigma when DORAEMON widens the box, and the measured result is that they move
in opposite directions for the whole second half of training.

## Measured on Arm W `trpo_rampw_kl006_s30_260809_161913`

`Noise/std_mean` (== `Policy/mean_noise_std`), by iteration:

```
0:0.7000  200:0.2621  500:0.1784  1000:0.1354  2000:0.1085
5000:0.0887  10000:0.0847  15000:0.0829  18205:0.0811
```

DR width over the SAME span (`DORAEMON/std/*`):

| dim | it 5000 | it 18205 | growth |
|:--|--:|--:|--:|
| `ocean_current_strength` | 0.0278 | 0.2882 | **10.4x** (29x from it 0) |
| `payload_cog_offset_xy_u` | 0.0328 | 0.2866 | **8.7x** (29x from it 0) |
| `water_density` | 4.3754 | 8.5504 | 2.0x |
| `payload_mass` | 0.4692 | 0.8609 | 1.8x |

**From iteration 5,000 to 18,205 the task got ~10-29x wider while exploration shrank 9%.**

`Noise/std_min` reaches **0.0500 at iteration 5,000 and is flat for the next 13,000** — at least one
dim pinned at the thruster floor. Config: `min_std_per_dim` = (0.1, 0.1, 0.05 x6). An all-floored
mean would be 0.0625; the observed 0.0811 means the thrusters average ~1.5x above their floor, so
this is "converged", not "dead".

## The three obvious ways to act on this are already refuted HERE

| intervention | measured outcome |
|:--|:--|
| raise `entropy_coef` to fight collapse (2026-03-30) | roll 9.77 -> **13.59 deg WORSE**, reward -17.49; verdict "entropy bonus interfered with exploitation" |
| ERC-TRPO hard entropy floor | froze policy updates after ~53 iters, reward stuck -306, **reverted same day** |
| SAC-style learnable entropy | added 04-10, disabled 04-13 |
| raise `min_std` | scalar is DEAD CODE when `min_std_per_dim` is set (`constraint_trpo.py:507-511`); per-dim floors measured non-binding |

See [[april_2026_entropy_collapse_campaign_machinery_bug_solved_conver]] — the April campaign fixed
the machinery bug (`log_std` outside the trust region, commit `3132605`) and closed with the
converged-sigma phenomenon explicitly UNRESOLVED. Sigma has tightened every campaign since:
0.22-0.34 (Apr) -> 0.175 -> 0.109 -> 0.0995 -> 0.084 (Jul) -> **0.0811 (Arm W, Aug)**.

## And harder DR is measured to LOWER exploration, not raise it

- [[ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder]]: E2 made DR harder by center-shift ->
  actor entropy COLLAPSED to -0.63 ("exploration dead") with the HIGHEST reward and success 0.972 —
  the overfit signature. Harder distribution produced specialization, not search.
- [[doraemon_over_widens_then_oscillates_when_a_converged_teacher_is]]: extra budget on a converged
  teacher over-widens past what the policy sustains, success drops below the floor, the box
  contracts — a non-stationary target the policy over-adapts to. **This is the same signature Arm W
  shows at 10,750+.**

So the intuition "difficulty rises, so exploration should rise" is not naive — but every attempt to
force it uniformly in time, or with a hard floor, has made things worse in this codebase.

## What is untried

**Coupling the exploration pressure to the curriculum state** — `entropy_coef_per_dim` scaled with
DORAEMON's realized expansion, so sigma rises when and only when the box widens. A wiki search for a
curriculum-coupled entropy schedule returns nothing. Every refuted attempt above was uniform-in-time
or a hard floor; none was difficulty-coupled.

Note that Arm D's `entropy_coef_per_dim` x k is a correction for BATCH SIZE (16384 vs the 4096 the
constants were calibrated on), not for difficulty. It does not test this axis.

## The observation that makes it worth a probe

Arm W at maximum width has its run-minimum sigma (0.0811) AND a return stalled at 242.5 against
`performance_lb` 250.0, so the curriculum cannot lock (see
[[doraemon_becomes_feasibility_limited_at_the_ceiling_the_kl_ub_0_]]). Whether exploration is the
limiter or the plant is simply harder than the policy can master is **not separable from this run**.
That is the experiment this page is waiting for.

---

## Update (2026-08-10T02:34:41.921119)

CLOSED BY MEASUREMENT, 2026-08-10 (M2 paired comparison). The structural fact below still holds - nothing in this architecture couples policy exploration to curriculum width - but it is NOT the bottleneck, so it is deprioritized as an experiment lead rather than solved.

M2 compared the sigma trajectory of the run that DID saturate (trpo_iterbudget_s30_260805_012813, final return 258.56, locked 21/21) against Arm W (trpo_rampw_kl006_s30_260809_161913, ended 0/21 saturated, final return 241.69). Pre-registered tolerance was +-10%. Observed deviation: 0.5-2.6%.

Matched on iteration (Noise/std_mean, window +-30): it 5000 REF 0.08797 vs ARMW 0.08870 (ratio 1.008); it 7000 0.08572 vs 0.08611 (1.005); it 7748 0.08517 vs 0.08567 (1.006); it 9950 0.08337 vs 0.08458 (1.015).

Matched on DR width instead of iteration - the stricter test, because the two arms differ in kl_ub and therefore reach a given difficulty at different iterations - using DORAEMON/std/ocean_current_strength thresholds 0.05 through 0.28: ARMW/REF ratio 0.974 to 0.990. Arm W is if anything slightly LOWER at equal difficulty.

Three findings that together close the hypothesis:
1. Both runs pinned Noise/std_min at exactly 0.05000, and both reached the identical maximum DR width 0.2887 on ocean_current_strength. Arm W did not fail to widen.
2. Arm W pinned the floor at iteration 3212; the reference pinned at or before 4999. Arm W collapsed EARLIER and still lost - a direct counterexample to "early collapse caused the failure".
3. The only thing that differed was return: 258.56 (above performance_lb 250) versus 241.69 (below). The failure is a return-level failure, which is what reverses the curriculum by design.

Derived, conditional on the 6 thruster dims being the pinned ones: arm-dim mean std at it 9950 is (0.08337*8 - 0.30)/2 = 0.1835 for REF and (0.08458*8 - 0.30)/2 = 0.1884 for Arm W - 2.7% apart, both sitting at ~1.8x their own 0.10 floor in free equilibrium. So the 0.083-0.088 band is this problem's equilibrium point, not a run-specific accident: halving kl_ub and doubling the iteration budget did not move it.

CAVEAT discovered while running M2: the reference run is a RESUMED run. Its event file starts at step 4999 with std_mean already 0.08807 and DR width already 0.1027, and launch.log line 56 reads "Loading model checkpoint from: .../RESUME_SRC/model_4999.pt". Its pre-5000 history is not in its own logs, so its true first-pinning iteration cannot be recovered from there. Every number above is taken from the window where both runs have data, and the DR-width-matched comparison is immune to the iteration offset.

WHAT REMAINS UNTRIED (recorded here so it is not lost by the status change): curriculum-coupled entropy_coef - making the entropy pressure a function of curriculum state rather than a constant. No published continuous-control work does this (a full-PDF grep of the DORAEMON paper arXiv:2311.01885 returns zero body mentions of policy entropy, action noise, or std). It stays a legitimate idea; it is simply no longer the explanation for THIS failure, and should not be proposed as the fix for the 250-floor problem. See wiki page sigma_decay_under_an_expanding_dr_curriculum_literature_verdict_ for the literature basis.

NEXT DIAGNOSTIC instead: bucket episodes by sampled DR value per dimension into quintiles and read mean return per bucket, to test whether one dimension's upper range is physically infeasible and drags the mean below the floor. Uses existing rollout logs, no training.

