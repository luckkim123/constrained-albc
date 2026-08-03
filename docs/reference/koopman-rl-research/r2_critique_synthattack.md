# Round 2 — SYNTHATTACK: adversarial critique of the Round-1 synthesis (§17–§18)

Target: `/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md` §17, §18 — especially the
§18.8 verdict table and the §18.9 ranking. Method mirrors Round 1: attack the synthesis with the
same standard Round 1 applied to Part I, with symmetric skepticism (corrections that went the doc's
way get the same scrutiny as those that went against it).

Primary sources touched directly this round (not via a Round-1 report):
- `constrained_albc/envs/main/mdp/observations.py:89-204` (p_t layout), `envs/main/config.py:361-410,
  486-560`, `envs/main/albc_env.py:686-700,806-830`, `envs/main/mdp/events.py:233`,
  `envs/_core/algorithms/constraint_trpo.py:158-186,350-366,520-527`.
- KIPPO page images (`kippo_pages/page-11.png`, `page-12.png`, `page-13.png`) — App. C/D/E read
  directly, not via `r1b_kippo_imageread.md`.

Verdict up front: the Round-1 synthesis is directionally sound and its confirmed defects hold up
(I re-verified the `constraint_trpo.py` param-grouping claim and it is correct). But the synthesis
over-rotated in three places, dropped a load-bearing control that its own source report demanded,
mis-pinned a code fact both Round-1 lenses got wrong, and — the largest problem — produced a
ranking whose top two entries skip the obvious cheap rung between them. And after 18 sections the
document still does not state, in one place, what happened to the user's two proposals.

---

## S1 (critical) — §18.9 #1 is not a coherent #1, and it silently dropped its own source's mandatory control

**The charge.** Ranking an arm as #1 whose stated prior is "honestly SMALL/NULL expected effect" is
only coherent if a null result is itself decision-relevant. Here it is not, for three compounding
reasons:

1. **A null is unfalsifiable at our screening convention.** Project convention is single-seed,
   ~2000 iters (and the user has repeatedly declined confirmation seeds — `feedback-no-multiseed-in-
   screening`). An arm whose predicted effect size is "small-to-negligible" run at n=1 cannot
   distinguish *null* from *underpowered*. The §18.7 source report itself says "a null result on an
   already-privileged critic would be informative" — that is only true with the power to detect a
   small effect, which single-seed screening does not have. The synthesis imported the sentence and
   dropped the precondition.
2. **The diminishing-returns prior already predicts the null.** §18.7 cites arXiv 2412.20537: even an
   *oracle* model barely helps a critic that already knows the world. Our critic already sees 28D p_t
   + 9D z. So the expected outcome is known before the run, and the run cannot update it (see 1).
   Spending a GPU-week to confirm a prediction you already believe is the definition of a low-value
   experiment.
3. **It is not the "cheapest true Koopman arm".** The critic-side probe still requires building the
   entire phi_x autoencoder + K + B + decoder + the aux training loop + the H-step sequence buffers.
   The *only* thing it saves relative to the actor-side arm is the trust-region protocol (§18.2) —
   real, but it is a fraction of the build. Calling it "cheapest" conflates *structural risk* (which
   really is lowest — I re-verified the `value_prefixes` grouping at `constraint_trpo.py:161`, so
   critic-side inputs genuinely never touch `_policy_params`) with *implementation cost* (which is
   ~80% of the actor-side arm).

**Dropped control.** The §18.7 report's own closing paragraph states the critic-side arm needs *the
same* unconstrained-latent comparator as the actor-side arm — "the identical control is needed here
too, to distinguish 'Koopman helped' from 'any auxiliary dynamics feature would have helped
identically'". §18.9 #2 carries that control as mandatory; §18.9 #1 does not carry it at all. So the
ranking's #1 arm, as written, cannot attribute a positive result to Koopman either. It is
uninformative in *both* outcome branches as currently specified.

**What a positive result would mean, and its mechanism** (the doc never says, which is why the arm
reads as aimless): the only mechanism by which a one-step Koopman prediction helps an already-
privileged critic is *variance reduction in the value target*, not information addition — the
prediction is a smoothed, model-consistent summary of where the state is going, which can reduce
the effective TD noise the critic must average over, even when it adds zero new information. That is
a testable, falsifiable claim with a direct instrument: value-loss variance and explained-variance on
the reward critic and the cost critic *separately* (§18.7 Q3 flags they may behave differently). If
the arm is kept at all, this — not "reward at 2000 iters" — is what it should measure, and that
reframing makes a null genuinely informative because the instrument is a within-run variance
statistic, not a between-seed mean comparison.

**Verdict.** The honest ranking puts §18.9 #3 (offline pre-analyses, zero training cost) first. The
critic-side probe belongs below it, restated as "value-target-variance probe, instrumented on critic
loss statistics, with the unconstrained-latent control" — or dropped.

---

## S2 (critical) — the ranking has no rung between "null-expected probe" and "novel-method program". The frozen pre-trained phi_x is missing.

§18.9 offers #1 (safe, expected null) and #2 (actor-side, explicitly "novel-method work (TRPO+aux
gap), not recipe application"). Between them sits an option the synthesis constructed and then never
listed:

**Pre-train phi_x offline on logged/scripted-excitation rollouts (§16.2 Stage 0), FREEZE it, train
ConstraintTRPO on `cat([phi_x(EmpNorm(o_t)), z])`.**

Properties, each traceable to something already in the doc:
- **Zero trust-region contact.** A frozen phi_x is a fixed input transform. There is no aux loss
  during RL, no double-owned parameters, no stale `old_mu`/`old_logp`, no `constraint_trpo.py` edit,
  no param-ownership decision. Every one of §18.8 row 1's costs evaporates.
- **Not an auxiliary loss under the project rule.** Training happens offline, before RL, on a
  separate corpus. The settled No-Encoder-Auxiliary-Losses rule (and the systemfit THEO-9 reading
  that the codebase's real axis is *input-change vs aux-loss*) puts this squarely on the permitted
  side — unlike the concurrent variant, which §17.1-6 concedes lands on the banned side.
- **Single-variable.** It is exactly one delta from baseline, satisfying the discipline §17.1-7 says
  the compound screening arm violated.
- **§16.2 Stage 0 and Stage 2 were never withdrawn.** §18.8 row 1 withdraws only Stage 1's KL
  reassurance. Stage 0 (offline pre-train) and Stage 2 (freeze) survive Round 1 intact, and the
  trust-region defect makes them *more* attractive, not less. The synthesis drew the opposite
  inference.

The one honest objection is §16.2 Stage 1's own: a frozen phi_x goes stale as the visited state
distribution shifts. That is an argument, not evidence — **KIPPO never tested a frozen phi_x**
(confirmed by direct read: "phi_x is never frozen"), so there is no published result either way. The
staleness concern is also weakest precisely here: our o_t is bounded, normalized, and largely a
delay embedding of physically-bounded quantities, and the DR envelope (not the policy) dominates the
visited distribution's spread.

**Verdict.** This should be the actor-side entry in the ranking, with the concurrent KIPPO-faithful
variant staged *behind* it as the escalation if the frozen version shows signal. The synthesis
jumped from "concurrent training is novel-method territory" to "the actor-side arm is novel-method
territory" without noticing that only the *concurrency* was the novel part.

---

## S3 (major) — p_t time-varying slice pinned: 3 dims, not 6 and not 7. Both Round-1 lenses were wrong.

Charge (c), settled by direct code read.

`observations.py:92-191`, 28D union layout:

| Block | Dims | Time-varying within an episode? |
|---|---|---|
| Hydro (volume, CoG, CoB) | [0:7] | No — set at reset |
| Dynamic response (quad damp roll, mass, added mass surge) | [7:10] | No |
| Payload (mass, CoG offset) | [10:14] | **No, in the default config** (see below) |
| Actuator (Kp, Kd, thrust coeff, tau_up) | [14:18] | No |
| **Water density** | **[18]** | **No** — `events.py:233` samples it at reset only |
| Ocean current velocity (x,y,z world) | [19:22] | **No, in the default config** (see below) |
| Buoy (volume, mass) | [22:24] | No |
| Latency (normalized delay steps) | [24] | No |
| **Measured body lin-vel (u,v,w)** | **[25:28]** | **YES** — `root_lin_vel_b`, a live state |
| Thruster health (fault-DR arm only) | [28:34] | No — `FaultInjectionCfg` is reset-time by construction |

Two config facts decide the contested dims:
- `ou_enable: bool = False` (`config.py:556`, docstring: "Enable OU process drift on ocean current
  (**False = fixed per episode**)"). I grepped the whole repo (`.py`, `.yaml`, `.json`, `.md`): there
  is **no override anywhere** setting it True. The OU drift path at `albc_env.py:698` is dead in the
  default task. Independently corroborated by `.omx/programs/teacher-final-closeout/PLAN.md:672`
  ("`ou_enable` defaults False").
- `payload_toggle_steps: int = 0` (`config.py:545`, `_setup_payload_toggle` returns early at
  `albc_env.py:816-818`). Also never overridden; corroborated by the omx wiki page
  `uniform_only_dr_full_roster_...` and `docs/reference/domain-randomization-and-doraemon.md:396`.

**Answers to charge (c):** water density **is** in p_t, at index [18], and it is **constant** per
episode. The time-varying slice is **[25:28] only — 3 of 28 dims (25/28 constant)**, or 3 of 34
(31/34 constant) on the fault-DR arm. The theory lens's `[19:22]+[25:28]=6` and the systemfit lens's
`24/28 constant` (=4) are both wrong, and §3's own "constant-per-episode except current/measured-vel"
is the wrong premise both inherited.

**Consequences the synthesis has to absorb:**
1. §17.1-3 / §18.8 row 4 (student-consistency term ≈ temporal smoothing, K≈I) gets **stronger**, not
   weaker. 25/28 constant is a harder degeneracy than 22/28.
2. **But §18.4 item 4's pre-check is now much less informative than advertised.** It was framed as
   "fit K on logged teacher z, test distinguishability from I — falsifies the idea for ~zero cost".
   With the *only* time-varying input being measured body linear velocity — which is driven by the
   policy's own actions and the (constant-per-episode) current, i.e. explicitly **not** an autonomous
   function of p_t — the pre-check is guaranteed to find *some* K ≠ I (a 3-dim velocity subspace does
   evolve), and that K will be a closed-loop artifact of the teacher policy, not Koopman structure.
   The test as designed has no clean null. It needs a control: fit K on z sequences generated by a
   *different* teacher checkpoint (or with actions replayed) and check whether the non-identity part
   is policy-invariant. Without that control, the "salvage path" in §18.8 row 4 will produce a false
   positive.
3. §4.2/§8.3's eigenvalue-1 steelman is even more nearly-exact than Round 1 allowed — 25 of 28 p_t
   dims are literally constant, so z(p_t) is *almost entirely* an eigenvalue-1 object.

---

## S4 (major) — §18.8 row 2's "unbundle → plain phi_x first" instruction collides with KIPPO's own ablation

Read directly off `kippo_pages/page-13.png` (Fig. D.1/D.2, the full loss-component ablation) and
`page-11.png` (§E.3):

- The full triple `KI Rec + KI Pred LS + KI Pred SS` (purple) is positive on all six environments.
- The **subsets are frequently negative**. `KI Rec + KI Pred LS` (green — i.e. reconstruction plus
  latent-space prediction, *without* state-space prediction) is negative on roughly four of six
  environments in Fig. D.1, and in Fig. D.2 the std-improvement of the subsets swings from about
  +100% to about −350%. (Magnitudes here are figure-reads, not stated numbers — the sign pattern is
  what is load-bearing.)
- §E.3 corroborates the mechanism: state-space prediction weight ω3 "above 0.25 generally outperform
  the baseline while ... configurations below 0.25 approach baseline"; the reconstruction weight is
  the tolerant one.

So: **the loss triple is not a bundle of optional extras — it is the working configuration, and
partial versions are the known-negative cells of KIPPO's own ablation.** §18.8 row 2 says "arm must be
UNBUNDLED (plain phi_x first; bilinear H, K(z), block-partition = separate later ablations)". The
listed items are all *architecture* deltas, which is correct; but "plain phi_x first" is ambiguous
and, on the natural reading, invites dropping loss terms. If an ALBC screening arm ships with
reconstruction + latent prediction and no state-space prediction (the tempting simplification, since
state-space prediction is the term that needs the decoder), it reproduces KIPPO's negative cell and
the resulting null tells us nothing about Koopman on ALBC.

**Fix:** row 2 must say explicitly that the unbundling is over *architecture* (H bilinear, K(z),
block-partitioned targets) and that the L_rec/L_pred-ls/L_pred-ss triple with weights near
(0.75, 0.1, 0.5) is the *minimum* configuration, not a maximum.

This also sharpens charge (b): §18.10 already flags the 7,200-model tuning budget (I verified the
sentence verbatim on `page-11.png`, App. E — note the r1b report attributes it to page 12; it is
page 11, content correct). Combined with the ablation-sign pattern, the honest framing is that KIPPO
has a **narrow working configuration discovered by a search we cannot replicate**, and a single-seed
2000-iter arm on a different optimizer, different plant, and DR the precedent lacked has a material
probability of landing outside it. "Screening arm" is not an honest label for that. The doc should
say plainly: *this is a research-program-sized commitment the user must consciously choose*, and the
consequence of choosing it is that a null result will be uninterpretable.

---

## S5 (major) — §18.8 row 2 and row 5 are in unacknowledged tension; THEO-9's invariance pressure is stated without its counter-pressure

Charge (d)(iv). Row 2 orders the invariance-pressure risk (THEO-9) pre-registered as a "null-to-
negative" prediction. Row 5 mandates "expansive AE + **reconstruction** (KIPPO branch)" as the
anti-collapse design. These interact and neither row says so.

THEO-9's argument (`r1_critique_theory.md:286-300`) is: with a shared K, any phi_x feature whose
one-step evolution depends on theta incurs irreducible loss, so the minimizer prefers theta-invariant
features. That is sound **as a statement about the K-carrying terms in isolation**. But phi_x is not
trained on those terms in isolation:

- KIPPO's weights (Table B.2, quoted in §18.10) are `L_KI = 0.75*L_rec + 0.1*L_pred-ls +
  0.5*L_pred-ss`. The **largest** weight is on reconstruction, which is a pure
  information-*preservation* objective: it rewards phi_x for retaining everything about o_t. The
  invariance pressure acts through the 0.1- and 0.5-weighted K-carrying terms and is directly opposed
  by the 0.75-weighted term. THEO-9 never mentions reconstruction.
- phi_x is **expansive** (m > n) with a reconstruction objective, i.e. approximately injective on the
  visited set. An approximately-invertible map cannot *destroy* the theta-correlated signal in o_t;
  it can only re-weight which directions are emphasized. THEO-9's phrasing ("strips exactly the env
  information this project needs") is stronger than its own mechanism supports.
- **The teacher's actor does not do implicit sysID.** It receives z from the privileged encoder,
  which bypasses phi_x entirely under §11.1's settled design. So on the teacher — the thing the
  screening arm actually trains — the invariance pressure has almost no adaptation channel to damage.
  THEO-9's own escape clause ("if the actor consumes phi_x(o_t) and phi_x has been
  invariance-regularized, the deployed adaptation channel narrows to z_hat alone") is a **student/
  deployment** concern, not a teacher-screening one, and the screening arm does not train a student.

**Verdict:** THEO-9 survives as a real, named risk — it was right that the doc's "may just weaken"
framing treated mis-specification as isotropic noise, and that is a genuine repair. But §18.8 row 2's
instruction to pre-register "null-to-negative" as *the* prediction is over-claimed: the net direction
is not derivable from the argument once reconstruction and the privileged z-bypass are in the
picture. The honest pre-registration is a *directional hypothesis with a named counter-pressure and a
measurement*: probe whether phi_x(o_t) retains theta-discriminative content (linear probe from
phi_x(o_t) to the 3 time-varying p_t channels and to episode-identity, vs the same probe on raw o_t).
That is a within-run instrument, and it is falsifiable — unlike a bare "expect null-to-negative".

Nothing stronger than a hypothesis is claimed elsewhere: §18.3 correctly labels it "plausible +
well-supported, not directly proven", and §17.1-4 states the mechanism, not a result. So the answer to
"is anything stronger claimed anywhere" is **no** — the overreach is only in row 2's framing of the
prediction as one-directional.

---

## S6 (major) — the identity-inclusion withdrawal uses the exact-realizability argument that row 12 elsewhere rules inapplicable

Charge (d)(iii). §18.8 row 5 withdraws identity-inclusion on KIPPO's authority. I read the actual
passage (`kippo_pages/page-13.png`, App. G):

> "Unlike [Song et al., 2021], we do not concatenate the original state with the encoded state, as
> this restricts the set of systems where linearization is possible. Specifically, finding a linear
> representation of a non-linear system that includes the original state becomes **impossible** when
> the system has multiple fixed points or general attractors ... linear systems ... are not
> topologically conjugate to non-linear systems with multiple fixed points [Draeger et al., 1995]."

This is an **exact-realizability** argument, in the same family as the [97] bilinear-existence result.
Round 1 explicitly ruled that family inapplicable to the representation role — §18.8 row 12: "for the
aux/representation role (model never rolled out) exact-realizability does not resolve the design; a
harder-to-satisfy affine constraint is if anything a STRONGER inductive bias." KIPPO's own linearity
is a *soft* constraint on policy-visited trajectories (its §3 says local, not global), so its
identity-concat objection is about an ideal it does not itself achieve.

The same standard applied twice gives opposite answers:
- Row 12 (against the doc's earlier claim): exact-realizability is irrelevant here → demote.
- Row 5 (for the critique): exact-realizability is decisive → withdraw.

Meanwhile [50] and [86] use identity-inclusion successfully in practice — two working results against
one paper's theory argument, and that theory argument is of a type the same synthesis discounts.

**Verdict: over-correction.** "Withdrawn" is too strong. Correct standing: identity-inclusion and
KIPPO-reconstruction are two *alternative* anti-collapse designs with a real theoretical tension on
multi-equilibrium plants; the KIPPO branch is the defensible default *because we are copying KIPPO's
recipe*, not because identity-inclusion is refuted. If the frozen-phi_x variant (S2) is pursued —
where there is no PPO-clip tolerance absorbing anything and reconstruction is trained offline —
identity-inclusion is back on the table as the cheaper anti-collapse guard. Round 1's §18.4 point
that identity-inclusion "re-imports the raw state's nonlinearity into the K-fit block" is the
*better* argument against it and does not depend on Draeger; that one should carry the verdict.

---

## S7 (major) — §6's minimal falsifiable variant vanished from every ranking without ever being rejected

Charge (e). §6 recommends, as the one thing to run if an empirical token is wanted: physics-informed
feature augmentation of o_t (+sin/cos roll/pitch, +ω|ω|, ~6-8 dims), arms {TRPO, TRPO+features,
NoEncoder, NoEncoder+features}. §4's steelman calls it "the only defensible fragment of Proposal 1".

It appears in §4, §6 — and then never again. It is absent from §10's updated shortlist, §15.4, §18.8
(not listed as superseded), and §18.9. No section rejects it. It simply evaporated when the KIPPO
literature arrived.

This is a straightforward laziness failure and a coherence defect. The physics-feature arm is:
- the cheapest possible arm (a few lines in the observation builder, no new module, no aux loss, no
  optimizer question, no trust-region contact, no deploy-export change beyond the obs spec);
- fully rule-compliant (input change, not aux loss);
- the correct *control* for the whole Koopman program — if a hand-designed nonlinear expansion of
  o_t moves nothing, an expensive learned one is unlikely to, and if it *does* move something, the
  learned-lifting arms have a mechanism-free explanation to rule out first.

It is also the natural companion to the mandatory "frozen-random-expansion" control §18.8 row 2
already demands for the actor-side arm — they are nearly the same experiment.

**Verdict:** either restore it to the ranking (I would put it at #2, behind the offline
pre-analyses) or state explicitly why it was dropped. The current document leaves a reader who reads
§6 and then §18.9 unable to tell whether it was refuted or forgotten.

---

## S8 (major) — after 18 sections there is no post-Round-1 verdict on the user's two proposals

Charge (f). §7 "Decision log" ends at the §8 revision. Part II never updates it. The reader who asked
the original question must diff §4, §5, §8.3, §17.1, §18.8 and §18.9 to find out what happened.

**The honest final verdicts, assembled:**

**Proposal 1 (lift ALL network inputs — policy obs, privileged obs, proprio history, commands —
before the encoder and base policy): still NOT SUPPORTED as stated.** Round 1 touched none of the
three reasons that kill the literal proposal: lifting p_t is vacuous (§4.2 — and S3 makes it *more*
vacuous: 25/28 dims are literally constant); lifting commands/actions is the survey's named
joint-lifting hazard for any predictive operator (§4.3, refined but not overturned by §10's
clarification, which only exempts action history in its *policy-input* role); and o_t is already a
46-52D delay embedding, so a second unlearned lifting in front of a learned one is redundant (§4.5 —
§18.8 row 11 *reinforces* this by confirming phi_x(o_t) is itself a short-history encoder).

What survived is a **narrower variant the user did not propose**: lift o_t only, keep the encoder,
z bypasses phi_x. That variant has one published precedent (KIPPO), which Round 1 downgraded to a
4-seed PPO no-DR result and which S4 shows has a narrow working configuration found by a 7,200-model
search. It is gated behind five preconditions (§18.9 #2) and, per S2, should be attempted in its
frozen form first.

**Proposal 2 (drop the encoder and student; Koopman + base policy alone): NOT SUPPORTED, unchanged,
though the argument changed.** §18.8 row 11 correctly narrowed §5.2's "decisive information argument"
(DPI bars only *adding* privileged information; it says nothing about optimization geometry). The
verdict survives on three other legs that Round 1 left standing: a pointwise phi(o_t) adds no
env-parameter information that o_t lacks; a phi given history has become the student under another
name (§5.2, §8.3); and discarding free ground-truth p_t available in simulation is strictly worse
than using it (§8.3 variant A). Round 1 added nothing supporting Proposal 2 — KIPPO and SKooP both
*add* a Koopman module and neither *removes* an information source.

**Fix:** a short "§19 — answers to the two proposals" block, or an updated §7. Without it the document
fails its primary reader.

---

## S9 (minor→major) — the KIPPO precedent is weaker than "one 4-seed PPO no-DR paper": within that paper it is mixed

From `kippo_pages/page-12.png` (Fig. C.1, KIPPO vs PPO training curves, 4 trials, 6 envs), read
directly: KIPPO clearly ahead on HalfCheetah and (late) InvertedPendulum; roughly tied on
LunarLander and Hopper; and **behind the PPO baseline for most of training on Walker2d and
BipedalWalker**, converging only at the end. The paper's own §C text concedes this in gentler words
("surpasses the baseline **towards the end**" for both Walker2d and BipedalWalker).

The headline "+6-60% mean return" is therefore an end-of-training aggregate dominated by one or two
environments, and the *convergence-speed* claim is reversed on two of six. This matters directly for
an ALBC screening arm, because a 2000-iter screen is exactly the "before the end" regime where KIPPO
loses on a third of its own benchmark suite.

§18.8 row 2's "one 4-seed PPO no-DR precedent" is right but understated; it should read "one 4-seed
PPO no-DR precedent whose effect is positive on 2/6 envs, neutral on 2/6, and negative-until-late on
2/6". This is a further hardening of charge (b) and, combined with S4, it makes the null-result
interpretation problem acute.

---

## S10 (minor) — the DR-coverage-check alternative is real, but "cheaper" was asserted across two different things

Charge (d)(ii). Checking the source (`r1_research_gapmeter.md:200-220`), the alternative is *not*
hand-waving: it is specified (compare real trajectory statistics, or fitted physical parameters,
against the DR support) and the argument that it answers a more decision-actionable question is
sound. The gap-meter demotion itself is well-earned — the axis-attribution assumption really is
unvalidated, and §18.6 states this accurately.

Two things the synthesis compressed away:
1. **Two different coverage checks got merged.** Coverage on *trajectory statistics* (state/output
   distributions from existing watertank logs) is genuinely cheap. Coverage on *physical parameters*
   — the report's own example, "fit a damping coefficient from a real decay test" — requires a **new
   hardware experiment**, and on a vehicle with IMU+pressure only, no DVL, and 2/6 thrusters faulted,
   fitting added-mass/damping coefficients is itself a constrained system-ID problem of non-trivial
   difficulty. §18.6/§18.8 row 3/§18.9 #5 all say "cheaper" without distinguishing these.
2. **Its support was not deep-read.** The report flags its own citation (arXiv:2502.13187) as "found
   in search but not deep-read here — flag as background". The synthesis promoted it to a load-bearing
   comparison without the flag. Given the Round-1b Bruder incident, that flag should have survived
   into §18.6.

Net: the demotion stands, the replacement should be stated as "trajectory-statistic coverage check
(cheap, from existing logs) first; parameter-level coverage is a separate hardware task".

---

## S11 (minor) — the LC-SAC narrowing reads as permission where the evidence supports only "no support"

Charge (d)(i). §9 cat 1 recorded: on the 3D quadrotor (closest analog) *all* Koopman-Lyapunov variants
underperform vanilla SAC (−8 to −15%), reward-shaping collapses (−93%). §18.5 recalibrated: 5 seeds,
point estimates below SAC but within ~1σ; cartpole variance improved; only reward-shaping collapses.
§18.8 row 8 concludes: prohibition "NARROWED to reward-shaping Koopman-Lyapunov variants".

The recalibration is correct on the facts and the original blanket wording was indeed too strong. But
"within 1σ" cuts **both** ways, and the synthesis only took one direction from it. On the closest
analog the point estimates are *all* below baseline; overlapping bands mean "no detectable
difference", which is not the same as "permitted". Row 8's phrasing — a prohibition narrowed to one
variant — reads as license for the others.

Honest standing: "No evidence of benefit for Koopman-Lyapunov actor-side terms on the closest
analog (3D quadrotor, 5 seeds, all point estimates below SAC, bands overlapping); clear evidence of
harm for the reward-shaping variant. Not a prohibition, but not a supported direction either — do
not spend on it without a mechanism argument." Low stakes (nobody is proposing this arm), but the
verdict-table entry is the kind of thing that gets quoted later.

---

## S12 (minor) — Round-1b page attributions, checked

Applying the Round-1b lesson to Round 1b itself. I re-read the two most load-bearing KIPPO pages
directly:
- "300 model configurations, each with 4 random seeds across 6 environments, resulting in 7,200
  trained models" — **verbatim correct**; located at App. E, **PDF page 11**, not page 12 as
  `r1b_kippo_imageread.md` states (page 12 is Fig. C.1).
- Identity-concat rejection — **verbatim correct**, and r1b's correction of the location (App. G,
  not §3.1) is itself correct; I confirmed it on page 13.
- Stop-gradient — confirmed on page 13's §F.3 body text ("The [stop-grad] operator ensures the state
  representations are optimized independently of the PPO loss"), independent of the Algorithm-3
  glyph read.

So r1b's content holds; only one page number is off by one. Recording it because §18.10's claims are
now load-bearing for the whole actor-side classification.

Also noted, not a defect: KIPPO's latent-dimension sweep (App. E.1) is {16, 32, 48} against state
dims {4, 8, 11, 17, 17, 24}, i.e. ratios from ~2x to 12x. §8.1's "m = 2-4× state dim" is a rough
summary of a much wider actual range, which matters if anyone tries to derive m for our 72D o_t from
that ratio. §18.8 row 7 (downgrading "try smaller m first") is directionally right; the ratio itself
should not be treated as guidance.

---

## Consistency scan of Part I against §18.8/§18.9 (charge (e))

| Part I claim | Listed as superseded? | Still consistent? |
|---|---|---|
| §6 "do not run as proposed" | No | Yes — reinforced |
| §6 minimal falsifiable variant (physics features) | No | **Orphaned — see S7** |
| §6 "genuinely Koopman-native: critic assist, offline EDMD diagnostic" | No | Partly — the offline EDMD diagnostic became the gap meter and was deferred (§18.8 row 3); §6 still presents it neutrally |
| §11.1 phi_x input = o_t only, staged bypass → K(z) → phi_x(o,z) | No | Yes — §18.8 row 2 is consistent with this order |
| §11.2 normalization swap | Row 6 | Withdrawn |
| §11.3 "try smaller m first" | Row 7 | Downgraded |
| §11.4 joint-lifting caveat resolution | No | Yes |
| §11.6 gap meter "direct thesis value" | Row 3 covers the §15 statement, not §11.6 | **Stale** — §11.6 still reads as an endorsed plan; a reader stopping there gets the pre-Round-1 verdict |
| §15.2 "Bruder = strongest template" | No | **Stale** — §18.10 narrowed it (analytical ODE prior, not a simulator); §15.2 text unchanged |
| §15.4 #3 deployment observer | No | Yes — §18.9 #4 "unchanged" |
| §15.4 #4 drop DR-replacement | No | Yes — survived all lenses |
| §16.2 Stage 0 (offline pre-train) / Stage 2 (freeze) | No (only Stage 1's KL claim, row 1) | Consistent, but **under-exploited — see S2** |
| §16.3 [100] active learning hijacks actions | No | Yes — survived |

Two stale-but-unflagged spots (§11.6, §15.2) plus one orphan (§6's variant). The doc's own convention
("where a later section contradicts an earlier one, the later governs") covers §11.6 and §15.2, since
§18.8/§18.10 do contradict them — but neither is in the supersession list, so the convention does not
actually fire for a reader searching that table. Add both rows.

---

## Summary of what Round 2 asks Round 3 to change

1. Re-rank §18.9: offline pre-analyses #1; physics-informed feature arm restored #2; **frozen
   pre-trained phi_x** as the actor-side entry #3, with concurrent-KIPPO staged behind it; critic-side
   probe demoted and restated as a value-target-variance probe carrying the unconstrained-latent
   control.
2. Rewrite §18.8 row 2: scope "unbundle" to architecture only; state the loss triple as the minimum;
   add the mixed within-paper result (S9); state plainly that the concurrent variant is a
   research-program commitment the user must consciously choose, with an uninterpretable null.
3. Fix the p_t fact everywhere (§3, §4.2, §8.3, §17.1-3, §18.4 item 4): 3 time-varying dims [25:28],
   25/28 constant, water density at [18] constant. Add the policy-invariance control to the K-vs-I
   pre-check.
4. Soften §18.8 row 5 from "withdrawn" to "alternative design, deprioritized on the re-imported-
   nonlinearity argument, not on Draeger"; reconcile with row 12's standard.
5. Restate row 2's invariance-pressure pre-registration as a two-sided hypothesis with a named
   counter-pressure (reconstruction, weight 0.75) and a probe instrument.
6. Add §19 (or update §7): the post-Round-1 verdicts on Proposal 1 and Proposal 2, in one place.
7. Add supersession rows for §11.6 and §15.2; adjudicate or record the §6 physics-feature orphan.
8. Row 8: restate LC-SAC as "no evidence of benefit", not "narrowed prohibition". Row 3: split
   trajectory-statistic coverage from parameter coverage; restore the not-deep-read flag on
   arXiv:2502.13187.

## Open research questions Round 3 could close

- Does anyone report a **frozen** pre-trained Koopman/latent lifting as an RL policy input (as opposed
  to concurrently trained)? If a precedent exists, S2's arm stops being novel at all. Searched-for but
  not searched this round.
- Is there any published RL result where an auxiliary latent-dynamics feature helps an
  **already-privileged** (asymmetric) critic? A hit would rescue §18.9 #1; the absence found in §18.7
  was inferred from an analogy (2412.20537), not from a targeted search on asymmetric critics.
- Does the reconstruction term measurably preserve context information under randomized dynamics
  (S5's counter-pressure)? IB-sim-to-real (2305.18464) and IIDA (2203.05549) were read for the
  *pressure* side only; the *preservation* side was never searched.
