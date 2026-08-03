## Critic/Value-Side Koopman Integration — Research Findings

### 1. Koopman-Assisted RL (KARL) — Rozwood, Mehrez, Paehler, Sun, Brunton, NeurIPS AI4Science 2023 / arXiv:2403.02290

**Mechanism.** Lifts *state* into a fixed polynomial dictionary φ(x) (monomial order 1–4, tuned per system) and *action* into a separate dictionary ψ(u) (also order 1–4). The lifted feature space is the Kronecker product ψ(u)⊗φ(x). A "controlled Koopman tensor" M is fit once, offline, by ordinary least squares on ~30,000 random-policy transitions: `min_M Σ‖M(ψ(u_i)⊗φ(x_i)) − φ(x'_i)‖²` (closed-form, no gradient descent, no learned dynamics model needed beyond this regression). The value function is then **not a neural network** but a linear-in-features form `V_w(x) = w^T φ(x)`, and the Koopman-critic target is `Q̂(x,u) = r(x,u) + γ w̄^T K^u φ(x)`, where `K^u` is the action-conditioned slice of the Koopman tensor — i.e., the entire NN critic is **replaced**, not augmented. This is used to reformulate two max-entropy algorithms: soft Koopman value iteration (SKVI) and soft actor Koopman-critic (SAKC), built on CleanRL. Policy loss stays standard SAC (KL-matching).

**Evidence.** Tested only on 4 low-dimensional (2–3D state) systems: linear state-space, chaotic Lorenz, fluid flow past a cylinder, stochastic double-well. SAKC "outperforms all other approaches" on the double-well and beats SAC variants on cylinder flow; on Lorenz all three actor-critic variants (SAC, SKVI, SAKC) are statistically indistinguishable and all beat value iteration; linear system results were statistically indistinguishable across methods (relegated to appendix). Reported via IQM + 95% bootstrap CIs, 25 seeds. Authors explicitly state KARL "does not extend to Atari and Mujoco" and is "currently limited to discrete-time" low-dim systems — this is an acknowledged, not resolved, limitation.

**Maturity.** Simulation-only, low-dimensional toy systems, no real hardware. Code released: `github.com/dynamicslab/KoopmanRL`, dataset on HuggingFace.

**Verdict: NOT-APPLICABLE.** KARL wholesale-replaces the critic with a linear-in-dictionary-features model fit by one-shot OLS from a fixed dictionary — this only works because the 4 test systems are 2–3D and (relatively) stationary; our system is 72D obs / 28D DR-randomized physical params with heavy, continuously-varying hydrodynamics/payload/current/fault randomization, and the paper's own stated limitation (no Mujoco-scale results) is a direct admission this doesn't scale to our regime.

---

### 2. Robust Koopman Control Barrier Filters for Safe Actor-Critic RL — arXiv:2605.26452

**Mechanism.** Learns a data-driven Koopman predictor that lifts nonlinear dynamics into a space where they behave affinely, then builds control barrier function (CBF) constraints in that lifted space, enforced via a quadratic-program safety layer that filters the actor's proposed action before execution. To handle Koopman model error under distribution shift, the CBF condition is *tightened* using "a projected residual margin estimated from held-out rollout data" (a robustness margin against Koopman approximation error — conceptually relevant to a heavily domain-randomized plant). Critically for this category: **the critic itself is not architecturally modified** — "the critic is trained on the executed safe action, while the actor is regularized toward the Koopman-CBF feasible set." So this is an action-level safety filter with critic *co-adaptation* (the critic sees the filtered outcome), not a Koopman prediction fed into the critic's input as privileged information.

**Evidence.** "Zero constraint violations on CartPole stabilization and tracking while matching or exceeding unconstrained SAC returns." On Safety Gymnasium locomotion (higher-dim than CartPole but still far below our 72D obs), results are mixed: "reduces violations in some settings but also exposes important limitations of first-order velocity barriers."

**Maturity.** Simulation only (CartPole, Safety Gymnasium); code availability and hardware validation not stated.

**Verdict: STRETCH, and architecturally the wrong shape.** The safety mechanism is a hard action-projection QP layer, not a soft cost-critic term — this is a structurally different paradigm from IPO's interior-point soft barrier and would mean displacing IPO's cost critics rather than composing with them. The Koopman-error robustness-margin *idea* (tighten constraint by a held-out-rollout residual) is a transferable concept for handling DR-induced model mismatch, but the paper's own admitted locomotion-scale limitations argue against assuming it holds at our scale.

---

### 3. KEEC (Koopman Embedded Equivariant Control) — arXiv:2312.01544

**Mechanism.** Learns a Koopman-linearized latent embedding z of state, then learns the value function *as a neural critic over that latent space* via TD(0), satisfying a latent Bellman equation `𝓑*V_g(z_t) = max_a r_g(z_t,a) + γV_g(𝒦Δt z_t)` where the transition inside the Bellman backup is the learned linear Koopman operator. The policy is then **not a separate trained network** — it is derived analytically from the value gradient and Koopman dynamics operator via a Hamilton-Jacobi-style closed form: `π*(z_t) = −[∇_a r_g]^†(γ∇_z V_g^T · 𝒰(z))Δt`. This is model-based optimal control with an implicit greedy policy, not actor-critic RL.

**Evidence.** Sim-only: Pendulum (Gym), Lorenz-63, wave-equation PDE (controlgym). KEEC beats SAC and a PCC (predictive-coding-control) baseline on all three, most dramatically on the PDE task (KEEC −277.6±29.2 vs SAC −1007.6±74.4, PCC −2249.2±133.6). Code released on GitHub.

**Maturity.** Sim-only, low-dim/PDE benchmarks, no real robot.

**Verdict: NOT-APPLICABLE.** KEEC has no actor network at all — the "policy" is an analytic function of the value gradient and Koopman operator. Adopting this would mean replacing our entire TRPO+IPO actor-critic training loop with model-based optimal control, not adding a critic input; incompatible by construction, and again validated only on low-dim/PDE toy tasks.

---

### 4. Boundary case worth flagging: LC-SAC (Lyapunov-Constrained SAC via Koopman) — arXiv:2602.04132

Not actually critic-side (included because it's the closest Koopman+constrained-RL analog to our IPO cost critic, and is easy to mistake for critic-side). EDMD lifts *error dynamics* into a linear space, from which a closed-form quadratic Control Lyapunov Function is derived via DARE; this CLF enters only as a CVaR-weighted Lagrangian penalty on the **actor** loss (`𝓛_π(θ) = 𝓙_SAC + λ(𝓛_v^CVaR − ζ)`). The paper states explicitly the critic is untouched ("avoids training an auxiliary Lyapunov network... critic remains standard SAC dual-head clipped double-Q").

**Evidence — and this is the useful negative signal for us.** On cartpole, LC-SAC-Mean gains +24–25% over vanilla SAC. But on the **3D quadrotor** tasks — the closest analog in this literature to our 6-DOF underactuated UUV — every Koopman-Lyapunov variant *underperforms* vanilla SAC: LC-SAC −15%/−9%, LC-SAC-Mean −8%/−12%, and the reward-shaping variant (Lyap-RS-SAC) collapses catastrophically (−93%/−94%), attributed to the auto-calibrated shaping weight becoming "ill-conditioned in high degrees-of-freedom dynamics." Sim only, 5 seeds, no code-availability statement found.

**Verdict: NOT-APPLICABLE**, but evidentially important: it is direct evidence that naively bolting a Koopman-Lyapunov constraint mechanism onto SAC-family RL *degrades* on the higher-DOF underactuated task class most similar to ours, even before considering our heavier DR.

---

## Composability assessment: Koopman critic-input prediction + our asymmetric TRPO+IPO setup

Our critic is already asymmetric (`cat([o_t 72D, z, p_t 28D])`), so architecturally, appending a SKooP-style H-step Koopman latent prediction as one more concatenated privileged channel is a trivial change — the shallowest possible integration point. But nothing found here (or in the already-reviewed SKooP) provides evidence for the two things that actually matter for us:

1. **Heavy parametric domain randomization.** KARL is explicit that it only works on 2–3D near-stationary systems; none of the 4 papers above test a Koopman operator/predictor under anything resembling our DR range (randomized hydrodynamic coefficients, payload, 0.5 m/s ocean currents, thruster faults). A Koopman operator is a linearization of *one* dynamics family; under our DR, the "true" operator shifts every episode. Either it would need to be conditioned on `p_t` (in which case it functionally duplicates the existing 28D→9D privileged encoder, with the same reconstruction-collapse risk already ruled out for that encoder) or it is fit narrowly and degrades outside its fitting distribution — an untested extrapolation, not a documented result.
2. **Dual advantage + cost-critic (IPO) composition.** Every critic-touching paper found (KARL, the CBF paper) uses a single unconstrained critic. None combine a Koopman-augmented critic input with a *separate* interior-point cost critic. The one paper that does combine Koopman with a Lyapunov-style constraint (LC-SAC) keeps it entirely on the actor side and — on the underactuated 3D task closest to ours — makes things worse, not better.

**Verdict: STRETCH.** The concat-in mechanism itself is cheap and structurally compatible with our existing asymmetric critic, but every piece of supporting evidence in this literature comes from low-dimensional, low-DR, single-critic settings; extending it to our 72D-obs / 28D-DR / dual-critic (TRPO advantage + IPO cost) UUV stack is an unverified extrapolation, and the one closest empirical analog (LC-SAC on 3D quadrotor) argues against assuming a free win.

## Sources

- [Koopman-Assisted Reinforcement Learning (arXiv:2403.02290)](https://arxiv.org/abs/2403.02290)
- [Koopman-Assisted Reinforcement Learning, HTML full text](https://arxiv.org/html/2403.02290)
- [KoopmanRL-NeurIPS project page](https://dynamicslab.github.io/KoopmanRL-NeurIPS/)
- [KoopmanRL-NeurIPS GitHub](https://github.com/dynamicslab/KoopmanRL-NeurIPS/blob/main/index.md)
- [Koopman-Assisted Reinforcement Learning, OpenReview](https://openreview.net/forum?id=IaUDEYN48p)
- [Robust Koopman Control Barrier Filters for Safe Actor-Critic Reinforcement Learning (arXiv:2605.26452)](https://arxiv.org/abs/2605.26452)
- [Robust Koopman Control Barrier Filters, HTML full text](https://arxiv.org/html/2605.26452)
- [Lyapunov Constrained Soft Actor-Critic (LC-SAC) using Koopman Operator Theory for Quadrotor Trajectory Tracking (arXiv:2602.04132)](https://arxiv.org/abs/2602.04132)
- [LC-SAC, HTML full text](https://arxiv.org/html/2602.04132)
- [KEEC: Koopman Embedded Equivariant Control (arXiv:2312.01544)](https://arxiv.org/abs/2312.01544)
- [KEEC, HTML full text](https://arxiv.org/html/2312.01544)
- [SKooP: Symmetric Koopman Predictions for Faster and More Generalizable Legged Robot Locomotion (arXiv:2607.11624)](https://arxiv.org/html/2607.11624) (already reviewed per assignment; cited here only as the additive-critic-input pattern referenced above)