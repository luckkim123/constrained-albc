---
title: "Consequently P-B1's final DORAEMON DR is WIDER than the reference's — P-B1 reach"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-15T10:45:08.430019
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Consequently P-B1's final DORAEMON DR is WIDER than the reference's — P-B1 reach

Consequently P-B1's final DORAEMON DR is WIDER than the reference's — P-B1 reached near-uniform Beta(1.64, 2.45) (config-ceiling-adjacent, matching the perflb200 pattern in `perflb200_final_dr_anatomy...`) vs the reference's contracted Beta(3-5) (the re-stall pulled its DR inward, same signature documented for the pre-perflb baseline). This means P-B1's `hard`/`medium` eval boxes sample OBJECTIVELY HARDER physics than the reference's — the hard-level roll "regression" (## tracking) is confounded with this DR-width difference and is NOT clean evidence that bias_ema obs causes a hard-DR floor rise or transient-trade (the H2 caveat in the proposal). Disentangling requires a DR-matched follow-up (same reached-DR range on both sides) — deferred to next week's design pass.

[EVIDENCE: doraemon_state.pt Beta(dist_a, dist_b), both runs, mean over 20 dims]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
