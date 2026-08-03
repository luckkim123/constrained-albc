## Axis A: Time-Delay / Hankel (HAVOK-style) Koopman with Control and Learning

### 1. Theory — does delay embedding recover hidden states or slowly-varying parameters?

**Recovers hidden STATES: well-established, strong evidence.**

- **Brunton, Brunton, Proctor, Kaiser, Kutz, "Chaos as an intermittently forced linear system," *Nature Communications* 8:19 (2017)** — the HAVOK paper. Builds a Hankel matrix from a *scalar* Lorenz measurement x(t), takes its SVD to get eigen-time-delay coordinates, and shows the leading r−1 coordinates obey a near-linear ODE forced intermittently by the r-th coordinate. That forcing term is effectively standing in for the unmeasured y(t), z(t) — i.e., delay embedding of one channel recovers enough of the hidden phase-space structure to explain lobe-switching. This is the concrete case of Takens-type hidden-state recovery the axis asks about.
- **Kamb, Kaiser, Brunton, Kutz, "Time-Delay Observables for Koopman: Theory and Applications," arXiv:1810.01479 (SIAM J. Applied Dynamical Systems 19(2), 2020).** Proves delay-coordinate representations of the Koopman operator are *system-independent/universal* given a fixed observable basis, and gives the analytic theory underpinning why HAVOK's forced-linear decomposition works. This is the rigorous companion to the 2017 empirical paper.
- **Bakarji, Champion, Kutz, Brunton, "Discovering governing equations from partial measurements with deep delay autoencoders," *Proc. Roy. Soc. A* 479:20230422 (2023), arXiv:2201.05136.** Directly targets the "hidden variable" problem: given only partial/incomplete measurements, Takens guarantees a delay-embedded attractor diffeomorphic to the full-state one, but the coordinate map back to a low-dimensional manifold is unknown — they learn it with a deep autoencoder on delay coordinates and recover closed-form sparse dynamics on Lorenz/Rössler/Lotka-Volterra and a real chaotic-waterwheel video. Confirms delay embedding + learning can reconstruct hidden state manifolds from partial observables, not just linearize known ones.

**Recovers slowly-varying PARAMETERS: theoretically plausible but NOT directly established for pure delay embedding — this is a gap, not a citation.**

- The Koopman literature does have an established technique for parameters: **augment the state with the parameter as an extra channel with (near-)zero drift**, which is why it shows up as an eigenvalue-≈1 ("quasi-static") Koopman mode — e.g. a battery SOC study reports a dominant integrator-type mode at λ=1.000001 (arXiv:2607.07594), and "Propagating Parameter Uncertainty in Power System Nonlinear Dynamic Simulations Using a Koopman Operator-Based Surrogate Model" (arXiv:2304.00147) explicitly augments the ODE system with dθ/dt≈0 parameter states and casts the combined system into a Koopman surrogate.
- **But that trick uses an explicit extra state channel, not implicit recovery from delay-embedding the physical observables alone.** I found no paper that shows plain time-delay embedding of proprioceptive signals (with no explicit parameter channel) provably yields eigenvalue-1 modes tracking payload/current/fault parameters. The inferential bridge is real (if you treat "physical parameter + fast state" as one skew-product system, it's technically autonomous and Takens-type arguments could in principle apply over a long-enough window) but it is my own inference from the state-recovery + augmented-parameter-state literatures combined, not a verified result. State this as an open theoretical question if the report needs a hard claim.

### 2. Practice — choosing delay window length/stride vs system timescales

Guidance across the literature is **thin and largely ad hoc**, which is itself a finding:

- Classical dynamical-systems heuristics (not control- or Koopman-specific): mutual-information minimization for the lag τ and false-nearest-neighbors for the embedding dimension (Kantz–Schreiber-style methods); a 2023 AIP *Chaos* paper adds a persistent-homology-based delay selector as an alternative (pubs.aip.org/aip/cha/article/33/3/032101).
- Robot-control-specific: **Yang & Bhounsule, "Koopman Operator Based Time-Delay Embeddings and State History Augmented LQR for Periodic Hybrid Systems," arXiv:2507.14455 (2025 preprint, not peer-reviewed)** cite Takens' lower bound (delays d > 2n+1) but in practice just set the delay count to span "one periodic cycle" (e.g. N=110 delays ≈ 1.1 s for a pendulum of period 1.14 s) — no systematic sweep or timescale-matching rule is given.
- **Sakib & Pan, "Learning Noise-Robust Stable Koopman Operator for Control with Hankel DMD," arXiv:2408.06607 (2024)** pick delay order N=2–4 empirically per task (CartPole, Mountain Car, Panda arm) and explicitly note there is no principled method tying N to system timescales.

Net: nobody in the control/robotics-Koopman literature has solved window selection systematically; it's picked per-system by matching an obvious period (for periodic systems) or by small-N trial and error (for RL-style tasks).

### 3. Delay-embedded Koopman features feeding a LEARNED POLICY (not MPC)

**This combination is essentially absent from the literature I could verify.** Every concrete delay-Koopman + control paper found uses LQR or MPC downstream of the Koopman/EDMD fit, not a learned RL policy:
- arXiv:2507.14455 → offline-fit A,B matrices → standard LQR.
- arXiv:2408.06607 → nonlinear MPC convexified via the learned Koopman model.
- Hankel-DMDc ship papers (arXiv:2502.15782, and the moored-ASV Bayesian-HDMDc paper, doi:10.3390/jmse13122267) → system identification / motion prediction only, no control loop shown.

**RoboKoop (Kumawat, Chakraborty, Mukhopadhyay, CoRL 2025, arXiv:2409.03107)** is the closest "Koopman + RL" precedent, but it builds a *contrastive spectral Koopman embedding from raw camera frames* for off-policy RL — it is not a time-delay/Hankel embedding of proprioceptive state, so it doesn't actually instantiate the HVOK mechanism this axis is investigating.

**Conclusion for Q3: unverifiable as a direct precedent.** No paper found wires explicit time-delay/Hankel-lifted features into an RL actor analogous to our phi_x(o_t) setup — this is a genuine literature gap, stated as such rather than filled with a fabricated citation.

### 4. Applicability to our stack

**What we already have vs. what HVOK-style lifting actually adds.** Our 72D o_t is *already* a hand-designed partial delay embedding: 30D tracking history (10 features × 3 past steps, stride 3) + 16D action history + a 3D leaky-integral error + a 3D bias-EMA. That bias-EMA is itself a crude hand-built analog of a Koopman "slow/quasi-static mode" (an EMA is a first-order low-pass — approximately an eigenvalue-near-1 filter) — i.e. we already have an ad hoc instrument aimed at exactly the same target (slow bias/parameter drift) that HVOK's forcing decomposition formalizes.

The critical distinction the literature makes clear: **HVOK's actual mechanism is not "more raw delayed channels," it's the SVD/DMD step that extracts a low-rank near-linear subspace + explicit forcing structure from a (possibly much longer) Hankel matrix.** Simply handing the already-delay-embedded 72D obs to a learned phi_x with recon/prediction aux losses is a different mechanism — it induces linear-subspace structure via a *learned loss*, not via the *imposed* linear-algebraic structure (SVD on Hankel blocks) that gives HAVOK its guarantees. Testing "does HVOK-style lifting help" properly means implementing genuine Hankel-SVD/EDMD-with-control-style structure (or a learned analog constrained to mimic it), not just widening the observation window.

**Blockers:**
1. No verified theory or empirical result shows plain delay-embedding (without an explicit parameter channel) makes DR parameters (payload, current, thruster fault) identifiable as eigenvalue-1 modes — the mechanism is plausible by extension of the augmented-parameter-state Koopman trick, but unconfirmed for this setting.
2. No precedent for wiring delay-Koopman features into an RL actor (all found work is LQR/MPC) — integration risk with ConstraintTRPO+IPO is untested territory, not just unhopeful but literally unexplored.
3. Window/stride selection has no transferable guidance; the one robot-control paper that tried it picked window ≈ one system period ad hoc. Our target parameters (current period ~O(10s), thruster faults persistent for the whole episode) operate on a timescale far longer than our existing 3-step/stride-3 window (a handful of control steps) — an HVOK-style attempt at parameter identifiability via Takens argument would need a Hankel window orders of magnitude longer than what o_t carries today, which is a substantial architecture change (large delay buffer + SVD/DMD fitting or a learned equivalent), not a drop-in swap for the "raw 72D obs" comparison arm.
4. This axis is explicitly about the actor's phi_x — allowed under the no-aux-loss rule (that rule targets only the privileged p_t→z encoder), but the engineering lift for #3 is real and the payoff is currently evidence-free for our exact use case.

**Verdict: STRETCH.**

The theoretical direction is genuinely on-target (delay-coordinate slow modes are the closest classical-Koopman analog to what our privileged encoder does by supervision, and our own bias-EMA is already an informal instance of the same idea), but three things keep it out of APPLICABLE-NOW: no RL-policy precedent, no timescale-matched window-selection guidance, and a required window length that is structurally incompatible with the current 3-step/stride-3 design — meaning a fair test needs new infrastructure (a much longer Hankel buffer + explicit SVD/DMD-style structure in phi_x), not a comparison against the existing 72D obs as-is.

## Sources

- [Chaos as an intermittently forced linear system — Brunton et al., Nature Communications 8:19 (2017)](https://www.nature.com/articles/s41467-017-00030-8)
- [Time-Delay Observables for Koopman: Theory and Applications — Kamb, Kaiser, Brunton, Kutz, arXiv:1810.01479](https://arxiv.org/abs/1810.01479)
- [Discovering governing equations from partial measurements with deep delay autoencoders — Bakarji, Champion, Kutz, Brunton, arXiv:2201.05136 (Proc. Roy. Soc. A 479:20230422, 2023)](https://arxiv.org/abs/2201.05136)
- [Koopman Operator Based Time-Delay Embeddings and State History Augmented LQR for Periodic Hybrid Systems — Yang & Bhounsule, arXiv:2507.14455 (2025 preprint)](https://arxiv.org/abs/2507.14455)
- [Learning Noise-Robust Stable Koopman Operator for Control with Hankel DMD — Sakib & Pan, arXiv:2408.06607 (2024)](https://arxiv.org/abs/2408.06607)
- [Propagating Parameter Uncertainty in Power System Nonlinear Dynamic Simulations Using a Koopman Operator-Based Surrogate Model, arXiv:2304.00147](https://arxiv.org/pdf/2304.00147)
- [Koopman Spectral Analysis of Lithium-Ion Battery Dynamics: State of Charge as a Marginally Stable Observable, arXiv:2607.07594](https://arxiv.org/pdf/2607.07594)
- [RoboKoop: Efficient Control Conditioned Representations from Visual Input in Robotics using Koopman Operator — Kumawat, Chakraborty, Mukhopadhyay, CoRL 2025, arXiv:2409.03107](https://arxiv.org/abs/2409.03107)
- [Model-free system identification of surface ships in waves via Hankel dynamic mode decomposition with control, arXiv:2502.15782](https://arxiv.org/html/2502.15782v1)
- [System Identification of a Moored ASV with Recessed Moon Pool via Deterministic and Bayesian Hankel-DMDc, JMSE 13(12):2267](https://doi.org/10.3390/jmse13122267)
- [Selecting embedding delays: An overview of embedding techniques and a new method using persistent homology, AIP Chaos 33(3):032101 (2023)](https://pubs.aip.org/aip/cha/article/33/3/032101/2881154/Selecting-embedding-delays-An-overview-of)