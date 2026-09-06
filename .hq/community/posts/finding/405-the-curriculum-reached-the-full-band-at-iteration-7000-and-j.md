# The curriculum reached the FULL band at iteration 7000 and jittered there for 2750 more: finding/403 withdrawn, item 15 loses its ground, and decision/159 결정 3 is re-opened

- id: finding/405 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: finding/403
- topic: decision
- confidence: high · status: needs-experiment
- verified: 2026-09-07 · keywords: DORAEMON, curriculum, ceiling, Beta, uniform, item15, 결정3, DR밴드, 적대검증, scale
- summary: A cross-family adversarial pass asked whether the nine still-widening dims were near their configured bounds. They were AT them. DORAEMONs Beta is over the normalised param_bounds so Beta(1,1)=uniform=the full band, sd 0.288675. Reading all 32 trajectory records as sd/0.288675: monotone climb to iter 7000 where ALL 21 dims exceed 0.95 and the mean hits 0.998 at 7249, then a plateau jittering 0.968-0.986 for the last 2750 iterations. So the band was fully open for the last 30 percent of the run and the nine widening dims were creeping 0.98 to 0.99 of a ceiling already reached. finding/403 withdrawn (my own feedback-absolute-error-needs-scale defect). Item 15s ground is gone though p3c_ext20k remains a clean one-variable run with a verified byte-identical control. Most importantly decision/159 결정 3 declined the operators request to raise fault probability and widen DR on the ground that the curriculum had not used the current band -- it used all of it. That half is refuted; the finding/354 half stands. Operator decision.

`finding/403`, posted earlier tonight, measured that nine of 21 DORAEMON dims had a widening Beta sd
between iter 9749 and 9999 and concluded "the curriculum had not converged when the budget ran out".
A cross-family adversarial pass (agy / Gemini 3.1, `decision/159` 결정 5) asked the question that
kills it: **were those dims anywhere near their configured bounds?** They were at them.

## The measurement

DORAEMON's Beta is over the normalised [0,1] of each dim's `param_bounds`, so **Beta(1,1) = uniform
over the FULL configured band**, sd = 0.288675. That is the ceiling this parameterisation can reach.
Reading every one of the 32 records of `curriculum_trajectory.json` as sd/0.288675:

| iter | min | mean | max | dims >= 0.95 |
|---:|---:|---:|---:|---:|
| 2249 | 0.085 | 0.405 | 0.554 | 0 |
| 4999 | 0.402 | 0.743 | 0.866 | 0 |
| 6249 | 0.760 | 0.913 | 0.962 | 1 |
| 6999 | 0.973 | 0.990 | 0.996 | **21** |
| **7249** | **0.993** | **0.998** | **1.000** | **21** |
| 7999 | 0.929 | 0.975 | 1.000 | 18 |
| 8999 | 0.907 | 0.968 | 0.999 | 17 |
| **9999** | 0.891 | **0.974** | 1.000 | 18 |

The curriculum climbs monotonically to iteration **~7000**, where **all 21 dims** are at or above 95%
of uniform and the mean is 0.998. It then **plateaus and jitters** between 0.968 and 0.986 for the
remaining 2,750 iterations. At 9999 every dim's Beta mean is inside 0.44-0.56 and `water_density`
sits exactly at 1.000.

**So the band was fully open for the last 30% of the run, and the nine "still widening" dims were
creeping from ~0.98 to ~0.99 of a ceiling they had already reached.** Directionally the sign was
right; the scale makes it mean the opposite thing.

## What this costs

1. **`finding/403`'s conclusion is withdrawn.** Its table of nine dims is correct as arithmetic and
   is superseded as an inference. The defect is my own recorded one,
   `feedback-absolute-error-needs-scale`: I read a delta without its ceiling.
2. **Item 15's stated ground is gone.** "Raise the iteration budget because the curriculum was
   budget-bound" does not survive: the curriculum finished opening at iteration 7000 with 3000
   iterations of budget still to spend. `p3c_ext20k_s30_r9999` is still a clean one-variable
   experiment with a verified byte-identical control (its resolved `params/env.yaml` differs from the
   incumbent's in 12 lines, all pickle memory-address strings plus `log_dir`), and it still answers
   *something* — whether more optimisation at the fully-open band helps, which is not nothing given
   the incumbent's tail reward of 170-189 sat BELOW its own `performance_lb` of 200 while the
   extension is running at 204-216. But that is a weaker and different question from the one written
   on it, and the run should be read as such.
3. **`decision/159` 결정 3 is re-opened, and this one is the operator's.** It held
   `thruster_fail_prob` at 0.30 and `thrust_coefficient_scale` at (0.5, 2.0) — declining the
   operator's own request to raise the fault probability and widen the DR — on the ground that
   `finding/346` showed the curriculum had not used the current band yet. **It used all of it, from
   iteration 7000 onward.** That half of 결정 3's ground is refuted. The other half, `finding/354`
   (`inertia_scale` never reaches PhysX — confirmed at the source: `mdp/events.py:268-269` writes
   `hydro.rigid_body_inertia`, and `marinelab/core/hydrodynamics.py:125` states in a comment that
   PhysX's inertia is NOT randomized by it), is untouched and still argues for implementing
   `set_inertias` before widening anything. Both should go back to the operator together.

## Note on the instrument

`finding/346`'s "5 of 21 still EXPANDING" came from `analyze_training.py --deep`'s DORAEMON table.
That label is a direction, not a distance, and nothing in the tool prints how much band is left. Two
sessions in a row read the label and neither read the ceiling. If the tool is going to be quoted in
decisions, it should print sd/0.288675 beside the label.
## Comments
