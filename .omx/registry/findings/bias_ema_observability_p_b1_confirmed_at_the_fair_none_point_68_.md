---
title: "bias_ema observability (P-B1) confirmed at the fair 'none' point (-68% roll, -29% pitch) AND unexpectedly cleared the DORAEMON feasibility stall on unchanged lb=250"
tags: ["bias_ema", "doraemon", "p-b1", "observability", "stall", "dr-anatomy"]
created: 2026-07-15T10:45:29.173902
updated: 2026-07-15T10:45:29.173902
sources: ["diagnose-20260715-193800"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# bias_ema observability (P-B1) confirmed at the fair 'none' point (-68% roll, -29% pitch) AND unexpectedly cleared the DORAEMON feasibility stall on unchanged lb=250

# P-B1 result (bias_ema obs 69->72D, use_bias_ema_obs False->True, config.py:405)

[FINDING] H1 CONFIRMED at the only DR-fair comparison point (`none`, DR=0): roll ss_error 0.664->0.215
(-68%), pitch ss_error 0.273->0.195 (-29%), CV and ss_jitter fall in step on both axes (not a
jitter-for-floor trade). This EXCEEDS the e2 void-plant mechanism (roll -53%) on the harder corrected
post-TAM plant. Binding constraint (thruster_util) and barrier_penalty unchanged on both runs, ruling
out an authority-ceiling explanation for the gain.
[EVIDENCE: eval/static_260715_192701 (P-B1) vs eval/static_260715_004654 (reference trpo_baseline_260714_192020),
summary.json none level; report diagnose-20260715-193800 tracking section, independently re-verified
against raw summary.json by report-reviewer]

[FINDING] UNANTICIPATED effect, not predicted by the proposal's H1/H2 framing: bias_ema observability
ALONE (same performance_lb=250 as the stalled reference) cleared the DORAEMON feasibility stall the
reference was stuck in — DORAEMON/mode -2 (stall) -> 0, doraemon_success_rate 0.40 -> 0.88,
DORAEMON/ess_ratio 0.41 -> 0.76. This is the SAME stall signature the perflb200 probe (lb 250->200,
see wiki perflb200_final_dr_anatomy...) targeted via a different single variable — here it cleared via
observability instead, on the unchanged lb. Consequence: P-B1's final DORAEMON DR reached a WIDER
Beta(1.64, 2.45) (near-uniform, ~2x the variance) vs the reference's contracted Beta(3.19, 5.46)
(report-reviewer independently recomputed Beta variance: ref ~0.024 vs P-B1 ~0.047).
[EVIDENCE: doraemon_state.pt dist_a/dist_b, both runs, mean over 20 dims; report diagnose-20260715-193800
doraemon section, independently re-verified by report-reviewer via torch.load]

[FINDING] Because P-B1 trained on a wider DR (the stall-clearing side effect), the hard-level roll
"regression" (ss_error 0.717->0.928, n_gt20 6.7->12.3) is CONFOUNDED with DR-width, not clean H2
evidence (rule03 run-relative-DR caveat applies at full force). Cannot be attributed to bias_ema obs
itself without a DR-matched follow-up.
[EVIDENCE: report diagnose-20260715-193800 doraemon + verdict sections]

# Decision

ADOPT `use_bias_ema_obs=True` supported by the `none`-level result alone. Hard-level caveat is real but
unresolved — needs a DR-matched follow-up (same reached-DR range on both sides, isolating bias_ema obs
from the stall-clearing side-effect) to fully disambiguate. Deferred to next week's design pass
(this week = token-saving run+analyze+eval only, no new design per user directive 2026-07-15).

Reviewer: report-reviewer agent independently re-verified all core numbers against raw summary.json and
doraemon_state.pt (not just the report's own tables) — verdict approve, 0 findings.

