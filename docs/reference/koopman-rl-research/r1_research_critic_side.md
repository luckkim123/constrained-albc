# Critic-Side Koopman Lifting: Research Report

Assignment: resolve epistemic THEO-1's sharpest sub-finding — SKooP fed its Koopman
autoencoder's prediction to the critic ONLY ("the actor only requires x_k as input"), which the
target doc filed as support for actor-side revision when it is better read as evidence for
critic-side design. This report investigates the critic-side design space directly.

---

## Q1. SKooP (arXiv 2607.11624) deep read

**Full citation**: D'Elia, Zhan, Turrisi, Romualdi, L'Erario, Camoriano, Pan, Pucci. "SKooP:
Symmetric Koopman Predictions for Faster and More Generalizable Legged Robot Locomotion with
Reinforcement Learning." Accepted IEEE/RSJ IROS, Pittsburgh, 2026. arXiv 2607.11624.
Verification depth: full-text-read (arxiv.org/html/2607.11624, fetched directly).

**What the critic receives** — a single privileged Koopman **one-step prediction**, not the raw
lifted state:

> "the critic receives a single privileged Koopman state prediction z_{k+1} = A f_φ(x_k) + B u_k"

The actor's input is untouched — it consumes only the raw state x_k. The paper is explicit that
this is a deliberate architectural choice, not an oversight or a "try actor-side later":

> "Since the actor only requires x_k as input, this architectural choice informs training without
> increasing computational overhead at deployment time."

The framing is **deployment-cost avoidance** (the Koopman machinery stays training-only, following
the asymmetric actor-critic tradition of Pinto et al. 2018 — see Q2), not a claim that actor-side
injection was tried and failed.

**Training schedule**: concurrent but decoupled. An Equivariant Controlled Denoising Autoencoder
(ecDAE) trains alongside PPO at every RL step, on its own optimizer, off a separate Prioritized
Experience Replay buffer distinct from the policy's on-policy buffer. No policy gradient flows into
the autoencoder — it is trained purely on reconstruction + one-step-prediction losses (their Eq. 7).
This is the same "decoupled optimizer" pattern the target doc already adopts from KIPPO — SKooP
independently corroborates it, on a different codebase (PPO + equivariant DAE vs. KIPPO's plain
autoencoder).

**Gains attributed**: reward/success and convergence-speed gains, task-dependent. On the hardest
task (push-door) SKooP "significantly outperforms PPO and PPOeqic in terms of reward values and
converges faster than SKooP-NoPred" (success rates ~82.8% right-door / 77.7% mirrored vs. PPO's
70%/0%). Note the 0% for the mirrored condition is the symmetry-equivariance contribution, not the
Koopman contribution — SKooP bundles two independent mechanisms (equivariant network structure +
Koopman prediction), and the paper's headline numbers do not cleanly separate them.

**Ablations that bear directly on Q1**:
- **SKooP-NoPred**: critic gets the lifted state z_k instead of the one-step prediction z_{k+1}.
  Converges *slightly faster early* (before the autoencoder itself has converged, so the prediction
  is initially noisy/wrong) but is overtaken by full SKooP later. This is the cleanest evidence in
  the paper that the *prediction*, not just "having a learned latent," is where the later-stage gain
  lives — a genuinely informative ablation.
- **SKooP-NoSym**: prediction without the symmetry (equivariance) constraint — isolates the Koopman
  contribution from the equivariant-network contribution, at least partially.
- **No ablation feeds the prediction to the actor.** The paper never reports trying actor-side
  injection and getting a worse result — it simply never explores that branch. The correct
  epistemic reading (which the target doc got wrong) is "untried", not "tried and negative." The
  critic-side design choice is motivated by deployment overhead, not by a documented actor-side
  failure.

**Code release**: no GitHub link in the paper body. Project page
(evelyd.github.io/SymmetricKoopmanPredictions) does list a repository:
**github.com/evelyd/SymmetricKoopmanPredictions** (verification depth: page-fetch only — the repo
itself was not opened/cloned; no license was visible on the project page, and the repo's own
license file was not checked in this pass). Treat the repo pointer as unverified for reuse until
someone opens it directly.

---

## Q2. Broader precedent for critic-only auxiliary/dynamics information

**Asymmetric-critic lineage (directly on point — our critic is already this pattern)**:
Pinto, Andrychowicz, Welinder, Zaremba, Abbeel, "Asymmetric Actor Critic for Image-Based Robot
Learning" (RSS 2018, arXiv 1710.06542) established the base pattern: full/privileged state to the
critic, partial observation to the actor, unbiased policy-gradient justification. Verification
depth: not re-fetched this pass (widely cited, standard result; treat as background, not load-
bearing without direct verification if it becomes a citation target). RMA (Kumar et al., "RMA:
Rapid Motor Adaptation for Legged Robots," RSS 2021) and follow-ons (DreamWaQ etc., per search
snippets — not individually verified beyond abstract level) extend this: privileged terrain/contact
state feeds the critic (or an estimator the actor imagines from), never the actor directly. **This
is precisely our own architecture already**: ALBC's asymmetric critic already sees 28D p_t
(privileged plant state) *plus* z (the 9D encoder output), while the actor sees only
EmpNorm(o_t) ⊕ z. We are not proposing to *introduce* asymmetric privilege — we already have it, at
a scale (28D raw + 9D compressed) larger than what SKooP's critic gets (a single one-step Koopman
prediction, no other privileged channel, since SKooP's baseline PPO critic apparently is *not*
asymmetric otherwise — the paper does not describe an existing privileged-critic baseline).

**This is the crux and it points toward a null-to-weak expectation.** A fetch of
**"Diminishing Return of Value Expansion Methods" (arXiv 2412.20537)** (verification depth:
full-text-fetch of HTML) is the single most directly relevant piece of evidence found for the
marginal-value question. Its core finding: model-based value expansion (rolling a learned or even
an *oracle* dynamics model forward and using it to enrich the value target) gives shrinking returns
in two dimensions — rollout horizon (gains plateau/degrade past ~5 steps) and model accuracy
(going from a learned model to a *perfect oracle* model gives only marginal further benefit). The
critical mechanism the paper isolates: **when the base value function already has a strong estimate
of the world, model-derived auxiliary information adds little** — "the zero-step expansion (H=0,
vanilla SAC) already captures the true return distribution well, making longer rollouts redundant
while only increasing gradient variance." The paper explicitly questions "whether these marginal
performance gains justify the added complexity and cost" once the base critic is already
well-informed.

Mapped onto ALBC: our critic is not SKooP's vanilla-PPO critic (previously privilege-free, information-
starved). It already has 28D raw privileged state *and* the learned 9D z. A Koopman one-step
prediction z_{k+1}^{Koop} computed from a linear operator over this same information is, at best,
a *smoothed, linearly-constrained re-derivation of information the critic can already read directly
and nonlinearly* through its existing MLP over p_t and z. The 2412.20537 mechanism — diminishing
marginal value once the base estimator already has strong information — is the closest empirical
analogy available, though it targets model-based *rollout* value expansion, not Koopman-specific
feature injection, so the transfer is by mechanism-analogy, not a direct experimental result on
Koopman critics.

**Informed Asymmetric Actor-Critic (arXiv 2509.26000)**, fetched at abstract level only (WebFetch
returned only abstract-level content, full text not retrievable in this pass — verification depth:
abstract only, flagged explicitly). Its claim: the critic does not need *full* state, only
"carefully selected privileged signals," which can "match or outperform full-state asymmetric
baselines while relying on strictly less state information." This is informative but answers the
opposite question from ours (which subset of privileged info suffices, not whether adding a new
derived feature on top of already-full privileged info helps). No stated analysis in the abstract of
the marginal-value question when the critic is already fully privileged; this paper could not be
deep-read in this pass, so treat as suggestive, not conclusive — it is weak indirect evidence that
*curated* privileged signals beat throwing in everything, which if anything argues against blindly
adding a Koopman feature to an already-privileged critic without justifying why that specific
feature earns its keep.

**KARL (Koopman-Assisted Reinforcement Learning, NeurIPS 2023 AI4Science workshop)**: located via
search (title-page + abstract level only — not deep-read this pass). It parameterizes the Koopman
operator with control actions to reformulate soft-value-iteration/SAC. This is a *value-function
reformulation* through Koopman linearity (the value itself is expressed via Koopman eigenfunctions),
not "add a Koopman prediction as an extra critic input feature" — architecturally distinct from both
SKooP's design and the critic-side proposal under review here. Not usable as direct precedent for
"inject one-step Koopman prediction into an already-privileged critic's input"; it is evidence that
Koopman structure *can* be married to a critic/value function, at the cost of a much deeper
reformulation than a feature-injection scheme.

**Conclusion for Q2**: no located study tests the exact marginal-value question — "does injecting a
Koopman-derived feature into a critic that is ALREADY privileged (raw state + a learned compressed
representation) produce a measurable gain over that already-privileged critic." SKooP's positive
result is confounded by starting from an *unprivileged* PPO critic baseline (single extra channel
added to nothing → measurable win is unsurprising) and by bundling equivariance with the Koopman
term. The closest mechanism-level evidence (2412.20537) predicts a small-to-negligible marginal
gain once the base estimator is already well-informed. This is a real gap in the literature, not
just an ALBC-specific unknown — the question "does critic-side model-derived auxiliary information
help a critic that already has privileged access" appears understudied.

---

## Q3. Constraint/cost critics — precedent for auxiliary dynamics features

Searched specifically for safety/cost-critic analogs of SKooP's design. Found
**"Feasibility Consistent Representation Learning for Safe Reinforcement Learning" (FCSRL,
arXiv 2405.11718)**, fetched full-text (HTML). Verification depth: full-text-fetch.

FCSRL is directly on-topic for Q3's crux question ("does the same mechanism help a constraint/cost
critic, or does it only compensate for missing privileged information?") and gives a **negative
result on the closest analog they tried**: the paper reports that a "value consistency" auxiliary
objective — i.e., exactly the pattern of training a dynamics-consistency-style auxiliary loss aimed
at the cost value function — **"does not exhibit similar advantages due to sparsity of the cost
signals."** They abandon augmenting the cost critic directly and instead introduce a separate
"feasibility score" auxiliary head (independent of both reward and cost critics), justified because
it is provably smoother (Proposition 4.3) than the cost value function itself. Their gains come
specifically from *cost signal sparsity being a problem that smoothing solves* — a failure mode ALBC's
cost critic does not obviously share (ALBC's IPO cost critics are trained on dense per-step
constraint costs, not sparse/rare safety violations à la Safety Gymnasium).

**Implication for Q3's crux question**: the one directly relevant empirical data point argues
*against* naively porting reward-critic auxiliary-dynamics tricks to a cost/constraint critic — the
authors tried something structurally similar (value-consistency auxiliary loss on the cost critic)
and it underperformed, specifically because of sparsity, which motivated a different mechanism
(feasibility smoothing) applied *outside* the critics rather than injected into them. No study was
found that reports a positive result from feeding a Koopman-style one-step dynamics prediction
directly into a cost/constraint critic. This is thin evidence (n=1 paper, different constraint
regime — sparse safety violations vs. ALBC's dense per-step attitude/rate costs), but it is the only
concrete data point located, and it points toward "gains from critic-side auxiliary dynamics
information are not guaranteed to transfer to cost critics, and the sparsity-vs-dense distinction
matters." If the mechanism argued for reward-critic gains is "better value bootstrapping via
smoother targets," ALBC's cost critic (dense costs, i.e., not the sparsity FCSRL targeted) starting
point is different enough that the FCSRL negative result may not transfer either way — genuinely
unresolved, not analogous in a way that licenses a confident prediction.

---

## Q4. Implementation surface on the ALBC stack

**Verified by direct grep of `constrained_albc/envs/_core/algorithms/constraint_trpo.py`**:

```
value_prefixes = ("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")
...
self.value_optimizer = optim.Adam(value_params, lr=value_lr)
```

Confirms the systemfit-critique's claim exactly: both the reward critic (`critic.`) and the cost
critic (`cost_critic.`) are grouped into the **Adam-optimized value-parameter set**, explicitly
*separate* from the TRPO natural-gradient policy group (which is documented in the same file as
"Policy (actor + encoder + log_std): TRPO natural gradient (no optimizer)"). This is a clean,
verified separation: a critic-side Koopman feature (whether feeding the reward critic, the cost
critic, or both) is added-input to a network trained by ordinary Adam SGD on TD/GAE losses — it
never enters the TRPO KL-constrained natural-gradient step, never touches `_policy_params`, and by
construction cannot move the quantity (`_kl_divergence` over actor mean/std) the trust-region line
search polices. So the systemfit reasoning holds up under code inspection: critic-side lifting is
mechanically outside the trust-region drift problem THEO-3 raises for actor-side/shared-encoder
designs, because the cost/reward critics here are not inside the natural-gradient group to begin
with — a structural fact, not something that needs separate defending.

**Other surface claims, checked**:
- **Actor input untouched**: trivially true for a design that literally only adds a critic-side
  input tensor; verified there is no code-level reason this would leak into the actor's obs
  construction — the actor forward path and critic forward path are separate networks reading
  separate concatenated tensors in this codebase's convention (consistent with the file's own
  comment distinguishing the two parameter groups).
- **Deploy export contract**: not directly grepped in this pass (out of scope of the assigned file),
  but follows logically from "actor input untouched" — the deploy-export path exports the actor
  policy only (per project memory `albc-deploy-export-is-tcn-only`), so a critic-side-only addition
  by definition cannot appear in the exported artifact. This is architecturally the same guarantee
  SKooP claims ("without increasing computational overhead at deployment time") and it holds for the
  same structural reason.
- **Student distillation path**: the student learns to imitate the teacher's z / actor behavior
  (GRU distillation of the encoder's z per project memory), not the critic. A critic-only addition
  has no student-side surface unless someone later chooses to also distill from the critic, which is
  not the proposal here.

**Is critic-side lifting therefore the lowest-risk Koopman arm?** Yes, on the risk axis specifically
— it is verified to sidestep the trust-region-drift objection (THEO-3) and the deploy/export/student
surfaces, for the structural reason above, not merely by argument.

**But the expected effect size is honestly weak, not "safe and therefore probably still valuable."**
Two independent lines above converge on the same caution:
1. Q2's diminishing-returns literature (2412.20537) predicts small marginal gains once the base
   critic already has strong information — and ours already has 28D privileged state + 9D z, more
   than SKooP's PPO critic had before its one addition.
2. Q3's one concrete cost-critic analog (FCSRL) reports a negative result for the structurally
   closest thing tried (value-consistency auxiliary loss on a cost critic), for a different but
   plausible-sounding reason (sparsity) that does not obviously apply to ALBC's dense costs but also
   does not obviously not apply.

The honest framing: critic-side Koopman lifting is the **cheapest, structurally safest experiment
in the Koopman design space** for this codebase (isolated from the trust region, from deploy, from
distillation), but it is **not evidenced to have a meaningful expected effect size** given the
critic is already privileged — the one paper that shows a clean win (SKooP) demonstrates it from an
unprivileged baseline, which is not our starting point. It should be ranked as a cheap,
low-downside screening probe, not promoted to "mechanism precedent solid" as the target doc's
Sec 15.4 does for the actor-side arm — if anything the target doc's error (treating SKooP's design
choice as support for actor-side change) inverts which arm SKooP's own evidence actually favors.

---

## References

1. D'Elia, E., Zhan, W., Turrisi, G., Romualdi, G., L'Erario, G., Camoriano, R., Pan, W., Pucci, D.
   "SKooP: Symmetric Koopman Predictions for Faster and More Generalizable Legged Robot Locomotion
   with Reinforcement Learning." IEEE/RSJ IROS 2026 (accepted). arXiv:2607.11624.
   https://arxiv.org/abs/2607.11624 — verification depth: full-text-read (HTML fetch).
2. Project page (SKooP): https://evelyd.github.io/SymmetricKoopmanPredictions/ — verification depth:
   page-fetch (used only to locate the code repo pointer and confirm no additional ablation detail
   beyond the paper).
3. Pinto, L., Andrychowicz, M., Welinder, P., Zaremba, W., Abbeel, P. "Asymmetric Actor Critic for
   Image-Based Robot Learning." RSS 2018. arXiv:1710.06542. Not re-fetched this pass — cited from
   general knowledge / search snippets as background lineage for asymmetric-critic precedent;
   verification depth: not verified (flag before using as a load-bearing citation).
4. Kumar, A. et al. "RMA: Rapid Motor Adaptation for Legged Robots." RSS 2021. Verification depth:
   snippet-level only (search result summary), not fetched full text this pass.
5. "Diminishing Return of Value Expansion Methods." arXiv:2412.20537.
   https://arxiv.org/html/2412.20537 — verification depth: full-text-fetch (HTML).
6. "Informed Asymmetric Actor-Critic: Leveraging Privileged Signals for Efficient Reinforcement
   Learning." arXiv:2509.26000. https://arxiv.org/abs/2509.26000 — verification depth: abstract only
   (full text could not be retrieved via WebFetch in this pass — flagged explicitly, do not treat any
   claim beyond the abstract as verified).
7. "Feasibility Consistent Representation Learning for Safe Reinforcement Learning" (FCSRL).
   arXiv:2405.11718. https://arxiv.org/html/2405.11718v1 — verification depth: full-text-fetch
   (HTML).
8. Koopman-Assisted Reinforcement Learning (KARL). NeurIPS 2023 (AI4Science workshop track per
   search results; also appears associated with NeurIPS main-conference virtual listing — venue
   attribution not fully disambiguated in this pass). arXiv reference not directly confirmed by
   number in this search pass (search returned a NeurIPS virtual page, not an arXiv abstract page).
   Verification depth: title/venue-level only from search snippets — NOT deep-read, do not cite
   mechanism-level claims about KARL beyond "reformulates SAC/soft-value-iteration via a
   control-parameterized Koopman operator" without further verification.
9. (Referenced, not independently re-verified this pass — carried from the target doc's own
   citation, already verified there per epistemic critique) Moalla et al., "No Representation, No
   Trust," arXiv:2405.00662, NeurIPS 2024 — used here only to note that THEO-3's trust-region
   objection is orthogonal to this report's critic-side finding, not to re-verify it.

---

## GitHub repos

1. **github.com/evelyd/SymmetricKoopmanPredictions** — SKooP's own code release (per the project
   page's stated repository link). What it implements: the equivariant controlled denoising
   autoencoder (ecDAE) + Koopman one-step prediction + PPO training loop for quadruped locomotion,
   in what is presumably a JAX or PyTorch RL stack (framework not confirmed — the repo itself was
   not opened in this pass, only the project page was fetched). License: not visible from the
   project page; check the repo's own LICENSE file before treating anything as reusable.
   Reusability for our PyTorch/rsl-rl stack: **unverified this pass** — flagged explicitly. If this
   becomes load-bearing for an implementation plan, the repo must be cloned and read directly next;
   do not assume PyTorch/rsl-rl compatibility from the project page alone.
2. No other GitHub repositories were located for the Q2/Q3 papers (KARL, Informed Asymmetric
   Actor-Critic, FCSRL, Diminishing Return of Value Expansion) in this search pass — none of the
   web-search or fetch results surfaced a code link for these four. This is a gap, not a confirmed
   absence — a dedicated GitHub search (`site:github.com` per paper) was not run for each; only the
   SKooP-specific search was performed given the assignment's Q1 focus.

---

## Implications for ALBC

**Mechanism-level, concrete claims only:**

1. **Critic-side Koopman lifting is structurally isolated from the trust-region drift problem**,
   verified by direct code inspection of `constraint_trpo.py`: both `critic.` and `cost_critic.`
   parameters are in the Adam-optimized `value_params` group, disjoint from the TRPO
   natural-gradient `_policy_params` group that the KL-constrained line search polices. Adding a
   Koopman one-step-prediction input to either critic changes only the value network's forward
   input tensor; it cannot alter the actor's parameterization, `_kl_divergence`, or the trust-region
   step, and by extension cannot affect the deploy-export contract (actor-only export) or the
   student distillation path (which imitates the actor/encoder z, not the critic).

2. **SKooP's critic-only design choice was motivated by deployment-overhead avoidance, not a
   documented actor-side failure.** No ablation in the paper feeds the Koopman prediction to the
   actor and reports a negative result — that branch is simply untried. Citing SKooP's design as
   evidence *for* the actor-side revision (as the target doc's Sec 8.3 does) is not supported by
   what SKooP actually shows; if SKooP is cited at all, it supports exploring the critic-side arm,
   not the actor-side one.

3. **The marginal-value question is the real crux, and the available evidence is unfavorable, not
   neutral.** ALBC's critic is already asymmetric-privileged (28D p_t + 9D z), unlike SKooP's
   PPO-critic baseline which started unprivileged. The closest mechanism-level literature
   (arXiv 2412.20537, diminishing returns of model-based value expansion) predicts small-to-
   negligible marginal gain once a critic already has strong information about the world — exactly
   ALBC's starting condition. This is an argument by mechanism-analogy (rollout-based value
   expansion, not Koopman-feature injection specifically), so it should be treated as a prior, not a
   settled prediction — but it is real, located evidence that should weigh against expecting a large
   effect, not merely an absence of evidence either way.

4. **Cost/constraint critics have one negative data point for the closest analog tried elsewhere.**
   FCSRL's value-consistency auxiliary objective on a cost critic underperformed, attributed to cost
   signal sparsity — a condition ALBC's dense per-step IPO costs likely do not share, so this does
   not transfer cleanly either direction. If the arm is run, the reward critic and cost critic should
   be instrumented separately (does the Koopman feature help the reward critic's value loss, the
   cost critic's, both, or neither) rather than assumed to behave identically — Q3's evidence
   suggests they may not.

5. **Recommended framing if this arm proceeds**: run it as a genuinely cheap, low-risk screening
   probe (consistent with its structural isolation from the trust region/deploy/distillation
   surfaces), but rank it as "cheap curiosity with a plausibly-null expected effect given our critic
   is already privileged" — not as "mechanism precedent solid." A useful discriminating design if
   this is tried: compare critic loss/value-accuracy WITH vs WITHOUT the Koopman one-step prediction
   feature, holding everything else fixed (single-variable, per the project's own Minimum-Change
   Revert discipline), separately for the reward critic and the cost critic, before touching the
   actor or z at all. A null result on an already-privileged critic would be informative and cheap;
   a positive result would be the first data point in the literature (as far as this search found)
   that model-derived auxiliary features add value to an already-privileged critic — which would
   itself be a small, genuine, reportable finding, not because it validates "Koopman" per se, but
   because it would isolate whether the linearity-constrained prediction adds anything beyond what
   an unconstrained learned latent-dynamics feature would (the same unconstrained-control-arm gap
   THEO-2 already flags for the actor-side design — the identical control is needed here too, to
   distinguish "Koopman helped" from "any auxiliary dynamics feature would have helped identically").
