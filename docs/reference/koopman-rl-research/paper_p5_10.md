# Koopman Operators in Robot Learning — Notes from pp. 1092–1097 (PDF pages 5–10)

*(Note: PDF page label field maps to printed page numbers 1092–1097, IEEE Trans. Robotics Vol.42, 2026, "Shi et al.: Koopman Operators in Robot Learning". Page anchors below use the printed page numbers.)*

## 1. Section-by-Section Summary

- **II-C. Koopman Approximation for Systems With Inputs** (p.1092) — covers three finite-dimensional strategies for incorporating control inputs into the Koopman framework: joint lifting, affine input form, control-coherent embeddings.
- **Remark 1 (DMD)** (p.1092) — situates Dynamic Mode Decomposition as a special case of EDMD with no lifting (or identity-map dictionary).
- **II-C.2, "HVOK Operator"** (p.1092) — Hankel-DMD/Variant Koopman formulation using time-delay embedding instead of an explicit lifting map.
- **Table I** (p.1093) — cross-tabulates robot platform × input-handling method × lifting-function family × downstream application × cited references, across manipulators, wheeled/legged robots, soft robots, aerial robots, underwater robots, rehabilitation robots, surgery robots.
- **III. Koopman-Based Modeling and Its Application** (p.1093–1097) — top-level section; states the three-stage Koopman pipeline (data collection → lifting function construction → downstream application).
  - **III-A. Data Collection for Koopman Modeling** (p.1094)
  - **III-B. Lifting Functions Selection for Koopman Embedding** (p.1094–1095) — three categories: manually selected, physics-informed, NN-based.
  - **III-C. Application in Robot Controller Design** (p.1095–1096)
    - III-C.1 Model-Based Controller (Koopman MPC / NMPC, LQR)
    - III-C.2 Active Learning (Fisher-information-based optimal data acquisition)
  - **III-D. Application in Robot State Estimation** (p.1096) — robust estimation across system variability; disturbance estimation/rejection; efficient nonlinear/high-dim state inference.
  - **III-E. Application in Robot Planning and Localization** (p.1096) — Koopman-linearized MPC planning, SLAM via bilinear lifting, terrain-traversability navigation, uncertainty-aware motion planning.
  - **III-F. Robustness and Stability of Koopman Models** (p.1097) — sources of model error, uncertainty quantification, stability-promoting operator fitting, robust/constraint-tightening MPC.
- **IV. Implementation of Koopman Methods in Different Robotic Systems** (p.1097 onward)
  - **IV-A. Robotic Manipulation** (p.1097) — begins; covers modeling/predictive-control category, RL/imitation-learning category, object-centric/dexterous-manipulation category (continues past p.1097, cut off at end of my page range).

## 2. Mathematically Precise Definitions / Algorithms

- **HVOK Hankel matrices** (delay-coordinate embedding of trajectory data), built from stacked, time-delayed snapshots instead of an explicit basis Ψ (p.1092):
  `H_X = [[x_1,...,x_{m-d}],[x_2,...,x_{m-d+1}],...,[x_d,...,x_{m-1}]]`, `H_Y` analogous shifted-by-one stack.
- **HVOK operator**: seeks linear operator `K_HVOK` satisfying `H_Y ≈ K_HVOK H_X` — "analogous to EDMD but operating on delay-embedded observables" (p.1092). Replaces explicit basis design with an implicit feature space from temporal lifting; described as yielding "more stable Koopman estimates in partially observed or highly nonlinear systems" (p.1092).
- **DMD as a special case of EDMD** (Remark 1, p.1092): exact-variant DMD [35] = EDMD with no lifting on the data, or equivalently EDMD dictionary set to the identity map.
- **Joint lifting of states and inputs** (p.1092): treats control input `u` as part of the extended state; defines observables `g(x,u)` over the combined space. Koopman operator acts on functions of both state and input, "without assuming an independent evolution of u." Stated limitation: assumes knowledge of future inputs and does not generalize well when input varies arbitrarily, since the input is not governed by a dynamical rule; effective for structured/repetitive input patterns (p.1092).
- **Affine input form in the lifted space** (p.1092): `g(x_{t+1}) ≈ K g(x_t) + B u_t`, where `K` is the finite-dimensional Koopman approximation for the autonomous part, `B` captures the linear influence of the control input. Preserves linear structure, aligns with classical control tools (LQR, MPC). Noted as "a particular case of the input-state separable model introduced in [36], which provides a solid theoretical backdrop to understand the errors associated with these approximations" (p.1092).
- **Control-coherent Koopman operators** [37] (p.1092): aims for an embedding space in which the evolution operator "remains coherent" as control inputs vary; improves generalization to new control sequences, learns Koopman operators robust to input variability; useful for manipulation tasks and underactuated systems where input variation is critical to task success.
- **Koopman MPC optimization** (eq. 12, p.1095):
  `minimize_{z,u} J({z_i}_{i=0}^{N_h}, {u_i}_{i=0}^{N_h})`
  `subject to z_{i+1} = F_K(z_i, u_i)`
  `z_0 = Ψ(x_t)`
  where `N_h` = horizon length, `J` = quadratic cost, `Ψ` = lifting dictionary, `F_K` = Koopman-based system model, `z_i, u_i` = lifted state/input at step i. Cost penalizes trajectory deviation; constraints enforce consistency with a Koopman system model.
- **Linear Koopman realization → convex QP** (eq. 13, p.1095):
  `minimize sum_i [z_i^T G_i z_i + u_i^T H_i u_i + g_i^T z_i + h_i^T u_i]`
  `s.t. z_{i+1} = K z_i + B u_i, z_0 = Ψ(x_t)`.
  Stated advantage: linear Koopman realization makes the problem convex → unique globally optimal solution, efficiently computable without initialization even for high-dimensional models, well-suited for real-time feedback control (cites [106],[107],[108]). Nonlinear/bilinear Koopman realizations make (12) nonconvex, less efficient, possibly only locally optimal ([109]); sometimes more accurate predictions warrant this trade-off; bilinear realizations combine some advantages of linear and nonlinear models (cites [43],[97]).
- **Active-learning Fisher information matrix** (eq. 14–15, p.1095): assumes lifted dynamics `Ψ(x_{t+1}) = K Ψ(x_t) + B u_k` form the mean of a normally distributed state in latent space `p(z_{t+1}|K, z_k)`. Fisher information:
  `I = E[ ∂/∂K log p(z_{t+1}|K,z_k) · ∂/∂K log p(z_{t+1}|K,z_k)^T ]`.
  For normally distributed systems with zero-mean, variance Σ, closed form:
  `I = (∂z_{t+1}/∂K)^T Σ^{-1} (∂z_{t+1}/∂K) ≤ Var[K*]^{-1}`
  — lower-bounds posterior uncertainty in estimation (Cramér–Rao bound, cites [110],[111]).
- **Optimal active-learning control problem** (eq. 16, p.1096):
  `minimize_{u} sum_{i} [ 𝕴(z_i, ᵗK) + u_i^T R u_i ]`
  `s.t. z_{i+1} = ᵗK z_i + ᵗB u_i, z_0 = Ψ(x_t)`
  where `R ≻ 0`, `𝕴(z_i, ᵗK)` is an optimality condition (D-, or T-optimality) reducing the matrix to a scalar, `ᵗ` superscript = current estimate of the Koopman operator given past state-control data. Solved receding-horizon to account for operator updates as new data arrives.

## 3. Lifting Function Design (III-B, p.1094–1095)

Three-way taxonomy (also structures Table I's "Lifting Functions" column):

1. **Manually selected basis functions** (p.1094): chosen from domain knowledge or trial-and-error. Examples: spectral elements → block-diagonal observation matrices [27]; Hermite polynomials for normally distributed data; radial basis functions (RBF) for complex spatially structured dynamics. "Effective in some cases, empirical design is often labor-intensive and may not generalize well to different systems or tasks" (p.1094).
2. **Physics-informed lifting functions** (p.1094): leverage structured robot properties (kinematic constraints, DOF, geometric configuration spaces) even absent a full dynamic model. Shi et al. [69]: incorporates physical insight — configuration symmetries and workspace constraints — into observable-space construction, "improving both the interpretability and robustness of the resulting Koopman model." Another approach [90]: synthesizes basis functions using higher-order time-state derivatives, "shows how including derivative terms in the observable space can enrich the expressiveness of the Koopman approximation."
3. **NN-based lifting functions** (p.1094): learn lifting directly from data using NNs [101]; fall under "Deep Koopman" [102] or "Autoencoder-Koopman" [16] frameworks, where NNs learn an embedding capturing latent linear dynamics. Stated trade-off: "offer high flexibility and expressiveness, they also introduce challenges, such as interpretability, generalization to out-of-distribution inputs, and the risk of overfitting" (p.1094).

**Selection guidance**: "The choice among the three aforementioned categories of methods should be guided by the characteristics of the system and the specific task at hand" (p.1094–1095). Empirically per Table I: NN-based methods dominate manipulation/legged locomotion (high complexity/nonlinearity); manually designed functions dominate wheeled robots (comparatively simpler, better-understood dynamics); aerial/soft robots use all three types, with HVOK specifically favored for aerial robots (strong environmental disturbances) and soft robots (slow response characteristics) (p.1095).

**Dimensionality guidance**: "the dimension of the dictionary required to achieve a high accuracy level might be extremely large. Therefore, for practical applications, it is imperative to design or learn dictionaries based on information available from the system and/or data to achieve a reasonable accuracy on relatively low-dimensional subspaces" (p.1092).

**Rigor / known failure mode** (p.1095, closing III-B): "it is noteworthy that most lack rigorous convergence analysis—that is, they do not examine whether the constructed observables span a Koopman-invariant subspace or yield an accurate approximation of the true Koopman operator. To address this gap, we provide a more in-depth theoretical discussion on the construction of lifting functions in Section V-C" (V-C is outside my assigned pages).

**Active-learning interaction with NN lifting** (p.1096, end of III-C.2): "the use of deep models to approximate the function observables has made significant strides in expanding the use of methods based on the Koopman operator [100],[112],[113]... While the added complexity in the observables provides more flexibility in the modeling range of the Koopman operators, it does reduce the effectiveness of active learning. This is a result of more data being required to effectively learn the nonlinear observables. When compared to deep NN models, the Koopman-based linear model still has a significant advantage in data-efficiency and control through active learning [100]." — direct evidence that richer/NN lifting costs sample efficiency relative to a linear-dictionary Koopman model.

## 4. Koopman ↔ Reinforcement Learning / Policy Learning / Learned-Controller Connections

- **General RL mention** (III-C, p.1095): "Beyond these, a growing body of work explores other promising directions, including adaptive control [84], robust control [46], and RL, where Koopman models are used to either approximate environment dynamics [67] or support the design of critic networks [103]." — two distinct RL roles named: (a) Koopman model as environment-dynamics approximator [67], (b) Koopman model supporting critic-network design [103]. No further elaboration on these within my page range (details, if any, appear later in the paper).
- **Table I, Soft Robots row**: NN-based lifting → downstream application "⑨ RL" → ref [67] (p.1093), consistent with the "approximate environment dynamics" role above.
- **Manipulation, RL/imitation-learning category** (IV-A, p.1097): "Another category leverages Koopman operators to improve reinforcement and imitation learning in manipulation. In [128], human-demonstrated trajectories are encoded into a human intent term via Koopman lifting, which is then used to shape reward functions for RL agents, enabling safe and task-constrained human–robot interaction. A deep Koopman framework to learn a compact latent representation of system dynamics from observation-only data is developed in [40]. A linear decoder then maps these latent representations to real-world actions, drastically reducing the amount of action-labeled data required for imitation learning."
- **Imitation-learning-only refs** (Table I, Manipulator row, p.1093): NN-based lifting → Imitation Learning, refs [40],[41]; DMD lifting → Imitation Learning, ref [42].
- **KOROL framework** [42] (IV-A, p.1097): object-centric/dexterous manipulation; extracts visual object features, applies Koopman rollouts in feature space to predict future trajectories, used by an inverse dynamics controller to generate manipulation actions — "offering interpretability and robustness in vision-based manipulation." (This is a downstream-controller usage, not RL policy learning per se, but listed adjacent to the imitation-learning discussion.)
- **Han et al. [41]** (p.1097): Koopman-based imitation-learning framework that "jointly models the dynamics of both the robotic hand and the manipulated object" via joint Koopman lifting (description continues onto next page, cut off at end of my range).
- No sentence in my assigned pages states that Koopman lifting is proposed as a *substitute* for a privileged-information encoder or for teacher-student distillation in an asymmetric-actor-critic RL setup. The RL usages named are: (a) dynamics-model surrogate for a critic/environment model [67],[103]; (b) reward-shaping via Koopman-encoded human-intent term [128]; (c) latent dynamics representation for imitation learning to cut action-labeling cost [40]. None describe Koopman lifting as inferring domain-randomization/privileged environmental parameters analogous to an RMA encoder's z.

## 5. System Identification Semantics

- **What the Koopman operator is said to "identify"**: throughout III-C/III-D/III-E, `K`/`K_HVOK`/`F_K` is consistently described as an approximation of the operator governing the *lifted dynamics of a single system* (autonomous evolution + control-affine term `B u_t`), not as an inference mechanism over external/environmental parameters. Section III-C.1 frames it as "a finite-dimensional approximation of the Koopman operator" plugged into LQR/MPC/NMPC (p.1095).
- **III-D framing** (p.1096): "the focus shifts to accurately recovering system states under uncertainty, disturbance, or partial observability" — Koopman-based state estimation is about recovering *state*, not identifying latent environment/physical parameters directly, though nearby work touches parameter/population variability:
  - **Robust estimation across system variability**: Dahdah and Forbes [114] "proposed a robust nonlinear observer synthesis method for a population of systems modeled using Koopman operators. By exploiting the linear representation in the lifted space, uncertainty due to manufacturing variations is quantified in the frequency domain, allowing the use of mixed H2/H∞ robust control techniques to design stable observers across dozens of motor drives" (p.1096–1097). This is population-level uncertainty quantification (manufacturing variation across many units), not per-episode latent-parameter inference of the kind an RMA encoder performs.
  - **Disturbance estimation/rejection**: EVOLVER framework [80] "utilizes Koopman-based latent structure modeling within an evolutionary disturbance observer, enabling rapid transient reactions and high-precision steady-state estimation, with convergence guarantees under optimal conditions" (p.1096) — a disturbance *observer*, i.e., online correction of state/prediction error, not an explicit encoder of physical-parameter vectors (currents, hydrodynamic coefficients).
  - **Efficient state inference**: Jiang et al. [115] — data-driven Kalman filter via sparse kernel-based Koopman operator transforming system into a linear dynamic model in kernel space for standard linear Kalman filtering (p.1096). KoopSE [98] — batch state estimation for control-affine systems, lifts dynamics into RKHS making the system bilinear, uses Random Fourier features, avoids linearization/manual feature selection (p.1096). Huang et al. [85] — Koopman-enhanced error-state Kalman filter (K-ESKF): "a deep NN learns Koopman observables to convert full-state nonlinear dynamics into a bilinear control system, improving propagation accuracy in the ESKF framework" for agile quadrotor pose estimation (p.1096).
- **Online/adaptive updates**: "Other efficient online variants, such as the method introduced in [17], further demonstrate that Koopman-style linear operator updates can be performed in real time for time-varying systems" (p.1094). This is the clearest statement of Koopman as adapting to *time-varying dynamics online* — closer to an online system-ID role — but it is about updating the operator `K` itself online, not about producing a compact latent code of privileged environmental parameters for conditioning a separate policy network.
- **No statement in my pages claims** Koopman lifting inherently performs implicit system identification of unobserved environment parameters (e.g., fault states, current velocity, hydrodynamic coefficients) in the sense the user's proposal (2) assumes. The paper's system-identification-adjacent claims are about (a) state recovery under noise/partial observability, (b) operator adaptation over time, (c) population-level uncertainty across manufacturing variation — categorically different from inferring a per-rollout privileged latent vector.

## 6. Underwater / Marine / Soft / Aerial Robot Applications

- **Underwater Robots** (Table I, p.1093) — depicted with a bioinspired robotic-fish image (not an ROV/AUV-with-manipulator form factor):
  - Jointly-lifted inputs, manually selected lifting → downstream "Modeling" → ref [87]
  - Inputs-affined, NN-based lifting → downstream MPC → refs [88], [89]
  - Inputs-affined, physics-informed lifting → downstream LQR → ref [90] (same [90] cited in III-B as the "higher-order time-state derivatives" physics-informed lifting paper, p.1094).
  - No RL, no state-estimation, no encoder/distillation entries for underwater robots in this table.
- **Soft Robots** (Table I, p.1093) — the most heavily represented platform: manually selected / physics-informed / NN-based / DMD / HVOK lifting; downstream MPC (multiple refs [54]-[57],[61]-[63],[64],[68]), Modeling ([58],[59],[69],[70]), RL (one entry, [67]), LQR ([71],[72]), Modeling via HVOK ([73],[74]). HVOK favored for soft robots per III-B closing discussion (p.1095) due to "slow response characteristics."
- **Aerial Robots** (Table I, p.1093): physics-informed ([75],[76]), manually selected ([77]-[80]), HVOK ([81],[82]), DMD ([83],[84]), NN-based ([85],[86]); downstream LQR/MPC/NMPC/State Observer/Adaptive Controller. HVOK favored for aerial robots (p.1095) due to "strong environmental disturbances." K-ESKF [85] for agile quadrotor pose estimation elaborated in III-D (p.1096).
- **No underwater vehicle-manipulator (UUV+arm)** combined system is mentioned anywhere in my assigned pages — all underwater entries are fish-like/AUV modeling, not manipulator-equipped platforms.

## 7. Stated Limitations, Open Challenges, Practical Guidance

**Data collection guidance (III-A, p.1094):**
- Data type/quantity is "crucial" to model accuracy and downstream control performance; optimizing collection is "essential for effective Koopman-based methods and remains an active area of research [95],[96]."
- Common method: random selection of initial conditions/inputs [61]; requires "sufficient diversity and promote persistent excitation—a key requirement for identifying expressive Koopman models"; sample initial states/inputs across the full operational envelope of the robot [95],[97]; an enclosed arena may be required for safety [98].
- Random collection is more widely used for soft robots [62],[70],[99] "as soft parts do less harm to their surroundings if an aggressive command is selected by chance" — i.e., random excitation is riskier for rigid systems.
- To mitigate safety risk, an alternative is to start from a baseline controller (open-loop or naive) and iteratively refine over time; e.g., Folkestad et al. [78] "employed a scheme in which the controller from the previous episode is used to generate data for the current one. This iterative process enables safer data collection while also improving the informativeness of the observations."
- Active-consideration-of-information-value during collection connects to active-learning paradigms [100], detailed in III-C.2.

**Lifting-function limitations** (p.1092, 1094, 1095): dictionary dimension needed for high accuracy can be "extremely large" — practical need to design/learn lower-dimensional, information-guided dictionaries (p.1092). NN-based lifting trades flexibility for interpretability loss, OOD generalization risk, overfitting risk (p.1094). Most reviewed lifting-function works "lack rigorous convergence analysis" — do not verify Koopman-invariant subspace span or true-operator approximation accuracy (p.1095).

**Control-design trade-offs** (III-C.1, p.1095): linear Koopman realization → convex QP, globally optimal, efficient even at high lifted-state dimension, suited to real-time MPC [106]-[108]. Nonlinear/bilinear realizations → nonconvex, less efficient, possibly only locally optimal [109]; sometimes justified by better prediction accuracy; bilinear realizations attempt to combine linear/nonlinear advantages [43],[97].

**Active learning cost** (III-C.2, p.1096): richer/deep-NN observables reduce active-learning effectiveness because more data is required to learn nonlinear observables well; linear/dictionary-based Koopman models retain a "significant advantage in data-efficiency and control through active learning" over deep NN models [100].

**Robustness/Stability limitations (III-F, p.1097)** — explicit statement: "performance can be significantly affected by inaccuracies in the learned models. These errors may arise from noisy measurements, limited observability, data scarcity, or the inability of finite-dimensional approximations to fully capture complex real-world nonlinear dynamics [121]." Specific mitigations surveyed:
- Shi et al. [84],[122]: quantify influence of noisy data by deriving loose/tight bounds on prediction errors for DMD/EDMD-learned Koopman models; bounds integrated into control design for uncertainty during planning/execution.
- Kalman-filter augmentation of an uncertainty model alongside lifted observables [61].
- Han et al. [65]: model a distribution over observables via an NN to provide additional uncertainty-mitigation mechanisms.
- Chen and Lv [123]: integrate an extended state observer into deep Koopman operator modeling for autonomous vehicle control.
- Mamakoukas et al. [124]: compute the nearest *stable* Koopman matrix to reduce reconstruction error and promote inherent model stability.
- Predictive-performance-bound approaches yielding robust MPC controllers adaptable during execution [125].
- Wang et al. [126]: constraint-tightening strategy within a tracking MPC framework, guaranteeing recursive feasibility and input-to-state stability under bounded uncertainty.
- Overarching stated insight (p.1097): "ensuring the effective utility of Koopman models for control requires integrating uncertainty and augmenting control design to account for the effects of prediction inaccuracies and instability" — i.e., the paper frames Koopman-model error as a design problem requiring explicit uncertainty quantification/robust control, not something resolved by the lifting step alone.

---

**Summary flag for the parent task's evaluation**: within pp.1092–1097, the paper (a) never claims Koopman lifting performs implicit inference of unobserved/privileged environmental parameters analogous to an RMA-style encoder (§5 above — closest analogues are disturbance *observers* and population-level manufacturing-variation uncertainty quantification, not per-episode latent parameter encoding); (b) explicitly states richer/NN-based lifting *reduces* data efficiency relative to plain linear-dictionary Koopman models (§3, p.1096); (c) explicitly flags that most surveyed lifting-function constructions lack convergence guarantees / proof that the observable space is Koopman-invariant (§3, p.1095). These are direct textual constraints relevant to judging the two proposals, though pages 5–10 alone do not contain a passage that either endorses or explicitly rules out lifting privileged/proprioceptive inputs jointly before an encoder+policy (proposal 1) or replacing an RMA encoder with Koopman lifting alone (proposal 2).