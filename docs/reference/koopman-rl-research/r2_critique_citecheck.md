# Round 2 — CITECHECK lens: spot-verification of Round-1's load-bearing new citations

Method: every priority citation was fetched as primary source (`curl` arXiv PDF → `pdftotext -layout`),
not via search snippet. Where the paper's own code settles a claim the paper leaves implicit, the
official repository was read (CaDM). Classification per item: **OK** / **DRIFT** (source says something
weaker, narrower, or differently-shaped) / **WRONG** / **UNREACHABLE**.

Sources cached at `/root/.claude/jobs/add36792/tmp/r2c/*.txt` (extracted text) for re-checking.

**Headline**: 13 of 14 priority citations resolve to real papers and no arXiv ID is hallucinated —
including `2605.17966`, which Round 1 itself flagged as possibly-fabricated. But **five load-bearing
characterizations do not survive contact with the primary text**, and two of them (CaDM's "4–7x",
the IB `HIB-w/o-ib` ablation) are legs of the same argument — the THEO-9 invariance-pressure claim
that §18.8 row 2 turns into a *pre-registered pre-launch prediction*. One more (OFENet "PPO on one
task") is flatly contradicted by the source's main results table.

---

## C-1 (CRITICAL) — THEO-9's evidence triad is 1-of-3 intact after primary-source checking

§17.1 defect 4 / §18.3 rests THEO-9 ("a shared single K under DR is an invariance pressure, the most
plausible mechanism by which a KIPPO arm HURTS here") on three convergent citations. Verified:

| Leg | §18.3 claim | Verdict |
|---|---|---|
| CaDM 2005.06800 | "non-conditioned dynamics model loses **4–7x** to context-conditioned under randomized dynamics" | **DRIFT** — cross-family comparison; matched effect is 1.1–3.5x (C-2) |
| IB s2r 2305.18464 | "compression **without an env-info-preserving term** almost fails" | **DRIFT/WRONG** — the ablated arm has no compression term either (C-4) |
| IIDA 2203.05549 | "a conditioned dynamics loss spontaneously clusters env identity" | **OK**, with a scope note (C-9) |

Consequence: §18.9 rank-2 requires "(e) pre-registered invariance-pressure prediction" *recorded before
launch*. Pre-registering a directional prediction is fine; presenting it as "well-supported by three
convergent, independently-sourced pieces of evidence" (the researcher's own verdict wording, carried
into §18.3 as "plausible + well-supported") is not, once two of the three are restated correctly. The
mechanism remains a legitimate hypothesis on its own logic — the *citational* support is one paper,
in a supervised-prediction setting, pointing at the contrapositive.

Recommended edit: keep the prediction, downgrade "well-supported" → "mechanistically plausible; one
adjacent supporting result (IIDA, by contrast); no direct test in the literature."

---

## C-2 (MAJOR) — CaDM "4–7x" is a cross-family comparison, not a shared-vs-context-conditioned gap. **DRIFT**

Source: Lee, Seo, Lee, Lee, Shin, *Context-aware Dynamics Model for Generalization in Model-Based RL*,
ICML 2020, arXiv:2005.06800. Read: full PDF text.

The R1 researcher's supporting numbers are **Vanilla DM vs PE-TS + CaDM**:
HalfCheetah moderate 1026.7±164.7 → 7087.2±1495.6 (6.90x); Ant moderate 520.0±97.6 → 2121.0±60.4 (4.08x).
Both quoted figures are verbatim-correct entries of Table 1 — but the two arms differ in **two** ways:
the base dynamics model changes (single Gaussian MLP → 5-model probabilistic ensemble + 20-particle
trajectory sampling) *and* the context conditioning is added.

The paper's own matched ablations (Table 1, Test-moderate column) isolate the context effect:

| Task (moderate) | Vanilla → Vanilla+CaDM | PE-TS → PE-TS+CaDM |
|---|---|---|
| CartPole | 124.7 → 154.3 (1.24x) | 171.3 → 187.3 (1.09x) |
| HalfCheetah | 1026.7 → 1556.1 (1.52x) | 2019.6 → 7087.2 (**3.51x**) |
| Ant | 520.0 → 1315.7 (2.53x) | 1075.1 → 2121.0 (1.97x) |
| CrippledHalfCheetah | 870.0 → 1375.3 (1.58x) | 1916.5 → 2618.7 (1.37x) |
| SlimHumanoid | 1004.4 → 1228.9 (1.22x) | 758.6 → 903.7 (1.19x) |
| Pendulum | −928.4 → −593.7 (n/a, negative returns) | −985.7 → −705.5 (n/a) |

The paper's own headline sentence uses the matched pair and its best case: *"when combined with PE-TS,
CaDM improves the average return from 2019.6 to 7087.2 for the HalfCheetah environment in the moderate
regime."* Honest restatement: **~1.1–3.5x, median ≈1.5x, one 3.5x outlier**, not 4–7x.

Two further scope facts §18.3 does not carry: the metric is **MPC episode return on held-out dynamics**
(not dynamics-prediction error, not representation quality), and the "vanilla" model is not an aux
representation shaper but the planner's forward model.

Minor: the abstract quote relayed as *"learning a global model that generalizes across different dynamics
remains a challenge"* is a paraphrase inside quotation marks; actual text is *"learning a global model
that can generalize across different dynamics is a challenging task."* Harmless, but it is the
paraphrase-in-quotes pattern that produced the Bruder incident.

---

## C-3 (MAJOR) — "CaDM's context encoder feeds the policy without stop-grad" is **WRONG** (reversed)

`r1_research_invariance_dr.md` (Q2, lines 88–95) states: *"CaDM's own default does not isolate the context
encoder from policy gradients, so citing CaDM as precedent for a stop-grad-gated K(z) is a mismatch — the
stop-grad is an ALBC-specific addition beyond CaDM."*

Paper evidence: Algorithm 1, line 20 updates the encoder parameters **φ ← φ − α∇φ (1/B)ΣL_i^pred** — the
prediction loss only. The RL objective never appears in any φ update.

Code evidence (official repo `younggyoseo/CaDM`, `cadm/model_free/ppo_cadm.py`), decisive:
- L335–337: `dynamics_model.load(load_path)` — the PPO arm loads a **pretrained** dynamics model.
- L155–162 `extract_context()` → `self.dynamics_model.get_context_pred(...)` returns a **NumPy array**;
  it is appended to `mb_contexts` and fed to the policy through the placeholder `train_model.context_X`
  (L62).
- L49–56: `params = tf.trainable_variables()` under `variable_scope('model')`; `grads = tf.gradients(loss,
  params)`; Adam applies only to those. The encoder is not in the graph at all.

So CaDM's model-free arm is not merely stop-grad-gated — the encoder is **frozen and outside the
computation graph**, a stronger isolation than `detach()`. Appendix A.5's description of the PPO+EP
baseline ("trained ... for the same number of samples used for training Vanilla + CaDM, and then train a
context-conditional policy") corroborates the two-stage design.

This reverses the direction of the evidence: CaDM is a precedent **for** gating.

---

## C-4 (MAJOR) — PrivilegedDreamer "UN-gated (no stop-grad)" is unsupported and most likely **WRONG**; the "literature-disputed" framing collapses

Source: Byrd, Crandell, Das, Inman, Wright, Ha, *PrivilegedDreamer*, arXiv:2502.11377. Read: full PDF text.

§18.3: *"PrivilegedDreamer ... is the closest full match ... but non-Koopman and UN-gated (no stop-grad),
while WMR deliberately CUTS the same gradient — the stop-grad question is literature-disputed → A/B it,
don't assume."* The researcher's own depth flag for this paper was **abstract-only**.

What the paper actually says:
- Both the LSTM estimation module η and the HIP prediction head are world-model components: *"It is still
  parameterized by φ because we treat it as part of the world model."*
- The total world-model loss, Eq. (1) `L(φ) = L_Dreamer + E[−ln η_φ(ω̃|x,a) − ln p_φ(ω̂|h,z)]`, contains
  **no return term**.
- Behavior learning: *"When training the policy, we start with a seed state sampled from the replay buffer
  and then proceed in imagination only, as in the original DreamerV2 ... the actor and critic networks are
  trained to maximize the estimated discounted sum of rewards in imagination **using a fixed world
  model**."*

In the DreamerV2 paradigm the actor gradient propagates *through* the frozen world model but never updates
φ. Functionally that is exactly the gating property at issue: the parameter estimator's representation is
not shaped by the RL objective. Nothing in the paper claims otherwise, and no ablation of an un-gated
variant exists.

Second half — "outperforms RMA-style": **OK with DRIFT**. Table II mean 668.56±70.87 (PrivilegedDreamer)
vs 368.86±305.00 (RMA). But the paper itself discounts the comparison: *"We suspect that RMA and PPO do
especially poorly on the Walker task because the 2 million timestep training limit is insufficient for
on-policy algorithms. Similarly, we suspect that the small training size affects the ability of RMA to
effectively adapt, and that it would be more competitive with our method with a larger training dataset."*
RMA's per-task std reaches ±416.57. The internally-controlled comparison is against
`DreamerV2 + Decoder + ConditionedNet` (473.22), which *does* isolate the HIP-conditioning design.

**Net effect on the doc**: WMR's cutoff is verbatim-real (C-5), CaDM is frozen (C-3), PrivilegedDreamer
is world-model-loss-only. All three checked data points now point the same way. §18.3's "literature-
disputed → A/B it, don't assume" should become: *"no published work in this family feeds an RL-objective
gradient into the context estimator; gating is the uniform convention. The `z.detach()` requirement
follows from the settled rule anyway; an un-gated A/B arm has no published precedent and should not be
budgeted as a coin-flip."*

---

## C-5 (OK) — WMR "gradient ... intentionally cut off" is verbatim

Source: Sun, Chen, Su, Cao, Liu, Xie, *Learning Humanoid Locomotion with World Model Reconstruction*,
arXiv:2502.16230. Read: full PDF text. (Researcher depth was abstract-only; now upgraded.)

Abstract, verbatim: *"the policy and the estimator are trained jointly; however, the gradient between them
is intentionally cut off. This ensures that the estimator focuses solely on world reconstruction,
independent of the locomotion policy's updates."* Contribution 2 lists a "gradient cut off mechanism."

Stronger than the doc reports — there is a dedicated **ablation**: Table II `WMR without Gradient Cutoff`
E_vel 0.693 / E_ang 0.421 / E_recon 0.459 vs WMR 0.156 / 0.252 / 0.098; text: *"The introduction of
gradient cutoff improved reconstruction accuracy by approximately 40%. Without Gradient Cutoff, the WMR
fails to learn basic walking behaviors such as foot lifting."* This is the strongest single piece of
evidence in the whole stop-grad question and the doc under-states it.

---

## C-6 (MAJOR) — IB sim-to-real: the quote is real, the characterization inverts what was ablated. **DRIFT**

Source: He, Wu, Bai, Lai, Wang, Pan, Hu, Zhang, *Bridging the Sim-to-Real Gap from the Information
Bottleneck Perspective*, arXiv:2305.18464v2. Read: full PDF text.

Verbatim confirmed (§6.3): *"we observe that HIB-w/o-ib almost fails."*
Objective confirmed (Eq. 10): `min −I(Z_t; S^p_t) + α I(H_t; Z_t)`.

But the ablation is defined two lines above the quote: *"(i) **HIB-w/o-ib only uses RL loss to update
history encoder f_ψ**, which is similar to a standard recurrent neural network policy."* It strips the
**entire** HIB objective — the privileged-preserving term `I(Z;S^p)` *and* the compression term `I(H;Z)`.
It is the plain-RNN baseline.

§18.3 relays it as *"compression without an env-info-preserving term almost fails"* and the researcher's
Q1 text elaborates *"an unconstrained compression/invariance pressure (no explicit env-preserving
counter-term) is empirically damaging."* No such variant exists in the paper. The paper's stated
conclusion is the opposite lever: *"both HIB loss and RL loss are important ... especially the HIB loss.
The HIB loss helps the agent learn a historical representation that contains privileged knowledge."*

What the paper supports: adding an explicit privileged-alignment term helps generalization.
What it does not support: that compression-without-preservation is the damaging ingredient — which is the
precise shape THEO-9 needs (a single shared K acting as an uncounterweighted compression pressure).

---

## C-7 (MAJOR) — OFENet "PPO on ONE task only (+39.2% HalfCheetah)" is **WRONG**

Source: Ota, Oiki, Jha, Mariyama, Nikovski, *Can Increasing Input Dimensionality Improve Deep RL?*,
ICML 2020, arXiv:2003.01629. Read: full PDF text.

§18.1: *"PPO evidence = ONE task (HalfCheetah +39.2%) vs 5-task SAC/TD3 coverage."*

Table 1 reports PPO on **all five** MuJoCo tasks, 5 seeds each, `OFE (ours)` vs `original`:

| Task | PPO (OFE) | PPO (orig) | Δ |
|---|---|---|---|
| Hopper-v2 | 2525.6 | 1753.5 | **+44.0%** |
| Walker2d-v2 | 3072.1 | 3016.7 | +1.8% |
| HalfCheetah-v2 | 3981.8 | 2860.4 | **+39.2%** |
| Ant-v2 | 1782.3 | 1678.9 | +6.2% |
| Humanoid-v2 | 670.3 | 652.4 | +2.7% |

The +39.2% arithmetic is right; the coverage claim is not. On-policy coverage **equals** off-policy
coverage. Text: *"Since TD3 (OFE) and PPO (OFE) also outperform original algorithm, it can be concluded
that OFENet is an effective method for improving deep RL algorithms on various benchmark tasks."*

The honest weakening is different in kind: PPO(OFE) wins on 5/5 but **three of the five margins are within
plausible seed noise** (1.8% / 2.7% / 6.2%), so the on-policy effect is real but *concentrated in two
tasks*. §18.1's conclusion ("on-policy evidence for the whole aux-dynamics class is SPARSE, not negative")
survives — but the specific supporting sentence must be replaced, and §18.9 rank-2 can legitimately cite a
5-task/5-seed on-policy precedent rather than a single data point. Note this cuts *in favour* of the arm
the doc downgraded: symmetric skepticism requires recording it.

(Related hygiene: `r1_research_degeneracy_guard.md` ref 9 lists OFENet at "WebSearch synthesis / secondary
summaries" depth while `r1_research_selfpred_class.md` ref 1 lists full-text ar5iv. The erroneous
one-task claim originates in the full-text report, which is the more troubling direction.)

---

## C-8 (MAJOR) — Moalla et al. 2405.00662: mechanism verified exactly, but over-transferred to TRPO. **DRIFT**

Source: Moalla, Miele, Pyatko, Pascanu, Gulcehre, *No Representation, No Trust: Connecting Representation,
Collapse, and Trust Issues in PPO*, NeurIPS 2024, arXiv:2405.00662v3. Read: full PDF text.

Verified **OK**, verbatim-level:
- PFO acts on *pre-activations*: *"With φ_θ(s) as the pre-activation of the penultimate layer of the actor
  π_θ..."*; two variants (penultimate-only, and all layers up to penultimate).
- Coefficient: *"we do not tune the coefficient of PFO; we pick the closest power of 10 that sets the
  magnitude of this loss to a similar magnitude of [the PPO loss]."*
- "TRPO/NPG not studied": confirmed — **zero** occurrences of `TRPO`, `NPG`, or `natural policy gradient`
  anywhere in the paper.

**DRIFT** on the load-bearing use. §17.1 defect 1 leg (iii) reads: *"literature: Moalla et al. ... shows
representation collapse BREAKS trust-region guarantees — the opposite of the doc's claim."* The paper's
demonstrated breakdown is specific to **PPO-Clip's per-sample heuristic**:

> *"PPO constructs a trust region around [π_θ(·|s)] ... the update computed on state s can not move the
> policy π_θ(·|s) outside of the trust region. However, [under feature aliasing] π_θ(·|s) will still
> change and move outside of the trust region due to the updates on other states s′. Leading to the trust
> region constraint being ineffective."*

The paper calls this object a "heuristic trust region" throughout. ConstraintTRPO enforces a **hard
batch-mean KL constraint with a line search**, which does bound the aggregate policy change irrespective
of per-state aliasing — a different object, and one the paper neither studies nor claims to break.

Defect 1's legs (i) (an out-of-band φ_x step changes π(·|o) with zero KL budget consumed; stored
`old_mu`/`old_logp` go stale, biasing the surrogate *before* the trust region applies) and (ii) (the
`constraint_trpo.py` param-prefix grouping / `storage.clear()` ordering facts) are independent and stand.
Only leg (iii) should be scoped: *"Moalla et al. establish that a PPO-Clip heuristic trust region breaks
under representation collapse; no analogous result exists for hard-KL TRPO, which remains the genuine gap
identified in §18.2."* Calling defect 1 "triple-confirmed" via this leg overstates.

---

## C-9 (OK, with scope note) — IIDA env-identity clustering

Source: Evans, Thankaraj, Pinto, *Context is Everything: Implicit Identification for Dynamics Adaptation*,
arXiv:2203.05549. Read: full PDF text.

Fig. 6 caption verbatim: *"In addition to similar latents for the same objects, we can see distinct
clusters corresponding to objects with distinct dynamics."* Body: *"We can see distinct clusters
corresponding to different sliding dynamics. Notably, the objects slid on cloth are all clustered close to
one another."* Training is end-to-end on the dynamics-prediction loss with no env-ID loss. Claim **OK**.

Scope the doc should carry: this is a **supervised offline dynamics predictor** on a real object-sliding
dataset where the latent factor is *object identity*, not an RL policy under simulated parameter DR; the
clusters shown are the transformer context-summarizer's latents (the RNN and averaging summarizers get
their own, weaker plots in App. VIII-C); and the self-consistency metric is a nearest-neighbour object-ID
retrieval rate, not a control result.

---

## C-10 (OK on text, DRIFT on the attached mechanism) — Diminishing Return of Value Expansion

Source: Palenicek, Lutter, Carvalho, Dennert, Ahmad, Peters, arXiv:2412.20537 (submitted TPAMI).
Read: full PDF text.

Abstract, verbatim: *"increased model accuracy only marginally improves sample efficiency compared to
learned models with identical horizons"*; *"even perfect models do not provide unrivaled sample
efficiency. Therefore, the bottleneck exists elsewhere."* Body: *"overcoming the small errors of current
models towards oracle dynamics will, at best, result in small improvements ... we argue that putting these
slight performance gains into perspective, they are underwhelming."* Model-free RETRACE matches the
model-based variants. So "oracle models barely help" is **OK**.

Is the transfer fair? Partly. §18.7 writes: *"model-derived value information gives shrinking gains once
**the critic already knows the world** (even an ORACLE model barely helps)."* The italicized clause is the
doc's own causal story — the paper explicitly declines to name the bottleneck ("exists elsewhere") and its
lever is *dynamics-model accuracy for multi-step TD-target construction* (MVE/CE/AE with horizon H), not
*a one-step model prediction appended to a critic's input*. Those are the same family (model-derived
information entering value learning) but different mechanisms; a diminishing return in one does not
formally imply a diminishing return in the other, and nothing in the paper concerns an already-privileged
critic.

Recommended: keep the citation as a directional prior ("the model-information-into-value-learning family
has shown small marginal gains even at oracle accuracy"), delete the borrowed explanation. The §18.7
verdict (cheap probe, null-expected prior) is unaffected — it is well-served by the *structural* argument
(§18.7's code-verified zero contact with trust region / deploy / student), which is the stronger leg
anyway.

---

## C-11 (DRIFT) — FCSRL: "value-consistency aux on a COST critic underperformed"

Source: Cen, Yao, Liu, Zhao, *Feasibility Consistent Representation Learning for Safe RL*, ICML 2024,
arXiv:2405.11718v2. Read: full PDF text.

Confirmed: the VC baseline is exactly a cost-value-consistency aux — *"the main idea of value consistent
model is to enforce the learned embedding to predict cost value function with a prediction head ṽ: Z → R,
i.e. ṽ(z_t) = V_c(s_t)."* Sparse-signal attribution is the paper's own: abstract *"the estimation of
safety constraints, which is typically more difficult than estimating a reward metric due to the sparse
nature of the constraint signals"*; App. B.3 *"the value function information is harder to extract via
representation learning and the effectiveness of value consistent model is not very remarkable. In
contrast, the feasibility score is easier to learned."*

**DRIFT on "underperformed."** VC is among the paper's *stronger* baselines: *"the SALE, VC, and FCSRL have
relatively higher performances than the remaining baseline."* FCSRL's margin over VC is *"relatively
small"* on tasks near the reward ceiling and larger *"on tasks where constraint is harder to satisfy."*
Read as "worse than no aux," the claim is unsupported; read as "a weaker representation target than
feasibility," it is exactly right. Since §18.7 uses it to argue a null-expected prior for a cost-side aux,
the correct statement is *"cost-value-consistency is a workable but comparatively weak representation
target; a better-shaped target beat it"* — which is a weaker null argument than the doc implies.

---

## C-12 (OK — upgraded from snippet, plus a remedy the doc omits) — arXiv 2605.17966

Real paper, ID resolves, R1's hallucination flag can be cleared: **Yue Wu, "Control-Channel Informativity
for Koopman EDMDc under Behavior-Policy Data," arXiv:2605.17966v1 [math.OC], 18 May 2026.** Read: full PDF
text (613 lines). Single author, no venue — weight accordingly.

§18.6's claim is **confirmed at abstract and theorem level**: *"Such data can predict the observed
behavior accurately while failing to identify how new input commands change the lifted state"*; *"If the
certificate vanishes, distinct lifted models agree on every collected transition but disagree under
counterfactual inputs."* The doc's extension ("in BOTH fits — replay converts a confound into a shared
identifiability weakness") follows validly: a replayed deterministic input sequence carries the same rank
deficiency into the sim fit and the real fit.

**But the doc omits the paper's own remedy, and it is operationally decisive for us.** The vanishing case
is *deterministic* feedback (*"If the data are collected under deterministic feedback u_k = κx_k, then
only the closed-loop coefficient ..."*). Prop. 2: with dither variance one, Fisher information for the
control coefficient is `N ε²/σ²` — *"intervention information grows quadratically with dither amplitude."*
Experiments: Duffing, dither 0, budget 80 → `C_int = 0`, counterfactual response error 0.610; dither 0.05
→ `C_int = 0.292`, error ~8.6e−? (orders lower). Van der Pol likewise.

Implication for a future ALBC gap-meter: **an ALBC rollout under the stochastic (sampled-action) policy is
already dithered** and generically identifiable; a replay driven by the *deterministic mean action* — which
is how `eval.py`/`play` normally run — is the degenerate case the paper describes. If the gap meter is
ever un-gated, the protocol must specify sampled-action replay (or injected dither) and report `C_int`.
That is a concrete, cheap addition to §18.6's protocol sketch that Round 1 did not extract.

---

## C-13 (OK, narrow) — S-G-W 2509.24920 CT eigenvalue renormalization

Source: Germain, Flamary, Kostic, Lounici, *A Spectral-Grassmann Wasserstein Metric for Operator
Representations of Dynamical Systems*, arXiv:2509.24920v1 [stat.ML], 29 Sep 2025. Read: full PDF text.

The mechanism is genuinely in the paper: *"while typically in data-driven methods datasets are sampled at
some frequency ω_ref = 1/Δt_k to estimate eigenvalues e^{λ_i Δt_k} of transfer operators, we build a
metric using the difference in the **generator** eigenvalues ... So, by re-normalizing eigenvalues, we can
compare systems observed at different time-scales in the universal time units."* A sampling-rate scenario
exists (Sec. 4.1(d)): *"When changing the sampling frequency in scenario (d), only GOT and our metric SGOT
are robust and remain low and almost constant."*

**Narrow the "validated across sample rates" wording** in §18.6 to what was actually run:
- one synthetic system — two damped harmonic oscillators at 0.5 / 1.0 Hz plus additive Gaussian noise;
- sampling swept **100–300 Hz around a 200 Hz reference** (a 1.5x span), on a *linear* system;
- GOT is equally robust in that scenario, so the property is not unique to SGOT;
- App. F caveats: *"In (d), the metric scale is not normalized, and the metric values remain relatively
  small"* and SGOT *"becomes slightly more sensitive to the sampling frequency as η decreases."*

Also worth stating plainly: `λ = log(μ)/Δt` is a textbook generator identity, not this paper's
contribution (the contribution is the OT metric). The doc does not need a citation to license the
renormalization; it needs one only for "a spectral distance that is empirically rate-robust exists," and
at the demonstrated scope that is a synthetic-linear-benchmark result, not a robot sim-to-real result.
Our operative gap is 25 Hz ZOH real vs a much faster sim — far outside a 1.5x span, and nonlinear.

Internal inconsistency: `r1_research_corrections.md` §7 records this paper at **abstract/snippet** depth;
`r1_research_gapmeter.md` ref 6 records **full-text-read**. The gapmeter reading is the accurate one; the
corrections report's §7 conclusion ("real-world = generic dynamical-systems ML benchmarks, no robots") is
nevertheless correct.

---

## C-14 (OK — clears an abstract-depth flag) — SSSD is in arXiv 1909.01419

Source: Haseli & Cortés, *Learning Koopman Eigenfunctions and Invariant Subspaces from Data: Symmetric
Subspace Decomposition*. Read: full PDF text.

Abstract: *"the Streaming Symmetric Subspace Decomposition (SSSD) algorithm ... employs **fixed memory**
and incorporates new data as is received."* Algorithm 2 is SSSD; Theorem 6.3 proves SSD ≡ SSSD; the text
notes SSSD is *"not only useful for streaming data sets but also for the case of non-streaming large"*
datasets that would otherwise exhaust memory. §18.5 and §18.9 item 4 are **correct**, and the
researcher's own `abstract/snippet` depth caveat on this item can be cleared.

---

## C-15 (OK) — Voelcker 2406.17718 scope; TD-MPC2 2310.16828 characterization

**Voelcker et al. (RLC 2024), arXiv:2406.17718** — read full PDF text. §18.1's scoping is verbatim-accurate:
*"we have to resort to studying simplified models ... and only consider the fixed policy case in our
analysis"*; *"One of the most important gaps between the work presented in this paper and the behavior of
online algorithms is the restrictive assumption of the fixed policy evaluation case"*; *"We also conduct
all of our theoretical work in the on-policy policy evaluation regime."* Prop. 7's condition is explicit
(`∀i<k: μ_i > λ_2` and `r_N = 0`) and the paper itself calls it *"restrictive as we consider a worst case
distraction for clarity."* **OK**, no correction needed.

**TD-MPC2 (ICLR 2024), arXiv:2310.16828** — read full PDF text. "104 continuous control tasks spanning 4
task domains" confirmed repeatedly; latent dynamics is `z′ = d(z,a,e)` (MLP) trained by joint-embedding
prediction *"without decoding observations"* — no linearity constraint. §18.1's use as an existence proof
that unconstrained latent-consistency scales is **OK**. Add one scope word the doc lacks: the model is
*used for planning* (MPPI trajectory optimization), so it is a control-centric world model, not purely an
auxiliary representation shaper — a stronger role than the ALBC aux use, which makes it a weaker analogy
for "the linearity constraint is unnecessary *as a regularizer*" than for "nonlinear latent consistency
works."

---

## C-16 (MINOR) — citation hygiene defects inside the R1 research reports

1. **Fabricated author.** `r1_research_gapmeter.md` ref 1 attributes arXiv:2303.15318 ("Closed-Loop Koopman
   Operator Approximation") to *"T. M. Dawson (and coauthors — exact author list not confirmed beyond first
   author from abstract page)."* The paper is by **Steven Dahdah and James Richard Forbes** (McGill). No
   Dawson exists on it. The main doc does not carry the name, so no doc-level damage — but this is the same
   failure class as the Bruder contamination, and it means that reference's *content* (the closed-loop
   identification-bias framing feeding §18.6) is snippet-relayed, not read.
2. **Wrong author list** for arXiv:2405.00662 in `r1_research_degeneracy_guard.md` ref 10 ("Moalla,
   Mahmoud, Tirinzoni, Lazaric") vs the correct Moalla, Miele, Pyatko, Pascanu, Gulcehre. Same report
   self-flags abstract-only depth; `r1_research_trustregion_drift.md` has it right and full-text.
3. **Relay-of-a-relay.** `r1_research_gapmeter.md` ref 7 (Krolicki et al., IFAC 2022) is *"abstract-only,
   sourced secondhand from the sibling research artifact `table1_legged_domainshift.md` produced in this
   same review round"* — a Round-1 artifact citing another Round-1 artifact, not a source.

---

## C-17 (MINOR) — inventory: snippet/abstract-depth citations that §18 nonetheless treats as established

Compiled from the researchers' own depth tables. None re-fetched here (out of budget); listed so §18 can
mark them, per the brief.

| Citation | Depth per its own report | Where §18 leans on it |
|---|---|---|
| PPG, arXiv:2009.04416 | snippet / secondary summaries (3 write-ups) | §18.2 mitigation option (1) "PPG-pattern" freeze-phase cadence |
| SPR, arXiv:2007.05929 | abstract-only; "flagged as a gap" | §18.2 option (2) "SPR-pattern" EMA/target encoder |
| Closed-loop Koopman, 2303.15318 | abstract-only **+ wrong author** | §18.6 "closed-loop identification bias is real and studied" |
| Mamakoukas 2005.04291 / Erichson / Pan–Duraisamy | "WebSearch synthesis only ... directional, not citation-grade" | §18.4 stability-constraint background |
| Krolicki IFAC 2022 | abstract-only, secondhand from a sibling R1 artifact | §18.6 / §14 legged Koopman background |
| Sim-to-real survey 2502.13187 | search-snippet only | §18.6's "DR-coverage check is the cheaper instrument" framing |
| T-MCL 2010.13303, ProtoCAD 2211.12774 ("13–27%"), 2605.04793 | abstract/snippet | §18.3 CaDM-family corroboration |
| arXiv:2509.26000 | abstract only | §18.7 critic-side background |
| RMA (RSS 2021) | "not verified"; prior knowledge | §18.3 / §18.7 comparisons |
| 2511.03482, 2501.07652 | title/abstract-snippet | correctly recorded as unverified leads (no action) |
| Song et al. 2021 (inside KIPPO §3.1) | "not located" | §18.4 identity-concat precedent chain |

Highest-value re-fetches if Round 3 runs: **2009.04416 and 2007.05929** — they are the only sources behind
§18.2's two most-recommended mitigation options, and §18.8 row 1 makes the update protocol a *precondition*
for the rank-2 arm. Verifying whether PPG's phase separation and SPR's target encoder actually transfer to
a hard-KL optimizer is now the single largest remaining citation risk in the doc.

---

## Summary table

| # | Citation | §18 use | Verdict |
|---|---|---|---|
| C-2 | CaDM 2005.06800 "4–7x" | §18.3 THEO-9 leg 1 | **DRIFT** — matched effect 1.1–3.5x; quoted pair is cross-family |
| C-3 | CaDM encoder / policy gradients | §18.3 stop-grad framing | **WRONG** (reversed) — encoder pretrained + frozen, outside the graph |
| C-4 | PrivilegedDreamer 2502.11377 "un-gated" | §18.3 stop-grad "disputed" | **WRONG/unsupported**; "beats RMA" OK but paper self-discounts |
| C-5 | WMR 2502.16230 "cut off" | §18.3 | **OK**, verbatim; doc under-states the ablation |
| C-6 | IB s2r 2305.18464 `HIB-w/o-ib` | §18.3 THEO-9 leg 2 | **DRIFT/WRONG** — ablation removes the whole objective, not just preservation |
| C-7 | OFENet 2003.01629 "PPO one task" | §18.1 on-policy sparsity | **WRONG** — 5 tasks, 5/5 wins, 2 large + 3 marginal |
| C-8 | Moalla 2405.00662 | §17.1 defect 1 leg (iii) | mechanism **OK**; transfer to hard-KL TRPO **DRIFT** |
| C-9 | IIDA 2203.05549 | §18.3 THEO-9 leg 3 | **OK** + scope (supervised, real object-sliding, per-object latents) |
| C-10 | 2412.20537 | §18.7 null prior | text **OK**; "critic already knows the world" is the doc's own, unattributable |
| C-11 | FCSRL 2405.11718 | §18.7 | **DRIFT** — VC is a *strong* baseline; "weaker target," not "underperformed" |
| C-12 | 2605.17966 | §18.6 | **OK**, upgraded to full-text; dither remedy + stochastic-replay requirement missing from doc |
| C-13 | S-G-W 2509.24920 | §18.6 rate fix | **OK**, narrow — one synthetic linear system, 1.5x rate span |
| C-14 | Haseli & Cortés 1909.01419 | §18.5 / §18.9-4 | **OK** — SSSD is in this paper, fixed memory, Thm 6.3 |
| C-15 | Voelcker 2406.17718; TD-MPC2 2310.16828 | §18.1 | both **OK**; add TD-MPC2's planning role as a scope note |

All arXiv IDs checked resolve to the claimed papers (2105.04906 VICReg, 2401.08898 Ni et al.,
2510.09042 MAKO, 2309.10278 PVKO, 2607.11624 SKooP verified by title lookup). Nothing **UNREACHABLE**.

---
NOTE (durable copy): fetched source caches were job-scratch and are not shipped; re-fetch via the arXiv ids listed in the main doc §8.
