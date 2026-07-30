---
title: "DORAEMON reactivity makes every single-variable probe two-variable: the curriculum is the uncontrolled second variable (p7_tail e1/e3/e4)"
tags: ["doraemon", "curriculum", "confound", "experiment-design", "p7_tail", "comparability", "performance_lb", "alpha-floor", "b0c", "auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-20T05:15:15.337690
updated: 2026-07-30T03:54:24.726456
sources: ["trpo_e1_latdr_260713_124923", "trpo_e3_extend10k_260713_224822", "trpo_e4_xyprune_260714_090201", "trpo_baseline_260713_031325", "diagnose-20260727-151917", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: ["eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md", "an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_.md", "doraemon_over_widens_then_oscillates_when_a_converged_teacher_is.md", "xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e.md", "doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md", "cross_run_dr_comparability_eval_py_doraemon_dr_from_already_prov.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
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

---

## Update (2026-07-27T06:43:06.022569)

B0c example (2026-07-27): even an OFF-curriculum uniform DR axis feeds back through the success gate. The max_thrust +/-15% band is uniform per-env DR (not a DORAEMON dim, none-collapsed at eval), yet the paired B0c run ended with doraemon_success_rate 0.81 -> 0.73, DORAEMON/entropy_before -22.77 -> -24.68 (tb_final.py window=10), and the driven dims at 9-11% of range vs the anchor's 13-14% (engine TIER 2 DORAEMON table, both runs). So the band's tiny eval deltas are partly curriculum-mediated -- the two-variable caveat applies even when the added axis is outside DORAEMON. Source: B0c analysis diagnose-20260727-151917, doraemon section.

---

## Merged from doraemon_reactivity_makes_this_like_every_probe_a_two_variable_e.md (2026-07-30T03:54:24.726456)

# DORAEMON reactivity makes this (like every probe) a two-variable experiment: wit

DORAEMON reactivity makes this (like every probe) a two-variable experiment: with the uniform band on, doraemon_success_rate ends lower (0.81 -> 0.73), cumulative difficulty entropy ends lower (DORAEMON/entropy_before -22.77 -> -24.68, final-10-iteration window), and the driven curriculum dims reach LESS of their range (ocean_current 14.3% -> 10.2%, obs_noise 13.9% -> 11.4%, payload_cog_xy 13.0% -> 8.9%; DORAEMON/ess_ratio 0.78 -> 0.77) — so part of the tiny eval deltas is curriculum-mediated, not purely the band.

[EVIDENCE: engine TIER 2 DORAEMON per-param table, both runs; tb_final.py window=10 for DORAEMON/entropy_before and DORAEMON/kl_step (0.0 both, final window); wiki doraemon_reactivity_makes_every_single_variable_probe_two_variab]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

DORAEMON reactivity makes this (like every probe) a two-variable experiment: with the uniform band on, doraemon_success_rate ends lower (0.81 -> 0.73), cumulative difficulty entropy ends lower (DORAEMON/entropy_before -22.77 -> -24.68, final-10-iteration window), and the driven curriculum dims reach LESS of their range (ocean_current 14.3% -> 10.2%, obs_noise 13.9% -> 11.4%, payload_cog_xy 13.0% -> 8.9%; DORAEMON/ess_ratio 0.78 -> 0.77) — so part of the tiny eval deltas is curriculum-mediated, not purely the band.

[EVIDENCE: engine TIER 2 DORAEMON per-param table, both runs; tb_final.py window=10 for DORAEMON/entropy_before and DORAEMON/kl_step (0.0 both, final window); wiki doraemon_reactivity_makes_every_single_variable_probe_two_variab]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
