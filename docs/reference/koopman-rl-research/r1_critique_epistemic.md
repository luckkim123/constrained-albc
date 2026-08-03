# Adversarial Critique — EPISTEMIC lens

Target: `/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md` (639 lines, read in full)
Reviewer stance: adversarial, symmetric skepticism. Nothing in the target was edited.
Spot-checks performed live during this critique: 4 web searches / 2 direct paper fetches, 3 repo greps,
3 omx-wiki page reads.

---

## Executive verdict

The doc is a genuinely strong literature harvest with a weak epistemic spine. Three structural
problems:

1. **The Sec 4 → Sec 8 flip is ~1/3 evidence, ~1/3 rule-reinterpretation-after-push-back, ~1/3
   unresolved-but-endorsed-anyway** — and the doc presents all three as evidence. It is not a pure
   capitulation, but the honest label is not "VERDICT PARTIALLY REVISED [by new literature]".
2. **The doc is organized around a brand, not a mechanism.** The exact mechanism KIPPO claims —
   expansive auxiliary-dynamics-prediction representation consumed by the RL agent — was published
   as OFENet at ICML 2020 (arXiv 2003.01629) and has a five-year comparison literature plus a
   dedicated theory paper (arXiv 2406.17718) the doc never touches. Nothing in the shortlist
   isolates the only testable content of the word "Koopman" (the *linearity* restriction).
3. **Verdict inflation across sections.** Every shortlist item ends the document with a stronger
   label than the evidence that produced it, and every caveat attached at first statement is
   dropped by Sec 15.4. This is narrative momentum, and it is measurable — I list four instances.

Both directions get hit: Sec 5's "decisive" information argument is a bad argument that its own
document contradicts, and Sec 15.4's "APPLICABLE-NOW, zero training-side risk" gap meter is defeated
by three facts already in this project's own wiki.

---

## THEO-1 (critical) — The Sec 4 → Sec 8 flip: adjudicated

**Target**: Sec 7 decision log ("VERDICT PARTIALLY REVISED"), Sec 8.3 "REVISED", Sec 15.4 item 1
("mechanism precedent solid").

**The tension the task names is real, and the doc's own resolution is incomplete.** Sec 4.4 listed
three named disqualifiers for a learned lifting. Score them against what Sec 8 actually supplies:

| Sec 4.4 disqualifier | Does Sec 8 defeat it? | With what? |
|---|---|---|
| (i) "auxiliary representation loss — the exact family the project's settled rule bans" | **No — reinterpreted, not defeated.** Sec 8.4.1 narrows the rule to "the p_t→z encoder … not covered by the rule's letter" | A re-reading of `.claude/rules/03` ("Encoder에 auxiliary loss … 절대 금지"). I checked the rule text: the scope argument is *defensible on the letter*. But it needed **zero new evidence** and was fully available when Sec 4 was written. The only input that changed between Sec 4 and Sec 8 on this point is user push-back. |
| (ii) "lifted-space prediction alone has trivial optima; the standard fixes are reconstruction (the failed path) or identity-inclusion" | **Yes, partially — this is the one genuinely evidential move.** KIPPO's expansive (m = 2–4n) autoencoder makes reconstruction easy where the project's compressive 9D z failed | Legitimate new information. See THEO-8 for why it is weaker than stated. |
| (iii) "under DR there is no single K … one shared K averages over plants" | **No.** Sec 8.4.2 concedes verbatim: "DR-single-K tension remains" | Nothing. The arm is endorsed with a named unresolved defeater. |

**So the correct label is not "revised by newer literature".** What KIPPO/SKooP genuinely defeat is a
premise Sec 4 never stated — "nobody has fed a Koopman-lifted observation to an RL actor". That is a
real and useful correction, and the underlying process failure it exposes is worse than the flip:
**Sec 4/5 issued "NOT SUPPORTED / category error" verdicts from a single survey with no literature
search at all.** The doc blames the survey's bibliography window (Sec 8.1); the defect is the
review's, not the survey's. A verdict that dissolves on the first web search was never entitled to
the word "decisive".

**Third position on KIPPO's weight (the task invited one, and the evidence supports it).** Verified
live: KIPPO is IJCAI 2025 proceedings #556 / arXiv 2505.14566, and is derived from Cozma's UT
Knoxville **MS thesis** (trace.tennessee.edu/utk_gradthes/11783). Compute footnote: "one complete
set of **24 runs**" = the doc's 4 trials × 6 envs. So the entire Sec 8 revision, and the #1 shortlist
slot, rests on: one MS-thesis-derived paper, 4 seeds/env, MuJoCo/Box2D, PPO (not trust-region-
constrained), **no DR, no constraints, no asymmetric critic**, and a claimed mechanism ("reduces
gradient variance specifically in critical regions") the doc records but never checks against the
paper's own evidence. Under this project's own standards — `rules/03` "No Premature Assertions",
"Multi-run Trajectory Comparison (not last value)", and the `feedback-sign-consistency-is-not-
magnitude` memory — that is a *single weak study*, exactly the evidence class the project routinely
refuses to act on internally.

**Sharpest sub-finding: SKooP is cited as support when its design decision is counter-evidence.**
Sec 8.2 records that SKooP feeds the Koopman prediction **to the critic only** and quotes "the actor
only requires x_k as input." A team that built the whole Koopman autoencoder and then deliberately
kept it out of the actor is evidence *against* actor-side lifting, or at minimum evidence that the
critic-side variant is the safer bet. The doc files it as a "critic-side sibling" supporting the
revision (Sec 8.3) and never runs the obvious inference. Note also that the doc's own Sec 9 cat-1
row carries a hard negative for actor-side Koopman terms (LC-SAC: all Koopman-Lyapunov variants
**underperform vanilla SAC by 8–15%** on the 3D quadrotor, the closest underactuated analog, with
the reward-shaping variant at −93%) — and that negative never reaches Sec 15.4's ranking discussion.

**Position the evidence actually supports**: "One weak-but-real precedent exists for actor-side
lifting; one adjacent team with the same machinery chose critic-only; one adjacent result is
strongly negative for actor-side Koopman terms in underactuated flight. A cheap screening arm is
defensible *as curiosity*, ranked below the critic-side variant, and 'mechanism precedent solid'
(Sec 15.4) is an unearned upgrade over Sec 8.3's own 'a 2000-iter screening arm is defensible'."

---

## THEO-2 (critical) — Missing comparison class: the doc is framed around a brand

**Target**: whole-document framing; Sec 8.3's mechanism hypothesis ("locally-linear latent dynamics
as an inductive bias → smoother/lower-variance policy-gradient optimization"); Sec 15.4 item 1.

Verified live: **OFENet — Ota, Oiki, Jha, Mariyama, Nikovski, "Can Increasing Input Dimensionality
Improve Deep Reinforcement Learning?", ICML 2020, arXiv 2003.01629.** Mechanism: an auxiliary
next-observation-prediction loss trains an **expansive** feature network whose output the RL agent
consumes instead of the raw state; the paper's headline is that higher-dimensional learned inputs
improve sample efficiency. That is KIPPO's architecture, KIPPO's claimed benefit, and KIPPO's
expansive-latent choice — **five years earlier, without the word Koopman.**

Strip the brand and KIPPO = OFENet + a *linearity restriction* on the latent transition. The
linearity restriction is the entire testable content of "Koopman" here. **No arm anywhere in the
doc isolates it.** Sec 8.4.4 and Sec 15.4 propose `{TRPO, TRPO+φ_x, NoEncoder, NoEncoder+φ_x}` —
every arm with a lift has the linearity constraint, so a positive result cannot distinguish
"Koopman helps" from "any latent-dynamics auxiliary task helps" from "a wider first layer helps".
That is the reviewer-fatal design flaw, and it follows directly from framing the hypothesis space as
"Koopman lifting" rather than "auxiliary latent-dynamics prediction, with/without a linearity
constraint".

The unsurveyed comparison class (existence verified for the two load-bearing ones):
SPR (Schwarzer et al.), SAC-AE, DreamerV3, TD-MPC2 latent consistency, OFENet, and the theory paper
**Voelcker et al., "When does Self-Prediction help? Understanding Auxiliary Tasks in Reinforcement
Learning", arXiv 2406.17718** — which analyses exactly this family under a linear model and finds
latent self-prediction helpful *as an auxiliary task alongside TD learning*, while reconstruction is
the better standalone objective. That paper is the single most decision-relevant citation for this
document and it is absent.

**Consequence for the doc's status**: as written, Sec 8–16 is a related-work section about a brand.
The mechanism-level literature is much larger, older, has its own theory, and has known negative and
mixed results (see THEO-3) — none of which is surveyed. Recommended minimum repair: add an
unconstrained-latent-predictor control arm, and re-title the hypothesis in mechanism terms.

---

## THEO-3 (critical) — Sec 16.2's trust-region claim is backwards, and it is load-bearing

**Target**: Sec 16.2 stage 1 — "TRPO's KL constraint already bounds per-update policy shift against
representation drift (Sec 11 homework item 2)". Also Sec 8.4.3's framing of the same issue as a
"watch" item.

Verified live by direct fetch of **Moalla, Mahmoud, Tirinzoni, Lazaric et al., "No Representation,
No Trust: Connecting Representation, Collapse, and Trust Issues in PPO", arXiv 2405.00662
(NeurIPS 2024)**: the paper finds representation collapse / feature-rank deterioration and trust-
region degradation are **mutually reinforcing**, and states the trust region "cannot alleviate or
prevent the collapse" — the paper's entire contribution (PFO) exists because the trust region is
*insufficient* here. The doc asserts the opposite as the reason concurrent training is safe.

This is not a citation nitpick. ALBC's algorithm is trust-region-based (ConstraintTRPO), the doc
proposes to put a **drifting learned representation underneath it**, and Sec 16.2 discharges the
resulting risk with a claim the literature contradicts. The KL constraint is computed in policy-
*output* space; it bounds nothing about the geometry of φ_x's output space between updates. A φ_x
update can move the actor's input manifold arbitrarily while the measured policy KL stays inside the
trust region — the trust region will report health while the thing it is measuring has changed
meaning.

**Second, compounding**: Sec 16.2 stage 1 adopts KIPPO's **decoupled** optimizer (aux loss does not
touch the policy objective). Voelcker et al. (2406.17718) is precisely about this axis and finds
self-prediction's benefit is tied to being learned *alongside* TD/value learning; in isolation it
underperforms reconstruction as a feature learner. The doc never states whether policy gradient
flows into φ_x, which is the single most consequential unresolved design choice in the proposal, and
it has directly relevant literature the doc did not consult.

---

## THEO-4 (critical) — Shortlist #2 (gap meter) "APPLICABLE-NOW, zero training-side risk" is not supported

**Target**: Sec 15.3, Sec 15.4 item 2, Sec 11.6 third option.

Sec 15.4 says the meter "needs only logged trajectories + EDMD fits + the S-G-W metric with a
noise-floor control." Three defeaters, all from this project's own omx wiki (read live):

1. **The real plant is not observable enough to fit K_real.** Wiki page
   `sim_hydro_nominal_is_analytical_not_measured…`: "HARD SENSOR CONSTRAINT (real robot): IMU +
   pressure ONLY. No DVL. … Horizontal linear velocity (surge/sway u,v) is NOT [observable]." EDMD
   needs state (or a delay embedding of measured outputs) plus synchronized inputs. K_real is
   therefore identifiable at best on the rotational + heave subspace — **not** the operator that
   K_sim would be compared against. The doc never mentions the sensor suite.
2. **Sampling/staleness mismatch would dominate the spectral distance.** Wiki page
   `real_albc_deployment_state_estimation_rates_measured_from_code…`: attitude+gyro **≤ ~25 Hz** ZOH,
   joints **10 Hz**, control 50 Hz — "the real policy runs on zero-order-held stale observations."
   Koopman eigenvalues are sample-rate-dependent by construction (λ_disc = e^{λ_cont Δt}), and ZOH
   staleness at a different rate than sim changes the identified operator outright. A spectral
   distance between operators fit at different effective Δt with different staleness measures the
   instrumentation, not the plant.
3. **The real vehicle is a faulted plant.** Wiki page
   `real_robot_has_2_faulted_thrusters…` (confidence HIGH): "The real ALBC vehicle currently has
   **2 of its 6 thrusters FAULTED** … no repair is planned before [near-term experiments]." A
   K_sim(nominal) vs K_real(2-thruster-fault) distance conflates fault, hydro-model error, and
   sampling into one uninterpretable number.

Plus two epistemic problems the task flagged and I confirm:

- **Decision-relevance is never argued.** Nowhere does the doc say what a spectral-distance number
  would cause the project to *do*. "Zero training-side risk" is not a benefit; it is only an absence
  of cost, and it is being used as if it were evidence of value.
- **The decision question it gestures at has a cheaper answer.** The operative question is "is the
  real plant inside the DR support?", which is a distributional-coverage check on trajectory
  statistics and needs no operator theory. Also note K_sim is **not well-defined** under DR: sim is a
  *family* K(θ_env), so "the" K_sim is a choice (nominal? DR-mean?) the doc never makes — the same
  single-K objection the doc itself raises against every other category (Sec 9 cross-cutting blocker,
  Sec 13.2) and does not apply to its own favorite item.
- **Caveat dropped between sections.** Sec 11.6 correctly notes "data/ is host-side, not visible
  in-container; plan the analysis for a host session"; Sec 15.4 upgrades to "APPLICABLE-NOW" and
  drops it. Whether the watertank datasets even contain ALBC-vehicle trajectories with synchronized
  thruster commands at a usable rate is **asserted, never verified** — and is unverifiable from
  inside this container, which the doc knew and then forgot.

---

## THEO-5 (major) — Shortlist #1 is now a 4-way compound arm, violating the doc's own screening discipline

**Target**: Sec 15.4 item 1 vs Sec 8.4.4 vs Sec 11.1.

Trace the growth of the "screening arm":

| Section | Arm content |
|---|---|
| Sec 8.4.4 | φ_x lift of o_t (KIPPO-style), rec + prediction losses |
| Sec 10 (Axis B) | + block-partitioned prediction targets (20D dynamic block lifted; command block excluded from targets) |
| Sec 13.1 | + **bilinear** term `H(φ_u(a) ⊗ φ_x(o))` ("supersedes the plain-affine sketch") |
| Sec 13.2 / 15.4 | + **z-conditioned scaffold** K(z), B(z) via hypernetwork |

That is four simultaneous deltas from the single precedent, on a different algorithm (ConstraintTRPO
+ IPO + asymmetric critic vs PPO), under DR that the precedent did not have, at **single seed,
2000 iters**. A null result cannot be attributed; a positive result cannot be attributed either.
This directly violates `.claude/rules/03` "Minimum-Change Revert" ("여러 변수 동시 revert → 다음
run에서 또 confound → 효과 분리 불가능") applied in the forward direction.

The asymmetry is the finding: **Sec 11.1 invokes "single-variable screening discipline" as a reason
to keep the user's z-into-φ_x idea out of the arm, and Sec 13/15 then stack three of the doc's own
additions into the same arm without re-invoking it.** Same discipline, applied to exclude the user's
variant and not applied to the author's. That is textbook motivated reasoning, and it is exactly the
failure class the task asked me to look for.

---

## THEO-6 (major) — Sec 5.2's "information argument (decisive)" is a bad argument the doc itself contradicts

**Target**: Sec 5, item 2 (labelled "decisive"); Sec 8.3 "UNCHANGED" reuses it.

Two defects:

(a) **Information invariance is not a learnability argument.** "Any fixed pointwise transform Ψ(o_t)
carries exactly the information of o_t" is true (for injective Ψ) and irrelevant — by the data-
processing inequality no learned representation ever *adds* information, so this argument, taken
seriously, refutes representation learning in general, including KIPPO, which the doc endorses three
sections later. The doc applies the argument in the direction it dislikes and suspends it in the
direction it likes.

(b) **"Removing encoder and student removes the only channels that carry that information" is false
on the doc's own facts.** Sec 3 and Sec 10 both state o_t already contains **46–52D of delay
embedding** (30D tracking history stride-3 ×3, 16D action history ×2, integral, bias-EMA). A delay
embedding *is* a channel carrying partial plant information — that is the whole premise of the
student, and of HVOK, and of the doc's own Sec 10 Axis A. The correct refutation of Proposal 2 is
the quantitative one the doc discovers later and never back-propagates: the embedded window is ~9
physical steps, "orders longer" windows would be needed to see currents (~O(10 s)) and episode-long
faults (Sec 10 Axis A). Prop-2's *conclusion* likely survives on the corrected argument. The word
"decisive" does not, and it was used to close a user proposal.

---

## THEO-7 (major) — `NoEncoder` is presented as an existing control; it is a registered task with no current-plant run

**Target**: Sec 5.3 ("The honest control for this proposal already exists"); Sec 6 and Sec 8.4.4
arm sets; Sec 6's "cheap, 2000-iter track" cost framing.

Verified by grep in `/workspace/constrained-albc`:
- Task registration exists: `constrained_albc/envs/main/__init__.py:47`
  (`Isaac-ConstrainedALBC-NoEncoder-v0`), cfg at `envs/main/agents/rsl_rl_ppo_cfg.py:333`.
- **No NoEncoder run exists on the current plant.** The only `noenc` artifact in the tree is
  `experiments/legacy/plots/rsl_rl/full_dof_ablation/2026-04-22_01-40-30_ablation_v2_noenc` — a
  **full-DOF** run from April, i.e. a different task family *and* a plant that predates both the TAM
  fix and the buoyfix change (project memory: `teacher_baseline_opt` = pre-TAM-fix; the buoyfix plant
  change closed `teacher_baseline_posttam`). It is not a usable control for anything proposed here.

So the proposed 4-arm screening set is **four new training runs, not two**, and the doc's repeated
"cheap" framing understates the cost by 2×. A registered task is not a baseline. (This is the
`feedback-check-artifact-provenance-before-reuse` failure mode: an existing artifact treated as a
substitute for requested work without dating it against the plant timeline.)

---

## THEO-8 (major) — The aux-loss escape hatch (Sec 8.4.1) reproduces the banned failure mode under a new name

**Target**: Sec 8.4.1 ("expansive (m > n) autoencoder where reconstruction is easy and collapse-
unlikely"), read together with Sec 14.2's adopted anti-collapse guard.

The project's recorded failure was not "z was small". It was, per `rules/03`: "decoder가 z를 무시하고
평균 예측, z는 collapse" — a **decoder-shortcut** failure. Shortcut severity depends on how much easy
signal the decoder can reach without using the learned part, not primarily on m vs n.

Now compose Sec 8.4.1 with Sec 14.2's recommendation, which the doc says to "adopt for φ_x
regardless": **z = [x, g'(x)]** (concatenate the raw state). Under identity-inclusion, the
reconstruction loss is solved *exactly* by the identity block alone, and the latent-prediction loss
is largely solved by the identity block's own dynamics. **g' can be a constant and both aux losses
still look healthy** — the 2026 failure mode, reproduced. The doc's two anti-collapse arguments
(expansive m; identity inclusion) are the same argument, and it defends against loss divergence,
not against the learned part being inert.

Aggravating: the project already owns the right instrument for this and the doc never proposes it.
`rules/03` "Encoder Verification Requires z_sweep": "Encoder 학습 여부를 TensorBoard aggregate만으로
단정 금지 … per-dimension sensitivity sweep 실행 필수." Sec 8.4.4's primary metrics are "gradient
variance / KL health / convergence speed … + eval static" — no φ_x-side sweep, no test that the
lifted coordinates carry signal. Under the project's own memory `feedback-test-must-be-able-to-fail`,
this arm currently has no gate that can fail for the right reason.

---

## THEO-9 (major) — The doc's own best-ranked near-term item silently vanishes from the final shortlist

**Target**: Sec 9 priority list item 1 vs Sec 10's updated shortlist vs Sec 15.4.

- Sec 9, #1: "NEAR-TERM training-side probe: student Koopman-consistency term (cat 6, supervised-
  only) — **smallest diff, rides existing distillation targets**; pairs naturally with the queued
  observability retrain roster." KIPPO listed as *the other* near-term candidate (co-equal).
- Sec 10: reordered to (1) KIPPO-style φ_x, (2) student-side consistency. Nothing in Sec 10's three
  axes bears on the student item's value; Axis B merely elaborated φ_x's *design*. Elaboration ≠
  evidence of efficacy.
- Sec 15.4: student-side item is **gone entirely**, with no verdict, displaced by the gap meter.
  Nothing in Sec 13–15 discusses it.

The item that disappeared is the one with the smallest diff, no new loss class, no new label source,
supervised targets already logged, and an already-scheduled host workstream (observability retrain,
per project memory). The ranking is tracking which item the most recent research round wrote the
most words about, not accumulated evidence. This is the clearest single instance of narrative
momentum in the document.

---

## THEO-10 (major) — Catalogued asymmetric standards of proof

Four matched pairs, same document:

| Applied against a user idea | Applied for a doc idea |
|---|---|
| Sec 4/5: rejects on *absence of a supporting result* ("No result in the survey says…", "NOT SUPPORTED by the paper") | Sec 8/15: accepts on *one* 4-seed MS-thesis-derived paper whose own mechanism claim is recorded but never verified |
| Sec 10 Axis A: "**No precedent** wires delay-Koopman features into an RL actor" → downgraded/dropped | Sec 15.3: "apparently **novel** … would be a novel contribution, not a reproduction" → treated as an asset |
| Sec 11.1: "single-variable screening discipline" used to keep z out of φ_x | Sec 13/15: three additional mechanisms stacked into the same arm without re-invoking it (THEO-5) |
| Sec 9 cross-cutting blocker + Sec 13.2: single-K-under-DR raised as a blocker against every surveyed category | Sec 15.3/15.4: the gap meter's own K_sim is never defined under DR (THEO-4) |

Absence of precedent cannot be a disqualifier in one direction and a selling point in the other.

---

## THEO-11 (minor) — "The survey's bibliography window predates…" misplaces the blame

Sec 8.1's opening frames the Sec-4 failure as the survey's coverage limit. The survey is arXiv
2408.04200, and the doc's own supporting report (`s2r_policy_transfer.md`, line 5) describes it as
"rev. 2025"; KIPPO is arXiv May 2025 / IJCAI 2025. More importantly, the survey's window is
irrelevant to the actual defect: **Sec 4/5 issued terminal verdicts without performing any
literature search.** Naming the survey's window as the cause reads as face-saving for the review
process and prevents the correct process lesson from being recorded ("do not issue NOT-SUPPORTED
from a single source").

---

## THEO-12 (minor) — "CONFIRMED white space" over-states its own source

Sec 15.1 declares four categories of confirmed white space. The source report
(`s2r_model_correction.md`, closing line) says: "**Recommend treating this as confirmed white space
rather than searching further**" — a stopping rule, not a proof — and that same report carries an
explicit verification-failure note: four+ key PDFs "returned corrupted/compressed text … conclusions
from these are marked accordingly and should be re-verified before being cited as load-bearing", plus
**one caught hallucination** (a search-snippet "towing-tank validation" claim that died on direct
fetch). `s2r_policy_transfer.md` similarly flags 2603.17416 and KODex as unverified. Sec 15.1/15.2
carry these forward with the hedges thinned ("Number-level claims unverified — PDFs corrupted" is
kept for Bruder; the general reliability warning is not). Negative results from keyword search over
a partly-unreadable corpus are the weakest evidence class in the document and are labelled
"CONFIRMED".

---

## Hostile-reviewer pass — top 5 rejection surfaces

If this were a paper's related-work + motivation section:

1. **"Your novelty is a brand."** The proposed mechanism is auxiliary latent-dynamics prediction with
   an expansive representation — OFENet, ICML 2020. No experiment isolates the linearity constraint
   that is the only Koopman-specific content. Reject until an unconstrained-latent control arm
   exists. (THEO-2)
2. **"Your motivation cites a survey that does not contain your problem."** The doc's own Sec 15.1
   verifies the survey has **zero** occurrences of sim-to-real / reality gap / domain randomization
   — while sim-to-real gap reduction is the stated research focus. A survey with no overlap with your
   problem statement cannot be the backbone of your related work.
3. **"Your single supporting result does not survive your own setting."** KIPPO: PPO, no DR, no
   constraints, 4 seeds, MuJoCo. Your setting: trust-region-constrained, 28D DR + discrete faults,
   IPO cost critics, asymmetric critic. The doc itself names the DR-single-K defeater and endorses
   anyway (THEO-1). Meanwhile the nearest underactuated-flight datapoint in your own Table (LC-SAC
   quadrotor) is **negative**.
4. **"You put a drifting representation under a trust region and cited the trust region as the
   safeguard."** Sec 16.2 vs arXiv 2405.00662. A reviewer who knows that paper stops reading here.
   (THEO-3)
5. **"Your headline applicable-now contribution is not measurable on your hardware."** IMU+pressure
   only (no DVL), ≤25 Hz ZOH attitude / 10 Hz joints, and 2 of 6 thrusters faulted — the gap meter
   cannot be computed on the plant it is proposed for, and no decision depends on its output.
   (THEO-4)

---

## What I did NOT find fault with (symmetry check)

- **Sec 4.2** (lifting p_t is meaningless: within-episode p_{t+1} = p_t ⇒ every function of p is an
  eigenfunction at λ=1) is correct, and the doc honestly re-uses it *against itself* in Sec 8.3.
- **Sec 13.1** (affine vs bilinear, resolved against pure affine) is the best-evidenced passage in
  the document — theorem-level claim, empirical signature, worked example, cross-checked between two
  clusters, with a self-correction recorded ("Correction on cross-check").
- **Sec 13.3** (CCK verdict: "NO, partially useful", explicitly contradicting the survey's own gloss)
  and **Sec 14.1** ([86] — "Survey's 'online update' phrasing is WRONG", verified against the paper)
  are exactly right: they attack the primary source rather than deferring to it, which is what Sec 4
  should have done from the start.
- **Sec 14.2** ([50]'s "domain shift" ≠ DR) is a load-bearing correction, correctly flagged as such.
- **Sec 16.1** (PE requirement applies to the model role, not the representation role; excitation
  data is free in sim and need not share the RL rollout stream) is a clean, correct dissolution of
  the user's question.
- **Sec 15.4 item 4** (Koopman-as-DR-replacement: NOT SUPPORTED, drop the framing) is well-supported
  and correctly labelled by both source reports.
