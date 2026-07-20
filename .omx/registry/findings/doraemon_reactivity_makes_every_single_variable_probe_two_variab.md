---
title: "DORAEMON reactivity makes every single-variable probe two-variable: the curriculum is the uncontrolled second variable (p7_tail e1/e3/e4)"
tags: ["doraemon", "curriculum", "confound", "experiment-design", "p7_tail", "comparability", "performance_lb", "alpha-floor"]
created: 2026-07-20T05:15:15.337690
updated: 2026-07-20T05:16:10.114042
sources: ["trpo_e1_latdr_260713_124923", "trpo_e3_extend10k_260713_224822", "trpo_e4_xyprune_260714_090201", "trpo_baseline_260713_031325"]
links: ["eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md", "an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_.md", "doraemon_over_widens_then_oscillates_when_a_converged_teacher_is.md", "xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e.md", "doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md", "cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-numeric-token", "generic-only-tags"]
---

# DORAEMON reactivity makes every single-variable probe two-variable: the curriculum is the uncontrolled second variable (p7_tail e1/e3/e4)

On this plant a "single-variable" probe is never single-variable: DORAEMON reacts to the
intervention, so the policy under test also trained under a DIFFERENT DR width than its
baseline. The intervention is variable 1; the curriculum's response is variable 2, uncontrolled.

This is the TRAINING-side twin of the already-recorded EVAL-side confound
([[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]]). That page says the
run's *exam* differs. This one says the run's *education* differed too — anchoring the
comparison to `none` fixes the exam, it does NOT undo the fact that the two policies were
trained on different distributions.

## Evidence: three p7_tail probes, three different interventions, three curriculum failures

| probe | intervention | DORAEMON response | end state | fair `none` att_norm ss_error |
|---|---|---|---|---|
| e1 latdr | control_delay (0,0)->(0,3) | CONTRACTED (return tax pinned success under alpha) | mode -2 all run, success 0.09, inertia std 0.111 (vs bl 0.268) | 0.532 -> 1.903 (3.6x worse) |
| e3 extend10k | +10000 iters, zero config delta | OVER-WIDENED then OSCILLATED | entropy_before -30.1 -> -18.6 (i10k) -> -24.4, success 0.368 < bl 0.429 | 0.532 -> 2.350 (4.4x worse) |
| e4 xyprune | DR dims 20 -> 16 (xy body-offsets) | OVER-WIDENED the SURVIVING dims | mode -2, success 0.360, inertia std 0.352 (vs bl 0.268) | 0.532 -> 0.712 (1.34x worse) |

Three unrelated levers — an off-curriculum channel, extra budget, fewer dims — all landed on a
broken curriculum and a regressed fair-level policy. The one p7_tail probe that did NOT break
the curriculum (e2 bias_ema obs, mode 0 / success 0.86) is also the one whose result was
adopted. That correlation is the point.

Mechanisms are recorded individually and are NOT the same failure:
[[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum__]] (contract/stall),
[[doraemon_over_widens_then_oscillates_when_a_converged_teacher_is]] (over-widen/oscillate),
[[xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e]] (dim removal -> survivors
over-widen). Root concept: [[doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e]].

## Why the curriculum is this touchy: alpha and performance_lb are a tight operating point

DORAEMON widens only while `doraemon_success_rate >= alpha` (0.5) against
`performance_lb` (config.py = 250), and the baseline's own mean return is ~247 — sitting just
UNDER the floor. Any intervention that shifts return by ~10%, or changes how much DR width the
same return has to cover, moves the curriculum off its operating point in one direction or the
other. There is very little slack by construction, which is why interventions this different
produce failures this consistent.

## What to do about it (design rule, not a veto)

1. **Report DORAEMON health as a first-class outcome of every probe, not a footnote.** Minimum
   set: end `DORAEMON/mode`, `doraemon_success_rate` vs baseline, and the end-of-run width of at
   least one reference dim (e.g. `DORAEMON/std/inertia_scale`). A probe whose curriculum ended
   in a different regime than its baseline has NOT tested its stated variable in isolation, and
   the report must say so.
2. **Read the direction of the confound before reading the result.** Narrower-than-baseline
   (e1) flatters the probe at hard/ood — e1's apparent tail win was pure exam artifact.
   Wider-than-baseline (e2, e4) UNDERSTATES a real gain — e4's roll-tail shrink was achieved on
   a harder exam and is conservative. Same table, opposite reading, decided by curriculum width.
3. **`none` is necessary but not sufficient.** It fixes the exam. For a claim that the
   intervention itself caused the delta, either show the curricula ended comparable, or re-grade
   both on a frozen shared DR
   ([[cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov]], still an open lead).
4. **A probe that shifts episode return materially needs its DORAEMON gate reconciled BEFORE
   launch** — make the channel a `_PARAM_DEFS` dim, or recalibrate `performance_lb` to the
   intervention-ON nominal return, MEASURED not guessed. Skipping this is how e1 spent a full
   5000-iter run and could answer neither of its own hypotheses.

## Scope

Established on the attitude-only teacher (`Isaac-ConstrainedALBC-TRPO-v0`) with DORAEMON DR
active, 4096 envs, 5000-iter probes against `trpo_baseline_260713_031325`. The
mechanism is DORAEMON's feedback loop, so it should hold wherever that curriculum is on; a run
with DORAEMON disabled or a uniform-only DR roster is not subject to it.

---

## Update (2026-07-20T05:16:10.114042)

## Related (exact slugs)

Link-target correction for the references above, whose slugs end in a character the inline
`[[...]]` form trims: the stall mechanism is
[[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_.md]] and the root concept is
[[doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md]].

