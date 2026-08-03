# Research Report: Representation Drift Under Trust-Region Policy Optimization

**Key**: trustregion_drift
**Assigned critique cluster**: THEO-7 (theory), THEO-1 (systemfit), THEO-3 (epistemic) — the triple-confirmed
finding that a drifting learned representation under a trust-region optimizer is not bounded by the KL
constraint, and the design doc's reassurance on this point is contradicted by literature.

---

## Q1. Moalla et al., "No Representation, No Trust" (NeurIPS 2024, arXiv:2405.00662) — deep read

### 1.1 The exact failure mechanism

The paper's central empirical/theoretical claim is that PPO's trust region is a **per-state, ratio-space**
heuristic (`π_θ(a|s)/π_old(a|s) ∈ [1-ε, 1+ε]`) that implicitly assumes gradient updates at different states
are approximately **decoupled**. That assumption is only true when the shared feature extractor produces a
**high-rank, well-conditioned representation**. As training proceeds under non-stationarity (changing
policy → changing state/reward distribution), the network's penultimate-layer pre-activation norms grow
unboundedly while the **feature rank collapses** — i.e., representations φ(s) for different states become
increasingly **colinear** (one or few dominant directions).

The mechanistic link to trust-region breakdown: when φ(s) and φ(s′) are nearly colinear, a gradient step
computed to keep the ratio at state `s` inside `[1-ε, 1+ε]` **necessarily moves the ratio at state `s′`
in a correlated way**, because the gradients through the shared trunk are themselves colinear (proportional
to φ). PPO's clip only checks/limits the ratio at the *sampled* state in the current minibatch — it has no
mechanism to prevent an update, legal by the per-state clip, from throwing the ratio at *other* states far
outside the trust region. The paper demonstrates this in closed form in a toy 1-D-representation setting
(`φ(y) = α·φ(x)`), and empirically shows (their Fig. 3) that "extremely low [clipped] ratios are observed
around the representation collapse of a PPO-Clip agent, implying that the heuristic trust region breaks down
when representation power is lacking." They also invoke prior theory (Wang et al. 2020, Thm. 2) that clipped
samples' ratios can still exceed the nominal bound when unclipped-sample gradients align with clipped-sample
gradients — exactly the collinearity condition produced by rank collapse.

**Causal chain**: non-stationarity → pre-activation norm growth + feature rank collapse → gradient
collinearity across states → the *local*, per-sample PPO-clip trust region no longer bounds the *global*
policy change → silent policy collapse that the clip mechanism was supposed to prevent.

### 1.2 PFO (Proximal Feature Optimization) — exact mechanism

PFO is an auxiliary L2 loss added to the standard PPO objective:

```
L_PFO(θ) = E_{s~π_old}[ (φ_θ(s) - φ_old(s))² ]
```

where `φ_θ` are the **pre-activations of the penultimate layer** of the current network and `φ_old` are the
same pre-activations computed with the parameters that collected the current rollout (i.e., the frozen
snapshot at rollout-collection time, analogous to `π_old` in the PPO ratio). This loss is computed over the
whole rollout and added at **every gradient step during the PPO update epochs** (same cadence as the PPO
policy loss — no separate phase). The coefficient is not tuned; the authors pick the nearest power-of-10 that
matches the PPO loss magnitude (coefficient = 1 for ALE and MuJoCo-tanh, = 10 for MuJoCo-ReLU). Two variants
are tested: constraining only the penultimate layer, or all pre-activations from input through penultimate
layer.

Conceptually, PFO applies **the same trust-region idea PPO applies to the policy ratio, but applied directly
to the feature space**: keep `φ_θ` close to `φ_old` in L2, which (a) directly prevents the pre-activation-norm
blowup and (b) as a side effect keeps feature rank higher (empirically, Fig. 6: PFO reduces pre-activation
norm, decreases dead neurons, lowers plasticity loss, raises feature rank, and reduces the fraction of ratios
that exceed the clip bound).

### 1.3 TRPO/NPG applicability — explicitly NOT studied

The paper's scope is **PPO-Clip only**. It does not run or theoretically analyze TRPO/NPG. The authors'
own framing distinguishes PPO-Clip's *per-sample, heuristic* ratio clip from TRPO's *batched, global* KL
constraint, and explicitly flags this as unstudied: the mechanism they demonstrate (a per-state clip failing
to bound the policy at *other* states because gradients are colinear) is a property of the *local, per-sample*
clip. A batched-KL constraint (TRPO/NPG family, including ConstraintTRPO+IPO) computes its trust-region
quantity as an **expectation over the whole batch** (`E_s[KL(π_old(·|s), π_θ(·|s))] ≤ δ`), so it is not
subject to the exact same "protects s but not s′" failure mode PFO targets — a batched KL divergence
naturally aggregates the drift at every state, including the drifted ones. **However**, this does not mean
TRPO is immune to the underlying cause. The root cause the paper identifies — representation collapse driven
by encoder non-stationarity — is a property of the *representation*, not of the *policy-optimization
mechanism that reads it*. A collapsed/colinear φ still means the actor's effective input space has lost
degrees of freedom; the KL constraint over the *policy output* distribution can be satisfied while the
*representation feeding that policy* has degenerated, because KL is computed on `π_θ(·|s)` (the policy
output), not on `φ_θ(s)` (the encoder's internal features) directly. **The doc's claim that "the KL
constraint bounds representation drift" is not directly supported by this paper — the paper shows the
opposite relationship: representation drift/collapse is what breaks the trust-region's protective guarantee,
and the paper never demonstrates that a KL bound on the *policy* transitively bounds drift in an *upstream,
auxiliary-loss-trained encoder feeding into that policy*.** For ALBC specifically, this matters more, not
less: `z` is produced by a *separate* encoder module optimized by its own auxiliary loss (not purely policy
gradient), so even a hard, well-behaved TRPO-KL constraint on the actor's output distribution provides **no
constraint whatsoever** on how far `z_θ` has moved from `z_old` between rollout collection and the multi-step
TRPO/IPO inner optimization — this is a distinct, additional failure surface beyond what Moalla et al. even
model (their φ is trained purely by the RL loss; ALBC's z has an independent auxiliary objective on top).

### 1.4 Recommendations extracted from the paper

- PFO works as an add-on regularizer; no tuning needed if coefficient is magnitude-matched to the primary
  loss.
- Avoid shared actor-critic trunks in sparse-reward regimes — critic-side rank collapse propagated through
  shared gradients caused *complete* collapse in one of their environments (Gravitar). (Directly relevant:
  ALBC uses an **asymmetric critic** reading privileged `p_t`, and a **shared encoder path** for the actor's
  `z` — the paper's caution about shared trunks propagating collapse is structurally analogous.)
- Resetting Adam optimizer moments after each rollout batch collection reduced feature norm / raised rank on
  ALE — an orthogonal mitigation, unrelated to trust-region mechanics, that the authors found empirically
  helpful without a first-principles explanation.
- The paper explicitly declines to claim a fundamental fix: "None of them seem to be a fundamental solution
  and a deeper understanding of the reasons driving representation deterioration under non-stationarity is
  still needed."
- Their studied architectures are **separate actor-critic networks without normalization layers**; they
  explicitly flag that generalization to architectures with LayerNorm/BatchNorm/transformers (i.e., ALBC's
  ELU+LayerNorm+softsign encoder) is **unexplored**.

---

## Q2. Published pairings of auxiliary representation learning with TRPO/NPG-family (hard-KL) optimizers

**Bottom line: no concrete precedent was found.** Extensive search (representation learning + TRPO/NPG,
"stale log-prob" + auxiliary representation, "representation drift" + trust region re-anchoring, self-
predictive/SPR/OFENet-style auxiliary objectives + natural policy gradient) turned up **zero papers that
pair an auxiliary representation-learning module with a hard-KL trust-region optimizer (TRPO/NPG family)
and explicitly solve the stale-`old_mu`/`old_logp`-under-representation-drift problem**. Every concrete
recipe found in the literature (KIPPO, PFO/Moalla et al., SPR, OFENet, PPG) is built on **PPO or an
off-policy actor-critic (SAC)**, never TRPO/NPG.

This is itself an evidentiary finding, not an absence of search effort: it corroborates the epistemic
critique (THEO-3) that the doc's confidence about "the KL constraint will bound this" rests on an analogy
to PPO-family practice that has **no direct TRPO-family instantiation to cite**. What follows are the
*adjacent* techniques that partially address the same underlying problem (stale statistics under a moving
representation), extracted from PPO-family and self-supervised-RL literature, each with an explicit note on
how far the transfer to TRPO/IPO can be trusted:

1. **Alternating/frozen-phase updates (PPG precedent, PPO-family).** Cobbe et al., "Phasic Policy Gradient"
   (2020/2021) splits training into a *policy phase* (standard PPO updates) and a separate *auxiliary phase*
   (value-function-feature distillation into the policy network, using disjoint networks during the policy
   phase to avoid interference). This is a **real, code-level precedent for "don't let the auxiliary/
   representation objective and the trust-region policy objective step on each other's optimization
   simultaneously"** — the mechanism a decoupled recipe for ALBC's encoder would need. Caveat: PPG's trust
   region is PPO's clip, not TRPO's KL; nobody has published the TRPO analogue. Transfer risk: PPG's
   auxiliary phase runs *between* full policy-phase rollout cycles, not *within* a single TRPO inner-loop
   optimization (TRPO/NPG typically take one conjugate-gradient step per rollout, not multiple epochs like
   PPO) — so the "alternate phases" pattern needs re-derivation for TRPO's single-step-per-rollout structure,
   it cannot be copied mechanically.

2. **EMA/target-encoder freezing (self-predictive RL precedent, mostly SAC/off-policy).** SPR (Schwarzer et
   al., arXiv:2007.05929, later "Momentum Predictive Representations") uses an EMA target encoder
   (`momentum-tau`, e.g. 0.01 decay coefficient in their public config) to generate self-prediction targets,
   with gradients stopped through the target branch. Ablations in the paper "emphasize the necessity of
   multi-step prediction and EMA-based target networks... using a target encoder has a large impact on the
   method" (exact ablation table numbers were not extractable from the fetched HTML/PDF — this is a
   **medium-confidence, not full-text-verified** claim; see confidence note in Implications). This is the
   most directly relevant *mechanism* precedent for "how do you stop a representation from drifting under the
   nose of an optimizer that assumes a fixed target" — but it is solving a **different** problem: SPR's EMA
   target prevents the self-prediction *target* from moving during a single gradient step (a moving-target
   problem, BYOL-style), not the TRPO-specific problem of `old_mu`/`old_logp` being computed under a `z_old`
   that is stale by the time the CG/line-search step is taken.

3. **Re-anchoring the trust-region reference point per outer iteration** — found one adjacent example
   ("Extreme Region Policy Distillation," arXiv:2605.25582, LLM RL) that re-anchors `π_old`/`θ_old` per
   batch iteration to control drift in an iterative distillation loop. This is **not a representation-module
   precedent** (it re-anchors the *policy* reference, not an *encoder*, and targets entropy collapse under
   PPO-style off-policy reuse, not colinearity/rank collapse) — included only because it is the closest hit
   for "re-anchor old statistics" as a general engineering pattern; it should not be over-read as evidence
   for the specific ALBC mechanism.

**Conclusion for Q2**: the "decoupled recipe" the design doc gestures at (freeze `phi_x` during the TRPO
inner loop, or re-anchor `old_mu`/`old_logp` after a representation step) is *plausible by analogy* to PPG's
phase-alternation and SPR's EMA-target pattern, but there is **no published TRPO/NPG instantiation of either
technique**, and no one has published a solution to the specific stale-`old_mu`-under-`z_old` problem that a
TRPO/IPO trust region introduces. This is a genuine, unresolved research gap, not an engineering detail
covered by precedent.

---

## Q3. KIPPO's actual update schedule — code-level

**No public GitHub repository was found.** Extensive search (`KIPPO Koopman PPO github`, author name search
`Andrei Cozma github`, direct guesses `koopman-ppo`, `kippo-rl`) returned no code repository — only the arXiv
paper (2505.14566, IJCAI 2025), the UTK master's thesis page (trace.tennessee.edu/utk_gradthes/11783, which
returned HTTP 405 and could not be fetched), and the IJCAI proceedings PDF. The arXiv HTML mirror
(`arxiv.org/html/2505.14566v2`) 404'd (paper is PDF-only on arXiv, no HTML rendering available), and the raw
PDF fetch returned only binary/FlateDecode stream data that could not be decoded by the fetch tool — so the
algorithm box, exact update-schedule pseudocode, and stop-gradient/optimizer details **could not be
extracted**. From the abstract and secondary summaries (not full-text-verified): "a Koopman-approximation
auxiliary network... added to the baseline policy optimization algorithms without altering the architecture
of the core policy or value function" — consistent with an auxiliary-loss-style integration similar to PFO,
but the paper does not appear (per every summary source) to address TRPO at all; it is built on PPO.

**Verdict for Q3: could not be resolved from available sources.** This should be reported to the doc authors
as an open gap — if the "decoupled recipe" claim in the design doc relies on KIPPO's schedule being known and
reproducible, that reliance is currently **unverifiable**; the paper's reproducibility for the specific
question asked (per-epoch update ratio, stop-gradient decision, optimizer separation) is not established by
any source reachable in this research pass. A follow-up would need direct PDF text extraction (e.g., via a
PDF-to-text tool rather than the web-fetch summarizer used here) or contacting the authors.

---

## Q4. EMA/target-encoder practice as a drift-rate control — evidence on how much it matters

- **SPR (Schwarzer et al. 2020/2021)**: ablations show the EMA target encoder has "a large impact" on
  final performance versus removing it (using the online encoder directly) — reported qualitatively as
  necessary alongside multi-step prediction; the exact quantitative ablation deltas could not be extracted
  from the sources reached (abstract-only depth for this specific claim).
- **BYOL-style self-predictive RL generally**: the standard recipe (per multiple secondary sources on
  self-predictive representations) is EMA target encoder + stop-gradient on the target branch, tuning the
  EMA momentum and the auxiliary loss weight as the two knobs that trade off representation stability against
  representation freshness/informativeness. Momentum values in practice cluster in the 0.99–0.999 range
  (`momentum-tau` reported as low decay coefficients like 0.01, i.e. `1-tau≈0.99`) — i.e., **slow drift by
  design**, updating the target network on a much longer timescale than the online network.
- This body of evidence establishes the qualitative direction (EMA/target-freezing measurably controls
  representation drift and is treated as necessary, not optional, in the closest analogous self-predictive-RL
  literature) but **does not transfer a validated momentum value or drift-rate budget to a TRPO/IPO trust
  region context** — no paper studies the interaction between EMA momentum and a hard-KL trust region's
  step-size/line-search behavior.

### Concrete safe-update-protocol options for `phi_x`/`z` under ConstraintTRPO (ranked by precedent strength)

| Option | Precedent | Precedent strength | Cost / risk |
|---|---|---|---|
| **Freeze encoder during the TRPO inner loop** (update only between rollout collections, one step per rollout like PPG's phase split) | PPG (PPO-family, phase alternation) | Medium — same *pattern*, no TRPO instantiation | Simple to implement in rsl-rl's rollout/update loop; loses within-rollout representation adaptation |
| **EMA/target encoder feeding the actor, online encoder trained by aux loss only** | SPR / BYOL-style self-predictive RL (mostly SAC/off-policy) | Medium — well-established *mechanism*, wrong optimizer family | Adds a second encoder copy + momentum hyperparameter to tune; no guidance on tau under a CG/line-search step |
| **Re-anchor `old_mu`/`old_logp` (and `z_old`) immediately before the TRPO inner-loop CG step, using the just-updated encoder** | Weak analogy only (LLM RL re-anchoring, different mechanism) | Low | Requires re-running a forward pass over the rollout with the new encoder before computing the surrogate — extra compute, and does not by itself prevent drift *during* the multi-substep CG/line-search itself |
| **Representation-KL / PFO-style auxiliary penalty on `phi_θ` vs `phi_old`, added alongside the TRPO/IPO objective** | PFO (Moalla et al., PPO-family) | Medium — direct mechanistic analogue, but studied under PPO-clip not TRPO-KL | Coefficient needs re-tuning for ALBC's TRPO+IPO loss scale (Moalla's power-of-10 heuristic is PPO-specific); does not address the CG-step staleness problem, only steady-state drift |
| **No mitigation (current doc's implicit position: "KL bounds it")** | Contradicted by Moalla et al.'s core finding (§1.3) | N/A — this is the option under critique | Confirmed unsafe per Q1; representation collapse is exactly what breaks trust-region guarantees, and the guarantee that does exist (policy-output KL) does not extend to an auxiliary-loss-trained upstream encoder |

None of these four mitigation options has been validated end-to-end for a TRPO/NPG-family optimizer in
published work. The strongest, most implementation-ready precedent is the **PFO L2-penalty pattern**
(direct code available, MIT-licensed, reusable) combined with **PPG-style phase separation** (pattern only,
no code) — a hybrid that has not itself been published or tested anywhere.

---

## Implications for ALBC (mechanism-level)

1. **The design doc's core reassurance is unsupported, and the literature points the opposite direction.**
   Moalla et al. do not show that a trust region bounds representation drift; they show representation
   collapse is *what breaks* the PPO-clip trust region's guarantee. ConstraintTRPO's batched KL constraint
   is computed on the **actor's output distribution**, not on `z` or on the encoder's pre-activations — so
   even a perfectly enforced KL bound provides **zero direct constraint** on how far `z_θ` (or the
   auxiliary-loss-trained encoder producing it) has moved between rollout collection (`z_old`) and the
   current TRPO/IPO inner-loop iterate. This is a strictly *harder* case than what Moalla et al. studied,
   because ALBC's encoder is trained by an **independent auxiliary objective**, not purely by the policy
   gradient flowing through φ as in their toy/Atari/MuJoCo setups.

2. **ConstraintTRPO's mechanics make the CG/line-search staleness problem sharper than PPO's.** TRPO computes
   a single natural-gradient step per rollout via conjugate gradient against the Fisher/KL curvature, then
   line-searches for the largest step satisfying the KL constraint and (for ConstraintTRPO+IPO) the
   cost/log-barrier constraints. If `z` (and thus the actor's effective input, thus the actual policy
   distribution being optimized) is allowed to move *during* this single-step optimization — e.g., because an
   encoder update is interleaved with it — the KL/IPO-feasibility check computed at the start of the line
   search no longer describes the policy actually being evaluated by the end of it. PPO's multi-epoch,
   multi-minibatch structure at least re-samples ratios repeatedly within a step, diluting (not solving) the
   staleness; TRPO's single CG+line-search step has **no such internal re-check**, making the failure mode
   Moalla et al. describe potentially more acute, not less, for a trust-region method with a harder
   constraint.

3. **Recommended near-term mitigation, given no direct precedent exists**: adopt the **PFO-style penalty**
   (`E[(φ_θ - φ_old)²]` on the encoder's pre-activations feeding `z`, coefficient scale-matched to the
   ConstraintTRPO+IPO objective) **combined with freezing/decoupling the encoder update from the TRPO inner
   loop** (PPG-style phase separation: update `z`'s encoder only between rollout collections, never during the
   CG/line-search step). This combination has the strongest — though still indirect and unvalidated —
   precedent support of the options surveyed. It should be treated as a **novel contribution requiring its
   own empirical validation**, not an established recipe being "applied," because no published work pairs
   either technique with a TRPO/NPG-family optimizer.

4. **The doc should not claim the KL constraint "handles" representation drift.** It should instead state
   explicitly (a) this is an open problem with no published precedent for TRPO/NPG-family optimizers, (b) the
   nearest analogous finding (Moalla et al., PPO-family) shows the *opposite* relationship — representation
   collapse breaks trust regions rather than being bounded by them, and (c) any encoder-drift mitigation added
   to ConstraintTRPO+IPO is new engineering work whose failure mode should be instrumented (feature rank,
   pre-activation norm, and the KL-vs-realized-policy-change gap during the CG/line-search step) before being
   trusted, per the workspace's own "no premature assertions" analysis-quality rule.

---

## References

1. Moalla, S., Miele, A., Pyatko, D., Pascanu, R., Gulcehre, C. "No Representation, No Trust: Connecting
   Representation, Collapse, and Trust Issues in PPO." NeurIPS 2024. arXiv:2405.00662.
   https://arxiv.org/abs/2405.00662 — verification depth: **full-text-read** (via arxiv.org/html/2405.00662v1,
   HTML mirror; equations, Fig. 3/6 findings, and recommendations section extracted directly).
2. Cozma, A., Harris, L., Qi, H. "KIPPO: Koopman-Inspired Proximal Policy Optimization." IJCAI 2025.
   arXiv:2505.14566. https://arxiv.org/abs/2505.14566 — verification depth: **abstract-only**; the arXiv HTML
   mirror 404'd and the PDF fetch returned undecodable binary stream data, so algorithm-box / update-schedule
   / stop-gradient details **could not be verified** despite being explicitly requested (see Q3).
3. Cozma, A. "Koopman-Inspired Proximal Policy Optimization (KIPPO)." Master's Thesis, University of
   Tennessee, Knoxville. https://trace.tennessee.edu/utk_gradthes/11783/ — verification depth: **unreachable**
   (HTTP 405 on fetch); listed for completeness only, not used as a source for any claim above.
4. Cobbe, K., Hilton, J., Klimov, O., Schulman, J. "Phasic Policy Gradient." ICML 2021 / arXiv:2009.04416. —
   verification depth: **snippet/secondary-summary** (search-result summaries of the paper and CleanRL/vitalab
   write-ups; the two-phase alternating-update mechanism and disjoint-network structure were consistently
   corroborated across 3 independent summaries, not read from the primary PDF directly).
5. Schwarzer, M., Anand, A., Goel, R., Hjelm, R.D., Courville, A., Bachman, P. "Data-Efficient Reinforcement
   Learning with Self-Predictive Representations." ICLR 2021 / arXiv:2007.05929. — verification depth:
   **abstract-only**; the specific quantitative ablation numbers for "EMA target vs. no target" could not be
   extracted from the fetched abstract page (full PDF was not separately fetched for this paper — flagged as
   a gap, see Q4 note on confidence).
6. "Extreme Region Policy Distillation" (title as indexed; LLM-RL trust-region distillation paper).
   arXiv:2605.25582. https://arxiv.org/pdf/2605.25582 — verification depth: **full-text-read** (via HTML
   fetch of the PDF-rendered page); used only as a weak/adjacent analogy for "re-anchoring old-policy
   statistics," explicitly flagged in the text above as not a representation-module precedent — do not
   over-weight this citation.
7. Wang, Y. et al. (2020), Theorem 2 on PPO clipped-ratio bound violation under gradient alignment — cited
   secondhand via Moalla et al. (source #1); **not independently verified** (no direct search/fetch performed
   on this citation; flagged as inherited, not primary-verified).

## GitHub repos

1. **https://github.com/CLAIRE-Labo/no-representation-no-trust** — official code for Moalla et al. (NeurIPS
   2024). Implements PPO training instrumented for representation-dynamics study, using **TorchRL** +
   **Hydra** for configuration, under **MIT license**. Main entry point `src/po_dynamics/solve.py`; PFO and
   other losses live under `src/po_dynamics/modules/`. **Reusability for ALBC's PyTorch/rsl-rl stack**: the
   PFO loss itself (`E[(φ_θ - φ_old)²]` on pre-activations) is a ~5-line, framework-agnostic PyTorch snippet
   that can be lifted directly into rsl-rl's `ConstraintTRPO` update step without needing TorchRL — the value
   is in the *loss formula and coefficient-selection heuristic*, not the surrounding TorchRL/Hydra scaffolding
   (that scaffolding would not be reused). Verification depth: fetched via WebFetch summarizer, not a direct
   file-by-file read of the loss module source — flagged as **medium-confidence** on exact code structure.
2. **KIPPO** — no public repository found despite targeted search (author name, plausible repo-name guesses,
   general "KIPPO github" query). Confirmed absent as of this research pass, not merely unindexed by search —
   multiple independent queries all failed to surface a link, and the paper/thesis pages themselves do not
   advertise one in the reachable summaries.
3. **https://github.com/mila-iqia/spr** — official SPR (Schwarzer et al.) code. Not independently fetched in
   this pass (surfaced only in search results, not opened); flagged for a follow-up if exact EMA-ablation
   numbers or the target-encoder implementation are needed with full-text verification.
