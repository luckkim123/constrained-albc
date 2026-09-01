# DORAEMON over-widens then oscillates when a converged teacher is given extra budget (chases alpha floor, overshoots, contracts)

- id: finding/077 · date: 2026-07-13 · author: wiki-form-conversion
- harness: omx · to: all
- subject: doraemon-over-widens-then-oscillates-when-a-converged-teache · supersedes: none
- topic: pattern
- confidence: high · status: none
- verified: none · keywords: doraemon, curriculum, budget, entropy_before, alpha, oscillation
- summary: DORAEMON over-widens then oscillates when a converged teacher is given extra budget (chases alpha floor, overshoots, contracts)

When a teacher that has already converged (reward saturated, curriculum mid-progression) is resumed for a large extra budget with zero config delta, DORAEMON does NOT converge the curriculum — it over-widens then oscillates. e3 (baseline 5000 -> +10000 iters): DORAEMON/entropy_before -30.1(resume) -> -18.6 PEAK@iter10000 (much wider) -> -24.4 END; DORAEMON/success_rate 0.654@7500 -> 0.368 END (< baseline 0.429 and < alpha 0.5). Mechanism: alpha=0.5 is a FEASIBILITY FLOOR (see doraemon_alpha_is_a_feasibility_floor_not_a_dr_expansion_lever); the extra budget lets DORAEMON push DR width past what the policy can sustain, success falls below alpha, so it contracts the distribution again -> a non-stationary over-hard training target. The policy chases the moving target and OVER-ADAPTS to disturbances absent at nominal: none-level roll DC-bias 15.5x baseline + jitter 5.6x baseline, while episode return falls below baseline. DR-std widths at end all exceed baseline (ocean_current 0.055->0.261=4.7x, lin_damp 0.230->0.313, added_mass 0.158->0.219, payload_mass 0.487->0.571). Signature to watch: entropy_before non-monotone (rise-then-fall) + success ending below alpha + reward peak mid-extension then decline. Evidence: analysis diagnose-20260714-084409 sections 0,9; run trpo_e3_extend10k_260713_224822.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["diagnose-20260714-084409"]
- qualityScore: 80
- qualityReasons: ["no-source-marker"]
## Comments
