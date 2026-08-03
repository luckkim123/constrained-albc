# Koopman Operators in Robot Learning — Notes from Assigned Pages (PDF pp.1–6 = printed pp.1088–1093)

*Shi, Haseli, Mamakoukas, Bruder, Abraham, Murphey, Cortés, Karydis. IEEE Trans. Robotics, Vol. 42, 2026.*
Page mapping used below: PDF p.1→p.1088, p.2→p.1089, p.3→p.1090, p.4→p.1091, p.5→p.1092, p.6→p.1093 (Table I).

---

## 1. Section-by-section summary

- **Abstract / Nomenclature** (p.1088): Frames Koopman operator theory as a "rigorous treatment of dynamics" giving a linear, higher-dimensional representation of nonlinear systems, valued for incremental (online) updates and low compute. States the review covers math foundations, input-approximation, lifting-function design, and surveys applications (aerial/legged robots, manipulators, soft robots, multiagent networks).
- **I. Introduction** (p.1088–1090): Motivates runtime learning for robots that cannot rely on large offline/simulated datasets (novel environments, unsimulable phenomena — human interaction, turbulent flow, mechanoreception, unknown boundary conditions). Poses the paper's guiding question: what tools support runtime learning from **"small data"**? Lists three claimed Koopman advantages: (1) Interpretability vs. deep-NN black boxes, (2) Data-efficiency, (3) Linear representation enabling linear-systems tools. States the roadmap: Sec. II fundamentals → Sec. III Koopman models for control/state-estimation/planning → Sec. IV system-level survey across manipulation, legged locomotion, soft/continuum, aerial, underwater, multiagent → Sec. V advanced theory for general nonlinear systems → Sec. VI future directions → Sec. VII conclusion. Notes prior reviews were narrower (data-driven methods only [19]; theory-only [21],[22],[23]; controller design [24]; soft robotics only [25]) — this paper claims to be the first comprehensive robotics-wide Koopman review.
- **II. Fundamentals of Koopman Operator Theory** (p.1090–1092)
  - **II.A Koopman Operator Fundamentals** (p.1090–1091): Formal definition of the operator on discrete-time systems; the "lifting"/observable-function concept; finite-dimensional Koopman-invariant subspaces.
  - **II.B Data-Driven Estimation and Prediction** (p.1091–1092): Extended DMD (EDMD) derivation, closed-form solution, eigenfunction predictor, convergence caveats; HVOK (Hankel view of Koopman) as an alternative using time-delay embedding; Remark on classical DMD as an EDMD special case.
  - **II.C Koopman Approximation for Systems With Inputs** (p.1092): Three approximation strategies — joint lifting, affine-in-input, control-coherent Koopman operators.
- **III. Koopman-Based Modeling and Its Application** (starts p.1092, continues past assigned pages): Opening paragraph only within my pages — contrasts Koopman-based modeling with explicit physical modeling/local linearization, positions it as attractive for high-dimensional/nonlinear/hybrid robot dynamics.
- **Table I** (p.1093): "Summary of Representative References and Implementation Details Across Various Robotic Systems" — cross-tabulates robot platform (Manipulator, Wheeled, Legged, Soft, Aerial, Underwater, Rehabilitation, Surgery Robots) × input-handling method (inputs-affined / jointly-lifted) × lifting-function type (manually selected / NN-based / physics-informed / DMD / HVOK) × downstream application (MPC, LQR, NMPC, State Observer, Modeling, Imitation Learning, Robust Controller, Adaptive Controller, RL) × reference numbers.

---

## 2. Mathematically precise definitions / algorithms

**Base system** (p.1090):
$$x_{t+1} = T(x_t) \qquad \text{(1)}, \quad x \in \mathcal{X} \subseteq \mathbb{R}^{N_x}$$

**Koopman operator definition** — acting on a vector space $\mathcal{F}$ of observables $g:\mathcal{X}\to\mathbb{C}$ (p.1090):
$$\mathcal{K}g = g \circ T \quad \forall g \in \mathcal{F} \qquad \text{(2)}$$
$$\mathcal{K}g(x_t) = g(T(x_t)) = g(x_{t+1}) \qquad \text{(3)}$$
$\mathcal{K}:\mathcal{F}\to\mathcal{F}$ must be well-defined, requiring $\mathcal{F}$ closed under composition with $T$; this can force $\mathcal{F}$ infinite-dimensional (p.1090).

**Finite-dimensional Koopman-invariant subspace** $\mathcal{S}\subset\mathcal{F}$, restricting $\mathcal{K}$ to $\mathcal{K}|_\mathcal{S}:\mathcal{S}\to\mathcal{S}$, represented by matrix $K$ w.r.t. basis $\Psi$ (vector-valued observable function) (p.1091):
$$\mathcal{K}\Psi = \Psi \circ T = K\Psi \qquad \text{(4)}, \quad K \in \mathbb{C}^{\dim(\mathcal{S})\times\dim(\mathcal{S})}$$

**Resulting exact linear lifted dynamics** (p.1091):
$$\Psi(x_{t+1}) = K\Psi(x_t) \qquad \text{(5)}$$
With $z_t := \Psi(x_t)$: $z_{t+1} = Kz_t$. If $\mathcal{S}$ contains all state observables $g_i(x)=x^i$ (the "**full-state observability assumption**" [27]), the lifted linear system (5) captures the *complete* information of the original nonlinear system (1) (p.1091).

**Extended DMD (EDMD)** (p.1091), from data matrices $X=[x_1,\dots,x_M]$, $Y=[y_1,\dots,y_M]$, $y_i=T(x_i)$:
$$\min_K \|\Psi(Y) - K\Psi(X)\|_F \qquad \text{(6)}$$
Closed-form solution:
$$K_{\text{EDMD}} = \Psi(Y)\Psi(X)^{\dagger} \qquad \text{(7)}$$
($\dagger$ = pseudoinverse.)

**EDMD predictor for a function** $f(\cdot)=v_f^T\Psi(\cdot)=\sum_{i=1}^N (v_f)_i\psi_i(\cdot)$ (p.1091):
$$\mathfrak{P}^{\text{EDMD}}_{\mathcal{K}f} := v_f^T K_{\text{EDMD}}\Psi \qquad \text{(8)}$$
Note: $\mathfrak{P}_{\mathcal{K}f}\in \text{span}(\Psi)$ even if $\mathcal{K}f \notin \text{span}(\Psi)$.

**Koopman eigenfunction approximation** — for $v_\phi$ a left eigenvector of $K_{\text{EDMD}}$ ($v_\phi^T K_{\text{EDMD}}=\lambda_\phi v_\phi^T$), with $\phi(\cdot)=v_\phi^T\Psi(\cdot)$ (p.1091):
$$\mathfrak{P}^{\text{EDMD}}_{\mathcal{K}\phi} := v_\phi^T K_{\text{EDMD}}\Psi = \lambda_\phi v_\phi^T \Psi = \lambda_\phi \phi \qquad \text{(9)}$$

**Connection to the true operator**: EDMD approximates the projected operator $\mathcal{P}_{\text{span}(\Psi)}\mathcal{K}:\mathcal{F}\to\mathcal{F}$ (10), where $\mathcal{P}_{\text{span}(\Psi)}$ is the $L_2(\mu_X)$-orthogonal projection onto $\text{span}(\Psi)$, empirical measure $\mu_X=\frac{1}{M}\sum_{i=1}^M \delta_{x_i}$ (11) (p.1091). As the dictionary grows, $K_{\text{EDMD}}$ converges (in operator topology) to $\mathcal{K}$, capturing its eigenvalues and giving weak convergence of eigenfunctions [30] (p.1091).

**HVOK (Hankel View of Koopman)** [28] (p.1092) — builds delay-embedded Hankel matrices instead of an explicit lifting map:
$$H_X = \begin{bmatrix} x_1 & \cdots & x_{m-d} \\ x_2 & \cdots & x_{m-d+1} \\ \vdots & \ddots & \vdots \\ x_d & \cdots & x_{m-1}\end{bmatrix}, \quad H_Y = \begin{bmatrix} x_2 & \cdots & x_{m-d+1} \\ x_3 & \cdots & x_{m-d+2} \\ \vdots & \ddots & \vdots \\ x_{d+1} & \cdots & x_m\end{bmatrix}$$
HVOK seeks $K_{\text{HVOK}}$ satisfying $H_Y \approx K_{\text{HVOK}} H_X$ — "analogous to EDMD but operating on delay-embedded observables" (p.1092). Motivated by Takens-type observability arguments; replaces explicit basis-design with an implicit feature space from temporal lifting.

**DMD as EDMD special case** (Remark 1, p.1092): classical/"exact" DMD [35] = EDMD with the dictionary set to the identity map (no lifting).

**Input handling — three finite-dimensional approximation strategies** (p.1092), since directly working in the infinite-dimensional input-extended setting is computationally intractable:

1. **Joint lifting of states and inputs**: define observables $g(x,u)$ over the combined $(x,u)$ space, treating $u$ as part of an extended state, without assuming an independent evolution rule for $u$.
2. **Affine input form in the lifted space**:
$$g(x_{t+1}) \approx K g(x_t) + B u_t$$
where $K$ is the finite-dim Koopman approximation of the autonomous part and $B$ captures the linear influence of the control input. Stated to be "a particular case of the input–state separable model introduced in [36]."
3. **Control-coherent Koopman operators** [37]: seeks an embedding space in which the evolution operator remains coherent across different control inputs ("preserving consistency" under varying $u$), improving generalization to new control sequences.

---

## 3. Lifting function design

- **Three design categories** shown in the overview figure (Fig. 1, p.1089): manually designed, physics-informed construction, and neural-network-based ($\phi(x)=g(x)$, "$\alpha \approx g(x)$" for the NN case).
- **Data-collection strategies** (Fig. 1, p.1089), listed alongside lifting design as the two halves of the modeling pipeline: random selection, nominal-controlled sampling, information-theory-based. No further elaboration of these three in my pages.
- **Dictionary / basis role**: the basis $\Psi$ used in EDMD must approximately span a Koopman-invariant subspace; approximation error of predictors (8)–(9) "depends on how close $\text{span}(\Psi)$ is to being invariant under the Koopman operator" (p.1091).
- **Failure mode — bigger dictionary ≠ better prediction** (p.1091): Explicit worked counterexample — linear system $x^+=0.5x$ with $\Psi_1(x)=x$ and $\Psi_2(x)=[x,\sin(x)]$. Although $\text{span}(\Psi_1)\subsetneq\text{span}(\Psi_2)$, prediction on $\text{span}(\Psi_1)$ is **exact** (it is Koopman-invariant for this system), while prediction on $\text{span}(\Psi_2)$ has **large errors for some functions**. Cites [31],[32],[33] for pruning methods to remove subspaces and improve prediction accuracy. This is presented as a general caution against naively enlarging the observable dictionary.
- **Sufficiency conditions and their practical limits** (p.1091–1092): To realize EDMD's asymptotic convergence to $\mathcal{K}$ [30], *both* the dictionary dimension and the number of data points must be "sufficiently large." Critically: **without a system model it is not possible to estimate a lower bound on the required dictionary dimension** to hit a predetermined accuracy target. If the dictionary is chosen from a generic basis of $\mathcal{F}$ (not informed by the system), the required dimension to reach high accuracy "might be extremely large" (p.1092).
- **Practical guidance stated directly** (p.1092): *"for practical applications, it is imperative to design or learn dictionaries based on information available from the system and/or data to achieve a reasonable accuracy on relatively low-dimensional subspaces."* — i.e., system/data-informed (physics-informed or learned) dictionaries are the recommended route to tractable dimensionality, not arbitrary generic bases.
- **HVOK as an alternative to explicit dictionary design** (p.1092): explicitly framed as replacing "the need for explicit basis-design with an implicit feature space constructed by temporal lifting," reported to yield "more stable Koopman estimates in partially observed or highly nonlinear systems," and to be particularly effective for systems with rich temporal structure such as **soft and bioinspired robots** (p.1092).
- **Input-lifting-specific caveat**: joint lifting of state+input "assumes knowledge of future inputs and does not generalize well when the input varies arbitrarily, since the input is not effectively governed by a dynamical rule" (p.1092) — a closure/generalization failure mode specific to this input-handling choice, distinct from the pure-observable pruning issue above.
- No explicit spectral-pole/eigenvalue-pathology discussion appears in my pages beyond the convergence-of-eigenfunctions statement in II.B.

---

## 4. Connection to reinforcement learning / policy learning / state representation

Sparse in the assigned pages — this appears to be developed later (Sec. III/IV, beyond p.6).

- Intro context only: RL is named as one of three actively-investigated robot-learning method families alongside neural ODEs and generative AI, all sharing the *offline, large-data* dependency the paper is positioning Koopman against: **"neural ordinary differential equations (ODEs) [1], [deep] reinforcement learning (RL) [2], and generative AI [3]"** (p.1088). This is a framing contrast, not a Koopman–RL integration claim.
- **The one concrete Koopman+RL data point in my pages**: Table I (p.1093), Soft Robots row — an entry with **NN-based lifting function** and downstream application **RL**, citing **reference [67]**. This is the sole table row across all platforms (Manipulator, Wheeled, Legged, Soft, Aerial, Underwater, Rehabilitation, Surgery) in pages 1–6 whose downstream application is RL rather than a classical/optimal controller (MPC, LQR, NMPC), a state observer, an imitation-learning policy, "Modeling," a robust controller, or an adaptive controller.
- Adjacent but not RL per se: Fig. 1's "Controller Design" box lists "Active Learning" alongside MPC/LQR (p.1089) — this is a control-loop learning component, not identified as RL, and not elaborated in text on these pages.
- No statement in pages 1–6 characterizes Koopman-lifted observables as a *state representation for a learned policy* in general, nor any discussion of using Koopman lifting to replace/augment a policy encoder. Section III (control/estimation/planning) and Section IV (per-domain survey, where soft-robot RL [67] presumably gets detailed) begin exactly at the edge of my assigned range (III starts p.1092, its body is on p.1093+ which I did not receive in detail beyond Table I).

**Assessment relevant to the user's proposal**: within pages 1–6, the paper gives no argument, theorem, or empirical claim that Koopman lifting "does system identification" in a sense that would obviate an encoder inferring latent environment/domain-randomization parameters (see §5 below) — the one Koopman+RL citation [67] is a single soft-robot reference, not a general finding about encoder replacement.

---

## 5. System identification semantics

- **What the Koopman operator estimates**: $\mathcal{K}$ (or its finite approximation $K$) approximates the system's *own* state-transition map $T$ in a lifted observable space — it is a (locally, on an invariant subspace) exact or approximate model of $x_{t+1}=T(x_t)$ itself, not an estimator of hidden/latent *parameters* of the environment (p.1090, Eq. 1–5). Nothing in pages 1–6 frames Koopman as inferring compact latent physical parameters (e.g., hydrodynamic coefficients, current strength) separate from the state — it only lifts and linearizes the *state* dynamics.
- **"Equivalence"/"substitution" framing and its stated benefits** (p.1090): two advantages given for the $g\mapsto\mathcal{K}g$ vs. $x\mapsto T(x)$ substitution: (1) "enables a global linear representation of the nonlinear dynamics $T$, thus enabling the application of techniques designed for linear systems," and (2) "facilitates the discovery of the underlying dynamics by estimating the linear operator in real time, which eliminates the need for least-square regression of the nonlinear function that, in general, requires a large amount of data." — This is about efficiently identifying the *dynamics operator*, not about disentangling or inferring specific latent environment-parameter values.
- **Data efficiency / runtime property** (p.1089): "Empirically, Koopman operators only require sparse datasets, making them amenable to runtime computation using only small datasets [17]." Advantage 2) reiterated on p.1090 ("Data-efficiency: ... demands only a limited number of measurements compared to most NN-based methods, making it suitable for real-time implementation").
- **Adaptive behavior claim** (p.1089): "Owing to their runtime computation affordances, Koopman operators can facilitate adaptive system behavior (e.g., spontaneous control response to unmodeled dynamics) that may be hard to achieve otherwise." — Online adaptability is claimed as an *empirical property*, alongside *formal properties* (stability, invariance, symmetry certification, information measures for active learning, LQR applicability, Lyapunov-based stability certificates [18]) (p.1089).
- **EDMD's estimation regime** (Sec. II.B, p.1091): as presented, EDMD is a batch least-squares fit from paired data matrices $X,Y$ (Eq. 6–7) — no online/recursive update formula appears within pages 1–6, though the Nomenclature (p.1088) predefines "$t$ — Index for online system propagation," signaling online estimation is covered later (beyond page 6).
- **Explicit convergence caveat bearing on identification claims** (p.1091–1092): EDMD's convergence to the true $\mathcal{K}$ requires *both* dictionary size and data volume to be "sufficiently large," and — critically — **without a system model there is no way to lower-bound the dictionary dimension needed for a target accuracy.** This directly undercuts any claim that Koopman lifting alone guarantees good identification without domain knowledge informing the dictionary.
- **No claim found (pages 1–6) that Koopman lifting infers latent environment/domain-randomization parameters.** The paper's system-identification framing throughout my assigned pages is about linearizing/estimating the *state* propagation operator $T$, not about estimating hidden scalar/vector environment parameters that a privileged encoder would otherwise regress. If the user's architecture wants Koopman to replace the encoder's job (mapping privileged params → z), pages 1–6 offer no theoretical support for that substitution — Koopman's stated substitution is $T \leftrightarrow \mathcal{K}$ (dynamics operator), not "hidden parameter $\leftrightarrow$ latent code."

---

## 6. Underwater / marine / soft / aerial robot applications

- **Underwater Robots** — Table I (p.1093) lists three representative entries (fish-robot photo shown), all under the "inputs-affined" input-handling column:
  - Manually selected lifting function → downstream "Modeling" application, ref [87].
  - NN-based lifting function → downstream "MPC," ref [88] or [89] (small-font table reference number not confidently legible from the rendered page — flagged as uncertain rather than asserted).
  - Physics-informed lifting function → downstream "LQR," ref [90].
  (Reference numbers for this row are read from a small table font and should be re-verified against the bibliography before citing precisely; the method/task pairings themselves — manual/NN/physics-informed lifting feeding Modeling/MPC/LQR — are legible with higher confidence.)
- **Soft Robots** — Table I (p.1093), by far the most heavily populated platform row, spanning refs roughly [54]–[74]:
  - Manually selected lifting → MPC [54]–[57]; Modeling [58],[59]; Modeling [60]; MPC [61]–[63].
  - NN-based lifting → MPC [64]; MPC [65],[66]; **RL [67]** (the sole Koopman+RL entry in my pages, see §4).
  - Physics-informed lifting → MPC [68]; Modeling [69]; Modeling [70].
  - DMD-based lifting → LQR [71].
  - HVOK-based lifting → LQR [72]; Modeling [73],[74].
  - All soft-robot rows are marked under the "jointly-lifted" input-handling column (consistent with soft robots' input/state coupling being harder to separate affinely).
  - Text corroboration (p.1092): HVOK "has shown strong effectiveness, particularly in systems with rich temporal structure, such as soft and bioinspired robots," because HVOK's implicit time-delay embedding avoids explicit basis design and gives "more stable Koopman estimates in partially observed or highly nonlinear systems."
- **Aerial Robots** — Table I (p.1093), refs [75]–[86]: physics-informed lifting → LQR [75], MPC [76]; manually selected lifting → MPC [77],[78], NMPC [79], State Observer [80]; HVOK lifting → MPC [81],[82]; DMD lifting → MPC [83], Adaptive Controller [84]; NN-based lifting → State Observer [85], NMPC [86]. No RL entries for aerial robots in my pages.
- **Marine/soft cross-reference**: no explicit "marine" category distinct from "Underwater Robots"; no separate discussion of e.g. underwater vehicle-manipulators specifically (my pages' underwater entries are generic underwater vehicle/fish-robot references, not UVMS-specific).

---

## 7. Limitations, open challenges, practical guidance

- **Infinite-dimensional rigor vs. finite-dimensional necessity** (p.1092): "Rigorous operator-theoretic approaches to address this challenge include two formal methods discussed in Section V-B and both approaches offer provable theoretical guarantees in the infinite-dimensional setting. In practice, however, directly working with infinite-dimensional spaces is computationally intractable. Therefore, a variety of finite-dimensional approximation strategies have been developed..." — the formally justified (infinite-dim) approach is not the one used in practice; practical methods (joint lifting, affine, control-coherent) are approximations without the same guarantees.
- **Dictionary-size/data-size joint sufficiency, with no way to bound it a priori** (p.1091–1092): convergence of EDMD to the true Koopman operator needs both large dictionary *and* large data; and "without a system's model, it is not possible to estimate a lower bound on the dictionary's dimension to achieve a predetermined level of accuracy."
- **Larger lifted space can actively hurt prediction** unless pruned (p.1091, the $x^+=0.5x$ counterexample) — an explicit warning against dictionary bloat as a default strategy, with citations [31],[32],[33] to pruning remedies.
- **Practical remedy stated directly** (p.1092): design/learn dictionaries using system/data information to keep accuracy achievable on "relatively low-dimensional subspaces," rather than relying on generic large bases.
- **Joint state-input lifting's generalization limit** (p.1092): fails to generalize when input varies arbitrarily/is not governed by a dynamical rule, since it assumes knowledge of future inputs; noted as still "effectively used in learning-based robotic systems with structured or repetitive input patterns" — i.e., viable only for structured/repetitive control regimes, a caveat directly relevant if the user's UUV control inputs (thruster commands under fault/DR) are not "structured or repetitive."
- **Data-collection guidance is only categorical in my pages** (Fig. 1, p.1089: random selection / nominal-controlled sampling / information-theory-based) with no elaboration, sample-size figures, or compute figures given within pages 1–6 — such detail, if present, would be in later sections.
- No explicit discussion in my pages of spectral pathologies (e.g., non-normality, spectral pollution) or of stability certification failure modes beyond the general claim (p.1089) that Koopman enables "constructive control Lyapunov functions [18]" as a *benefit*, not a limitation.

---

## Notes on category coverage
- Categories 4 (RL) and 5 (system-ID-as-parameter-inference) are the thinnest in these pages — the paper's substantive treatment of both likely lives in Sections III/IV/V, which begin exactly at the edge of my assigned range (Sec. III opens p.1092, its body and Sec. IV's per-domain deep dives are beyond p.6).
- No explicit "closure" terminology or spectral-pollution discussion found in my pages — "none in my pages" for that specific sub-topic within category 3.