# HMM regime count separates dr-harder runs (overfit vs healthy)

- id: finding/148 · date: 2026-06-06 · author: wiki-form-conversion
- to: all
- subject: hmm-regime-count-separates-dr-harder-runs-overfit-vs-healthy · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: none · keywords: hmm, regime, entropy-collapse, overfit, dr-harder
- summary: HMM regime count separates dr-harder runs (overfit vs healthy)

analyze_training.py --deep HMM regime structure is a clean discriminator across the dr-harder 2x2: teacher = SINGLE regime (healthy plateau); E1 (kl_ub 0.12) = TWO regimes (warmup state mean_reward=-222 + operating state +239, sharper warmup from wider trust region); E2 (ocean 0.3) = a DESTRUCTIVE low-reward regime (state mean_reward=-348.29, dur=37, self-transition 0.97) alongside high state +282.79, i.e. the policy oscillates into a bad mode -> pairs with its entropy collapse (-0.63). Use HMM regime count + worst-state mean_reward as an overfit/instability signal, not just final scalars. Re-visit: diagnose-20260606-180317 REGIMES blocks.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["diagnose-20260606-180317"]
## Comments
