# Research report — degeneracy_guard (THEO-6/THEO-8/THEO-9 rebuttal cluster)

Scope: adjudicate whether the doc's simultaneous recommendation of (a) identity-inclusion `z=[x,g'(x)]`
(from [50] Li et al. 2024/2025, and [86] KoopNet) and (b) adopting KIPPO's architecture/framing is a
real contradiction or a role confusion, and design a falsifiable degeneracy gate for `phi_x`.

## Q1 — Is the Draeger/topological-conjugacy objection load-bearing for a regularizer role, or only for exact linearization?

**The citation is real and precisely what the evidence-lens critique quoted.** KIPPO (Cozma, Harris,
Qi, IJCAI 2025, §3.1, as extracted by the evidence-lens reviewer from the local PDF — I could not get
a clean text extraction of the KIPPO PDF myself; the quote is taken on the evidence-critique's
verified authority, not independently re-verified in this pass, so treat as **snippet-level, one hop
removed**): "we do not concatenate the original state with the encoded state, as this restricts the set
of systems where linearization is possible. Specifically, finding a linear representation of a
non-linear system that includes the original state becomes impossible when the system has multiple
fixed points or general attractors... linear systems (with a single fixed point at the origin) are not
topologically conjugate to non-linear systems with multiple fixed points [Draeger et al., 1995]." I
could not independently locate the Draeger et al. 1995 primary source (two targeted searches returned
nothing); its content as reported is consistent with a standard dynamical-systems fact (topological
conjugacy preserves fixed-point count and index, so a system with N fixed points cannot be conjugate to
a linear system, which has exactly one), and I treat that underlying mathematical fact as
well-established independent of pinning the exact citation.

**Is it about exact linearization or does it bind a regularizer too?** The obstruction is a statement
about **exact global conjugacy** — the existence of a single smooth invertible map `phi` such that
`phi` intertwines the nonlinear flow with a linear flow *everywhere*. `arXiv:2304.11860` ("On the
lifting and reconstruction of nonlinear systems with multiple invariant sets") states this class of
result formally via Frobenius-integrability-type obstructions and is explicit that the failure is a
statement about **exact, global** linearization; for systems with multiple invariant sets the fix is
architectural (switched/patched linear systems, local charts around each invariant set), not a
statement that *approximate, local, or auxiliary-loss* linearity is meaningless (WebFetch summary of
2304.11860, PDF-extraction depth — flagged as processed-through-a-summarizer, not a verbatim quote
audit; treat as directional, not word-level evidence). This matches the structural argument already in
the doc's own §13.1(d): a soft regularizer whose gradients shape `phi_x`, never rolled out or inverted,
is not making a global-conjugacy claim, so the topological non-existence result does not directly forbid
the regularizer role.

**But identity-inclusion specifically is not "a regularizer using linearity" — it is a structural
guarantee about the family of realizable operators, and that part of the objection *is* load-bearing
regardless of role.** KIPPO's argument is not "linearity fails as a regularizer near multiple fixed
points"; it is "if you concatenate the raw state into z, then no K exists — not even approximately in a
meaningful sense — that can correctly play the role of a *global* linear evolution map for that z on a
multi-equilibrium plant, because z's dynamics inherit the nonlinear system's fixed-point structure by
construction (x is literally one of the coordinates, and x has ≥2 fixed points)." This is a **narrower
and more mundane claim than global topological conjugacy**: with z=[x,g'(x)], the sub-block dynamics on
x is exactly the original nonlinear x-dynamics, so *any* linear K acting on z incurs the same modeling
error on the x-block as fitting a global linear model directly to the raw state — which is a much
weaker, purely-approximation-theoretic statement, not a nonexistence theorem, and it degrades gracefully
(a poor but nonzero-quality linear fit to x, same as always existed before Koopman was introduced).  So
the correct verdict is: **identity-inclusion does not "break" the regularizer through a nonexistence
theorem — it re-introduces the raw-state's own linear-approximation error into the K term, verbatim**.
For a UUV+arm plant whose x already includes near-non-affine coupling terms (arm-hull, thruster
nonlinearity), that means the K-fit component of the loss on the identity block is dominated by the
plant's *own* nonlinearity and contributes little discriminating gradient — closer to THEO-4's finding
(K≈I on near-constant p_t) than to a hard theoretical wall.

**Verdict**: The Draeger objection is real, correctly quoted, and directly on point for a plant with
multiple equilibria (this UUV+arm plant qualifies: hover attitudes, arm configurations, and fault
regimes are all distinguishable operating points). It is not, strictly, a nonexistence theorem for the
*regularizer* role, but it correctly predicts that identity-inclusion **degrades the K-fit signal to
near-uselessness on the raw-state block**, which is the operationally relevant consequence either way.
KIPPO's choice to reject identity-inclusion and instead rely on an expansive-autoencoder +
reconstruction-loss architecture is the literature's actual answer to "how do you prevent degenerate `K
=` trivial-collapse without concatenating raw state," and the doc cannot adopt both [50]'s guard and
KIPPO's architecture as if they were compatible add-ons — they are two different, mutually exclusive
solutions to the same degeneracy problem, chosen by different author teams for different reasons ([50]:
robot has bounded/normalized state, single-domain-per-training setup, no representation-role concern;
KIPPO: explicitly designed for the actor-facing representation role and explicitly rejects [50]'s
solution for exactly this project's regime — multiple equilibria).

## Q2 — Catalog of degeneracy guards, and which detect an *inert* learned part (not just loss health)

| Guard | Mechanism | Detects inert `g'`? | Evidence |
|---|---|---|---|
| **Reconstruction loss** (standard Koopman-AE: Lusch/Kutz/Brunton 2018, Takeishi et al. 2017) | `‖x − decode(encode(x))‖` | **No** — this project's own failure mode (decoder ignores z, predicts mean) is a reconstruction-healthy, `g'`-inert failure. Reconstruction bounds the *decoder's* sufficiency, not whether every latent dim is used. Lusch et al. 2018 combine reconstruction + prediction + linearity losses jointly (ar5iv.labs.arxiv.org/html/1712.09707, WebFetch summary, snippet-level) but report no per-dimension sensitivity diagnostic — they rely on visual inspection of eigenfunction trajectories, which does not scale or generalize to a 9–34D unsupervisable latent. |
| **Identity-inclusion** ([50] Li et al. 2024, z=[x,g'(x)]) | Makes `A=B=0,g≡0` infeasible as a *global* minimizer since the identity block must be reproduced | **No** — proves g' cannot literally collapse to zero everywhere (the identity block forces some signal through), but does not prove g' carries *useful, non-redundant* information; g' can converge to a near-constant or a smooth-but-low-rank function of x and still pass every aggregate loss check, because the loss is dominated by the (already-solved) identity block. This is exactly THEO-8's finding, reproduced here as independently confirmed by the literature's own framing: [50]'s guard is against the *literal* degenerate solution (A=B=0), not against a *functionally* inert g'. |
| **Spectral/orthogonality constraints** (Erichson et al. Lyapunov-based stability constraints; Pan & Duraisamy tridiagonal-K unit-circle constraint; Mamakoukas et al. "Learning Stable Models for Prediction and Control" arXiv:2005.04291 — nearest-stable-matrix projection; "Eigenvalue Initialisation and Regularisation for Koopman Autoencoders" OpenReview 6TugHflAGRU) | Constrain the *spectrum* of the fitted K to be stable / near-unit-circle | **Partial, orthogonal axis** — these guard against a *diverging or ill-conditioned* K, not against an inert g'. They are compatible with (and a plausible required companion to) any anti-collapse guard, since a near-identity K passes trivially through a stability constraint (eigenvalues at 1 are marginal but not unstable) — so stability constraints alone would not catch this project's THEO-4 failure mode (K≈I on near-constant z) either. |
| **Variance/covariance regularizers (VICReg-style)** (Bardes, Ponce, LeCun, "VICReg: Variance-Invariance-Covariance Regularization", arXiv:2105.04906, ICLR 2022) | Two explicit terms: (1) per-dimension variance floor (`hinge(γ − std(z_i))`), (2) pairwise covariance penalty (off-diagonal decorrelation) | **Yes, directly** — this is the closest matched tool in the literature to "detect an inert dimension" rather than "detect a collapsed loss": a dead/constant dimension has std≈0 and is directly penalized by term (1); a redundant dimension that duplicates another is caught by term (2). VICReg's stated motivation is precisely to avoid the class of collapse this project suffered (encoder outputs a near-constant vector while every other loss term looks healthy) without needing negative pairs, stop-gradient, or architectural tricks — a good structural match for an unsupervised aux head bolted onto an RL actor. |
| **EMA/target networks** (BYOL-style, used in SPR/self-predictive representations for RL — Schwarzer et al.) | Predict a slowly-moving target encoder's output instead of the online encoder's own output | **No, for a different reason** — EMA targets prevent a different collapse (the "representation and predictor co-adapt to a trivial fixed point" failure of *bootstrapped* self-prediction), not the "one branch of the loss is solved by a shortcut" failure this project has. Not directly applicable unless the aux dynamics loss is restructured as a bootstrapped self-prediction task. |
| **Supervised heads** (this project's existing z_sweep discipline; also a natural fit for [50]'s per-dimension ablation instinct) | Train or probe a small supervised readout from (a subset of) z to a known target (e.g., DR parameter, or the raw privileged block) | **Yes, most directly, but requires labels** — a linear-probe accuracy check per dimension is the standard supervised diagnostic for "does this representation carry X" (see Q4). Its limitation is that it can only certify recoverability of *labeled* quantities; an inert g' that happens to encode something real but unlabeled (e.g., an emergent combination of hydrodynamic terms) would not be caught by a probe restricted to known DR parameters. |

**Combinations that detect an inert learned part (not just loss health).** No single guard in this
catalog does both "prevent the literal A=B=0 collapse" and "certify functional usefulness" — they are
answering different questions, and the doc's error (per THEO-8) was treating literal-collapse-prevention
([50]'s guard) as if it were functional-usefulness-certification. The combination that would actually
close the gap: **identity-inclusion or expansive-AE (either structural anti-collapse guard) PLUS a
VICReg-style per-dimension variance/covariance term restricted to the *g'* block only (not the identity
block) PLUS a periodic supervised probe (z_sweep-style) of g' against the six time-varying `p_t` channels
this project's own THEO-3 identified (ocean current, measured lin_vel) as the only dynamically
non-trivial signal available**. Restricting the variance/covariance regularizer to g' specifically (never
mixing it with the identity block's trivially-high variance) is necessary — otherwise the identity block
alone can satisfy a global variance floor while g' stays flat, which is the same shortcut failure
re-admitted through the regularizer's own aggregate statistic.

## Q3 — Latent size m evidence beyond KIPPO's {16,32,48}

- **OFENet** (Ota, Oiki, Jha, Mariyama, Nikovski, "Can Increasing Input Dimensionality Improve Deep
  Reinforcement Learning?", ICML 2020, arXiv:2003.01629) uses an explicitly **expansive** design — the
  auxiliary next-state-prediction network grows the representation to many multiples of the raw state
  dimension (the paper's headline claim is that *higher*-dimensional learned features improve sample
  efficiency, contrary to the "compress for RL" intuition). Per the search-result synthesis (I did not
  get a clean full-text extraction with the exact per-task dimension table — flag as search-snippet
  level, not verified against the primary PDF table), **"performance improved up to a certain threshold
  as dimensionality increased"** — i.e., OFENet itself reports the expansive-helps trend is not
  monotonic without limit; there is a documented ceiling, just not one this report can quote a number
  for without a primary-source re-read.
- **[50] (Li et al.)**: grow-on-plateau via the incremental refinement loop — `n^(k+1) = n^(k) + Δn`,
  a hand-set hyperparameter step, driven by an ablation showing dataset-coverage growth mattered more
  than dimension growth alone (8.4x vs 4.8x error inflation when each was removed, per the sub-report
  read earlier in this job — I am relaying that figure from the already-verified sibling report, not
  re-deriving it). This is evidence that **m alone is a weaker lever than data coverage** for the
  incremental-Koopman family — a caution against treating "increase m" as a fix in isolation.
- **KIPPO**: latent dims swept {16, 32, 48}; "dimensions of 32 or higher tend to boost returns and
  reduce variance" and "typically set to 2–4x the state dimension" (already verified by the sibling
  evidence-lens report, relayed here, not independently re-fetched this pass).
- **Koopman-AE works generally** (Lusch/Kutz/Brunton 2018; Takeishi et al. 2017, "Learning Koopman
  Invariant Subspaces for Dynamic Mode Decomposition") use comparatively **small, hand-tuned** latent
  dims (often ≤ 2x state dim or smaller, task-specific, chosen by matching the known number of
  physical modes) — these are model-fidelity-oriented works, not representation-for-RL works, and their
  small-m choices reflect wanting an interpretable, near-minimal spectral decomposition rather than an
  RL-friendly wide feature space. This is a genuinely different design objective than KIPPO/OFENet's,
  and the doc's "try smaller m first" instinct (criticized in the evidence-lens sibling report's THEO-7)
  is importing a fidelity-era heuristic into a representation-for-RL setting where the closest matched
  precedents (KIPPO, OFENet) both report larger-is-better up to an unquantified ceiling.
- **Evidence on over-expansion hurting**: none of the sources surfaced report a *sharp* failure mode
  from over-expansion beyond "diminishing then flat returns" (OFENet) — I did not find a paper reporting
  active *harm* from m too large, only saturation. This is a genuine literature gap, not a settled
  negative result; state it as absence of evidence, not evidence of no harm (a wider, under-constrained
  g' is also more capacity for the doc's own inert-dimension failure mode to hide in, which is a
  mechanism-level concern this report raises independently, not one sourced from a paper).

**Verdict for ALBC**: the state-dim-relative guidance from the two RL-representation-role precedents
(KIPPO, OFENet) both point toward the doc's default (2–4x) being reasonable-to-generous, not toward
shrinking m; the "try smaller m because o_t is pre-lifted" argument in the doc is an untested inference
with no cited precedent behind it (confirmed, consistent with the sibling evidence report's THEO-7).

## Q4 — A falsifiable health gate for phi_x, analogous to z_sweep

The project's existing z_sweep rule (`rules/03`: "Encoder 학습 여부를 TensorBoard aggregate만으로 단정 금지 …
per-dimension sensitivity sweep 실행 필수") is a per-dimension sensitivity probe. The equivalent for
`phi_x` needs to test three distinct failure modes separately, each with a cited precedent metric:

1. **Dead/constant-dimension detection** — per-dimension variance of `phi_x(o_t)` (or of the g' block
   specifically) across a held-out batch of `o_t` sampled from the actual visited state distribution.
   Precedent: VICReg's variance term (arXiv:2105.04906) treats `std(z_i) < γ` as the collapse signature;
   directly portable as a **pass/fail threshold**, not just a soft loss — run it as an eval-time check,
   not only a training loss.
2. **Redundant/low-rank block detection** — effective rank of the g'-block covariance matrix across a
   batch (e.g., participation ratio `(Σλ_i)² / Σλ_i²` on the eigenvalues of the empirical covariance, or
   simply `rank` at a numerical tolerance). Precedent: Moalla et al., "No Representation, No Trust:
   Connecting Representation, Collapse, and Trust Issues in PPO", arXiv:2405.00662 (NeurIPS 2024) — I
   could not extract the paper's exact formula from a snippet-level fetch (their metric is described in
   the abstract as tracking "representation rank" and "capacity loss / ability to fit random targets";
   the precise rank estimator is in the body, which I was not able to pull text from in this pass — flag
   as **not independently verified at formula level**, cite with that caveat). The qualitative test this
   metric is built for — a healthy representation should be able to fit new/random targets, a collapsed
   one loses that capacity — is directly reusable: fit a small linear/MLP head from `g'(o_t)` to a
   held-out random target and check the achievable train loss drops as training epochs increase; a
   flat/non-decreasing curve indicates capacity loss.
3. **Linear-probe recoverability of the only non-trivial dynamical signal** — supervised linear (or
   shallow-MLP) probe from `g'(o_t)` (or the full `phi_x`) to the **six time-varying `p_t` channels**
   this project's own THEO-3 finding identifies as the only non-constant physical signal in `p_t`
   (ocean-current velocity_w[:3], measured root_lin_vel_b[:3]) — analogous in spirit to standard linear
   probing in representation learning (the technique underlying VICReg's own downstream evaluation
   protocol and standard SSL evaluation practice) but targeted at *this project's* known-nontrivial
   physical quantities rather than a generic downstream task. A gate that fails when probe R² stays near
   the degenerate-baseline R² (predicting the training-set mean) is the direct, falsifiable analog of the
   z_sweep rule, and — per this project's own `feedback-derive-a-metrics-healthy-target` memory — the
   healthy target for that R² should be derived from a degenerate baseline's score, not assumed to be
   1.0.
4. **K-fit informativeness check (specific to THEO-4)** — before trusting any Koopman-consistency loss
   (student or teacher side), compute the *closed-form* optimal `K = arg min ‖Kz_t − z_{t+1}‖` on a
   batch of already-logged z-sequences and report `‖K − I‖` and the residual-vs-identity-baseline
   improvement. If the fitted `K` is statistically indistinguishable from `I` (or if `K=I` already
   achieves within-noise loss), the Koopman-consistency term is confirmed vacuous on current data
   *before* spending a training run on it — directly operationalizing THEO-4's structural objection into
   a 20-line, pre-registered falsification check, exactly the kind of check the sibling theory-lens
   report noted the doc never proposed.

None of items 1–4 require new infrastructure beyond a batch of logged `o_t`/`p_t`/`z` sequences the
project already produces; all four are cheap, precede any training-run commitment, and each is
constructed so that a genuinely inert `g'` (or a vacuous K-term) *fails* it — satisfying this project's
own `feedback-test-must-be-able-to-fail` standard, which the sibling epistemic-lens report found this
document's current metric set (gradient variance / KL health / eval static) does not meet for the φ_x
arm.

---

## References

1. Cozma, A., Harris, L., Qi, H. "KIPPO: Koopman-Inspired Proximal Policy Optimization." IJCAI 2025,
   proceedings entry #556 (pp. 4994–5002). arXiv:2505.14566. https://arxiv.org/abs/2505.14566 —
   **verification depth: snippet/relayed** for the §3.1 identity-concatenation-rejection quote (I relied
   on the sibling evidence-lens report's already-verified local PDF extraction; my own WebFetch of the
   arXiv PDF returned only binary/stream metadata, not readable text). Abstract-level independently
   confirmed via WebSearch synthesis.
2. Li, F., Abuduweili, Z., Yun, S., Chen, R., Zhao, W., Liu, C. "Continual Learning and Lifting of
   Koopman Dynamics for Linear Control of Legged Robots." arXiv:2411.14321 (also PMLR v283, L4DC 2025).
   https://arxiv.org/pdf/2411.14321 — **verification depth: relayed from sibling report's full-text
   read** (pp. 1–10, Sections 1–4.5); not independently re-fetched this pass.
3. Draeger, A. et al. 1995 — cited within KIPPO §3.1 for the fixed-point/topological-conjugacy claim.
   **Verification depth: could not locate the primary source** (two targeted WebSearch queries returned
   no matching paper); relaying the claim as reported inside KIPPO's text, not independently confirmed.
4. Lusch, B., Kutz, J.N., Brunton, S.L. "Deep learning for universal linear embeddings of nonlinear
   dynamics." Nature Communications 9, 4950 (2018). arXiv:1712.09707.
   https://ar5iv.labs.arxiv.org/html/1712.09707 — **verification depth: WebFetch summary of ar5iv HTML**
   (model-summarized, not a verbatim full-text audit); confirms no identity-concatenation, reconstruction
   + prediction + linearity joint loss, and an auxiliary network for continuous-spectrum eigenvalues.
5. "On the lifting and reconstruction of nonlinear systems with multiple invariant sets."
   arXiv:2304.11860. https://arxiv.org/pdf/2304.11860 — **verification depth: WebFetch summary of PDF**
   (model-summarized); establishes the topological-obstruction-to-exact-global-linearization framing for
   multi-equilibrium systems and that approximate/regularizer roles are less constrained than exact
   global linearization.
6. Otto, S.E., Rowley, C.W. "Koopman Operators for Estimation and Control of Dynamical Systems."
   Annual Review of Control, Robotics, and Autonomous Systems, 2021. **verification depth: abstract-level
   only** — could not retrieve section-level detail on multiple-equilibria treatment in this pass.
7. Takeishi, N., Kawahara, Y., Yairi, T. "Learning Koopman Invariant Subspaces for Dynamic Mode
   Decomposition." NeurIPS 2017. **verification depth: not independently fetched this pass** — referenced
   from prior general knowledge of the paper's small-latent-dim, spectral-subspace design objective;
   flagged as **unverified this session**, should be re-checked before being cited as load-bearing.
8. Bardes, A., Ponce, J., LeCun, Y. "VICReg: Variance-Invariance-Covariance Regularization for
   Self-Supervised Learning." ICLR 2022. arXiv:2105.04906. https://arxiv.org/abs/2105.04906 —
   **verification depth: WebSearch synthesis** across OpenReview/arXiv abstract and multiple secondary
   summaries; not a full-text read of the paper body.
9. Ota, K., Oiki, T., Jha, D., Mariyama, T., Nikovski, D. "Can Increasing Input Dimensionality Improve
   Deep Reinforcement Learning?" ICML 2020. arXiv:2003.01629. https://arxiv.org/abs/2003.01629 —
   **verification depth: WebSearch synthesis / secondary summaries** (AI-Scholar article, ResearchGate
   listing); did not extract the primary PDF's dimension-vs-performance table directly.
10. Moalla, S., Mahmoud, A., Tirinzoni, A., Lazaric, A. et al. "No Representation, No Trust: Connecting
    Representation, Collapse, and Trust Issues in PPO." NeurIPS 2024. arXiv:2405.00662.
    https://arxiv.org/abs/2405.00662 — **verification depth: abstract-level only** (WebFetch could not
    retrieve full body text); the exact feature-rank formula and PFO mechanism are not independently
    confirmed at formula level in this pass — this matches and does not improve on the sibling
    epistemic-lens report's own citation depth for this paper.
11. Erichson, N.B. et al. — Lyapunov-based stability constraints for Koopman autoencoders; Pan, S.,
    Duraisamy, K. — tridiagonal-K unit-circle stability constraint; Mamakoukas, G. et al. "Learning
    Stable Models for Prediction and Control." arXiv:2005.04291. **verification depth: WebSearch
    synthesis only** — names and mechanisms relayed from search-result summaries (a secondary review
    page), not from any primary-source full text; treat the specific attributions as **directional, not
    citation-grade**, and re-verify before quoting a specific theorem or method name from these authors.
12. Song, et al. 2021 — cited inside KIPPO §3.1 as the identity-concatenation precedent KIPPO explicitly
    departs from. **Verification depth: not located** — WebSearch could not identify the specific paper;
    relayed only as referenced inside the KIPPO quote from source 1.

## GitHub repos

- **BethanyL/DeepKoopman** — https://github.com/BethanyL/DeepKoopman — reference implementation of
  Lusch/Kutz/Brunton 2018 (TensorFlow, per repo description "neural networks to learn Koopman
  eigenfunctions"). License not verified in this pass. Reusable for a PyTorch/rsl-rl stack: not directly
  (different framework, different DL-era conventions) — but the loss decomposition (reconstruction +
  k-step prediction + linearity + auxiliary continuous-eigenvalue network) is a clean, small reference to
  port loss-term-by-loss-term rather than reuse as a library. A community PyTorch port exists as a fork
  (`yongqianxiao/DeepKoopman`, also surfaced in search) — not audited for correctness in this pass.
- **intelligent-control-lab/Incremental-Koopman** — https://github.com/intelligent-control-lab/Incremental-Koopman
  — code for [50] (Li et al., legged-robot incremental Koopman lifting), per the sibling report's
  citation line (not independently browsed this pass — flag as **unverified repo content**, only its
  existence and URL are confirmed via the earlier sub-report's citation). Reusable for a PyTorch/rsl-rl
  stack: the `z=[x,g'(x)]` anti-collapse architecture and the discounted k-step rollout + light-weighted
  reconstruction loss (α=0.1) are small, portable design choices (a few dozen lines) rather than
  something requiring the full repo as a dependency.
- **VICReg reference implementations** — `facebookresearch/vicreg` (official, not directly surfaced in
  this session's searches but the canonical repo for arXiv:2105.04906; **not independently verified to
  exist/be current in this pass** — flag as recalled, not searched) and
  `BalajiAI/VICReg` (JAX/Flax reimplementation, surfaced directly in search results this session, URL
  https://github.com/BalajiAI/VICReg). Reusable for a PyTorch/rsl-rl stack: the variance-hinge +
  covariance-off-diagonal loss terms are ~15–20 lines of PyTorch, trivially portable regardless of which
  reference is used; recommend re-implementing directly from the loss formula in the paper rather than
  depending on either repo, given the small size of the actual reusable logic.

## Implications for ALBC

1. **Do not adopt [50]'s identity-inclusion guard for the KIPPO-style `phi_x` arm as-is.** KIPPO's own
   paper rejects it by name, for a reason (multi-equilibrium plants) that applies directly to this UUV+arm
   system (hover attitudes, arm configurations, fault regimes are all distinguishable operating regimes).
   The doc's §14.2 "adopt for phi_x regardless" is the specific claim to strike. If the anti-collapse
   concern that motivated reaching for [50]'s guard is real (it is — the project's own history), the
   mechanism-matched fix from the literature is KIPPO's own choice: an **expansive** `phi_x` (2–4x state
   dim, consistent with both KIPPO's and OFENet's reported ranges) with a **light-weighted reconstruction
   loss** (α≈0.1, per [50]'s own ablation finding that light reconstruction beats heavy) — not raw-state
   concatenation.
2. **Add a `phi_x`-specific degeneracy gate before any training run that includes a Koopman-consistency
   term**, mirroring the existing z_sweep discipline: (a) per-dimension variance floor check on `g'`
   only, (b) an effective-rank / random-target-fit capacity check, (c) a linear probe from `g'` to the
   six known time-varying `p_t` channels (ocean current, measured lin_vel) with a degenerate-baseline
   R² floor, and (d) a pre-training closed-form check of whether `K=arg min‖Kz_t−z_{t+1}‖` is
   distinguishable from `K=I` on already-logged teacher z-sequences. Item (d) directly falsifies or
   confirms THEO-4's "K≈I is the optimum" concern *before* any GPU time is spent, and is the single
   cheapest, highest-value addition this research surfaces.
3. **The Draeger/multi-fixed-point objection is a reason to keep, not abandon, an expansive-AE +
   reconstruction design for `phi_x`** — it is evidence *for* the doc's existing §8.4.1 architecture
   (KIPPO-style) and evidence *against* the specific paragraph (§14.2) that layers [50]'s guard on top of
   it. The two recommendations were never actually compatible; resolving THEO-6/8/9 means picking one
   guard, and the literature's own preference (KIPPO explicitly, for exactly this plant class) points to
   the expansive-AE side.
4. **The "Koopman" framing itself is the wrong axis to test in isolation** (this echoes the epistemic-lens
   report's THEO-2, independently reached here from the Q3/latent-size angle): OFENet gets the same
   claimed benefit (expansive learned features via next-state-prediction) without any linearity
   constraint, and reports the same saturating-with-m trend KIPPO reports. Any screening arm should
   include an unconstrained-latent-predictor control (drop the linearity term, keep everything else) to
   attribute a positive result correctly — otherwise a positive result from the degeneracy-guard-fixed
   `phi_x+K` arm cannot distinguish "the linearity constraint helped" from "an expansive auxiliary-prediction
   feature space helped, and linearity was irrelevant or actively neutral," which is exactly the
   uncontrolled-comparison risk this project's own single-variable screening discipline exists to prevent.
