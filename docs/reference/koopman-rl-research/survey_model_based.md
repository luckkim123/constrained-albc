## Model-Based RL with Koopman Models — Research Findings

### 1. End-to-end RL of Koopman models for economic NMPC (Mayfrank et al.)

**Papers**: Mayfrank, Mitsos, Dahmen, "End-to-end reinforcement learning of Koopman models for economic nonlinear model predictive control," *Computers & Chemical Engineering* 190 (2024) 108824. [arXiv:2308.01674](https://arxiv.org/abs/2308.01674) / [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0098135424002424). Follow-up: [arXiv:2511.04522](https://arxiv.org/abs/2511.04522) "End-to-End RL of Koopman Models for eNMPC of an Air Separation Unit" (later, larger-scale case study).

**Mechanism**: A nonlinear encoder ψ_θ lifts the plant state x to a Koopman latent z₀ = ψ_θ(x₀); latent dynamics are strictly linear, z_{t+1} = A_θz_t + B_θu_t; a decoder recovers x̂_t = C_θz_t. Instead of fitting (A,B,C,ψ) by system identification (SI) for prediction accuracy, the whole pipeline is unrolled inside an MPC and trained end-to-end with PPO: the reward is the actual NMPC/eNMPC control objective (negative tracking error for NMPC; economic cost savings relative to a steady-state baseline, minus constraint-violation penalty, for eNMPC). The Koopman model is thus optimized for *closed-loop control performance*, not open-loop prediction accuracy — policy gradients flow through the linear model used inside the MPC solve.

**Evidence**: Case study is a two-state CSTR (concentration, temperature; two inputs — production rate, coolant flow). Reported result: RL-trained Koopman models outperform SI-trained Koopman models in closed-loop NMPC/eNMPC score, and the RL-trained eNMPC controller adapts to changed constraints/setpoints without retraining, unlike a model-free MLP policy baseline which must be retrained from scratch for the new setting. (I extracted specific numeric scores — e.g., roughly a 60-plus-percent NMPC score improvement over SI, and a ~9% eNMPC cost gap vs. SI — from an automated fetch of the paper body; I was not able to open the PDF directly to hand-verify these digits, so treat the *existence and direction* of the result as confirmed, the exact magnitudes as indicative pending a manual read of the PDF/table.)

**Maturity**: Published, peer-reviewed journal (Comput. Chem. Eng. 2024), with a 2025/2026 follow-up scaling to an air separation unit — this is an active, maturing line, not a one-off.

### 2. Dyna-style Koopman surrogate rollouts (Plotzki & Peitz)

**Paper**: Plotzki, Peitz, "Koopman-based surrogate modeling for reinforcement-learning-control of Rayleigh-Bénard convection," [arXiv:2603.28074](https://arxiv.org/abs/2603.28074) (TU Dortmund / Lamarr Institute).

**Mechanism**: A Linear Recurrent Autoencoder Network (LRAN) — conv encoder/decoder, latent dim 200, controls injected via an affine transform (matrix U + bias) on the latent state — is trained with a discounted multi-step reconstruction loss (T=10, δ=0.9) to produce a space where dynamics are linear (Koopman-style). This surrogate then generates **cheap synthetic rollouts** for PPO training, explicitly in the Dyna sense: a "random-action" surrogate is pretrained offline on ~3,300 DNS episodes; a "policy-aware" surrogate is periodically refreshed on-policy (MBPO-style) to fight distribution shift, since the surrogate is only valid on states its training data covers.

**Evidence**: Task = controlling 12 thermal actuators to minimize Nusselt number (heat transport) in 2D Rayleigh-Bénard convection (Ra=10⁴). Surrogate rollouts run **25.6× faster** than the ground-truth DNS solver. Training on the surrogate alone gets close but not to full quality (Nu≈2.97–3.31 vs. Nu≈2.74 for pure-DNS PPO); a **surrogate-pretrain-then-DNS-finetune** schedule matches state-of-the-art control quality (Nu≈2.73–2.75) while cutting total wall-clock training time **>40%** (2h24m–3h6m vs. 4h11m pure DNS).

**Maturity**: Single-institution arXiv preprint (2026), not yet a widely cited/adopted method — a clean proof-of-concept, not production-tested.

### 3. Real2Sim2Real continuum/soft-robot RL surrogate (survey ref [67])

**Paper**: Ji, Gao, Xiao, Sun, "Efficient Real2Sim2Real of Continuum Robots Using Deep Reinforcement Learning With Koopman Operator," *IEEE Transactions on Industrial Electronics* (2025), preprint on [TechRxiv](https://www.techrxiv.org/doi/full/10.36227/techrxiv.172954270.09322852/v1), IEEE Xplore doc 10875033. Confirmed as the exact citation behind ref [67] in the survey "Koopman Operators in Robot Learning" ([arXiv:2408.04200](https://arxiv.org/html/2408.04200v2), sentence: *"Koopman models are used to either approximate environment dynamics [67] or support the design of critic networks [103]"*) — verified via Semantic Scholar's reference-context field, not by manually opening the survey's bibliography (both PDF and full HTML of the survey were too long for the fetch tool to reach the references section, so this citation is corroborated by matching context text rather than by reading the printed "[67]" entry myself).

**Mechanism**: A continuum (soft, hyper-redundant) robot is system-identified with a Koopman operator from real-robot data (the "Real2Sim" step) to serve as a **surrogate training environment**, replacing an expensive/risky physical rollout loop. An online RL policy is then trained inside this Koopman-surrogate simulator, with training efficiency boosted by injecting imperfect/suboptimal demonstrations into the RL loop (safety-critical framing — avoids exploring dangerous actions directly on real hardware). The trained policy is deployed back to the real continuum robot ("Sim2Real"/"2Real"). Reported limitation: hysteresis in the real robot's actuation is **not captured** by the linear Koopman surrogate, degrading tracking performance at deployment — I could not retrieve the exact quantitative tracking-error/sample-efficiency numbers (TechRxiv and IEEE Xplore both blocked the fetch with 403; abstract-level search snippets confirm the mechanism and the hysteresis caveat but not hard numbers).

**Maturity**: Peer-reviewed IEEE journal (TIE 2025), single-robot case study — a validated but narrow proof-of-concept, not a general recipe.

### 4. DeepKoCo — task-relevant latent Koopman planning

**Paper**: van der Heijden, Ferranti, Kober, Babuška, "DeepKoCo: Efficient latent planning with a task-relevant Koopman representation," IROS 2021, [arXiv:2011.12690](https://arxiv.org/abs/2011.12690).

**Mechanism**: A "lossy" autoencoder maps pixel observations to a Koopman latent whose linear dynamics are trained to reconstruct/predict only the **task cost signal**, not full pixel dynamics (deliberately throwing away task-irrelevant variation, e.g. visual distractors). Because the latent dynamics are linear, planning reduces to **linear MPC** in the latent space rather than nonlinear trajectory optimization — this is a model-based RL / model-predictive-planning method with a Koopman world model, structurally close to PlaNet/Dreamer but with a linear (not stochastic-nonlinear) latent transition.

**Evidence**: Claimed to match final performance of model-free baselines on complex control tasks while being markedly more robust to distractor dynamics (task-irrelevant visual clutter) — I could not retrieve the paper's actual reward numbers/benchmark table (the PDF is binary/compressed and unparseable by the fetch tool, and no HTML mirror exists for this 2020 arXiv submission); this claim rests on the abstract only, not a verified results table.

**Maturity**: Peer-reviewed IEEE conference (IROS 2021), state-based-observation lineage (not something we've re-covered per your instructions on KIPPO/Koopman-encoder/SKooP).

---

## Applicability to Our Stack

**Teacher training (4096-env GPU rollout) — NOT-APPLICABLE.** Every one of these methods buys its speedup by replacing an *expensive* ground-truth generator (DNS solve, real hardware rollout, or an eNMPC's own costly mechanistic simulation) with a *cheap* linear surrogate. Our ground truth is already the cheap side of that trade: Isaac Sim on GPU with 4096 parallel envs is the fast bulk-rollout generator these papers are trying to approximate. Inserting a Koopman surrogate here would mean training a lower-fidelity linear model to imitate a simulator that is already producing more physically-correct data faster than the surrogate-fitting process itself would run. There is no latency/cost gap for a surrogate to close.

**Student DAgger — NOT-APPLICABLE for the bulk-training loop, STRETCH for a narrow real-hardware use.** DAgger's bottleneck is teacher-label queries on student-visited states, and the teacher (same GPU-parallel Isaac Sim policy) is not expensive to query either — so a Koopman surrogate doesn't relieve any real constraint there. The one place a method like Ji et al.'s Real2Sim2Real is structurally relevant is *after* deployment: if the real UUV's actual dynamics deviate from any DR sample the teacher/student saw (unmodeled hysteresis, biofouling, thruster wear), a Koopman operator identified online from real telemetry could, in principle, provide a cheap local surrogate for safety-checked on-robot fine-tuning. That is a genuinely different project (online real-robot adaptation), not an acceleration of the existing sim-side teacher/student pipeline, so it's a stretch at best and not something to fold into the current campaign.

**Core blocker for all four, independent of the above**: every demonstrated system here is a *single fixed plant* — one CSTR, one Rayleigh-Bénard Ra, one continuum-robot instance, one DeepMind-Control-Suite body. None handles a persistently-randomized 28D DR family (hydrodynamic coefficients, payload, ocean current, thruster faults) inside one Koopman operator. A linear operator fit (or RL-tuned) for one plant instance does not transfer across our DR distribution — you would need either a family of Koopman models conditioned on p_t (defeating the point of a cheap single-operator surrogate) or a single operator expressive enough to span the whole DR range (undermined by the very same linearization assumption that makes these methods cheap). This is the same "no single K for a DR plant family" issue that already ruled out replacing the privileged encoder with a Koopman encoder in your prior review — it applies with equal force to a Koopman *rollout generator*.

**Verdict**: **NOT-APPLICABLE** — our ground-truth generator (4096-env GPU sim) is already cheaper than any Koopman surrogate would be to build and validate, and the heavy DR plant family blocks a single Koopman operator from being valid across our training distribution in the first place.

## Sources

- [arXiv:2308.01674 — End-to-End RL of Koopman Models for Economic NMPC](https://arxiv.org/abs/2308.01674)
- [ScienceDirect — Comput. Chem. Eng. 190 (2024) 108824](https://www.sciencedirect.com/science/article/pii/S0098135424002424)
- [arXiv:2511.04522 — End-to-End RL of Koopman Models for eNMPC of an Air Separation Unit](https://arxiv.org/abs/2511.04522)
- [arXiv:2603.28074 — Koopman-based surrogate modeling for RL-control of Rayleigh-Bénard convection](https://arxiv.org/abs/2603.28074)
- [TechRxiv — Efficient Real2Sim2Real of Continuum Robots Using Deep RL With Koopman Operator](https://www.techrxiv.org/doi/full/10.36227/techrxiv.172954270.09322852/v1)
- [IEEE Xplore doc 10875033 — same paper, IEEE Trans. Industrial Electronics 2025](https://ieeexplore.ieee.org/document/10875033)
- [arXiv:2408.04200 — Koopman Operators in Robot Learning (survey; source of ref [67])](https://arxiv.org/html/2408.04200v2)
- [arXiv:2011.12690 — DeepKoCo: Efficient latent planning with a task-relevant Koopman representation](https://arxiv.org/abs/2011.12690)
- [Semantic Scholar reference-context lookup for arXiv:2408.04200 (used to confirm ref [67] identity)](https://api.semanticscholar.org/graph/v1/paper/arXiv:2408.04200/references)

**Explicit caveats on evidence quality**: (1) Mayfrank et al.'s exact numeric results (CSTR NMPC/eNMPC scores) were extracted by the fetch tool from the paper's body text, not hand-verified against the PDF/tables myself — mechanism and directional finding are solid, exact digits should be treated as indicative. (2) The survey's ref [67] → Ji et al. mapping is confirmed via Semantic Scholar's citation-context match (identical sentence text), not by reading the survey's printed bibliography line myself, since both the PDF and full HTML of the 2408.04200 survey were too long for the fetch tool to reach the references section. (3) DeepKoCo's quantitative results table could not be retrieved (PDF unparseable, no HTML mirror for this 2020 submission) — only the qualitative abstract claims are reported.