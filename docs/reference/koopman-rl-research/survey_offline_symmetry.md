## Category: Offline RL / Symmetry / Data Augmentation (Koopman)

### 1. KFC — Koopman Forward (Conservative) Q-learning (Weissenbacher, Sinha, Garg, Kawahara — **ICML 2022 Spotlight**)

**Verified**: [arXiv:2111.01365](https://arxiv.org/pdf/2111.01365), [OpenReview q1QmAqT_4Zh](https://openreview.net/forum?id=q1QmAqT_4Zh), [MLR proceedings PDF](https://proceedings.mlr.press/v162/weissenbacher22a/weissenbacher22a.pdf), [GitHub](https://github.com/matthias-weissenbacher/KFC).

**Mechanism**:
- A bilinear Koopman forward model lifts state `s_t` into a finite-dim latent via encoder `E`, trained with two losses: VAE reconstruction `D(E(s_t)) = s_t`, and forward prediction `D((K_0 + Σ_i K_i a_t,i) E(s_t)) = s_{t+1}` (action-conditioned linear operator `K(a_t)`).
- Symmetry generators `σ_a` are extracted from the learned operator two ways: **KFC** solves the commutation (Sylvester) equation `σ_a · K(a) − K(a) · σ_a = 0`; **KFC++** eigendecomposes `K(a) = U diag(λ) U⁻¹` and builds `σ_a(ε) = Re(U diag(ε_1..ε_n) U⁻¹)`, giving more directions to explore.
- Augmentation: `s̃ = D((𝟙 + ε σ_a) E(s))`, applied identically to `s_t` and `s_{t+1}` (avoids needing to forecast). Applied with probability `p_K=0.8`, else a plain Gaussian state shift.
- Plugs into **CQL**: only the Q-update's `(s_t, s_{t+1})` pair is replaced by the augmented pair; the policy-improvement step and reward are untouched. Pure data-augmentation wrapper around an existing offline actor-critic.

**Evidence** (D4RL normalized return, Table 1 excerpt vs. CQL / S4RL-N / S4RL-Adv baselines):

| Task | CQL | S4RL(𝒩) | S4RL(Adv) | KFC | KFC++ |
|---|---|---|---|---|---|
| antmaze-umaze | 74.0 | 91.3 | 94.1 | 96.9 | **99.8** |
| halfcheetah-medium | 44.4 | 48.8 | 48.6 | 55.9 | **59.1** |
| hopper-medium | 58.0 | 78.9 | 81.3 | 90.6 | **94.2** |
| walker2d-medium | 79.2 | 93.6 | 93.1 | 102.1 | **108.0** |
| kitchen-complete | 43.8 | 77.1 | 88.1 | 94.1 | **94.9** |

Also evaluated on Metaworld/Robosuite (push, pick-place, door-close): "KFC and KFC++ consistently outperform CQL and the two best S4RL variants," with the largest margins on harder tasks. Both degrade on "-random" splits (random-action data gives a poor dynamics/symmetry estimate). **Maturity**: published, code released, but authors note the released CQL codebase "won't reproduce the paper's results" — reference implementation only, not production-grade.

**Follow-up found**: [Equivariant Data Augmentation for Generalization in Offline RL (arXiv:2309.07578, DeepMind, 2023)](https://arxiv.org/abs/2309.07578) — adjacent lineage, *not* explicitly Koopman-operator-framed (checks a learned dynamics model for translation-equivariance + entropy regularizer to grow the equivariant augmentation set). Same problem class (augment a fixed offline dataset via inferred dynamics symmetry) but a different formalism; no confirmed citation link to KFC found. Not pursued further given the category's Koopman focus.

**No genuine on-policy Koopman-symmetry-augmentation paper was found.** Repeated searches for "Koopman symmetry data augmentation" combined with PPO/SAC/on-policy/TRPO surfaced only KIPPO and SKooP (both already excluded per your brief) and general Koopman-dynamics-modeling work, not symmetry-augmentation of on-policy rollout buffers. This looks like an open gap, not a search miss — say so rather than force a citation.

### 2. KATS — Koopman-Assisted Trajectory Synthesis (offline **imitation** learning)

**Partially verified**: [OpenReview UAZCKdd4R7](https://openreview.net/forum?id=UAZCKdd4R7) exists and is indexed (title, abstract-level description confirmed via three independent search snippets); I could not get past OpenReview's CAPTCHA to read the full PDF (tried direct fetch, `ar5iv`-style proxy, and an `r.jina.ai` proxy — all blocked), and could **not find an arXiv mirror or a confirmed acceptance venue**. Treat authorship/exact numbers as unverified; only the mechanism description below is corroborated by multiple independent snippets.

**Mechanism (as described in search snippets, not full-text-confirmed)**:
- Targets covariate shift in offline imitation learning directly — the same failure mode DAgger exists to fix, but without further environment/expert queries.
- Instead of single-step state perturbation (KFC-style), it synthesizes **entire multi-step trajectories** in a learned Koopman latent space, using a "state-equivariant assumption" for tractability and a "refined generator matrix" to control Koopman approximation error accumulating over a full rollout.
- Explicit motivation: single-step augmentation violates system dynamics; naive trajectory-level rollout compounds errors — KATS is positioned as fixing both failure modes at once.

**Evidence**: none I can independently confirm — no accessible table of benchmark results or baselines was retrievable. Do not treat any number for KATS as established.

**Maturity**: apparently a recent (dated Oct 2025) OpenReview submission — likely under review for a 2026 venue, not a published/cited result yet. Low maturity, unverified.

---

## Applicability to our stack

| Method | Where it would plug in | Verdict |
|---|---|---|
| KFC / KFC++ | N/A — no static offline dataset exists in our pipeline | **NOT-APPLICABLE** — teacher training is on-policy ConstraintTRPO+IPO with 4096 live sim envs; KFC's entire premise is augmenting a *frozen* offline dataset for a conservative Q-learning backbone (CQL), which we don't run. |
| Equivariant DA (2309.07578) | N/A, same reason, plus different formalism | **NOT-APPLICABLE** — offline-RL-generalization method, not Koopman, not our setting. |
| KATS | Student DAgger buffer: augment `(o_t history → z_target)` trajectories before/alongside GRU distillation | **STRETCH** |

**KATS is the only piece of this category that touches a real seam in our stack** — student distillation is exactly a fixed-buffer, covariate-shift-sensitive imitation problem, the setting KATS targets. If it worked, it could reduce how many additional teacher rollouts DAgger needs to collect per iteration by synthesizing augmented trajectories in a learned Koopman latent space instead.

Concrete blockers before it's actually usable here:

1. **What gets lifted is undefined for us.** KFC/KATS lift a *stationary system state* into Koopman space. Our natural candidate object is `o_t` (72D obs) or the teacher's `z` target (9D latent) — but `z` is produced by a frozen encoder we've already ruled out adding auxiliary structure to ("no auxiliary losses on the p_t→z encoder" is settled). A Koopman model over `o_t` for augmentation-only purposes (not touching the encoder's training loss) would sidestep that constraint, but nobody has published this variant — it's an extrapolation, not a verified recipe.
2. **Heavy per-episode domain randomization breaks the stationarity assumption both methods lean on.** Hydrodynamic coefficients, payload, ocean current, and thruster faults change the *dynamics itself* across episodes/DR levels. A single global Koopman operator fit across our DR distribution is unlikely to capture a clean symmetry group the way KFC/KATS assume for a roughly-fixed-dynamics offline dataset; would need a `p_t`-conditioned Koopman operator, which is unaddressed in either paper.
3. **Weak motivation relative to their setting.** KFC/KATS exist because offline datasets are scarce and fixed. We are not data-scarce — we can generate more teacher rollouts for the DAgger buffer cheaply in sim (4096 parallel envs). The marginal value of synthetic trajectory augmentation is lower here than in a genuine offline-data-limited robomimic/D4RL setting.
4. **KATS itself is unverified-maturity** — no confirmed venue, no accessible numbers, so even if the mechanism transfers, there's no evidence yet that it beats plain DAgger re-querying.

**Bottom line**: nothing in this category is ready to adopt. If pursued at all, the only defensible next step is a scoped feasibility check — fit a `p_t`-conditioned Koopman forward model on `o_t` from existing teacher rollouts and see whether a stable symmetry generator even exists under our DR distribution — before touching the DAgger pipeline. Not recommended as a near-term experiment given point 3.

## Sources

- [Koopman Q-learning: Offline RL via Symmetries of Dynamics (arXiv:2111.01365)](https://arxiv.org/pdf/2111.01365)
- [Koopman Q-learning — OpenReview (ICML 2022, q1QmAqT_4Zh)](https://openreview.net/forum?id=q1QmAqT_4Zh)
- [Koopman Q-learning — ICML 2022 Spotlight page](https://icml.cc/virtual/2022/spotlight/17726)
- [Koopman Q-learning — MLR Press PDF](https://proceedings.mlr.press/v162/weissenbacher22a/weissenbacher22a.pdf)
- [KFC — GitHub (official code)](https://github.com/matthias-weissenbacher/KFC)
- [Koopman-Assisted Trajectory Synthesis — OpenReview (UAZCKdd4R7)](https://openreview.net/forum?id=UAZCKdd4R7)
- [Equivariant Data Augmentation for Generalization in Offline RL (arXiv:2309.07578)](https://arxiv.org/abs/2309.07578)
- [Guided Data Augmentation for Offline RL and Imitation Learning (arXiv:2310.18247)](https://arxiv.org/pdf/2310.18247) — checked for a KFC citation/comparison, could not confirm (PDF unreadable via fetch tool)