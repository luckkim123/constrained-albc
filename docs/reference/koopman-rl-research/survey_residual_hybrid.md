## Category: Hybrid / Residual Control — RL Policy Fused with a Koopman Model-Based Controller

Two distinct fusion patterns show up in the literature: (A) RL learns a **residual action/policy on top of a Koopman-based nominal model or controller**, and (B) RL **tunes the parameters of a Koopman-MPC** rather than adding an action. A third, non-RL but structurally identical pattern — **supervised residual Koopman models plugged into MPC** — is included because it's the most evidence-rich validation that the "nominal Koopman + additive correction" architecture works on real hardware, and it directly answers the applicability question for our stack.

### 1. KORR — Robust Online Residual Refinement via Koopman-Guided Dynamics Modeling
**arXiv:2509.12562** (Gong, Lyu, Ding, Xiao, Wang; Sept 2025) — fetched abstract, PDF, and HTML.

- **Mechanism**: A neural lift function φ maps the state into a latent space where a learned linear operator (matrices A, B) predicts `φ(x_{t+1}) ≈ A φ(x_t) + B u_t`. A base policy (imitation-learned) proposes an action; a residual head produces `δu`, and `u_final = u_base + δu`. The key trick: the residual head is conditioned not on the base action alone but on the **Koopman-predicted next latent state** ("imagined state prediction"), giving it a globally-informed, long-horizon-consistent correction signal. There is **no MPC optimization at inference** — Koopman is used as a fast, linear one-step forward-prediction feature generator that conditions a learned residual policy, not as a plant model inside a solved optimal-control problem.
- **Evidence**: IsaacGym, 6-DOF long-horizon furniture assembly (One_Leg, Round_Table, Lamp), 1024 episodes/condition, baseline = ResiP (residual imitation policy, no Koopman conditioning). Quoted numbers (success rate, no-disturbance → with-disturbance):
  - One_Leg (low randomness): ResiP 98.14%→85.35%, KORR 98.73%→90.38%
  - One_Leg (med randomness): ResiP 84.99%→46.09%, KORR 87.21%→52.31%
  - Round_Table (low): ResiP 96.19%→80.27%, KORR 96.78%→81.35%
  - Lamp (low): ResiP 86.58%→60.55%, KORR 89.65%→63.48%
  Gains are consistently a few points, largest (≈6 pts) under disturbance/med-randomness — i.e., the Koopman-conditioned residual buys robustness margin, not raw performance.
- **Maturity**: Simulation only (IsaacGym). No hardware.

### 2. Esfahani, Vaidya, Velni — Performance-Oriented Data-Driven Control: Fusing Koopman Operator and MPC-Based Reinforcement Learning
**IEEE Control Systems Letters, vol. 8, pp. 3021–3026, 2024.** DOI page: https://ieeexplore.ieee.org/document/10808167/ (paywalled; abstract confirmed via search-engine snippet and ResearchGate listing, full text not accessible — flagging this explicitly rather than fabricating detail).

- **Mechanism**: This is pattern (B), not an action-space residual. A Koopman-based MPC (KMPC) is built from a data-driven linear-in-latent-space model, but the linear Koopman model can't capture the true nonlinear plant exactly, so closed-loop performance under the nominal KMPC is suboptimal. The authors **fully parameterize the KMPC's objective function** (cost weights / terminal terms) and use an RL algorithm (deterministic-policy-gradient family, per the related eNMPC literature this paper sits in) to **tune those MPC parameters online against realized closed-loop cost**, rather than tuning the Koopman model itself. RL never outputs a control action directly — it outputs MPC hyperparameters, and the MPC still solves the optimization each step.
- **Evidence**: Abstract-level only. I could not verify the specific test plant, RL algorithm name, or quantitative KMPC-vs-KMPC+RL numbers from accessible sources (IEEE Xplore blocked the fetch, ResearchGate returned 403). Stated declaratively: **the exact numeric results are unverified** — do not treat any number here as confirmed for this paper.
- **Maturity**: Journal-published (peer-reviewed), but evidence depth is limited to what's publicly abstracted. This is part of a broader process-control lineage (companion works: "Sample-Efficient RL of Koopman eNMPC," ScienceDirect 2025; "Leveraging RL and Koopman Theory for Enhanced MPC Performance," arXiv:2505.08122) applied mainly to chemical-process/economic-NMPC systems, not legged/UUV robotics.

### 3. RK-MPC — Residual Koopman Model Predictive Control for Quadruped Locomotion in Offroad Environments
**arXiv:2604.04221** — fetched abstract.

- **Mechanism**: Not RL. A nominal template (reduced-order) model gives the base dynamics; a **compact linear residual predictor is learned via supervised regression in Koopman/lifted coordinates** and added to the template model to correct model mismatch (rough terrain, unmodeled ground contact). The corrected model is embedded directly inside a **convex QP-MPC**, running onboard at 500 Hz — i.e., Koopman-residual-corrected linear model feeding a real-time optimization-based controller, no learned policy in the loop at all.
- **Evidence**: Gazebo sim **and Unitree Go1 hardware**, blind locomotion across grass/gravel/snow/ice. Baselines: EDMD-style Koopman dictionaries (monomial, SE(3)-structured). No numeric success-rate/tracking-error table was extractable from the abstract-level fetch (only qualitative "reliable blind locomotion" claims) — flagging as unverified rather than inventing figures.
- **Maturity**: Hardware-validated (Unitree Go1), the strongest maturity of the four.

### 4. Residual Koopman Model Predictive Control for Enhanced Vehicle Dynamics
**arXiv:2507.18396** — fetched abstract.

- **Mechanism**: Also not RL. A linear kinematic MPC (LMPC) gives a baseline control; a **neural-network residual KMPC computes a compensation input** capturing the nonlinear/unmodeled dynamics; the two control commands are summed. This preserves the interpretability of the mechanistic base model while letting the residual absorb what the linear model misses.
- **Evidence**: Carsim-Matlab sim **and a physical 1:10-scale F1TENTH car**. Quantitative vs. traditional LMPC: lateral error −11.7% to −22.1%, heading error −8.9% to −15.8%, front-wheel steering stability +up to 27.6%; and vs. traditional KMPC, RKMPC needs only **20% of the training data**.
- **Maturity**: Hardware-validated (real 1:10 car), best-documented numbers of the four.

---

## Applicability to Our Stack

**Where it would plug in**: Our attitude-hold/attitude-tracking UUV subsystem is the natural target — a Koopman-linear model of near-hover roll/pitch/yaw-rate dynamics (built from p_t-conditioned rollouts, since we already have privileged physical parameters) could serve as a nominal feedforward/LQR-style base controller, with the trained ConstraintTRPO+IPO policy acting as the residual, mirroring pattern (A)/RK-MPC/vehicle-RKMPC. Alternatively, pattern (B) (RL tunes a KMPC cost) could apply if we ever move the deployed controller off a learned policy entirely onto an MPC — we don't currently have an MPC stage, so this is a bigger structural change.

**Blockers, specific to this stack**:
1. **Thruster faults break the linear nominal model's premise.** Every one of the four papers' residual/base split assumes the *nominal* model stays a reasonable approximation and the residual corrects a bounded mismatch. Our heavy DR explicitly includes thruster faults, which change the input matrix `B` structurally (lost/degraded actuator), not just add bounded disturbance to `A`. A single global Koopman `(A,B)` fit across our full DR distribution (payload, hydrodynamics, ocean current, thruster faults) is a much harder regime than off-road quadruped terrain variation (RK-MPC) or vehicle tire-model nonlinearity (RKMPC) — those are bounded-mismatch problems; actuator dropout is a bounded-authority problem, which a linear residual doesn't fix.
2. **IPO's cost/constraint critics have no natural counterpart in a base-Koopman/residual-RL split.** Our constraint machinery is threaded through the whole trained policy (cost critic + constraint critic + IPO barrier). Making the RL component "just a residual" on top of a fixed Koopman controller would require re-deriving which agent (base or residual) owns constraint satisfaction — none of the 4 papers deal with a constrained-policy formulation as rich as ConstraintTRPO+IPO; RK-MPC and vehicle-RKMPC have no constraint-critic RL at all, and KORR/Esfahani don't either.
3. **No existing UUV precedent for this exact fusion.** A supplementary search found Koopman-MPC for AUVs (no RL) and RL for AUV control (no Koopman) as separate lines, but no paper combining Koopman-residual with RL for underwater vehicles — so any attempt here would be a first-of-kind adaptation, not a transfer of a validated recipe.
4. **Architecture mismatch with our asymmetric-critic design.** Our critic already sees `p_t` directly (28D privileged input) and the actor gets a 9D encoder latent `z` — i.e., we already have a "privileged Koopman-like latent" feeding the value function, just not literally a linear operator. Bolting a *second*, separately-trained Koopman linear model in as a nominal controller duplicates machinery we've already built (and already rejected auxiliary losses for, per the "no encoder auxiliary losses" settled decision) rather than reusing it.

**Verdict: STRETCH.** The architecture pattern (linear/Koopman nominal + learned residual, either action-space or MPC-parameter-space) is validated on hardware in adjacent domains (quadruped, ground vehicle) with concrete double-digit-percent gains, but our thruster-fault DR breaks the bounded-mismatch assumption every cited paper relies on, and none of the 4 papers show how to reconcile the fusion with a constrained-RL (IPO) formulation as rich as ours — both would need to be solved from scratch, not adapted.

## Sources

- https://arxiv.org/abs/2509.12562 (KORR abstract)
- https://arxiv.org/pdf/2509.12562 (KORR full text)
- https://arxiv.org/html/2509.12562 (KORR HTML, results table)
- https://ieeexplore.ieee.org/document/10808167/ (Esfahani/Vaidya/Velni, IEEE CSL 2024, DOI page — abstract accessible via search snippet only, full text paywalled)
- https://www.researchgate.net/publication/387234822_Performance-Oriented_Data-Driven_Control_Fusing_Koopman_Operator_and_MPC-Based_Reinforcement_Learning (blocked, 403 — listing confirms title/authors/venue only)
- https://arxiv.org/abs/2604.04221 (RK-MPC, quadruped)
- https://arxiv.org/abs/2507.18396 (Residual KMPC, vehicle dynamics)
- https://arxiv.org/abs/2505.08122 (companion: RL + Koopman for eNMPC, process control — context only, not a primary pick)
- https://www.sciencedirect.com/science/article/pii/S0098135425002443 (companion: Sample-Efficient RL of Koopman eNMPC — context only)