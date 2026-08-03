# AXIS 1 — Koopman Operators for Policy/Controller Sim-to-Real Transfer

## Bottom line

The literature explicitly framing **Koopman operators as a sim-to-real / reality-gap-reduction tool for a *learned RL policy*** is genuinely thin. Confirmed directly: the most current comprehensive survey, *Koopman Operators in Robot Learning* (arXiv 2408.04200, rev. 2025), contains **zero occurrences** of "sim-to-real," "sim2real," "reality gap," "domain randomization," "domain adaptation," or "domain gap" anywhere in its full text — verified by full-text search, not abstract-only. Koopman-for-robotics work overwhelmingly frames itself as *model-based control / MPC / safety filtering* (a linear surrogate model for planning), not as a mechanism inside an RL sim2real pipeline. Where Koopman methods do cross into sim→real, the pattern that recurs is narrower than the "policy transfer" framing you're testing for: **freeze a sim-trained nonlinear lifting function, adapt only the linear operator (A/B matrices) with a small amount of real data** — closer to classical linear system re-identification than to DR-replacement or Koopman-space domain alignment. Nothing found does Koopman-space adversarial/moment-matching alignment between sim and real *trajectory distributions* (your question 3) as a going concern — only one adjacent temporal-drift paper (KOMET) uses Koopman on a *parameter* trajectory, a different axis entirely.

---

## Q1 — Koopman credited with improving zero-shot POLICY sim2real transfer

**No clean hit.** Nothing found trains an RL policy in sim, wraps/conditions it with a Koopman representation, and reports a zero-shot real-hardware success-rate or reward improvement attributable to the Koopman component specifically. The nearest matches are all *model*-transfer, not *policy*-transfer:

### Digital Twins Meet the Koopman Operator (arXiv 2409.10347)
- **Mechanism**: EDMD lifts nonlinear off-road ground-vehicle dynamics into a linear space (`Kg(x) = g∘f(x,u)`), parameterized by trajectory curvature; feeds an MPC planner, not an RL policy.
- **Pipeline position**: digital-twin sim generates the training trajectories → Koopman model → terrain-aware planner → MPC → deployed on a real 1:5-scale AgileX Hunter SE vehicle.
- **Evidence (real hardware)**: explicit sim2real gap number — synthetic-data training gives a 0.1539 m sim-vs-real error gap, digital-twin-data training gives 0.1458 m (**↓5.2%**), plus a **5.84×** tracking-error improvement over an unaugmented baseline. This is the one paper in this search with a quoted, hardware-validated sim2real-gap percentage tied to Koopman modeling.
- **Maturity**: research prototype, scaled vehicle, ~40 min teleop training data.
- **Verdict**: **STRETCH** — real evidence and a genuine sim2real-gap metric, but it's a Koopman-MPC dynamics model, not a policy, and the vehicle/task (ground planar navigation) is far from 6-DOF UUV manipulation.

### Whole-Body Safe Control of Robotic Systems with Koopman Neural Dynamics (arXiv 2603.03740, CMU)
- **Mechanism**: neural Koopman embedding ψ_ω lifts manipulator dynamics; a QP safety filter runs on the linear lifted model.
- **Sim→hardware adaptation**: confirmed by direct fetch — "we collect hardware data and fine-tune only the A and B matrices of the lifted linear dynamics"; the embedding ψ_ω itself is **frozen**. Exact quote: "a lightweight adaptation step efficiently accounts for actuation and unmodeled dynamics differences between simulation and hardware, enabling migration with minimal retraining."
- **Evidence (real hardware)**: Kinova Gen3 7-DoF arm; mean joint-angle error 0.140 rad, mean end-effector error 0.031 m after adaptation; QP-infeasibility counts (42/4000 and 113/4000 steps) reported per scenario. No domain randomization used anywhere.
- **Maturity**: arXiv preprint, no stated venue in the fetched content.
- **Verdict**: **STRETCH** — this is the closest structural analog to your KIPPO-style "freeze φ_x, no new sim2real surface" idea found in the literature, but for a safety-filter dynamics model on a manipulator, not an RL policy on a UUV, and it explicitly does *not* use DR at all (pure real-data re-identification of the linear operator instead).

### Physics-informed Mixture-of-Koopmans Vehicle Dynamics (arXiv 2603.17416) — **UNVERIFIED, flag**
A WebSearch-engine summary asserted the same "freeze the sim-pretrained encoder, adapt only the Koopman operator for a new/real vehicle" pattern for electric-drive trucks. Direct PDF fetch could not confirm this mechanism (PDF text extraction was degraded/ambiguous). **Do not treat this as confirmed** — cite only as a lead needing primary-source verification, not as evidence.

---

## Q2 — Koopman structure for robustness to dynamics mismatch (DR-replacement / DR-complement)

### KORR — Robust Online Residual Refinement via Koopman-Guided Dynamics Modeling (arXiv 2509.12562)
- **Mechanism**: encoder lifts state to linear latent z; residual policy conditions on the Koopman-*predicted* next latent state rather than the raw current observation, for "globally informed" residual action corrections on top of a frozen base policy.
- **Framing**: explicitly *not* sim2real — the paper frames itself as robustness/generalization to perturbations and randomized initial conditions, evaluated entirely in IsaacGym (IKEA furniture-assembly tasks). It **complements** rather than replaces DR: disturbances are applied only at eval time, not as a training-time randomization strategy.
- **Self-reported limitation** (direct quote from the paper): "experiments are mainly conducted in simulation, and transferring KORR to real-world systems may still face challenges such as sim-to-real discrepancies." The authors themselves flag the sim2real question as open.
- **Verdict**: **NOT-APPLICABLE** as a sim2real mechanism today (sim-only, self-acknowledged gap), but the "condition residual correction on Koopman-predicted state" idea is a plausible STRETCH pattern if you were adding a residual/observer layer on top of your teacher-student stack — not evidence for the KIPPO/frozen-φ idea specifically.

### KODex — On the Utility of Koopman Operator Theory in Learning Dexterous Manipulation Skills (arXiv 2303.13446 / CoRL-adjacent, MLR v229) — **partially unverified**
Abstract-level claim: policies with Koopman-linearized reference dynamics show "zero-shot out-of-distribution generalization comparable to state-of-the-art imitation learning" and "robust[ness] to changes in physical properties." Full-text extraction failed (fetch tooling could not retrieve body content), so the exact evaluation protocol — whether "physical properties" means simulated parameter randomization or actual real-hardware variation — **could not be verified**. Treat the robustness claim as a lead, not a confirmed finding.

### KCPO — Koopman Constrained Policy Optimization (ICML 2023)
Uses a Koopman autoencoder inside differentiable MPC to get OOD generalization to *unseen hard constraints* (Pendulum, Cartpole, Reacher, Differential Drive — all sim). This is constraint-generalization, not dynamics-mismatch/sim2real generalization. **NOT-APPLICABLE** to this axis; tangential relevance to your IPO constraint-handling work, not to the sim2real question.

---

## Q3 — Koopman-space domain ALIGNMENT (spectra/operator matching between sim and real)

**No hit found.** No paper surfaced that explicitly does adversarial or moment-matching alignment of sim vs. real trajectory distributions *in Koopman-lifted space*, or that treats K_sim vs. K_real spectral comparison as a domain-alignment *loss* (as opposed to a passive diagnostic). The closest adjacent ideas:

- A generic (non-robot, non-Koopman-specific) point on spectral estimation surfaced during search: "unstructured operator approximation often does not converge to the real eigenvalues/eigenfunctions... spectrum is not close to the real one" — a caution about approximation fidelity in Koopman spectral estimates generally, relevant methodologically to your proposed K_sim-vs-K_real gap-meter (the meter's own estimation error needs characterizing before trusting a spectral-distance number), but not a sim2real-alignment method itself.
- **KOMET — Koopman Operator Identification of Model Parameter Trajectories for Temporal Domain Generalization** (arXiv 2603.26923): applies EDMD to the trajectory of a *model's trained parameter vector over time* to predict future parameter drift with "zero-retraining adaptation." This is Koopman-for-domain-generalization, but the "domain" axis is **temporal drift of one deployed model**, not **sim vs. real** as two distinct fixed domains. Structurally interesting (it's the only paper found using Koopman to model *domain drift itself* as a dynamical system) but not directly transplantable without its own validation — flagging as a nearest-neighbor idea, not a result.
- **NOT-APPLICABLE** conclusion for Q3 stands: your proposed K_sim-vs-K_real spectral gap meter appears to be a novel contribution relative to the current literature, not a replication of an existing method.

---

## Q4 — Sim-to-sim Koopman transfer gesturing beyond SKooP

No additional sim-to-sim Koopman transfer paper was found beyond what's already in your excluded list. KORR is the closest near-miss (perturbation robustness within one simulator, not cross-simulator transfer) and is sim-only, single-domain. Nothing surfaced tests a Koopman-lifted policy or model across two *different* simulators/dynamics engines as a proxy for sim2real. Treat Q4 as **unanswered by the current literature** rather than answered negatively — the search did not turn up a paper that tried and failed; it turned up no attempt.

---

## Non-Koopman nearest neighbors (for calibration — the field solves this problem, just not with Koopman)

| Paper | What it does | Why it's the shape a Koopman paper would need to take |
|---|---|---|
| FADA — Few-Shot Domain Adaptation via Dynamics Alignment for Humanoid Control (arXiv 2606.28476) | Freezes an oracle/teacher policy trained with privileged info, distills to a Planner+IDM, then fine-tunes **only the IDM** on ~2 min of real rollouts to align action generation with real dynamics. Real humanoid hardware confirmed. | Structurally near-identical to the "freeze φ, adapt small real-data-fit component" pattern seen in the Koopman papers above (2409.10347, 2603.03740) — but done with a plain neural IDM, not a Koopman operator. If someone swapped the IDM for a Koopman linear operator, that would BE the Q1 paper you're looking for. It doesn't exist yet as far as this search found. |
| Data-Informed Domain Randomization for AUVs (MDPI 2023, 10.3390/app13031723) | Minimizes the mismatch between simulated and real AUV trajectory distributions by adjusting DR parameters using real trajectory data — same problem statement as your own stack, same domain (UUV). | Confirms the "sim vs. real trajectory distribution mismatch for underwater vehicles" problem is actively worked, but with DR-parameter fitting, not Koopman-space alignment — reinforces that Q3's Koopman-specific angle is open territory rather than solved-elsewhere-and-missed. |
| Towards Certified Sim-to-Real Transfer via Stochastic Simulation-Gap Functions (arXiv 2603.20672) | Formal, certified bound on sim-vs-real discrepancy for safe transfer (confirmed non-Koopman via direct fetch). | Shows the field's non-Koopman answer to "quantify a sim2real gap with a mathematical object" — a possible framing template for how to *justify* a Koopman spectral-gap meter formally, if you wanted the meter to carry a certificate rather than be a heuristic diagnostic. |

---

## Applicability to your stack — summary verdicts

| Idea | Verdict | Basis |
|---|---|---|
| KIPPO-style frozen sim-trained φ_x lifting on actor obs | **STRETCH** | No paper does this for an RL *policy*; but 2603.03740 and (unverified) 2603.17416 show the identical *freeze-lifting/adapt-operator* pattern for Koopman *dynamics models* in real deployment — precedent for the mechanism, not for the RL-policy application |
| K_sim vs. K_real spectral comparison as a gap meter | **APPLICABLE-NOW, and apparently novel** | No existing paper does this as an active alignment/diagnostic tool for sim2real; the one caution found is that Koopman spectral estimates are themselves approximation-error-prone, so validate the meter's own noise floor before trusting deltas |
| Online Koopman observer at deployment (OM-Koop-style) | Not re-evaluated (excluded/already covered per your list) | — |
| Koopman as DR-replacement | **NOT SUPPORTED** by anything found — no paper claims Koopman structure lets you *reduce* DR breadth; KORR treats them as complementary at most, and only in sim | Absence of evidence, not evidence of failure — the field hasn't tested this claim either way |
| Koopman-space domain-alignment loss (adversarial/moment-matching) | **NOT-APPLICABLE / greenfield** | No prior art found; this would be a genuine methodological contribution rather than an adaptation of existing work |

---

## Sources

- [Efficient Real2Sim2Real of Continuum Robots Using Deep RL with Koopman Operator (IEEE TIE)](https://ieeexplore.ieee.org/document/10875033/) — already covered, excluded from analysis per brief
- [Digital Twins Meet the Koopman Operator: Data-Driven Learning for Robust Autonomy](https://arxiv.org/html/2409.10347v2)
- [Whole-Body Safe Control of Robotic Systems with Koopman Neural Dynamics](https://arxiv.org/html/2603.03740v3)
- [Robust Online Residual Refinement via Koopman-Guided Dynamics Modeling (KORR)](https://arxiv.org/html/2509.12562v1)
- [On the Utility of Koopman Operator Theory in Learning Dexterous Manipulation Skills (KODex)](https://arxiv.org/abs/2303.13446)
- [Koopman Constrained Policy Optimization (KCPO), ICML 2023](https://openreview.net/forum?id=3W7vPqWCeM)
- [Physics-informed Deep Mixture-of-Koopmans Vehicle Dynamics Model](https://arxiv.org/pdf/2603.17416) — mechanism claim unverified, see caveat above
- [Koopman Operator Identification of Model Parameter Trajectories for Temporal Domain Generalization (KOMET)](https://arxiv.org/abs/2603.26923)
- [Koopman Operators in Robot Learning (survey)](https://arxiv.org/abs/2408.04200) — full-text-verified absence of sim2real/DR terminology
- [Koopman-Assisted Reinforcement Learning](https://arxiv.org/abs/2403.02290) — sim-only, no sim2real framing, included as a negative check
- [Off-Road Navigation of Legged Robots Using Linear Transfer Operators](https://arxiv.org/pdf/2305.02938) — Perron-Frobenius/transfer-operator framing, no confirmed sim2real claim
- [FADA: Few-Shot Domain Adaptation via Dynamics Alignment for Humanoid Control](https://arxiv.org/pdf/2606.28476) — non-Koopman nearest neighbor
- [Reinforcement Learning for Autonomous Underwater Vehicles via Data-Informed Domain Randomization](https://www.mdpi.com/2076-3417/13/3/1723) — non-Koopman nearest neighbor, same domain
- [Towards Certified Sim-to-Real Transfer via Stochastic Simulation-Gap Functions](https://arxiv.org/pdf/2603.20672) — confirmed non-Koopman
- [Task-Oriented Koopman-Based Control with Contrastive Encoder, CoRL 2023](https://arxiv.org/abs/2309.16077) — real-robot lidar evaluation but no explicit sim2real/domain-gap discussion found

**Files/paths relevant to this task**: none — this was a pure literature-search subagent task with no repository writes. One fetched PDF was cached locally by the tool at `/root/.claude/projects/-workspace/add36792-5228-49ca-a6e5-ffa3c915bb4e/tool-results/webfetch-1785754168439-dtvwy5.pdf` (Mixture-of-Koopmans paper, unverified claim) — not authoritative, primary arXiv source is the link above.