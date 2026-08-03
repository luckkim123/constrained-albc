# Research report — invariance_dr (THEO-9 rebuttal cluster)

**Assignment**: Resolve THEO-9 — the claim that a single shared dynamics-prediction operator (single `K`)
trained across 4096 DR-randomized plants acts as an invariance regularizer, preferentially discarding
env-identifying information the ALBC encoder/policy needs, and the proposed fix `K(z)` (context-conditioned
operator). Also cover Q1–Q4 as specified.

---

## Q1 — Direct evidence: shared dynamics-prediction aux loss vs env-parameter information in the representation

**No paper found that runs the doc's exact ablation** (single shared K-style linear/near-linear operator
fit jointly across a DR distribution, then probes the pre-K representation for env-parameter recoverability
before vs. after adding the aux loss). This is a genuine evidence gap — say so plainly rather than
manufacture a citation.

What the literature *does* establish, converging from three independent directions, is the general
mechanism THEO-9 invokes:

1. **A shared/global dynamics model under domain randomization is empirically known to underperform a
   context-conditioned one, and the standard diagnosis in that literature is exactly "a single model
   averages across the distribution."** CaDM (Lee et al. 2020, ICML) states the problem directly: "learning
   a global model that generalizes across different dynamics remains a challenge" and shows a **non-
   context-conditioned ("vanilla") dynamics model losing to a context-conditioned one by ~4–7x** on held-out
   dynamics (HalfCheetah moderate: vanilla DM 1026.7±164.7 vs. PE-TS+CaDM 7087.2±1495.6; Ant moderate:
   520.0±97.6 vs. 2121.0±60.4) — full-text-read, Lee et al. 2020. This is evidence of the *symptom*
   (single-model degradation under DR), not a direct information-theoretic diagnosis of *why*, but it is
   the closest empirical anchor: the field's default explanation for why a single model underperforms is
   that it is forced toward a compromise fit, i.e. toward whatever is invariant/common across the sampled
   dynamics, at the expense of per-instance accuracy.

2. **General domain-randomization literature independently confirms the robustness/optimality trade-off
   THEO-9 describes**, framed at the policy level rather than the representation level: DR "trades
   optimality for robustness," and "excessively high randomization leads to over-regularized policies";
   DR-trained policies are frequently described as "conservative" and struggling with out-of-distribution
   dynamics because they rely on "interpolation" over the trained distribution (search snippets, ICLR 2024
   domain randomization paper and adjacent 2025 sim-to-real surveys — abstract/snippet depth, full ICLR PDF
   was not machine-readable via WebFetch, binary size limit). This is the policy-level analogue of THEO-9's
   representation-level claim and is consistent with it, but is not itself a representation-level proof.

3. **Information-bottleneck framing of sim-to-real (Bridging the Sim-to-Real Gap from the Information
   Bottleneck Perspective, arXiv 2305.18464) makes the opposite-direction risk explicit and is directly
   relevant**: compressing a history-conditioned representation *without* an explicit term that preserves
   privileged/env information degrades adaptation. Their objective is `max I(Z_t; S^p_t) − β·I(H_t; Z_t)` —
   i.e., compression (the `I(H_t;Z_t)` term) is only safe because it is explicitly counterweighted by a term
   that *forces* env-identifying information (`S^p_t`, privileged state) to survive. Their own ablation
   (removing the IB/MI-preservation term, "HIB-w/o-ib") shows performance "almost fails" — full-text-read of
   abstract+extracted sections via ar5iv. This is the mirror image of THEO-9's concern: an *unconstrained*
   compression/invariance pressure (no explicit env-preserving counter-term) is empirically damaging to
   adaptation-relevant information. A single shared `K` fit with no per-env output branch is exactly an
   unconstrained compression pressure in this sense — it has no analogous counter-term forcing it to retain
   θ-dependent structure.

4. **IIDA (arXiv 2203.05549, "Context is Everything: Implicit Identification for Dynamics Adaptation")
   demonstrates the constructive counter-case that supports the diagnosis by contrast**: when the dynamics
   predictor *is* context-conditioned (`f_θ(s,a; z_e)`, `z_e` inferred from a small history), the dynamics-
   prediction loss alone (no auxiliary identification loss) causes the context encoder to organically
   recover environment-identifying structure — their latent-space visualization shows distinct clusters
   corresponding to different physical dynamics, with **no explicit env-ID loss required** (full-text-read
   via ar5iv). This is direct evidence that the failure mode in THEO-9 is specifically about *sharing one
   operator with no per-env conditioning path*, not about dynamics-prediction losses in general: conditioned
   dynamics-prediction losses are demonstrably information-preserving (even information-*producing*) for env
   identity; it is the *unconditioned, single-operator* case that has no mechanism to keep that information
   and is structurally pushed away from it, because the loss only rewards fθ,K on components of φ(x) whose
   evolution is θ-invariant.

**Verdict on Q1**: No paper runs THEO-9's exact experiment, so the claim is not directly proven in the
literature. But three convergent, independently-sourced pieces of evidence (CaDM's global-vs-context-model
gap, the IB sim-to-real ablation showing unconstrained compression damages adaptation-relevant information,
and IIDA's demonstration that *conditioned* dynamics losses spontaneously preserve/create env-identity while
being silent on the unconditioned case) make THEO-9's mechanism plausible and consistent with the field's
consensus failure mode for global dynamics models under parameter distributions. This is "plausible and
well-supported by adjacent evidence," not "directly demonstrated."

---

## Q2 — Context-conditioned dynamics models (CaDM family) as the principled fix

### CaDM (Lee et al., ICML 2020, arXiv:2005.06800) — full-text-read

- **Context inference**: MLP encoder `g(τ^P_{t,K}; φ)` over a history of K past `(Δs, a)` transition pairs
  (state *differences*, not raw states — chosen to be robust to state normalization/offset), producing a
  10-D context vector `z_t`.
- **Loss**: forward dynamics `f(s_{t+1}|s_t,a_t,z_t;θ)` + backward dynamics `b(s_t|s_{t+1},a_t,z_t;ψ)`,
  jointly, plus a multi-step-ahead (M-step) forward loss. The **backward** term is the paper's key trick —
  it is a second prediction target with no obvious "shared/invariant" solution, which empirically forces
  `z_t` to carry more dynamics-specific signal than the forward loss alone would.
- **Policy path — critical for THEO-9/K(z) design**: CaDM uses `z_t` in **two separate roles**: (a) inside
  the dynamics model for MPC planning (PE-TS+CaDM), and (b) as an *additional input to a model-free policy*,
  `π(a_t | s_t, g(τ^P_{t,K};φ))`. **No stop-gradient is used or discussed between the context encoder and
  the policy** in the base paper — the context path is jointly trained, differentiable end-to-end into both
  the dynamics loss and (in the model-free variant) the RL objective. This matters for the doc's `K(z)`
  design: CaDM's own default does *not* isolate the context encoder from policy gradients, so citing CaDM as
  precedent for "stop-grad the context path" would be inaccurate — that isolation choice would be a design
  addition beyond CaDM, better supported by RMA/WMR-style architectures (see Q3).
- **Results**: context-conditioned model beats a non-conditioned "vanilla" dynamics model by 4–7x on
  moderately-shifted test dynamics (numbers above).
- **Reusability**: TensorFlow 1.15 codebase (github.com/younggyoseo/CaDM), 5 commits, no visible license,
  not actively maintained — **not directly reusable for a PyTorch/rsl-rl stack**; the architecture (small
  history-window MLP context encoder + forward/backward joint loss) is trivial to reimplement from scratch
  in PyTorch (~100 lines), which is the realistic reuse path.

### Successors surveyed

- **T-MCL (Seo, Lee, Clavera, Kurutach, Shin, Abbeel, NeurIPS 2020, arXiv:2010.13303)**: multi-headed
  dynamics model, each head specializes to a cluster of similar dynamics via a trajectory-wise winner-take-
  all update, *combined with* context learning per-head. This is a **discrete/mixture** alternative to
  CaDM's continuous context vector — relevant if ALBC's DR distribution is more naturally multi-modal
  (e.g., thruster-fault on/off is closer to a discrete mode than a continuous parameter) — abstract/snippet
  depth via WebSearch.
- **ProtoCAD (arXiv:2211.12774, "Prototypical context-aware dynamics generalization")**: adds a
  temporally-consistent prototype-clustering regularizer on top of the CaDM-style context vector; reports
  13.2%/26.7% mean/median improvement over RSSM (a *shared* recurrent world model) across dynamics-
  generalization tasks — another independent data point that context-conditioning beats a shared model, this
  time in the visual-control / RSSM setting — abstract/snippet depth.
- **"RIA"**: no paper matching this description was found under that acronym in this search pass; not
  confirmed to exist as named. Do not cite it.
- **GHN/hypernetwork-conditioned dynamics**: no dedicated GHN-for-dynamics-under-DR paper was found;
  Graph HyperNetworks (Zhang et al.) are a general parameter-prediction architecture cited by CaDM's related
  work as a structurally-adjacent idea (predict per-instance weights from a graph/context) but not applied
  to Koopman/dynamics-under-DR in what was found.

**Verdict on Q2**: CaDM and its family are a real, well-established precedent for "condition the operator on
an inferred context rather than sharing one operator," and consistently outperform the shared/global
baseline (4–7x in CaDM; 13–27% in ProtoCAD; qualitatively similar in T-MCL). None of them isolate the
context path from the policy by default — that architectural choice, if the doc wants it, needs to be
justified independently (see Q3), not borrowed from CaDM.

---

## Q3 — RMA-style adaptation module + dynamics-prediction aux task coexisting

This is the thinnest-evidenced question. No paper was found that runs the *exact* ablation (RMA adaptation
module present, dynamics-prediction aux task added on top, isolate whether the aux task helps or fights the
adaptation channel). What was found:

- **World Model Reconstruction for humanoid locomotion (arXiv:2502.16230)** is the closest architectural
  precedent, and it is informative by its *design choice*: the paper explicitly states "the policy takes
  inputs entirely from the reconstructed information... the policy and the estimator are trained jointly;
  **however, the gradient between them is intentionally cut off**" (abstract, WebFetch). This is a direct,
  named instance of the exact concern in THEO-9's design consequence: the authors evidently judged that
  letting the auxiliary reconstruction/estimation objective and the policy objective share gradients through
  the same representation was risky enough to warrant an explicit architectural firewall (stop-gradient).
  That is affirmative precedent for "isolate the aux-loss-trained context path from the policy path with
  stop-gradient" as a real, deployed mitigation pattern in privileged-distillation-style locomotion work —
  though the paper does not report an ablation *without* the stop-gradient, so the counterfactual magnitude
  of the risk it is guarding against is not quantified.
- **PrivilegedDreamer (arXiv:2502.11377)** is a stronger positive precedent for **why K(z) specifically (not
  stop-gradient) can work**: it uses "a dual recurrent architecture that explicitly estimates hidden
  parameters from limited historical data" and **conditions the model, actor, and critic networks on these
  estimated parameters** — i.e., no stop-gradient; the estimate flows everywhere, including into the world
  model itself (structurally the closest published analogue to the doc's `K(z)` proposal, in a Dreamer-style
  RL loop rather than MPC/system-ID). It reports outperforming RMA-style and domain-adaptation baselines
  across five hidden-parameter-MDP tasks (abstract/snippet depth — full quantitative table not extracted).
  This is evidence *against* stop-gradient being necessary in general: PrivilegedDreamer gets gains letting
  gradients flow freely into the estimator from model+actor+critic, contradicting the WMR paper's choice.
  The two papers disagree on the design question, which itself is useful: **the literature does not converge
  on stop-gradient vs. joint gradient-flow as the right answer**; both are used successfully in adjacent
  settings.
- **RMA itself (Kumar et al. 2021)**: the base architecture has **no dynamics-prediction aux loss** — phase
  1 trains a policy conditioned on true privileged parameters, phase 2 trains the adaptation module with pure
  supervised regression to *match* those parameters (or the phase-1 latent) from proprioceptive history. RMA
  was not designed to coexist with a separate dynamics-prediction objective, so it offers no direct evidence
  either way on the coexistence question; it is only useful as the baseline architecture that CaDM/K(z)-style
  proposals would be added on top of.

**Verdict on Q3**: Direct evidence of the specific interaction (does adding a dynamics-prediction aux task to
an RMA-style adaptation module help or hurt) is not available in the literature surveyed. The two closest
analogues actively disagree on whether gradient isolation is needed (WMR: yes, cuts gradient; PrivilegedDreamer:
no, lets it flow and reports gains). This should be reported to the project as an open empirical question,
not resolved by citation — if ALBC adds a `K(z)` term, both variants (with and without stop-gradient into the
existing 9-D encoder) are defensible starting points and the literature does not pick a winner.

---

## Q4 — Parameter-conditioned linear/Koopman latent dynamics precedent for `K(z)`

- **MAKO (Han, Wong, Law, Yin, arXiv:2510.09042, "Meta-Adaptive Koopman Operators...")** — full-text-read
  (arxiv HTML v1). Closest Koopman-specific precedent found.
  - Structure: **per-task Koopman operators** `A^i, B^i, C^i` fit for each of a set of parametric task
    settings `Θ^i` during meta-training, sharing a common learned observable/lifting map `ψ_θ` (the "MNN")
    across tasks. This is *not* the doc's `K(z)` (a single continuously-parameterized operator function of an
    inferred latent) — it is closer to a **discrete multi-task/meta-learning** setup: a shared lift + a
    small set of task-specific linear operators, adapted online via **gradient descent on new data** at
    deployment, not by amortized inference from a context encoder.
  - Conditioning input: the shared lifting network `ψ_θ(x)` is **not itself conditioned on the task/context
    latent** — only the downstream linear operators are task-specific. This is a meaningfully different
    design from the doc's proposal, where `z` (from the existing 9-D encoder) would condition `K` directly.
  - Gradient flow: fully end-to-end/differentiable, no stop-gradient reported, joint loss over `ψ_θ` and all
    `{A^i,B^i,C^i}`.
  - Quantitative comparison vs. a **single shared operator** (the doc's exact concern) is **not reported** —
    MAKO's baselines are DeSKO (nominal-only training) and other non-adaptive Koopman baselines, not an
    ablation isolating "one K across all Θ" vs. "per-task K." This is a real evidence gap even within the
    closest paper found.
  - Scope: pure system identification + MPC, **no RL policy in the loop** — cannot directly transfer
    quantitative claims to ALBC's actor-critic setting.
- **Parameter-Varying Koopman Operator (arXiv:2309.10278)**: an LPV-style Koopman model — local
  time-invariant linear systems interpolated in the lifted space as a function of a (measured/known)
  scheduling parameter, giving a state-dependent input matrix. Uses **known/measured** scheduling parameters,
  not an inferred latent from a history encoder — i.e., closer to "K(θ_true)" than "K(z)". Relevant as the
  classical-control precedent that parameter-conditioned Koopman operators are a well-established idea
  (LPV/Koopman literature predates the RL framing by years), but does not address the "infer θ from a latent"
  problem that ALBC actually faces (θ is not observable at deployment).
- **Continuous-time Koopman autoencoder with parameter-conditioned linear generator** (found via search,
  fluid-dynamics forecasting context): explicitly conditions the continuous Koopman generator on governing
  physical parameters (Reynolds/Mach number) to capture families of dynamical systems in one model — same
  pattern as PVKO, conditioned on **known physical parameters**, not an inferred RL-style context latent.
  Abstract/snippet depth only.
- **Bilinear Mamba-Koopman (arXiv:2605.04793)**: control-input-dependent coupling in the latent dynamics
  ("effective operator adapts to the current input") — this is conditioning on the *control signal*, not on
  an environment/plant-identity latent; a different axis of adaptivity than THEO-9's concern. Not directly
  relevant to the DR/plant-identity question. Pure system-ID/MPC, no RL.

**Verdict on Q4**: The strongest and most literal precedent for a *linear/Koopman* operator conditioned on
inferred context is MAKO, and even MAKO does not match the doc's `K(z)` design exactly (per-task discrete
operators + online gradient adaptation, vs. a single continuously-parameterized function of an amortized
latent). All the Koopman-specific precedent that *does* match the doc's functional form (parameter-
conditioned linear generator) conditions on **known physical parameters**, not an inferred latent — none of
the Koopman literature surveyed solves the "infer the conditioning variable from history, in an RL policy
loop" problem the way IIDA/CaDM/PrivilegedDreamer do outside the Koopman-specific literature. The nearest
full match to the doc's actual requirement (linear/near-linear latent dynamics, conditioned on an *inferred*,
not measured, context, feeding an RL policy) is **PrivilegedDreamer**, which is not Koopman-specific but is
architecturally the right shape: estimator → conditions {model, actor, critic}, no stop-gradient, reports
gains over RMA-style baselines.

---

## Implications for ALBC

1. **THEO-9's mechanism is well-supported by adjacent evidence though not directly proven for the exact
   K/DR setup.** The convergent signal (CaDM's 4–7x gap between shared and context-conditioned dynamics
   models under randomized dynamics; the IB sim-to-real paper's ablation showing unconstrained compression
   damages adaptation-relevant information; IIDA showing conditioned dynamics losses spontaneously *create*
   env-identifying clusters with no extra loss) makes "a single K fit across 4096 DR plants prefers
   plant-invariant features of `phi_x`" the most defensible prior, not a speculative worry. The doc's
   "may just weaken" framing in §8.4-2 understates this; §4.4(iii)'s "exactly" overstates it (no paper
   claims the residual captures *exactly* the encoder's target information — it captures *some*
   θ-correlated signal mixed with model-misspecification error, per the general mis-specification argument
   in the critique, which this search corroborates rather than refutes).

2. **If ALBC adds a single, unconditioned K trained jointly across the full DR distribution as a soft aux
   regularizer on `phi_x` (or on the 9-D `z`), predict a directional risk to the adaptive channel, not a
   neutral outcome.** The mechanism (loss only rewards θ-invariant components of the representation) is the
   same one that makes global dynamics models lose to context-conditioned ones by a wide margin in every
   analogous RL/model-based paper found. Given the project's explicit focus on real thruster-fault
   adaptation (2/6 thrusters currently faulted) and the student's GRU distillation of `z`, this is exactly
   the channel that must not be invariance-regularized away.

3. **`K(z)` (conditioning the operator on the existing 9-D `z` from the encoder) is a defensible fix and has
   real precedent, but the doc should not claim it is a solved/standard pattern.** No paper in this search
   implements the doc's exact form (continuous latent-conditioned linear operator, fed by an existing
   amortized encoder, inside an actor-critic RL loop). The closest matches (MAKO: discrete per-task operators,
   pure system-ID; PrivilegedDreamer: right shape, not Koopman-specific, in RL) both work by different
   mechanisms than what the doc sketches. Treat `K(z)` as a reasonable, motivated experiment, not an
   established recipe — and note both mechanism precedents (MAKO's per-instance operator adaptation, and
   PrivilegedDreamer's shared-conditioning) as alternative concrete designs worth comparing rather than
   assuming the continuous-conditioning form is best.

4. **Whether to stop-gradient `K(z)`'s context input away from the existing encoder/policy path is an open
   question the literature does not resolve — do not adopt either default without an ALBC-specific ablation.**
   WMR (locomotion) cuts the gradient between its estimator and policy; PrivilegedDreamer does not and reports
   gains from full gradient flow. Given ALBC's specific risk (constraint-satisfaction policy trained with
   ConstraintTRPO+IPO, asymmetric critic, and a downstream GRU student distilling `z`), the safer starting
   point is **stop-gradient from the K-fitting loss into the shared encoder**, on the grounds that this
   isolates the invariance pressure to a side-branch (`K`'s own parameters and possibly a dedicated small
   projection head) without risking the encoder's existing 9-D `z` — this is the WMR-style conservative
   choice, cheaper to fall back from than PrivilegedDreamer's fully-coupled design if it turns out to hurt.
   This should be run as an A/B (stop-grad vs. not) rather than asserted, exactly as the "constructive fix
   space" framing in THEO-9's design-consequence line demands.

5. **If ALBC instead wants precedent for accepting the invariance pressure and predicting a null/negative
   result** (THEO-9's third listed option), that framing is also literature-consistent: general DR-robustness
   findings describe DR policies as systematically "conservative" and reliant on "interpolation," which is
   the policy-level symptom of exactly the representation-level invariance pressure THEO-9 describes. This
   gives the doc a citable, if generic, backstop if the `K(z)` experiment does not pan out.

---

## References

1. Lee, K., Seo, Y., Lee, S., Lee, H., Shin, J. — "Context-aware Dynamics Model for Generalization in
   Model-Based Reinforcement Learning" — ICML 2020, PMLR v119, pp. 5757–5766. arXiv:2005.06800.
   https://arxiv.org/abs/2005.06800 — verification depth: full-text-read (via ar5iv HTML).

2. Seo, Y., Lee, K., Clavera, I., Kurutach, T., Shin, J., Abbeel, P. — "Trajectory-wise Multiple Choice
   Learning for Dynamics Generalization in Reinforcement Learning" — NeurIPS 2020. arXiv:2010.13303.
   https://arxiv.org/abs/2010.13303 — verification depth: abstract/snippet.

3. Wang, J. et al. — "Prototypical context-aware dynamics generalization for high-dimensional model-based
   reinforcement learning" — arXiv:2211.12774 (also IEEE Trans., 2024 IEEE version).
   https://arxiv.org/abs/2211.12774 — verification depth: abstract/snippet.

4. [Authors unresolved in this pass] — "Bridging the Sim-to-Real Gap from the Information Bottleneck
   Perspective" — arXiv:2305.18464. https://arxiv.org/abs/2305.18464 — verification depth: full-text-read
   of abstract + extracted method/results sections (via ar5iv HTML; author names not confirmed in the
   extracted text — re-verify author list before citing in the final doc).

5. [Authors unresolved in this pass] — "Context is Everything: Implicit Identification for Dynamics
   Adaptation" (IIDA) — arXiv:2203.05549. https://arxiv.org/abs/2203.05549 — verification depth:
   full-text-read of method/results sections (via ar5iv HTML; author names not confirmed — re-verify before
   citing).

6. [Authors unresolved in this pass] — "Learning Humanoid Locomotion with World Model Reconstruction" —
   arXiv:2502.16230. https://arxiv.org/abs/2502.16230 — verification depth: abstract-only (WebFetch could
   not access full text — PDF exceeded fetch size limit).

7. [Authors unresolved in this pass] — "PrivilegedDreamer: Explicit Imagination of Privileged Information
   for Rapid Adaptation of Learned Policies" — arXiv:2502.11377. https://arxiv.org/abs/2502.11377 —
   verification depth: abstract-only (PDF exceeded fetch size limit; full quantitative results not
   extracted — re-verify numbers before citing specifics).

8. Han, M., Wong, K., Law, A. W.-K., Yin, X. — "MAKO: Meta-Adaptive Koopman Operators for Learning-based
   Model Predictive Control of Parametrically Uncertain Nonlinear Systems" — arXiv:2510.09042.
   https://arxiv.org/html/2510.09042v1 — verification depth: full-text-read (via arxiv HTML v1).

9. [Authors unresolved] — "Parameter-Varying Koopman Operator for Nonlinear System Modeling and Control" —
   arXiv:2309.10278 (also IEEE, 2023/2024). https://arxiv.org/abs/2309.10278 — verification depth:
   abstract/snippet.

10. [Authors unresolved] — "Bilinear Mamba-Koopman Neural MPC for Varying Dynamics" — arXiv:2605.04793.
    https://arxiv.org/abs/2605.04793 — verification depth: abstract/snippet.
    **Note on date**: this arXiv ID (2605.xxxxx) implies a submission year past the assistant's training
    cutoff conventions (2026); treat the existence/content of this specific paper as reported by live web
    search, not independently cross-checked against arXiv's own listing page.

11. Kumar, A., Fu, Z., Pathak, D., Malik, J. — "RMA: Rapid Motor Adaptation for Legged Robots" — RSS 2021
    (background reference, not independently re-verified in this pass beyond prior general knowledge +
    corroborating search snippets). verification depth: snippet-corroborated prior knowledge — flag for
    independent re-verification if precise architectural claims are load-bearing in the final doc.

**General caveat**: several 2025/2026-dated arXiv IDs surfaced by WebSearch (e.g. 2502.xxxxx, 2505.xxxxx,
2602.xxxxx, 2605.xxxxx, 2607.xxxxx) were only reachable at abstract depth — WebFetch repeatedly hit a
10 MB PDF size cap and ar5iv mirrors are not yet populated for the newest IDs. Their content above is
reported at the verification depth stated per-item; do not treat abstract/snippet-depth items as fully
vetted the way the full-text-read items (CaDM, MAKO, IIDA, the IB sim-to-real ablation) are.

---

## GitHub repos

1. **github.com/younggyoseo/CaDM** — implements CaDM (Lee et al. 2020). TensorFlow 1.15, 5 commits, no
   visible license, not actively maintained. **Reusability for PyTorch/rsl-rl**: not directly reusable
   as code; the core idea (small-MLP history encoder over `(Δs,a)` pairs → context vector → forward+backward
   dynamics heads) is simple enough to reimplement natively in the existing `_core/encoder/` module (~100
   lines), which is the realistic path for ALBC rather than importing this repo.

2. **github.com/younggyoseo/trajectory_mcl** — implements T-MCL (Seo et al. 2020, NeurIPS). Not fetched in
   detail this pass (time-boxed); expect similar TF1-era codebase given same author/lab as CaDM. Relevant
   only as a design reference (multi-head dynamics model with trajectory-wise winner-take-all) if ALBC's DR
   distribution is judged closer to discrete modes (e.g. fault on/off) than continuous parameters — worth a
   second look if `K(z)` underperforms and a discrete/mixture-of-K alternative is wanted.

3. **No MAKO code repository was found** (searched explicitly; arXiv paper gives no code link in the
   fetched content, and no GitHub topic search surfaced an author-released implementation as of this
   search). If MAKO's per-task-operator design is wanted as a reusable pattern, it will need to be
   reimplemented from the paper's equations, not adopted from existing code.
