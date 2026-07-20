---
title: "The DORAEMON success_rate PEAK is set by performance_lb, not policy quality: lb=250 peaks 0.63-0.67 and ends CONTRACTED; lb=200 peaks 0.97 and reaches the config ceiling"
tags: ["doraemon", "success-rate", "performance_lb", "alpha-floor", "curriculum-starvation", "p-a2", "baseline"]
created: 2026-07-16T05:59:59.870186
updated: 2026-07-20T03:15:54.941980
sources: []
links: ["performance_lb_recon_needs_zero_new_rollouts_doraemon_state_pt_a.md", "an_off_doraemon_channel_that_costs_return_stalls_the_curriculum.md", "p_a8_perflb200_more_iters_5000_8000_closed_the_deployment_ood_dr.md", "decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# The DORAEMON success_rate PEAK is set by performance_lb, not policy quality: lb=250 peaks 0.63-0.67 and ends CONTRACTED; lb=200 peaks 0.97 and reaches the config ceiling

# The success_rate PEAK is set by performance_lb, not by policy quality

User question (2026-07-16), reading `teacher_baseline_opt`: "baseline's success only peaks around 0.6
then declines -- shouldn't it rise to ~0.9 and then decay toward 0.5 as DR hardens? Is the policy
under-trained while DR ramped too hard?"

Both halves of the read are answered here: the SHAPE intuition is CORRECT and is the documented healthy
signature; the CAUSAL read ("DR ramped too fast on an under-trained policy") is INVERTED.

# Measured: the peak tracks lb, not training quality

TB `DORAEMON/success_rate`, EventAccumulator, stride-1 (sampled per 250 = step_interval):

| run | lb | peak | peak @ iter | final | final @ iter |
|:--|--:|--:|--:|--:|--:|
| trpo_baseline_260713_031325 (opt, pre-TAM) | 250 | 0.6270 | 3258 | 0.4285 | 4999 |
| trpo_baseline_260714_192020 (posttam) | 250 | 0.6655 | 1961 | 0.3955 | 4999 |
| trpo_perflb200_260715_023744 | 200 | **0.9680** | 1235 | 0.7055 | 4999 |
| trpo_perflb200-moreiters_260715_195227 | 200 | **0.9680** | 1235 | 0.4955 | 7999 |

[FINDING] The two lb=250 runs peak at 0.627/0.666; the two lb=200 runs peak at 0.968 -- a ~30-point
gap, reached ~2-3x earlier (iter 1235 vs 1961-3258). All four share the same shape (fast rise to peak,
then sustained non-recovering decline); only the HEIGHT differs, and it partitions exactly by lb.
[EVIDENCE: TB DORAEMON/success_rate via EventAccumulator, 4 runs, 2026-07-16]
[CONFIDENCE: HIGH]

[FINDING] lb=250 makes a 0.9 peak STRUCTURALLY IMPOSSIBLE: success = P(episode_return >= lb), and the
posttam baseline's measured training-return distribution has MEDIAN 241.2 -- BELOW the 250 bar. More
than half its episodes fail the bar on its own DR, so success cannot approach 0.9 no matter how well
the policy trains. The 0.627 peak is a mis-set bar, not an under-trained policy.
[EVIDENCE: doraemon_state.pt buffer_returns n=2000 (per performance_lb_recon_needs_zero_new_rollouts...):
baseline 260714_192020 p25 212.0 / median 241.2 / p95 282.0 with lb=250 -> success 0.3955;
perflb200 p25 189.5 / median 229.5 with lb=200 -> success 0.7055]
[CONFIDENCE: HIGH]

# Why "DR ramped too fast" is inverted: the curriculum was STARVED, and ended CONTRACTED

[FINDING] DORAEMON cannot outrun the policy -- alpha is a CLOSED LOOP: it widens only while
success >= alpha=0.5 and runs the inverted/contracting problem below it. The lb=250 baseline ended at
success 0.4285 < alpha, i.e. in the contract regime, and its FINAL DR is NARROWER than perflb200's:
Beta ~(3-5) center-peaked (contracted) vs perflb200's ~(1.6,1.6) near-uniform = full config range.
So the baseline's curriculum did not over-expand; it never got the headroom to expand at all.
[EVIDENCE: doraemon.py:430-467 alpha branches (widen only when success>=alpha);
TB baseline final success 0.4285; wiki perflb200_final_dr_anatomy: "perflb 17/20 params ~= (1.6,1.6)
= near-uniform = full config range; baseline ~= (3-5) center-peaked = CONTRACTED (re-stall pulled DR
inward)"; reached xi ranges perflb added_mass [0.503,1.498] full vs baseline [0.559,1.489]]
[CONFIDENCE: HIGH]

MECHANISM IN ONE LINE: lb=250 sat at the policy's own return ceiling (~247), so the alpha feedback loop
had no headroom -- success hovered near alpha from early on, any widening immediately pushed it under,
and the curriculum re-contracted. Low peak -> starved curriculum -> NARROWER final DR. The user's
feared outcome (DR harder than the policy can handle) IS the end state (final 0.4285 < alpha), but its
cause is the bar, not the ramp rate, and its consequence is contraction, not over-expansion.

# Corollary: the healthy signature, and what success_rate is not

- HEALTHY signature (perflb200): fast rise to ~0.97, hold >0.9 for ~1k iters, steady decline to ~0.7 at
  5k, converging to alpha 0.5 by ~8k. This IS the designed alpha closed-loop equilibrium, not
  degradation (already recorded in perflb200_final_dr_anatomy).
- STARVED signature (lb=250 baselines): peak <0.7, decline crossing BELOW alpha, final DR contracted.
- success_rate is lb-RELATIVE and is NOT a cross-run difficulty measure: perflb200's higher success
  (0.71 vs 0.40) comes from a LOWER BAR on a WIDER DR, not an easier task. Never compare success_rate
  across runs with different lb as if it measured skill.

# Decision / next experiment (lead)

This is the strongest single argument for prioritising P-A2 (performance_lb recalibration) BEFORE any
further teacher run: lb determines where the alpha equilibrium lands, hence the entire reachable DR
anatomy. It is also free -- see [[performance_lb_recon_needs_zero_new_rollouts_doraemon_state_pt_a]].
Also explains e1's whole-run stall from the same root: lb=250 vs baseline return ~247 is a razor-thin
margin, so e1's ~10% return tax from action delay pushed it under the bar and pinned mode=-2 for the
entire run -- see [[an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_]].
Open: the p25 recon is taken under the DR the run REACHED, so it is not the paper's App A.1 no-DR
rule; a no-DR rollout with TRAINING episode structure is still never-done (eval.py cannot supply it).

---

## Update (2026-07-20T03:15:54.941980)

## Audit close-out (2026-07-20, backlog audit)

CLOSED. This lead's ask -- "prioritise P-A2 (performance_lb recalibration) BEFORE any further teacher
run" -- was already satisfied when the lead was written; the lead post-dates its own answer by 9 minutes.

- P-A2 was EXECUTED: probe run `trpo_perflb200_260715_023744`, extended by P-A8
  `trpo_perflb200-moreiters_260715_195227` (see [[p_a8_perflb200_more_iters_5000_8000_closed_the_deployment_ood_dr]]).
- It was then RE-ADJUDICATED against the now-adopted bias_ema-ON config in
  [[decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema]] (2026-07-16T05:50, resolved):
  lb=200 makes success 0.989 (feasibility constraint inert -- the historic lb=68 failure class),
  measured-p25 rule gives 261.8, current lb=250 -> success 0.882 sits inside the live self-pacing band,
  so "no change is FORCED".
- Verified in code: `constrained_albc/envs/main/config.py:544` -> `performance_lb=250.0`, matching that
  decision. Nothing is pending.

CARRIED CAVEAT (does not reopen this lead): the p25 numbers came from reading the `doraemon_state.pt`
buffer, not from a proper no-DR App A.1 measurement, which per
[[performance_lb_recon_needs_zero_new_rollouts_doraemon_state_pt_a]] "remains never-done". The DECISION
is settled; the ideal measurement is not. If lb is ever revisited, do the App A.1 measurement first.
