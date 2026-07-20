---
title: "an off-DORAEMON channel that costs return stalls the curriculum below the alpha floor (mode -2 entire run)"
tags: ["doraemon", "curriculum", "stall", "mode-infeasible", "performance_lb", "alpha-floor", "control_delay", "entropy-collapse", "e1"]
created: 2026-07-13T10:08:06.059795
updated: 2026-07-13T10:08:06.059795
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md", "doraemon.py", "config.py"]
links: ["teacher_dr_harder_doraemon_curriculum_froze_before_run_end_unuse.md", "doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever_e.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# an off-DORAEMON channel that costs return stalls the curriculum below the alpha floor (mode -2 entire run)

Failure mode complementary to the uniform-ceiling freeze ([[teacher dr_harder: DORAEMON
curriculum froze before run end]], where success saturates ABOVE alpha and headroom goes
unused). Here success falls BELOW the floor and STAYS there.

When a training channel costs episode return but is NOT one of DORAEMON's `_PARAM_DEFS` dims
(20 dims; e.g. control_delay_steps is absent), the curriculum cannot ease that channel to
restore feasibility. If the cost is large enough to pin mean return below `performance_lb`
(config.py:532 = 250.0), `doraemon_success_rate` never reaches `alpha` (0.5), DORAEMON sits in
mode=-2 (infeasible) for the ENTIRE run, `kl_step ~ 0` (no widening move accepted), and it
CONTRACTS its own dims instead of widening -- dragging policy entropy toward collapse.

e1 latency probe (control_delay_steps (0,0)->(0,3), 0-60ms) 2026-07-13, diagnostic signature:
- mean return ~197 << lb 250 (baseline ~247 sits just under lb, so a ~10%-costly off-curriculum
  channel is enough to stall it)
- doraemon_success_rate 0.09 (baseline peaked 0.594), mode=-2 end-of-run, ess_ratio 0.10, kl_step ~0
- inertia_scale Beta-std CONTRACTED to 0.111 vs baseline widened to 0.268
- policy entropy collapsed (-9.22), noise_std floored

Discriminator vs the uniform-ceiling freeze: freeze = success ABOVE alpha, mode never infeasible,
headroom unused, treatment = widen HardDR bounds. Stall = success BELOW alpha, mode -2 all run,
curriculum contracts, treatment = either make the costly channel a DORAEMON dim (so it can be
eased) OR recalibrate performance_lb to the channel-on nominal return (MEASURED, not guessed).
Never "just train longer" -- the slope is flat because the curriculum is structurally infeasible,
not a transient. Root concept: [[doraemon alpha is a feasibility floor not a DR expansion lever]].
