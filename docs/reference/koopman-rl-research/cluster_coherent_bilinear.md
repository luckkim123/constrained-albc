## Resolved Citations

Pulled directly from the survey's bibliography (Read, pages 17–20) and cross-checked against in-text usage (Sec. II-C.3, p.5; Sec. III-A "Application in Robot Controller Design," p.6; Table I, p.6):

| Ref | Full citation | Confirmed via |
|---|---|---|
| **[37]** | H. H. Asada and J. A. Solano-Castellanos, "Control-Coherent Koopman Modeling: A Physical Modeling Approach," *Proc. IEEE 63rd Conf. Decis. Control (CDC)*, 2024, pp. 7314–7319. arXiv:2403.16306. | Bibliography list + direct quote in Sec. II-C.3: *"The recent control-coherent approach [37] focuses on 'preserving consistency' in the Koopman embeddings under different control inputs... particularly useful for manipulation tasks and underactuated systems."* |
| **[43]** | X. Zhang, M. K. Bouafoura, L. Shi, and K. Karydis, "A Koopman Operator-Based NMPC Framework for Mobile Robot Navigation under Uncertainty," *Proc. European Control Conf. (ECC)*, 2025, pp. 2523–2530. arXiv:2504.21215. | Bibliography list + Table I (Wheeled Robots row, "Physics-informed" lifting → NMPC → [43]) + Sec. III-A quote: *"Bilinear Koopman model realizations have been explored recently (e.g., [43]) to combine some of the advantages of linear and nonlinear models [97]."* |
| **[97]** | D. Bruder, X. Fu, and R. Vasudevan, "Advantages of Bilinear [Koopman] Realizations for the Modeling and Control of Systems with Unknown Dynamics," *IEEE Robot. Autom. Lett.*, vol. 6, no. 3, pp. 4369–4376, Jan. 2021. arXiv:2010.09961. | Same Sec. III-A quote above, plus bibliography entry. |

All three were fetched and read in full (arXiv HTML/PDF, not abstracts only).

---

## [37] Control-Coherent Koopman Modeling (Asada & Solano-Castellanos, CDC 2024)

**Mechanism.** The state is split as $x_t = [p_t; q_t]$: $p_t$ is a set of state variables *directly and only* driven by $u_t$ (an "actuation subsystem," Def. 1: $p_{t+1}=f_p(x_t,u_t)$, $q_{t+1}=f_q(x_t)$, $\partial f_{p,i}/\partial u_t \neq 0$). If that actuation subsystem is additionally **exactly linear in $u$** in its own local coordinates (Def. 2: $p_{t+1}=h(x_t)+B_p u_t$ — true of e.g. a DC-motor rotor, $I\ddot\phi=\tau_m-\tau_{load}$, where $\tau_m$ is the input), then the method (a) subtracts the *known* linear term to form a shifted autonomous system $\tilde p_{t+1}=p_{t+1}-B_pu_t=h(x_t)$, (b) computes the Koopman operator $A$ of this purely autonomous system (standard EDMD/RBF lifting on $q$, no lifting needed on $p$ since it is already linear), then (c) adds the known $B_pu_t$ term back. Result: $z_{t+1}=Az_t+Bu_t$ with $B=\begin{bmatrix}B_p\\0\end{bmatrix}$ **exact by construction**, never fit by regression.

**Failure of naive DMDc it fixes.** Standard DMDc solves $(\hat A,\hat B)=\arg\min\sum\|z_+-Az_--Bu_-\|^2$ jointly — nothing in this objective enforces the causally-required zero block in $B$. The paper shows this is invisible in *open-loop* prediction error but fatal once the model drives an MPC: DMDc's fitted $B$ lets torque commands appear to move joint *angles* directly and instantaneously (impossible physically — torque only accelerates; angle changes only over two discrete steps), and the MPC optimizer exploits this phantom pathway.

**Evidence (numbers, 2-link planar arm, MPC tracking, cm):**

| Trajectory radius | CCK | DMDc | Bilinear [97] |
|---|---|---|---|
| 5 cm | 0.76 | 1.06 | 0.95 |
| 25 cm | 1.75 | 13.53 | 1.78 |
| 40 cm | 1.70 | 37.74 | 2.33 |

DMDc is 8–22× worse than CCK on the larger trajectories, **despite the one-step prediction-error histograms being essentially identical** (mean $4.557\times10^{-3}$ CCK vs $4.557\times10^{-3}$ DMDc vs $4.581\times10^{-3}$ bilinear — Fig. 4). An isolating ablation (Fig. 5: keep $A_{DMDc}$, swap in $B_{CCK}$) drops DMDc's error from 37.74 cm to 0.82 cm, attributing the entire failure to $B$'s structure, not $A$.

**Assumptions / guarantees.** This is a *constructive Proposition* (proven by direct algebraic construction), not a statistical error bound. It requires: (1) an actuation subsystem exists with independent state $p$ (Remark 2 — needs power-train compliance or similar so $p,q$ are dynamically distinct, not algebraically coupled); (2) that subsystem is **exactly** (not approximately) linear in $u$ in the *local actuator coordinates*; (3) the observable set includes $p$ itself. No error analysis is given for the case where (2) only holds approximately.

**Maturity.** CDC 2024, single simulated 2-DOF planar arm, no hardware, no theory beyond the exact-linear-actuator case.

**Caveat on the survey's framing:** the survey paraphrases [37] as improving "generalization to new control sequences" and yielding embeddings "robust to input variability" — the paper itself does not run a novel-control-sequence generalization experiment; its only empirical claim is the MPC-tracking result above. Flagging this as the survey's gloss going somewhat beyond what [37] demonstrates.

---

## [97] Advantages of Bilinear Koopman Realizations (Bruder, Fu, Vasudevan, RA-L 2021)

**Formal definitions (Def. II.1).** Over an observable set $\{z_i\in\mathcal Z\}$ (functions of state only):
- **Bilinear** realization: $\dot z_i=\sum_j a_{ij}z_j+\sum_j b_{ij}u_j+\sum_j\sum_k h_{ijk}z_ku_j$
- **Linear** realization: same with all $h_{ijk}=0$ — i.e. exactly the affine-in-input form $\dot z=Kz+Bu$ our KIPPO ansatz uses (modulo the encoder $\phi_u$).

**Theorem II.1 (necessary and sufficient conditions, exact statement).** The realization over $\bar{\mathcal Z}$ is:
1. **Bilinear** iff $\frac{\partial z_i}{\partial x}F \in \text{span}(\bar{\mathcal Z}\cup\mathcal U\cup\{f\cdot g\,|\,f\in\bar{\mathcal Z},g\in\mathcal U\})$ for all $i$, and $\mathcal X\subset\text{span}(\bar{\mathcal Z})$.
2. **Linear** iff the *stronger* $\frac{\partial z_i}{\partial x}F \in \text{span}(\bar{\mathcal Z}\cup\mathcal U)$ holds — no state–input product terms needed.

**Corollary II.1 (proof given).** Every **control-affine** system $F(x,u)=F_x(x)+\sum_jF_u^j(x)u_j$ admits a valid (possibly infinite-dimensional) **bilinear** realization over *any* basis of $\mathcal Z$ (generic polynomial/Fourier/RBF dictionaries all work) — because $\partial z_i/\partial x \cdot F_u^j(x)$ is itself a function of $x$ only, hence expressible in $\bar{\mathcal Z}$, hence its product with $u_j$ is exactly a bilinear term by the chain rule. **No such guarantee exists for a linear (affine-in-$u$) realization** — nothing forces $\partial z_i/\partial x\cdot F_u^j$ to be state-*independent*.

**Consequence for dictionary growth, verified empirically (3-link planar arm, torque input, monomial bases up to $\rho=6$, 927 basis functions):** linear-model normalized prediction error stays flat at ~0.55–0.60 from 10 to 927 basis functions; bilinear and nonlinear models drop monotonically to ~0.03–0.05 with far fewer basis functions (336 and 220 respectively). This is the direct empirical signature of the theorem: a linear realization for this system likely **does not exist**, at any dimension.

**MPC evidence (numbers):**

| Controller | Mean tracking error (cm) | Mean compute time (ms) |
|---|---|---|
| K-MPC (linear/affine) | 74.3 | 6.11 |
| K-BMPC (bilinear) | 2.03 | 9.6 |
| K-NMPC (nonlinear) | 1.92 | 1160 |

Bilinear is >36× more accurate than affine, near-matches full-nonlinear accuracy, at >500× less compute than nonlinear (achieved by freezing the bilinear term's lifted-state factor at $z[0]$ over the MPC horizon, turning it into a convex QP per step — Eqs. 45–46).

**What drives the gap:** any state-dependence of the input's effect, $\partial F/\partial u$ depending on $x$ — for the arm this is $H(\theta)^{-1}$ (configuration-dependent actuation gain); structurally identical to a UUV thruster whose delivered force/torque gain depends on vehicle velocity (drag/added-mass coupling) or fault state.

**Maturity.** RA-L 2021, single simulated 3-link arm, no hardware — but this is the **theoretically strongest** of the three: a proven necessary-and-sufficient condition plus a general corollary (holds for any control-affine system, not just this arm).

---

## [43] Koopman-based NMPC for Mobile Robot Navigation under Uncertainty (Zhang, Bouafoura, Shi, Karydis, ECC 2025)

**Mechanism.** Uses exactly [97]'s bilinear form: $\dot z=Az+Bu+H(u\otimes z)$, applied to a differential-drive robot under **input-scaled** stochastic disturbance — $v_t=\beta v,\ v_s=\alpha v,\ \omega_s=\gamma\omega$ with $\alpha,\beta,\gamma\sim\text{Exp}(1/\lambda)$ — i.e. perturbation magnitude scales *with the commanded input*, structurally the same shape as thruster fault DR (a degraded thruster delivers a state/fault-dependent fraction of nominal command). Lifting dictionary is deliberately minimal and physics-informed: $\phi(x)=[1,x,\cos\psi,\sin\psi]$, because differential-drive kinematics are a textbook bilinear system (control × trig terms). Identification is closed-form least squares: $[A,B,H]=Z'[Z,U\otimes Z,U]^+$. Design choice distinct from [97]: dynamics predicted in lifted bilinear space, but constraints/optimization kept in original state space to control NMPC compute cost.

**Evidence (numbers):**
- Nominal ($\lambda=0$): both standard and Koopman-NMPC succeed; Koopman ~11% faster.
- Small input-scaled perturbation ($\lambda=0.01$–$0.03$): standard NMPC fails 80–100% of trials; Koopman-bilinear-NMPC still succeeds.
- Moderate uncertainty ($\lambda\geq0.05$): standard NMPC 100% failure; Koopman-NMPC retains 60–80% success.
- Gazebo digital twin (ROSbot2.0): 60% success on tightly-spaced-obstacle maps, mean position error 0.09 m.
- Hardware (motion capture): 88% overall success across 10 obstacle configs × 5 trials; held-out prediction RMSE 5.55%.

**Maturity.** ECC 2025 — the only one of the three validated sim → digital twin → real hardware, though on a much simpler (3-state unicycle) plant than a 6-DOF UUV.

---

## Answers to the Cluster's Three Key Questions

**(1) What is "control coherence" formally, and what EDMDc failure does it fix?**
Formally (per [37]), control coherence = the lifted input matrix $B$ has the *causally correct sparsity structure* — nonzero only in the block corresponding to the directly-actuated observables, zero everywhere else — obtained by physical construction rather than least-squares fit. It fixes a failure that is **invisible in one-step prediction error** (DMDc and CCK have near-identical prediction-error histograms) but catastrophic under closed-loop MPC (8–22× worse tracking, Table I above), because DMDc's regression has no mechanism to prevent a physically-impossible direct control→non-actuated-state coupling from appearing in $B$, and the MPC optimizer exploits it. Evidence is the Table I numbers plus the $B$-only ablation (Fig. 5) isolating the effect to $B$. Note this is a narrower, more literal claim ("$B$'s zero-pattern must match true actuator causality") than the survey's looser gloss about "coherence under varying control inputs" / "generalization to new control sequences," which [37] does not directly test.

**(2) When do bilinear forms measurably beat affine — what properties, what numbers?**
Per [97]'s theorem: whenever the system is control-affine but the input's effect on the chosen observables is *state-dependent* (i.e. $\partial z_i/\partial x\cdot F_u^j$ is not constant across the dictionary) — concretely, whenever actuation gain depends on state (configuration-dependent $H(\theta)^{-1}$ for a robot arm; by direct analogy, drag/added-mass-coupled or fault-scaled thruster gain for a UUV). Numbers: prediction error flat (~0.55–0.60 normalized) for linear vs. dropping to ~0.03–0.05 for bilinear/nonlinear as dictionary grows; MPC tracking error 74.3 cm (linear) vs 2.03 cm (bilinear) vs 1.92 cm (nonlinear) — a >36× gap — at near-linear compute cost for bilinear. [43] shows the same pattern operationally: standard (non-bilinear-aware) NMPC success collapses to 0–20% under input-scaled disturbance while bilinear-Koopman-NMPC retains 60–100%, with the gap widening as the disturbance (≈ actuator-nonlinearity/fault magnitude) grows.

**(3) For the ESC-filter → quadratic thrust map → fault-DR chain: is affine-in-encoded-action adequate, or is bilinear $z(x)\otimes u$ needed?**
All three sources converge on the same answer: **bilinear coupling is needed; affine-in-encoded-action is not adequate**, for a specific and checkable reason.

Apply [97]'s litmus test directly: is the full actuation path (raw action → ESC filter state → quadratic force map → body-frame force/torque, modulated by hydro coefficients and fault DR) control-affine in $a_t$? Structurally yes — each thruster's contribution is additive, $\sum_j F_u^j(x_{\text{full}})\cdot[\text{function of }a_{t,j}]$, with $F_u^j$ depending on state via drag/added-mass and on fault DR via a state/fault-scaled gain. Given control-affine structure, [97]'s Corollary guarantees a **bilinear** realization exists and converges with dictionary size, but gives **no such guarantee for an affine-in-input realization regardless of dictionary richness** — the missing ingredient is *state-dependence*, not encoding richness. Making $\phi_u$ a nonlinear learned encoder of $a_t$ does not supply this: $B\,\phi_u(a_t)$ is still, in [97]'s exact taxonomy, a "linear (affine-in-input) realization" with a richer input feature — it remains the form whose approximation error was empirically flat/non-improving in Fig. 2. The theorem's cross term is specifically $z(x)\otimes u$ (state observable × input), not "input encoded more richly."

[43] is a directly on-point worked example: a control-affine system with an **input-scaled disturbance** (structurally the shape of thruster fault DR) is handled with exactly a bilinear $H(u\otimes z)$ term, and standard non-bilinear NMPC's success rate collapses precisely as that disturbance grows — the failure mode the aux-model risks if it stays purely affine.

[37]'s fix is complementary, not competing: it argues for *structured sparsity* in $B$ rather than richer bilinear terms, but its exactness guarantee only holds where the actuator truly is affine in $u$ in local coordinates — that is at most the ESC-filter's own internal state (a genuine first-order LTI filter), *before* the quadratic thrust map and fault modulation. Since the quadratic map and fault DR sit strictly between the filter and the rigid-body dynamics and are themselves state/fault-dependent nonlinear maps, CCK's exact-$B$ construction cannot cover a $\phi_u(a_t)$ that already spans the whole actuation chain — applying it would require decomposing $\phi_u$ down to the filter-state level and pushing the map/fault nonlinearity into a bilinear coupling on $\phi_x$ anyway.

**Recommendation implied by the cited literature:** extend the planned aux-model to
$$\phi_x(o_{t+1}) \approx K\,\phi_x(o_t) + B\,\phi_u(a_t) + H\big(\phi_u(a_t)\otimes \phi_x(o_t)\big)$$
i.e. [97]/[43]'s bilinear form, not a purely affine one. If the team wants to retain [37]'s "no phantom pathway" discipline, $H$ should be scoped/sparsified to touch only the lifted-state components plausibly carrying hydrodynamic/fault information, rather than left dense — CCK's core lesson is that an unconstrained fitted coupling matrix can achieve excellent prediction error while still encoding a physically incoherent pathway that a downstream controller (here, the RL policy or any model-based component reading $\phi_x$) can exploit.

**Explicit limitation:** none of the three papers studies a UUV thruster system (ESC filter + quadratic thrust map + fault DR); the conclusion above is a structural-analogy argument (control-affine plant with state/fault-dependent actuation gain) grounded in [97]'s proven theorem and [43]'s closely analogous input-scaled-disturbance experiment, not a directly transferable empirical result for this exact plant. Also unverifiable from the fetched material: any quantitative error bound for the bilinear form on a 6-DOF, multi-thruster, heavily-DR'd system — [97] gives existence/convergence, not a convergence *rate*; [37] gives exactness only under the exact-affine-actuator precondition; [43] gives only empirical success/error numbers on a much simpler 3-state unicycle plant.

## Sources

- [Control-Coherent Koopman Modeling: A Physical Modeling Approach (arXiv:2403.16306)](https://arxiv.org/abs/2403.16306) — full PDF read
- [Advantages of Bilinear Koopman Realizations for the Modeling and Control of Systems with Unknown Dynamics (arXiv:2010.09961)](https://arxiv.org/abs/2010.09961) — full PDF read
- [A Koopman Operator-based NMPC Framework for Mobile Robot Navigation under Uncertainty (arXiv:2504.21215)](https://arxiv.org/html/2504.21215v1) — read via WebFetch summary of full text
- [Koopman Operators in Robot Learning survey (arXiv:2408.04200 / IEEE T-RO vol.42, 2026)](https://arxiv.org/pdf/2408.04200) — local PDF at `/workspace/references/Koopman Operators in Robot Learning.pdf`, pages 5–6, 7–9, 13–14, 17–20 read directly