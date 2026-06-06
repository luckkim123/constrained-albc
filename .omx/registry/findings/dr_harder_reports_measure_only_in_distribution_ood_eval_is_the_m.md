---
title: "DR-harder reports measure only in-distribution; OOD eval is the missing decisive test"
tags: ["dr-harder", "ood", "generalization", "eval", "overfit"]
created: 2026-06-06T11:39:29.533121
updated: 2026-06-06T11:39:29.533121
sources: ["diagnose-20260606-202950"]
links: ["ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder.md", "hmm_regime_count_separates_dr_harder_runs_overfit_vs_healthy.md"]
category: debugging
confidence: high
schemaVersion: 1
---

# DR-harder reports measure only in-distribution; OOD eval is the missing decisive test

dr-harder's stated goal is a policy that generalizes to OOD, but the standard eval (eval_dr static none/soft/medium/hard) tests ONLY levels INSIDE the DORAEMON training distribution. So a report can call a run 'best tracker' (E2: reward 253.9, hard roll 1.19deg, lowest of 3) while that is purely in-distribution. The decisive differential test is OOD eval (levels BEYOND hard: stronger current/payload than DORAEMON ever sampled, or perturbing an axis not in the DR set), run side-by-side with the 4 in-dist levels and reported as a generalization gap. Why it matters here: E2 shows textbook overfit (Policy/entropy -0.60 COLLAPSED, none-level per-env CV ~0% = deterministic policy, persistent bad HMM regime mean_reward -348). Overfit is exactly the failure mode that breaks OOD. Without OOD eval, in-dist 'E2 is best' and 'E2 overfit -> worst OOD' are indistinguishable. Action: add an OOD eval mode + generalization-gap report section (harness work, not this analysis session). cf [[ocean_nominal_shift_collapses_actor_entropy_e2_dr_harder]] [[hmm_regime_count_separates_dr_harder_runs_overfit_vs_healthy]].
