# Adversarial critique — THEORY lens

Target: `/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md` (639 lines, read in full).
Cross-checked against: `cluster_separable_theory.md`, `cluster_coherent_bilinear.md`, `axis_hvok_delay.md`,
and ALBC source (`constrained_albc/envs/main/mdp/observations.py`,
`constrained_albc/envs/main/albc_env.py`, `marinelab/core/ocean_current.py`,
`constrained_albc/envs/_core/encoder/actor_critic_encoder.py:219`).

Scope: reasoning defects only. Citation provenance is a sibling critic's job; where I use a source
report it is to show the doc's *own* evidence does not carry its *own* conclusion.

Summary of stance: the doc's factual survey work is strong and several of its verdicts are correct
for the right reasons (§4.1 "Koopman linearity is a property of time evolution, not of the obs→action
map" is exactly right and I do not attack it; §13.3 CCK verdict is well-argued; §15.1 white-space claim
is appropriately scoped). But three of its load-bearing arguments are logically invalid, one headline
"resolved" claim inverts one of its own source reports, its #1 near-term recommendation is
mathematically near-vacuous on this system, and two of its "facts about our plant" are contradicted
by the code.

---

## THEO-1 (critical) — §5.2 "information argument (decisive)" is a true theorem used to prove a false claim, and the doc itself contradicts it 300 lines later

**Attacked text.** §5.2(2): "any fixed pointwise transform `Ψ(o_t)` carries exactly the information of
`o_t`. A memoryless base policy on `Ψ(o_t)` cannot infer episode-specific parameters absent from `o_t`
… If Ψ is given history to fix this, it has become a history encoder — the student under another name."
Labelled "(decisive)" and re-asserted in §8.3 ("the information argument stands").

**Three separate defects.**

1. *Scope inflation.* The data-processing inequality supports exactly one conclusion: Ψ cannot **add**
   environment information that is absent from `o_t`. It says nothing about whether Ψ makes the
   information that *is* present easier to exploit at finite capacity, finite samples, and finite
   optimization steps. The entire representation-learning literature — and KIPPO/SKooP specifically,
   which the doc accepts in §8 — rests on information-preserving transforms improving *optimization
   geometry and sample complexity*, not information content. Using an invariance-of-information
   theorem to reject a representation intervention is a category error, and it is the same error the
   doc correctly diagnoses in the user's proposal ("Koopman linearity is about time evolution").
   Classification: **OVERREACH → WRONG as a blanket "cannot help".** It is TRUE only for the narrow
   claim "Ψ cannot recover the encoder's privileged channel."

2. *False dichotomy, contradicted by the doc's own §3.* "Fixed pointwise transform" vs "history
   encoder" is not a dichotomy here, because `o_t` **already contains 46–52D of delay embedding**
   (§3, §10: 30D tracking history stride-3 ×3, 16D action history ×2, 3D integral, 3D bias-EMA).
   A "pointwise" Ψ on `o_t` is therefore *already* a short-window history encoder. The doc's own §10
   Axis A makes this point explicitly ("our 72D o_t is already a hand-designed partial delay
   embedding"). So §5.2's clean split — and the "it becomes the student by another name" dismissal —
   does not survive contact with §3. The real question is window length vs identifiability, which is
   a quantitative question the doc never asks in §5.

3. *Internal contradiction.* §8.3 keeps Proposal 2 "unsupported" on the strength of the information
   argument, while §8.4 item 4 prescribes the arm set `{TRPO baseline, TRPO+phi_x, NoEncoder,
   NoEncoder+phi_x}` — i.e. it recommends running the steelmanned Proposal 2 (`NoEncoder+phi_x`) as a
   screening arm. Either the information argument kills that arm or it doesn't. As written the doc
   both forbids and schedules it.

**What the doc should say instead.** "Ψ cannot restore the encoder's privileged channel (DPI). Whether
Ψ improves the *achievable* partially-observed policy is an empirical question with published positive
precedent (KIPPO) and is exactly what the `NoEncoder` vs `NoEncoder+phi_x` pair tests."

---

## THEO-2 (critical) — §13.1 "resolved AGAINST pure affine" overstates [97], mis-attributes KCF, and silently discards the opposite verdict from its own source report

**Attacked text.** §13.1: "[97] Theorem II.1 + Corollary: control-affine plant with state-dependent
input gain … admits a bilinear realization over generic dictionaries, but **NO linear realization at
any dictionary size**"; heading "resolved AGAINST pure affine"; and the KCF reading "the additive form
equals `Psi+ = A(u) Psi` only with input-dependence confined to the inhomogeneous column (**Lemma 4.5's
affine special case**)".

**(a) The non-existence claim is not a theorem.** `cluster_coherent_bilinear.md` states [97] Cor. II.1
as: every control-affine system admits a (possibly infinite-dim) *bilinear* realization over any basis,
and "**no such guarantee exists** for a linear realization". Absence of a guarantee ≠ proof of
non-existence. The source report's own wording for the empirical arm result is hedged — "a linear
realization for this system **likely** does not exist" — an inference from a flat error curve
(0.55–0.60 over 10→927 basis functions) on a 3-link arm. The doc hardened "no guarantee / likely not"
into "NO linear realization at any dictionary size". Classification: **OVERREACH (stated as a theorem
it is not).**

**(b) The KCF attribution is wrong in both directions.** With an augmented constant coordinate,
`phi_x(o+) = K phi_x(o) + B phi_u(a)` is `Psi+ = A(u) Psi` with
`A(u) = [[K, B phi_u(u)],[0,1]]` — u-dependence confined to the inhomogeneous column. That is **not**
Lemma 4.5's case: Lemma 4.5 (per `cluster_separable_theory.md`) is `A(u)` **affine in u**,
`A + Σ u_i B_i`, which has u multiplying the *state* block. With a nonlinear `phi_u`, the doc's form is
neither affine-in-u (so not Lemma 4.5) nor Th. 4.3-general (so the source cluster's opposite reading is
also wrong). The correct statement is: it is the *inhomogeneous-column-only* sub-family — strictly
weaker than bilinear in state-coupling, strictly richer than affine-in-u in input dependence. The doc's
substantive conclusion (the missing ingredient is *state*-dependence of the input effect) is right; the
theorem it hangs it on is misquoted.

**(c) The "reconciliation" is an unacknowledged override.** `cluster_separable_theory.md`'s bottom line
is the *opposite* verdict: "the survey's cited works do **not** argue for switching to bilinear or
switched forms on nonlinearity grounds alone — a sufficiently expressive learned `phi_u` inside an
affine composition is theoretically adequate for the static deadband/quadratic nonlinearity per [36]'s
own general theorem", and its point 5 recommends "keeping the affine-in-lifted-action design **as an
engineering default**". §13.1 presents the disagreement as "they reconcile as follows" and then adopts
one side while labelling the other a "correction on cross-check". Since the correction (b) is itself
inaccurate, the override is unearned. A reader of §13.1 alone cannot tell that half the evidence base
concluded the reverse.

**(d) Decisive for our use case: fidelity is the wrong criterion for an aux representation loss.**
Every number cited in §13.1 is a *model-fidelity-for-model-based-control* number: MPC tracking error
(74.3 vs 2.03 cm), NMPC success rate under input-scaled disturbance, open-loop prediction error. In the
KIPPO role the aux model is a **soft regularizer whose gradients shape `phi_x`**; it is never rolled
out, never inverted, never optimized against. The doc knows this — §8.4-2 calls linearity "an inductive
bias, not exact model", and §16.1 argues the representation role needs neither PE nor a global K. A
non-existence-of-exact-realization result therefore does not resolve the design question in the
representation role; at most it says "the affine residual will not go to zero", which for a regularizer
is not obviously bad (a nonzero-residual, harder-to-satisfy constraint is a *stronger* bias; a bilinear
`H` term makes the constraint *easier* to satisfy and thus the bias *weaker*). "Resolved AGAINST pure
affine" does not follow for our use case. Classification: **WRONG as a resolution for the aux-loss
role; TRUE only for the (unproposed) model-based role.**

**Consequence.** §13.1's "design update (supersedes the plain-affine sketch)" installs a bilinear `H`
term with sparsity discipline into the shortlisted screening arm on the strength of (a)+(b)+(d). That
extra machinery is unjustified at screening time and violates the doc's own single-variable discipline
(§11.1). Affine-vs-bilinear is a follow-up ablation, not a prerequisite.

---

## THEO-3 (major) — §4.2 and §8.3 both assert `p_{t+1} = p_t`; the code says 6 of 28 dims are time-varying, and the eigenvalue-1 steelman is a non-sequitur anyway

**Attacked text.** §4.2(2): "within an episode `p_{t+1} = p_t` (trivial identity dynamics), so every
function of `p_t` is a Koopman eigenfunction with eigenvalue 1. There is nothing to linearize."
§8.3: "constant-per-episode DR parameters ARE Koopman eigenfunctions (eigenvalue 1) of the episode's
extended system, so 'Koopman can express parameter inference from history' is **formally true**."

**(a) Factually false for ≥6 of 28 dims — and the doc's own §3 says so.**
`observations.py:89-192`: `p_t[19:22]` is `env._hydro.current.velocity_w[:, :3]` and `p_t[25:28]` is
`env._robot.data.root_lin_vel_b`. Measured body linear velocity is a *fast state*, not a parameter;
and the ocean current is driven by an OU process when `cfg.ou_enable` (`albc_env.py:698, 918-932`,
`_ou_base_current`), i.e. genuinely time-varying within the episode. §3 records the exception
("constant-per-episode except current/measured-vel") and then §4.2/§8.3 drop it. Since `z` is
recomputed every step from `p_t` (`actor_critic_encoder.py:219`), `z` has non-trivial dynamics.
"Nothing to linearize" is **WRONG** as stated; the 22 constant dims are trivial, the other 6 are the
only dynamically interesting ones and they are exactly the ones the eigenvalue-1 argument does not
cover.

**(b) The steelman is a non-sequitur even where the constancy holds.** Being an eigenvalue-1
eigenfunction of the *extended* system `(x, θ)` is trivially true of every function of θ and carries
**zero** information about whether θ is recoverable from the *output* `o_t` history. Recoverability is
an observability/identifiability property of the pair (dynamics, output map) under the visited input
distribution — a Takens/adaptive-observer question, not a spectral one. "Koopman can express parameter
inference from history is formally true" is therefore not formally true as written: what is formally
true is "θ is an invariant of the extended flow", which is a tautology (θ is a constant). The doc then
uses this pseudo-result to conclude the student should be kept — a conclusion I agree with, reached by
an argument that proves nothing. Classification: **OVERREACH (vacuous premise dressed as a theorem).**

**(c) §4.2 answers a question the proposal did not ask.** The user's Proposal 1 wants a feature map on
`p_t` for the *encoder's regression*, which is a static approximation-theory question. §4.2 rebuts it
with a *dynamical* triviality result. The dynamical argument is correct and the rebuttal is still
roughly right (via the UAT-style argument in §4.4 — but see THEO-5), but §4.2 as written is a
non-sequitur for the claim it is placed under.

---

## THEO-4 (critical) — §9 priority-1 recommendation (student Koopman-consistency term) is near-vacuous on this system: `K = I` is the optimum

**Attacked text.** §9, category 6 and priority ranking item 1: "NEAR-TERM training-side probe: student
Koopman-consistency term (cat 6, supervised-only) — smallest diff, rides existing distillation targets",
loss `||K z_hat_t - z_hat_{t+1}||^2` against logged teacher z-sequences. Repeated in §10's
"Updated shortlist" item 2.

**Why it fails, quantitatively.** The teacher latent is `z_t = softsign(LN(enc(p_t)))` with 22 of the
28 `p_t` dims literally constant within an episode. Therefore `z_{t+1} ≈ z_t` for the overwhelming
majority of the signal energy, and the global minimizer over `K` of `||K z_t - z_{t+1}||²` on such
sequences is `K ≈ I`. The term collapses to a temporal-smoothness penalty on `z_hat` with a learned
near-identity gain — it contains no Koopman content whatever, because the "dynamics" it is asked to
discover are the identity by construction.

**The non-constant residue makes it worse, not better.** The 6 time-varying dims (OU current,
measured lin-vel) are driven by the vehicle state and the actions — they are *not* an autonomous
function of `z`. An operator `K` acting on `z` alone is structurally incapable of predicting them; the
loss on those dims is irreducible and its gradient is noise injected into the student's head. Fixing
that requires conditioning on `o_t`/`a_t`, at which point the term stops being "no new loss class /
smallest diff" and becomes a full aux dynamics model on the student.

**Actively harmful branch.** A smoothness penalty on `z_hat_{t+1} - z_hat_t` directly opposes the one
thing the student must do well: converge fast at episode start, when it has no history and must swing
`z_hat` from prior to plant estimate. The doc's own campaign memory records the student's
identification transient as the live issue (observability retrain). This item should be reclassified
from "priority 1, smallest diff" to "rejected on structural grounds" unless someone first shows the
teacher `z` sequences have non-identity temporal structure — a 20-line check on already-logged data
that the doc never proposes.

---

## THEO-5 (major) — §4.4 universal-approximation non-sequitur (same error class as THEO-1)

**Attacked text.** §4.4: "A fixed nonlinear expansion feeding a universal-approximator MLP adds no
capacity the MLP lacks." §4 steelman: "Expected effect: small; MLPs learn such features readily."

UAT is an existence statement about *weights*, not about what SGD finds in 2000 iterations from a given
initialization with a given data distribution. Explicit feature maps change the induced
kernel/NTK, the conditioning of the optimization, and the sample complexity of the target function —
which is why physics-informed features routinely help finite-budget learners. Note the doc's own
evidence base contains a direct counterexample: `cluster_underwater_row.md` / §13.4's marine
dictionaries (signed-quadratic `v|v|`, arctan(vy/vx)) are exactly "features an MLP could learn" that
measurably help in the cited work. "No capacity added" is TRUE and irrelevant; "therefore no effect" is
a non-sequitur. Since this plank supports the Proposal-1 NOT-SUPPORTED verdict — which §8 only
*partially* revised (the fixed-dictionary sub-case was never revisited) — it is load-bearing.
Classification: **OVERREACH.**

---

## THEO-6 (major) — §16.1 "persistent excitation not required" conflates plant diversity with input excitation, and contradicts §4.4(ii)

**Attacked text.** §16.1: "PE is a least-squares system-ID requirement for identifying a global K; the
representation role only needs coverage of the state distribution the policy visits … DR at 4096 envs
(payload/current/fault) supplies plant diversity no excitation signal on real hardware could match."

Three problems.

1. **Plant diversity ≠ excitation.** PE is a rank/conditioning property of the *input* sequence
   conditional on the state. Randomizing the plant across envs does not excite the input channel; if
   anything it makes a single `(K,B,H)` fit worse-conditioned by mixing regimes (the doc's own §13.2
   point). The sentence is a non-sequitur w.r.t. PE.
2. **The representation role is not excitation-free, because the loss shapes `phi_x`.** `phi_x` is
   trained *by* the prediction residual. If the data cannot distinguish operators, the residual is
   minimizable by degenerate representations — which is precisely §4.4(ii)'s own observation that
   lifted-space prediction alone has trivial optima (constant Ψ). Degenerate optima *are* an
   identifiability failure. §16.1 asserts identifiability is irrelevant here without reconciling with
   §4.4(ii).
3. **Timing.** On-policy action entropy *decreases* as TRPO converges, so the input-channel
   informativity is worst exactly in the late-training regime §16.2 Stage-1 says concurrent training
   exists to serve. "Early-training policy is near-random (natural excitation)" argues for the Stage-0
   pretrain, not against PE mattering.

Classification: **OVERREACH.** Defensible restatement: "`phi_x` needs state-distribution coverage, not
PE; the *operator* `(K,B,H)` needs excitation, and since it is only a scaffold, its under-identification
weakens rather than corrupts the bias — with the caveat that a weakly-identified scaffold gives a
weakly-defined inductive bias, which is a null-result risk for the arm."

---

## THEO-7 (major) — §16.2 "TRPO's KL constraint already bounds representation drift" is mechanically false

**Attacked text.** §16.2 Stage 1: "TRPO's KL constraint already bounds per-update policy shift against
representation drift."

TRPO's trust region constrains `D_KL(π_old(·|s) ‖ π_new(·|s))` on sampled states with the *network
inputs held fixed*. If `phi_x` is updated concurrently, the map `o ↦ π(·|o)` changes without consuming
any KL budget: the constraint is enforced on `π(·|y)` while the deployed policy is `π(·|phi_x(o))`.
Worse, the sampled old log-probs were computed under `phi_x_old`, so the KL actually measured after a
`phi_x` update is not the KL between the old and new deployed policies — the trust region is silently
violated, in an amount nobody is measuring. The same staleness hits the value function and the IPO cost
critics (their inputs moved), which is the mechanism by which representation drift usually shows up as
constraint-violation spikes rather than as reward loss.

This matters because §16.2 offers the KL constraint as the *reason* concurrent training is safe on our
stack (KIPPO used PPO, whose clipping has the identical hole). Minimum fix to state in any proposal:
update `phi_x` only *between* TRPO iterations, stop-grad the policy loss into `phi_x` (KIPPO's
"decoupled" recipe already implies this), and recompute the reference policy/critic targets after each
`phi_x` step — or add a representation-drift term to the KL estimate. Classification: **WRONG.**

---

## THEO-8 (major) — §13.2 / §11.1 `K(z)` is not well-posed as stated: it needs a sufficiency assumption, a stop-gradient, and a stationary index

The doc's fix for the DR-family problem is `K(z), B(z)` via a small hypernetwork (§13.2 item 1,
§11.1 staging "bypass → K(z) → phi_x(o,z)"). The §13.2 diagnosis is correct and well-supported ("a
single fixed `(K,B,H)` assumes one lifted subspace jointly invariant across the ENTIRE DR distribution
— stronger than any cited theorem guarantees" is TRUE and matches `cluster_separable_theory.md` point
2). The proposed remedy has three unstated conditions.

1. **Sufficiency.** A family `{K(θ)}` indexed by the *true* parameter is well-posed (it is exactly
   KCF's per-mode operator family). Indexing by `z` is well-posed only if `z` is a sufficient statistic
   of θ for the lifted dynamics. Nothing enforces that: `z` is a 9D softsign-squashed compression of
   28–34D trained *solely* through the policy objective, so it is free to discard distinctions that are
   control-irrelevant but dynamics-relevant. If two plants map to the same `z`, `K(z)` is a
   well-defined function that is nonetheless the wrong operator for at least one of them, and the
   prediction residual will be blamed on model form. The project's documented z-collapse history makes
   this the expected case, not a corner case.
2. **Gradient path.** Unless `z` is stop-gradded into the hypernetwork, `K(z)` puts an auxiliary
   dynamics loss **on the p_t→z encoder** — squarely inside the settled No-Encoder-Auxiliary-Losses
   rule that §8.4-1 carefully argues around for the obs-side module. §8.4-1's argument ("phi_x is a new
   module, not covered by the rule's letter") does not extend to `K(z)`, and the doc never notices.
3. **Moving index.** `z` is non-stationary during training (the doc's own z-drift/KL-spike incident,
   §11.2), so the hypernetwork regresses on a drifting index; combined with the standard gauge freedom
   (`phi → Tphi, K → TKT⁻¹`, plus any reparameterization of `z` absorbed by the hypernetwork), nothing
   about the fitted `K(·)` is identifiable or interpretable. Prediction can still work; the "parameter-
   varying operator" reading the doc attaches to it cannot.

---

## THEO-9 (major) — the single-K objective is not neutral under DR: it is an *invariance pressure* that strips exactly the env information this project needs

**Attacked text.** §8.4-2: "one (K,B) fit across 4096 randomized plants averages dynamics; as a soft
regularizer this **may just weaken**." §4.4(iii): "the residual carries **exactly** the env information
the encoder exists to capture."

The "may just weaken" framing treats mis-specification as isotropic noise. It isn't. With a *single*
shared operator, any feature of `phi_x` whose one-step evolution depends on θ incurs irreducible loss,
while θ-invariant features incur none. The minimizer therefore *prefers plant-invariant features* — the
aux objective is a domain-invariance regularizer on `phi_x`. For a project whose stated research focus
is sim-to-real adaptation under a 28D DR + thruster faults, systematically pushing the policy's input
representation toward plant-invariance is a directional risk the doc never names, and it is the most
plausible mechanism by which a KIPPO arm could *hurt* here while helping on undomain-randomized MuJoCo.
It also interacts with the student: if the actor consumes `phi_x(o_t)` and `phi_x` has been
invariance-regularized, the deployed adaptation channel narrows to `z_hat` alone.

Separately, "the residual carries **exactly** the env information the encoder exists to capture" is
unjustified — a mis-specified model's residual carries *some* θ-correlated signal, mixed with
approximation error of the lift; "exactly" is rhetorical.

Design consequence the doc should draw (either direction is defensible, but it must be chosen): use
`K(z)` (with THEO-8's caveats), or exclude adaptation-relevant blocks from the prediction target, or
accept the invariance pressure and predict a *null-to-negative* result rather than the doc's implied
upside.

---

## THEO-10 (major) — §8.3/§8.4 launder KIPPO's marketing line into a mechanism, then propose measuring a quantity nobody claimed, without the decisive control

1. **No mechanism.** "Locally-linear latent dynamics → smoother/lower-variance policy-gradient
   optimization" (§8.3) has no theorem behind it, and the doc's own §8.1 correctly labels it a
   *claimed* mechanism quoted from the paper ("reduces gradient variance specifically in critical
   regions"). §8.3 then promotes it from quotation to "the honest mechanism hypothesis". Policy-
   gradient variance is a property of the score function and the advantage estimator; a representation
   change alters the Fisher geometry, which is a *plausible* pathway, but "latent dynamics are linear"
   → "gradient variance drops" is not derivable. Classification: **UNVERIFIABLE, presented as
   mechanism.** Honest wording: "unexplained empirical effect with published replication on MuJoCo."
2. **Metric mismatch.** §8.4-4 makes "gradient variance" a primary screening metric. KIPPO's reported
   26–91% "variance reduction" is *return* variance across 4 trials — a different quantity, and one a
   single-seed screen (the project's convention, correctly noted in §8.4-4) structurally cannot
   measure. The doc thus proposes a metric that measures neither the paper's claim nor a quantity the
   arm design can resolve.
3. **Missing control.** The prescribed arm set `{baseline, +phi_x, NoEncoder, NoEncoder+phi_x}` cannot
   attribute any effect to *Koopman structure*: an expansive `phi_x` also changes input dimensionality,
   effective width, and (per §11.2) the normalizer. The decisive control is `phi_x` of identical size
   trained **without** the Koopman prediction loss (plain AE, or a frozen random expansion). Without
   it, a positive result is uninterpretable and a negative result cannot distinguish "Koopman doesn't
   help" from "our `phi_x` was badly conditioned". This is a strict requirement of the doc's own
   single-variable discipline (§11.1) that the doc violates.

---

## THEO-11 (major) — §10 Axis A: "window must match the parameter timescale" is a non-sequitur, and it is the stated reason for dropping the HVOK axis

**Attacked text.** §10 Axis A: "a fair test needs windows matched to parameter timescales (currents
~O(10s), faults episode-long) — orders longer than the current 9-physical-step embedded history, i.e.
new infrastructure, not a drop-in arm." (Consequence: §10's shortlist drops the HVOK variant.)

A constant parameter has *no* timescale; the window needed to identify θ is set by how quickly the
dynamics **reveal** θ under the visited inputs (an excitation/observability question), not by how slowly
θ varies. If anything the implication runs the other way: an episode-long-constant fault is the
*easiest* case, because every sample in the window is informative about the same θ. The doc's own
Axis C cites the counterexample: RMA's adapter identifies episode-constant parameters from a 50-step
history. So the premise ("orders of magnitude longer window required") does not follow from the
observation ("faults are episode-long"), and the drop decision rests on it.

Secondary: "Slow-PARAMETER recovery from delay embedding ALONE is NOT established" (§10) is accurate as
a statement about the *Koopman/HAVOK* literature (`axis_hvok_delay.md` §1 is careful and honest about
this). But framed as a theory gap it is misleading: recovery of a constant parameter from output
history is classical nonlinear observability of the parameter-augmented system (adaptive observers,
identifiability analysis) — well-established theory outside the Koopman banner, with the binding
condition being *identifiability under the visited input distribution*, not the existence of a
paper. The doc treats "no Koopman paper says it" as "not established", which overstates the theoretical
uncertainty. Classification: **OVERREACH (non-sequitur premise) + scope error on "not established".**

---

## THEO-12 (major) — §15.3 gap meter is not identified: EDMD spectra depend on dictionary AND sampling distribution, and the proposed noise-floor control does not cover the latter

**Attacked text.** §15.3 / §11.6: `K_sim` vs `K_real` spectral distance on watertank datasets as "a
QUANTITATIVE per-axis sim-to-real gap meter", ranked APPLICABLE-NOW and novel, with the caution
"validate the meter's own noise floor (e.g. `K_sim`-vs-`K_sim` across seeds/data splits)".

An EDMD operator is a *projection of the Koopman operator onto a dictionary, weighted by the empirical
data measure*. Two fits therefore differ for three reasons: (i) the plant differs (what we want to
measure), (ii) the dictionary is not invariant (approximation error, differs by data region), (iii) the
trajectories were generated by different controllers/maneuvers/initial conditions, so the sampling
measures differ. Real watertank logs and sim rollouts differ maximally in (iii). The proposed control —
`K_sim` vs `K_sim` across seeds/splits — holds the input distribution *fixed*, so it calibrates only
sampling noise, not distribution mismatch. As specified, the meter is confounded and will report a large
"gap" for a perfectly matched plant driven by a different controller.

The fix is cheap and should be in the doc: replay the *real* input sequences and initial conditions in
sim, fit `K_sim` on that replay, and use `K_sim(replay)` vs `K_real` as the gap; add
`K_sim(replay)` vs `K_sim(on-policy)` as the distribution-mismatch control. Without it, this
"APPLICABLE-NOW, zero-risk, novel-contribution" item is not measuring what it claims.

---

## THEO-13 (minor) — §11.2 normalization: the p_t remedy does not transfer to o_t block-wise, and bundling it into the arm is a second confound

"Replace running-stat EmpiricalNorm with static DR-derived min-max at `phi_x` input + bounded (tanh)
output" transfers from the `p_t` encoder only because every `p_t` dim is drawn by the DR sampler and so
has a known support. `o_t` does not: the 3D integral error is a leaky accumulator and the 3D bias-EMA is
a filter state (`albc_env.py:384-387`) — neither has a DR-derived bound; the tracking-history and
action-history blocks have known ranges but the integral/EMA blocks need clipping or per-block
treatment. Also: a normalizer swap is an independent intervention. Shipping it inside the same
screening arm as `phi_x` violates the single-variable discipline §11.1 asserts one paragraph earlier
(see THEO-10 item 3).

---

## THEO-14 (minor) — §10 Axis B half-reads Koehler, and the resulting design carries two mutually redundant justifications

§10 Axis B: "Koehler arXiv 2207.12132 (lifting state-only provably yields LPV input matrix — justifies
keeping u raw)". An LPV input matrix means `B = B(x)` — *state-dependent input gain*, which is the
bilinear coupling §13.1 spends a page arguing for. Cited as "justifies keeping u raw" it supports
dropping `phi_u`, yet §13.1's design update keeps `B phi_u(a)` **and** adds `H(phi_u ⊗ phi_x)`. Either
the input encoder or the state-dependent gain is doing the work; the doc should say which, or the
screening arm carries redundant parameters whose contributions cannot be separated.

---

## THEO-15 (minor) — §5.2 "carries exactly the information" should be "at most", and the difference is not harmless

A transform carries the same information only if injective. §11.3 explicitly contemplates a *small* `m`
("our 72D obs is partially pre-lifted, so try smaller m first") — i.e. a compressive `phi_x`, which
strictly *loses* information. For the `NoEncoder+phi_x` arm that is a live failure mode (the policy's
only env channel is `o_t`; a lossy `phi_x` can destroy it), and the doc's information framing —
built on an "exactly" that assumes neutrality — never raises it. The anti-collapse guard the doc adopts
from [50] (`z = [x, g'(x)]`, §14.2) happens to fix this, but as an unremarked side effect; and if
identity-inclusion is adopted, the arm is no longer "lift vs no lift" but "extra features appended",
which is a different (and weaker) test of KIPPO's claim than KIPPO ran.

---

## What survives

- §4.1 (Koopman linearity is about time evolution, not the obs→action map) — TRUE, correctly the
  central rebuttal, and the doc states it precisely.
- §13.2 item 1 (a single fixed operator across the DR distribution is stronger than any cited theorem
  guarantees) — TRUE and well-sourced. The *remedy* is what needs the conditions in THEO-8.
- §13.2 item 2 (ESC filter + latency is a Markovity problem, not a model-form problem) — TRUE and the
  most useful engineering observation in the document.
- §13.3 (CCK verdict: exactness precondition fails between filter and rigid body; the transferable part
  is the phantom-pathway failure mode) — well-argued, correctly narrower than the survey's gloss.
- §14.2 ([50]'s "domain shift" is not DR) — a genuine load-bearing correction, correctly flagged.
- §15.1 (white-space claim, scoped as absence-of-evidence) — appropriately hedged.
- §16.3 ([100] active learning does not transfer because it hijacks the policy's actions) — correct and
  non-obvious.
