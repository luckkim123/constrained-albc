# Koopman Operators in Robot Learning — Notes from pp.1102–1107 (PDF pages 15–20)

*Page anchors below use the paper's own printed page numbers (1102–1107), which correspond to PDF pages 15–20 of this file.*

## 1. Section-by-section summary

- **(cont.) Optimization-based dictionary learning — consistency index properties** (p.1102): four numbered properties of the consistency index $\mathcal{I}_C$, followed by the closed-form robust minimax formulation (eq. 30) and a pendulum example (Fig. 4) showing it beats residual-error EDMD for long-term prediction.
- **V.B.2) Algebraic Search for Koopman-Invariant Subspaces** (p.1102–1103): introduces Symmetric Subspace Decomposition (SSD) [31],[32] and Tunable SSD (T-SSD) [33], with Fig. 5 (accuracy/expressiveness tradeoff) and Fig. 6 (Duffing oscillator example).
- **VI. Open Directions and Challenges** (p.1103–1104): eight named subsections — *Incorporating constraints into Koopman space*; *Stochastic simulation and belief-space planning*; *Sampling rate selection*; *Extension to fine/dexterous manipulation*; *Further expansion on soft robotics*; *Extension to hybrid systems*; *Uncertainty in lifted features*; *Study of the underlying optimization problems*.
- **VII. Conclusion** (p.1104): summary paragraph closing the survey.
- **Acknowledgment + References [1]–[167]** (p.1104–1107): full bibliography (no body text).

---

## 2. Mathematically precise definitions/algorithms

**Consistency index $\mathcal{I}_C$** (p.1102), properties as stated in text:
1. $\mathcal{I}_C \in [0,1]$.
2. Unlike the residual-error cost (eq. 27, from earlier pages), $\mathcal{I}_C$ depends only on the subspace $\mathrm{span}(\Psi)$, not the specific basis chosen.
3. Under a change of basis, $\mathcal{I}_C$ can be viewed as the maximum eigenvalue of a positive semidefinite matrix $(I - K_F K_B)$ (note: $K_F K_B$ is *not generally symmetric*), enabling standard eigen-solvers.
4. It gives a **tight upper bound on the relative prediction error of EDMD** over the entire subspace:
$$\sqrt{\mathcal{I}_C(\Psi,X,Y)} = \max_{f\in\mathrm{span}(\Psi),\,\|\mathcal{K}f\|_{L_2(\mu_X)}\neq0} \frac{\|\mathcal{K}f-\mathfrak{P}_{\mathcal{K}f}\|_{L_2(\mu_X)}}{\|\mathcal{K}f\|_{L_2(\mu_X)}}$$
where $\mathfrak{P}_{\mathcal{K}f}$ is EDMD's predictor for $\mathcal{K}f$ (referencing eq. 8 from earlier pages) and the $L_2$ norm is computed w.r.t. the empirical measure (eq. 11, earlier pages).

**Robust minimax formulation (eq. 30)** (p.1102) — minimizing the consistency index equals:
$$\min_{\Psi\in\mathrm{PF}} \max_{f\in\mathrm{span}(\Psi),\,\|\mathcal{K}f\|_{L_2(\mu_X)}\neq0} \frac{\|\mathcal{K}f-\mathfrak{P}_{\mathcal{K}f}\|_{L_2(\mu_X)}}{\|\mathcal{K}f\|_{L_2(\mu_X)}}$$
i.e. minimizing the *maximum* EDMD prediction error over the **entire (uncountable)** subspace, as opposed to only the finitely many functions in the residual-error objective — the reason it generalizes/predicts better long-term (Fig. 4). A closed-form expression exists for the inner max. Caveat stated explicitly: optimization-based dictionary selection typically needs a large dataset and is "typically only applicable to offline precomputation of the dictionary" (p.1102).

**Symmetric Subspace Decomposition, SSD** [31],[32] (p.1102): given a finite-dimensional search space spanned by dictionary $\Psi_s$, any basis $\Psi$ with elements in $\mathrm{span}(\Psi_s)$ can be written $\Psi^T(\cdot)=\Psi_s^T(\cdot)C$ for a full-column-rank matrix $C$. $\mathrm{span}(\Psi)$ is Koopman-invariant iff, in the data, the range spaces satisfy
$$\mathcal{R}(\Psi_s(X)^TC) = \mathcal{R}(\Psi_s(Y)^TC) \quad (31)$$
Finding the **largest invariant subspace** in $\mathrm{span}(\Psi_s)$ reduces to finding the $C$ with the maximum number of columns satisfying (31). [31] gives a data-driven necessary-and-almost-surely-sufficient condition to identify all Koopman eigenfunctions in an arbitrary finite-dim function space (via forward/backward EDMD eigendecomposition, referencing eq. 29 from earlier pages); [31]/[32] give an efficient, provably correct SSD algorithm (and a parallel version for high-dim search spaces).

**Tunable SSD, T-SSD** [33] (p.1102–1103): relaxes the exact equality in (31) to *closeness*, controlled by an accuracy parameter $\epsilon\in[0,1]$ that specifies the distance between $\mathcal{R}(\Psi_s(X)^TC)$ and $\mathcal{R}(\Psi_s(Y)^TC)$.
- $\epsilon=1$: no accuracy constraint (up to 100% prediction error) → **T-SSD ≡ EDMD** on the search space.
- $\epsilon=0$: zero prediction error required → **T-SSD ≡ SSD** (maximal Koopman-invariant subspace, exact prediction).
- T-SSD is thus a **generalization of both EDMD and SSD**, trading off accuracy vs. expressiveness (dimension of the identified subspace) via $\epsilon$ (Fig. 5).

**Fig. 4 setup** (p.1102): pendulum $[\dot\theta,\dot\omega]=[\omega,\,-9.81\sin\theta-0.1\omega]$; dictionary family $\Psi(\theta,\omega)=[\theta,\omega,\mathrm{NN}_1,\mathrm{NN}_2,\mathrm{NN}_3]$ (5 functions, NN = feedforward net). Compares consistency-index-optimal subspace vs. residual-error(EDMD)-optimal subspace; the former gives superior long-term prediction.

**Fig. 6 setup** (p.1103): Duffing system $[\dot x_1,\dot x_2]=[x_2,\,-0.5x_2+x_1(1-x_1)^2]$ over $[-2,2]^2$; search space = all polynomials up to degree 10. Right plot = relative EDMD error over the full normalized polynomial basis; left plot = same error for the T-SSD-identified subspace at $\epsilon=0.02$ — visibly much lower error concentrated correctly.

---

## 3. Lifting function design

- **SSD/T-SSD are themselves a lifting-function-design tool**: rather than manually picking a dictionary (polynomial/RBF/Fourier) or optimizing one end-to-end, they **algebraically search a large candidate search space** ($\Psi_s$) for the maximal (SSD) or $\epsilon$-approximately (T-SSD) Koopman-invariant sub-dictionary (p.1102–1103, Figs. 5–6).
- Explicit **known limitation**: "Exact Koopman-invariant subspaces capturing complete information about the dynamics are rare" — a typical/useful approach is instead to allow some bounded, characterized, tunable error via T-SSD (p.1102).
- Optimization-based dictionary selection (consistency-index minimization) has a **practical cost**: needs a large dataset and is "typically only applicable to offline precomputation" — i.e., **not naturally an online/runtime lifting design method** (p.1102).
- **Open challenge — constraint lifting** (p.1103): "how to lift different types of constraints from the original space into the Koopman space requires more research," with a suggestion that the operator's algebraic/geometric structure could help — stated as unresolved, not solved.
- **Open challenge — dimensionality vs. tractability** (p.1104, *Further expansion on soft robotics*): "One fundamental limitation of Koopman-based linearization is the need to lift the system into a high-dimensional space, which can become computationally expensive or even intractable" for continuum/soft-bodied (high-DOF) systems. Dimensionality-reduction/simplified parametric approximations are used as a workaround but "inevitably introduce biases and limit generalizability, particularly in contact-rich scenarios or tasks involving large deformations." How to choose the right lifted description for soft robots "is an open research area" (p.1104).
- **Open challenge — statistical structure of lifted observables** (p.1104, *Uncertainty in lifted features*): most prior work assumes zero-mean Gaussian uncertainty on the approximate Koopman operator; the paper states it is *unclear* whether Gaussian-modeled states (even with control input) push forward into Gaussian-distributed lifted observables, and whether/under what conditions "lifting observables also preserves this statistical structure" — flagged as a key direction for future research, i.e., an acknowledged **open/unsolved issue**, not something the lifting machinery is shown to guarantee.
- **Open challenge — optimization tractability of lifted (bi)linear models** (p.1104, *Study of the underlying optimization problems*): the lifted system is described by a linear (most often) or **bilinear** model; that the higher-dimensional lifted dynamics can be (bi)linear while the original lower-dim dynamics stays nonlinear "may create challenges for solving the underlying optimization problems for control," e.g. recursive feasibility of Koopman-NMPC; "how to design appropriate cost functions that generalize across robotic systems remains open."

---

## 4. Connections to REINFORCEMENT LEARNING / policy learning / state representation

These pages contain **no dedicated "Koopman + RL" open-directions subsection** (the Open Directions list in these pages is: constraints, stochastic/belief-space planning, sampling rate, dexterous manipulation, soft robotics, hybrid systems, uncertainty, optimization tractability — none titled "reinforcement learning"). RL connections here are confined to **citations in the reference list** (titles only, no body-text elaboration on these pages):

- **[2]** J. Kober, J. A. Bagnell, J. Peters, "Reinforcement learning in robotics: A survey," *IJRR* 32(11), 2013 — general RL-in-robotics survey citation (p.1104).
- **[40]** J. Bi, K. Lim, K. Chen, Y. Huang, H. Soh, "Imitation learning with limited actions via diffusion planners and deep Koopman controllers," ICRA 2024 (p.1105) — imitation learning combined with deep Koopman controllers.
- **[41]** Y. Han, M. Xie, Y. Zhao, H. Ravichandar, "On the utility of Koopman operator theory in learning dexterous manipulation skills," CoRL 2023 (p.1105).
- **[42]** H. Chen et al., "KOROL: Learning visualizable object feature with Koopman operator rollout for manipulation," CoRL 2024 (p.1105).
- **[51]** H. N. Esfahani, U. Vaidya, J. M. Velni, "Performance-oriented data-driven control: Fusing Koopman operator and MPC-based reinforcement learning," *IEEE Contr. Syst. Lett.*, 2024 (p.1105) — directly fuses Koopman + RL for control.
- **[103]** P. Rozwood, E. Mehrez, L. Paehler, W. Sun, S. Brunton, "Koopman-assisted reinforcement learning," NeurIPS AI4Science Workshop, 2023 (p.1106) — directly Koopman + RL.
- **[104]** I. Abraham, G. De La Torre, T. D. Murphy, "Model-based learning using Koopman operators," RSS 2017 (p.1106) — model-based learning (RL-adjacent), MIT Press.
- **[116]** B. van der Heijden, L. Ferranti, J. Kober, R. Babuška, "Deepkoco: Efficient latent planning with a task-relevant Koopman representation," IROS 2021 (p.1106) — latent-space planning with Koopman representation.
- **[128]** A. Sinha, Y. Wang, "Koopman operator-based knowledge-guided reinforcement learning for safe human-robot interaction," *Front. AI* 6, 2023 (p.1107) — directly Koopman + RL, safety-focused.

None of these titles is elaborated in the body text on these pages; they appear only as bibliography entries. No claim in the extracted body text says Koopman lifting *replaces* an encoder or RL policy — that claim is not made anywhere on pp.1102–1107.

---

## 5. SYSTEM IDENTIFICATION semantics

- **What SSD/T-SSD "identify"**: a Koopman-invariant (or $\epsilon$-approximately invariant) **linear subspace of observables/eigenfunctions** such that the *finite-dimensional lifted dynamics* obey $g(x_{t+1}) = Kg(x_t)$ exactly or within a bounded error — i.e., they identify a **global (bi)linear representation of the system's dynamics**, not environment/domain-randomization *parameters* (p.1102–1103). This is a structural/spectral system-ID target (invariant subspace + operator $K$ on it), not a latent parameter-inference target.
- **Sampling rate selection** (p.1103): "a practically important question concerns how to select an appropriate sampling rate, particularly in online or adaptive learning scenarios where **model updates depend heavily on the temporal resolution of the data**," citing [166] which shows "insufficient sampling can degrade disturbance estimation and control accuracy." Sampling rate also "governs the error bounds associated with predictions." This is about the *data/model* side of Koopman system ID, not about inferring hidden env parameters.
- **Uncertainty in lifted features** (p.1104): flags that whether Gaussian-distributed states imply Gaussian-distributed *lifted* observables (and hence whether the standard zero-mean-Gaussian operator-uncertainty assumption is valid) is an **open/unresolved question**, especially "with the addition of control input." This directly bears on whether Koopman lifting is a reliable mechanism for representing/propagating uncertain latent conditions — the paper treats it as unproven, not established.
- **Optimization tractability note** (p.1104): the (bi)linear lifted model **does not conflict** with the original dynamics being nonlinear — i.e., Koopman lifting is presented as a *re-representation of known/observed state-transition dynamics* in a linear-in-observables form, not as a mechanism that discovers or estimates unmeasured environment/physical parameters (currents, hydrodynamic coefficients, faults, etc.). No text on these pages claims Koopman lifting performs implicit inference of unobserved (privileged) environment parameters.
- **Stochastic Koopman operator** [65],[164],[165] is invoked only for "stochastic simulation and belief-space planning" under uncertainty (p.1103) — a control/planning research direction, explicitly stated as needing "more work... to study efficient implementation, reliability, and adaptability," not a demonstrated capability.

---

## 6. Underwater/marine/soft/aerial robot applications

- **Conclusion statement** (p.1104): "...across a wide array of robotic domains, including aerial, legged, wheeled, **underwater**, soft, and manipulator robots." (General claim, no specifics on these pages beyond this sentence.)
- **[87]** X. Lin, S. Liu, C. Liu, Y. Wang, "Dynamic modeling of **robotic fish** considering background flow using Koopman operators," IROS 2024 (p.1106) — marine/underwater biomimetic robot, Koopman dynamics model with flow disturbance.
- **[88]** C. Rodwell, J. Buzhardt, P. Tallapragada, "A Koopman operator approach for the pitch stabilization of a **hydrofoil** in an unsteady flow field," ACC 2023 (p.1106) — underwater/marine hydrofoil control.
- **[89]** S. Li, Z. Xu, J. Liu, C. Xu, "Learning-based extended dynamic mode decomposition for addressing path-following problem of **underactuated ships** with unknown dynamics," *IJCAS* 20(12), 2022 (p.1106) — marine surface vessel, EDMD-based.
- Soft robotics (non-marine but discussed at length): explicit **open-challenge subsection** "Further expansion on soft robotics" (p.1104) — see §3 above for the dimensionality/intractability limitation; multiple soft-robot references cited elsewhere in the bibliography (pneumatic actuators, continuum manipulators) but those citation entries themselves are outside pp.1102–1107's body text discussion.
- No AUV/UUV (autonomous/uncrewed underwater vehicle) or manipulator-on-UUV titles found in this reference range.

---

## 7. Stated limitations, open challenges, practical guidance

Direct from **Section VI (p.1103–1104)**, each an explicitly named open problem:

1. **Constraint lifting** (p.1103): no established method to lift general/conflicting constraints from state space into Koopman observable space; "requires more research."
2. **Stochastic simulation & belief-space planning** (p.1103): handling multimodal distributions and robust plans under uncertainty is "vital," advances in stochastic Koopman operator [65],[164],[165] are a possible path, but "more work is needed to study efficient implementation, reliability, and adaptability."
3. **Sampling rate selection** (p.1103): open question of how to pick sampling rate for online/adaptive learning; insufficient sampling degrades disturbance estimation and control accuracy [166]; governs prediction error bounds.
4. **Fine/dexterous manipulation** (p.1103): "emergence of Koopman-based approaches for dexterous manipulation marks a promising expansion," handling contact-rich/discontinuous dynamics; "this specific direction of research is still nascent."
5. **Soft robotics expansion** (p.1104): fundamental limitation = high-dimensional lifting becomes computationally expensive/intractable for high-DOF continuum/soft bodies; dimensionality-reduction workarounds introduce bias and limit generalizability in contact-rich/large-deformation cases; choosing the right soft-robot description for Koopman compatibility is "open research area."
6. **Hybrid systems** (p.1104): discrete-time and continuous-time systems each handled, but hybrid (mechatronic/robotic) systems are "more subtle and has received less attention." A recent result [16] shows unforced heterogeneous hybrid systems can still be lifted, but extending to systems with inputs and broader hybrid-governed evolution "remains open."
7. **Uncertainty in lifted features** (p.1104): zero-mean Gaussian uncertainty assumption on the approximate Koopman operator "should be revisited"; unclear whether Gaussian state models push forward to Gaussian lifted-observable distributions, especially with control input; named as "a key direction of future research."
8. **Underlying optimization problems** (p.1104): (bi)linear lifted-space representation of nonlinear original dynamics can create challenges for control optimization (e.g., recursive feasibility of Koopman-NMPC); designing cost functions that generalize across robotic systems "remains open."

**Practical guidance** (p.1102): optimization-based dictionary-selection methods (consistency-index minimization) "require access to a large dataset and are typically only applicable to offline precomputation of the dictionary" — i.e., not a claimed online/on-the-fly method in this section.

**Conclusion (p.1104)** restates the survey's framing: Koopman operator theory is "a mathematical tool that can enable global linearization by elevating an original nonlinear system to a higher dimensional linear space," covering data collection, lifting-function selection, and controller synthesis as the paper's three described components — with the open-directions list above presented as the current, *unsolved* frontier, not as capabilities already delivered.

---

### Note directly relevant to the two proposals under evaluation

Nothing in pp.1102–1107 supports the claim that Koopman lifting **performs implicit system identification of latent/privileged environment parameters** (hydrodynamic coefficients, currents, thruster faults) in the sense an RMA-style encoder does. What is "identified" here is a (possibly bilinear) **operator/invariant-subspace representation of the observed state dynamics** (§2, §5) — a different object from inferring unobserved environment parameters from history. The paper itself flags this exact adjacent question (state uncertainty → lifted-observable uncertainty propagation) as an **open, unresolved research question** (p.1104, *Uncertainty in lifted features*), not a solved property. Separately, no RL-Koopman fusion described in these pages proposes replacing a privileged-parameter encoder+student-distillation pipeline with lifting alone — the RL-adjacent citations here ([51],[103],[104],[128]) are titles only, with no body-text argument on these pages that lifting removes the need for encoders or state estimation.