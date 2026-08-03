# Research report: K_sim-vs-K_real spectral gap meter (THEO-12 / THEO-4)

**Assignment**: determine whether a defensible version of the §15.3/§11.6 "quantitative per-axis
sim-to-real gap meter" exists, or recommend dropping it.

**Bottom line up front**: a defensible *minimal* protocol exists in principle (replay-matched inputs +
rate-matched + subspace-scoped + fault-matched), but every piece of literature found either (a) doesn't
solve the specific confound stacked in this system, or (b) solves one confound while leaving the other
three untouched — no single method in the literature clears all four simultaneously, and the corrected
protocol's implementation cost (a working closed-loop Koopman identification pipeline, a fault-injected
sim replay harness, a subspace-restricted comparison, and a rate-decimation study) is not "zero
training-side risk" as the doc claims. Against a strictly cheaper, already-decision-relevant alternative
(DR-support coverage check on trajectory statistics), the gap meter's incremental value is thin. **My
recommendation is to defer, not drop outright**: state the protocol as a documented pre-condition (Q1-Q3
fixes below) that must be satisfied before the meter is trusted, but do not schedule the work as
"applicable-now" — it should sit behind (a) confirming watertank data actually contains ALBC-vehicle
runs with the needed signals (host-side, unverified per critique) and (b) exhausting the coverage-check
alternative first, since that alternative answers a strictly more decision-relevant question at a
fraction of the engineering cost.

---

## Q1: Closed-loop identification bias for EDMD/DMD

**Does replaying real input sequences in sim (matched initial conditions) remove the sampling-measure
confound in principle? Any precedent for replay-matched operator comparison?**

The critique's proposed fix — fit `K_sim` on sim rollouts driven by the *actual logged input sequence*
from the real watertank run, matched initial conditions — is a form of **open-loop replay**, and the
closed-loop-identification literature says this is directionally correct but not free.

- **General closed-loop sysID theory** (classical, e.g. bias-in-closed-loop-identification literature):
  identifying a plant from data generated under feedback is biased if the controller's output is
  treated as an exogenous input while ignoring that it was computed from the plant's own (noisy)
  output — the correlation between input and output-noise inflates bias versus true open-loop
  excitation. This is textbook (see e.g. the "Bias issues in closed loop identification" survey
  literature; and closed-loop system identification surveys, e.g. Van den Hof & Schrama-style
  results) [full-text not re-verified here, general control-theory consensus, cited via search
  synthesis — flagged as background knowledge, not deep-read].
- **Directly on point — Closed-Loop Koopman Operator Approximation**, T. M. Dawson et al.,
  arXiv:2303.15318 (2023). Abstract-level read (WebFetch on the arXiv abstract page; full PDF not
  parsed due to compressed-stream extraction failure — flagged as abstract-only). This paper explicitly
  frames the problem: existing EDMD/DMDc methods assume open-loop data, but many systems (unstable
  plants, or here, a policy-controlled ROV that cannot safely run open-loop near a real deployment
  regime) can only be excited in closed loop. Their solution is **not** input-replay — it is a
  structural identification method that uses knowledge of the controller and closed-loop topology to
  simultaneously identify plant + controller-closed-loop operators, leveraging Koopman linearity.
  Reference implementation: `github.com/decargroup/closed_loop_koopman` (extends
  `github.com/decargroup/pykoop`), MIT-style academic license (verify on repo page before reuse).
  **Relevance**: this is evidence that closed-loop bias in EDMD is a real, actively-studied problem
  (not a strawman the critique invented), and that the standard fix in the literature is *not* simple
  input replay but a dedicated closed-loop estimator — which the doc does not propose or budget for.
- **Directly on point — "Control-Channel Informativity for Koopman EDMDc under Behavior-Policy Data,"**
  arXiv:2605.17966 (2026, very recent — matches this project's "current date August 2026" window).
  WebFetch summary (PDF fetched, summarized — treat as snippet-depth, not verified equation-by-equation).
  This paper is the most directly relevant found: it shows that when EDMDc is fit on data from a
  **fixed feedback policy** (exactly this project's DR-teacher-driven sim rollouts, or a real ROV run
  under its onboard controller), input variation is *correlated with state through the policy*, and the
  fitted control-channel block can be unidentifiable or misleading — the operator predicts the observed
  closed-loop behavior well while failing to generalize to *new* inputs. They introduce a "conditional
  intervention certificate" as a diagnostic for whether a fitted EDMDc operator's control channel would
  remain valid off the training policy. **This is a direct, recent, close match to the doc's replay
  proposal**: it says explicitly that a spectral/operator comparison built from single-policy data
  (whether real ROV logs or sim DR rollouts) inherits this identifiability gap unless checked.

**Does replay remove the confound?** Partially, and only for one of the two datasets being compared.
Replaying the *real* input sequence in sim and fitting `K_sim(replay)` removes the sampling-measure
mismatch **between the sim fit and the real fit**, because both are now conditioned on the same input
trajectory distribution. But it does **not** address the deeper identifiability problem raised by
arXiv:2605.17966: if that shared input sequence itself came from one closed-loop policy (not
persistently-exciting / not exploratory), *both* `K_sim(replay)` and `K_real` may be identifying the
same **degenerate, policy-restricted control-channel block** — i.e., replay matching converts a
distribution-mismatch confound into a shared identifiability weakness, rather than eliminating the risk.
The critique's own proposed `K_sim(replay)` vs `K_sim(on-policy)` control catches distribution mismatch
but not this identifiability issue — that would need a second control (e.g. an intervention-certificate
check, or supplementing replay data with even a small amount of persistently-exciting input if such data
exists in the watertank set).

**Precedent for replay-matched operator comparison specifically for sim-to-real**: no paper was found
that does exactly this (replay real inputs in sim, then spectrally compare `K_sim(replay)` to `K_real`)
for a sim-to-real gap-measurement purpose. The closed-loop-Koopman line of work (Dawson et al.) motivates
replay/closed-loop-aware identification as *necessary infrastructure*, not as a validated sim-to-real
metric. This is a gap in the literature, not a refutation — but it means the doc's "novel contribution"
framing is accurate (nobody has built this specific instrument) while its "APPLICABLE-NOW, zero risk"
framing is not (the necessary infrastructure — closed-loop-aware EDMD, or a persistently-exciting replay
input set — does not yet exist for this project and is itself open research plumbing).

## Q2: EDMD from partial observations (IMU + pressure only)

**Is a rotational+heave-subspace operator comparison still meaningful?**

- **Hankel-DMDc precedent** — Palma, Serani, Aram, Wundrow, Drazen, Diez, "Model-free system
  identification of surface ships in waves via Hankel dynamic mode decomposition with control,"
  arXiv:2502.15782 (2025). Full-text HTML read via `arxiv.org/html/2502.15782`. Important correction to
  the doc's framing: **this paper does NOT do output-only/partial-state identification** — it uses the
  full ship state vector (heave, roll, pitch, yaw, surge velocity, sway velocity) plus forcing inputs
  (rudder, wave elevation), with delay embedding used to capture *nonlinear* wave-encounter dynamics, not
  to compensate for missing state channels. So this specific citation from the original doc is not
  direct precedent for the ALBC partial-observation case; it is precedent for delay-embedded EDMD
  generally, not for identifiability-under-partial-state specifically. This is worth flagging back: the
  doc's Q2 framing implicitly assumed 2502.15782 addresses partial observability — it doesn't, on the
  evidence read here.
- **Actual precedent for partial-state Koopman**: "System Identification of a Moored ASV with Recessed
  Moon Pool via Deterministic and Bayesian Hankel-DMDc" (arXiv:2511.03482 / JMSE 13(12):2267, found in
  search but not deep-read here — flagged as title/abstract-level only) is a closer match in spirit
  (marine vehicle, Hankel-DMDc) but was not verified for partial-observability content within this
  research pass. "Finite Sample Identification of Partially Observed Bilinear Dynamical Systems"
  (arXiv:2501.07652, found in search, not deep-read) is the more theoretically relevant hit — bilinear
  systems under partial observation is exactly the ALBC structure (thruster/DR terms multiply state),
  but I was not able to verify its content beyond the title in this pass; **flag as an unverified lead**,
  not a confirmed precedent.
- **What is identifiable in principle**: delay-embedding theory (Takens-style, which underlies
  Hankel-DMD) says that with a sufficiently long delay window of even a *scalar* output, a
  diffeomorphic reconstruction of the full state's attractor is generically possible — this is the
  standard justification for output-only Hankel-DMD. Applied to ALBC: attitude + angular rate + a heave
  proxy (pressure-derived), delay-embedded, can in principle span an embedding that is diffeomorphic to
  the full 6-DOF state **if** the missing DOFs (surge/sway velocity) are dynamically coupled into the
  observed channels with a delay embedding long enough to capture that coupling — which for an
  underwater vehicle with hydrodynamic cross-coupling (added mass, cross-flow drag) is plausible in
  principle but has **not been demonstrated or even attempted** for this vehicle. There is no evidence
  in the literature reviewed that this Takens-style argument has been operationalized and validated for
  a real underwater vehicle's IMU+pressure-only sensor suite.

**Answer**: A rotational+heave-subspace `K` comparison is meaningful **only if reframed** as "does the
delay-embedded observable subspace reachable from IMU+pressure alone show a spectral gap" — which is a
narrower, weaker claim than "sim-to-real gap in the vehicle's dynamics." It cannot support the doc's
"per-axis" claim for the horizontal-velocity axes (surge/sway) at all, since those are unobserved on the
real system by the critique's own wiki evidence (THEO-4 defeater #1, confirmed correct here) — no
literature found overturns that; delay-embedding *might* recover a diffeomorphic proxy for those axes in
principle, but this project has zero empirical evidence that it does, and the standard EDMD literature
(including the ship paper actually read) does not attempt or validate partial-to-full state recovery via
delay embedding for a comparably under-observed system. **The critique's constraint stands**: comparing
`K_sim` (full-state visibility) to `K_real` (rotational+heave-subspace-only) is not an apples-to-apples
operator comparison unless `K_sim` is *also* restricted to the same delay-embedded partial-observation
subspace — which the doc does not specify, and which is a nontrivial (if standard) EDMD variant to
implement correctly (get the delay length right, verify observability numerically, e.g. via a
delay-embedding rank/singular-value check).

## Q3: Sample-rate / ZOH sensitivity — is rate-matching practiced?

- **Direct, strong precedent found**: "A Spectral-Grassmann Wasserstein metric for operator
  representations of dynamical systems" (arXiv:2509.24920 / NeurIPS-track paper, OpenReview
  B02EqvyiF3), read via `arxiv.org/html/2509.24920` (full-text HTML successfully parsed). This is very
  likely the "S-G-W metric" the original doc's §15.3 refers to. Key finding, confirmed from the
  paper's own text: the metric achieves sampling-frequency invariance by **re-normalizing discrete-time
  eigenvalues into continuous-time generator eigenvalues** (`λ = log(μ)/Δt`, comparing the continuous
  generator spectrum rather than raw discrete eigenvalues `μ = e^{λΔt}`), explicitly validated across
  different sampling timescales (their Figure 1d). This is real, direct precedent for rate-matching
  before spectral comparison — and it is a *cleaner* and more principled fix than the manual
  "decimate sim to 25 Hz ZOH, match the joint 10 Hz" approach implied by the doc, because it removes the
  need to force both datasets onto one common sample grid at all — each can stay at its native rate and
  be compared in the frequency-invariant continuous-time domain.
- **Caveat, also confirmed from the same read**: the paper's invariance result is about *sampling
  frequency* of otherwise-matched, fully-observed, open-loop, noise-free trajectory data. It explicitly
  does **not** address: dictionary/basis-choice sensitivity, closed-loop/policy-driven identification
  bias, partial observability, or noise-floor calibration (confirmed absent from the paper's stated
  assumptions and experiments in this pass). So it resolves Q3 specifically but does nothing for Q1/Q2 —
  it cannot be used as a drop-in fix for the whole meter, only for the rate-mismatch piece.
- **On ZOH/staleness specifically** (not just rate): re-normalizing to continuous-time eigenvalues
  corrects for *sampling interval* differences (discretization mapping), but ZOH staleness — the real
  policy acting on an observation that is up to 1/25s to 1/10s stale, versus sim's presumably
  fresher-observation control loop — is a distinct effect: it changes the *effective input signal* seen
  by the plant (a held, delayed control command), not just the sample clock. The S-G-W renormalization
  does not correct for this; it would need to be handled at the data-generation stage (matching sim's
  control loop to the same ZOH/staleness pattern before logging, which the project's DR config
  presumably could do by injecting the same effective latency) rather than at the comparison stage.
  This is a real, unresolved gap: rate can be fixed post-hoc via S-G-W-style renormalization, but
  staleness cannot — it must be matched at the generation/replay stage, which folds back into the Q1
  replay protocol (replay must reproduce the real ZOH pattern, not just the nominal command sequence).

**Answer**: yes, rate-matching precedent exists and is stronger than what the critique proposed (continuous-
time eigenvalue renormalization > naive decimation), but it is one piece of the puzzle — staleness/ZOH
still needs to be baked into the replay generation, not fixed by a post-hoc metric.

## Q4: Decision-relevance — what would a spectral distance actually drive, and is coverage-checking cheaper and better?

**Candidate decisions and their support:**

1. **Per-axis DR-range recalibration** (decompose distance per mode/axis, tells you which physical axis
   is most wrong → widen/narrow that axis's DR range). This is the most concrete candidate, but it
   requires the operator comparison to be axis-interpretable, which for EDMD in a lifted dictionary space
   is not automatic — eigenvectors/modes of a lifted operator do not correspond 1:1 to physical state
   axes unless the dictionary is specifically designed for that decomposition (e.g. block-diagonal or
   physically-structured basis functions). No source found in this pass demonstrates axis-attributable
   EDMD spectral decomposition for a comparably multi-axis underwater system; this is an unverified
   design assumption in the original doc, not a demonstrated technique.
2. **Plant-model triage (which hydro coefficient family to remeasure)** — theoretically plausible (a
   systematic frequency-domain mismatch in a particular mode could implicate added mass vs damping vs
   restoring terms), but again requires physically-interpretable modes; same gap as (1). No literature
   found validating this specific triage use of EDMD spectra for underwater hydrodynamics.
3. **Regime/terrain classification precedent** — the doc's own [53] citation (Krolicki et al., IFAC-
   PapersOnLine 2022, per the sibling `table1_legged_domainshift.md` research artifact reviewed here)
   is real but abstract-level only (paywalled, not independently verified full-text) and is a
   **within-sim, per-terrain classification** result (switched-system Koopman model, distinct spectral
   signature per terrain, used for sensor-free terrain classification), not a sim-vs-real gap metric.
   It supports "Koopman spectra can carry regime-discriminative information" in general, which is weak
   transferable support — it does not validate that a *sim-vs-real* spectral distance is meaningful or
   decision-actionable, only that *spectra differ across known regimes* in a simulated multi-domain
   setting.
4. **DR-support coverage check (cheaper alternative)**: this asks "is the real plant's observed
   trajectory statistics (state/output distribution, or simple physical parameter estimates like
   measured damping/added-mass ratios) inside the range spanned by the DR distribution used in
   training?" This is a standard, much lower-engineering-cost question — descriptive statistics /
   distributional-coverage checks, no operator identification, no dictionary choice, no closed-loop bias,
   no rate-matching subtlety, no partial-observability identifiability question. Sim-to-real domain-
   randomization theory (general RL sim-to-real survey literature, e.g. arXiv:2502.13187 found in
   search but not deep-read here — flag as background) treats DR-coverage as the standard sufficient
   condition for transfer: if the real dynamics parameter lies inside the randomized training
   distribution's support, transfer is theoretically expected to work; if outside, it isn't, regardless
   of any spectral-distance number.

**Honest comparison**: the coverage check answers a coarser but strictly cleaner question ("is the real
plant in-distribution for the trained DR envelope, yes/no, per-parameter"), computable directly from
already-logged watertank trajectory statistics or even single physical measurements (e.g., fit a damping
coefficient from a real decay test, compare it to the DR range), with none of the four confounds raised
in the critique. The spectral gap meter, even after all four fixes (closed-loop-aware identification per
Q1, subspace-restricted delay embedding per Q2, continuous-time rate renormalization per Q3, and a
fault-matched sim-replay condition), would deliver a **global scalar or per-mode number whose physical-
axis attribution is unproven for this system** — i.e., even a maximally-corrected version answers a
*less* decision-actionable question than the coverage check, at strictly higher implementation cost. The
literature does not offer a rescue that changes this ordering.

---

## Recommendation

**Do not ship as "APPLICABLE-NOW, zero training-side risk."** A defensible minimal protocol is:
(i) closed-loop-aware identification, not naive EDMD-on-logs, informed by arXiv:2303.15318/2605.17966
(likely requiring a real implementation using `pykoop`/`closed_loop_koopman` as a starting point, not a
weekend script); (ii) subspace-restricted comparison (rotational + heave-proxy delay-embedding only,
`K_sim` restricted to the same observable subspace as `K_real`, with an observability/rank check before
trusting the embedding); (iii) continuous-time eigenvalue renormalization per the S-G-W approach
(arXiv:2509.24920) to remove rate confounds, plus a separate ZOH/staleness match baked into the sim
replay generation (not fixable post-hoc); (iv) a fault-matched sim condition (2-of-6 thruster fault
injected into the sim replay, not nominal sim) so `K_sim` and `K_real` share the same fault state; (v)
axis-attribution of the resulting distance is **unproven** — treat any per-axis claim as a hypothesis to
validate, not a result to report, until a physically-structured dictionary is built and checked; (vi) run
the DR-coverage check first — it is cheaper, has none of these confounds, and if it already tells you the
real plant is out-of-DR-support on some axis, the spectral meter adds little beyond confirming that at
much higher cost. Given (i)-(v) is a nontrivial engineering program (not a quick add-on) and (vi) is
strictly cheaper and answers a more actionable question, **this item should be reclassified from
APPLICABLE-NOW to a deferred/exploratory item**, gated behind confirming the watertank dataset actually
contains synchronized ALBC-vehicle thruster-command + IMU + pressure logs at a usable rate (per critique's
own flagged, unverified caveat) — do not schedule engineering time against it before that data-existence
check and the coverage-check alternative are both done.

---

## References

1. T. M. Dawson (and coauthors — exact author list not confirmed beyond first author from abstract
   page), "Closed-Loop Koopman Operator Approximation," arXiv:2303.15318, 2023.
   https://arxiv.org/abs/2303.15318 — **verification: abstract-only** (WebFetch on abstract page;
   full PDF text extraction failed due to compressed PDF stream, not independently re-attempted via
   HTML mirror in this pass).
2. Anonymous/unconfirmed authors, "Control-Channel Informativity for Koopman EDMDc under Behavior-Policy
   Data," arXiv:2605.17966, 2026. https://arxiv.org/pdf/2605.17966 — **verification: snippet/summary
   depth** (WebFetch PDF summary; not independently re-derived from equations). Note: arXiv id format
   (26XX.XXXXX) is consistent with a 2026 submission given the stated current date of August 2026;
   flagging because it is very recent and could not be cross-checked against a second source.
3. G. Palma, A. Serani, S. Aram, D. W. Wundrow, D. Drazen, M. Diez, "Model-free system identification of
   surface ships in waves via Hankel dynamic mode decomposition with control," arXiv:2502.15782, 2025
   (also Ocean Engineering, ScienceDirect S002980182502222X). https://arxiv.org/html/2502.15782 —
   **verification: full-text-read** (HTML version successfully parsed, Section 5.1 and delay-embedding
   discussion read directly).
4. [Title/authors from search snippet only — not independently confirmed] "System Identification of a
   Moored ASV with Recessed Moon Pool via Deterministic and Bayesian Hankel-DMDc," arXiv:2511.03482 /
   JMSE 13(12):2267. https://arxiv.org/pdf/2511.03482 — **verification: title/abstract-snippet only**,
   not fetched or read in this pass; flagged as an unverified lead for partial-observation marine-vehicle
   Hankel-DMDc precedent.
5. [Title from search snippet only] "Finite Sample Identification of Partially Observed Bilinear
   Dynamical Systems," arXiv:2501.07652. https://arxiv.org/pdf/2501.07652 — **verification:
   title-only**, not fetched; flagged as the most theoretically relevant unverified lead for Q2
   (bilinear structure matches ALBC's thruster/DR-parameter multiplicative coupling).
6. [Authors from search result, exact author list not independently verified] "A Spectral-Grassmann
   Wasserstein metric for operator representations of dynamical systems," arXiv:2509.24920, 2025 /
   OpenReview B02EqvyiF3. https://arxiv.org/html/2509.24920 — **verification: full-text-read** (HTML
   version parsed; abstract, sampling-invariance mechanism (Section on eigenvalue renormalization),
   dictionary-invariance absence, closed-loop-data absence, and application list (classification,
   dimensionality reduction, Fréchet-mean interpolation) all confirmed directly from the paper text).
7. A. Krolicki, D. Rufino, A. Zheng, S. S. K. S. Narayanan, J. Erb, U. Vaidya, "Modeling Quadruped Leg
   Dynamics on Deformable Terrains Using Data-Driven Koopman Operators," IFAC-PapersOnLine 55(37):
   420–425, 2022 (MECC 2022). https://www.sciencedirect.com/science/article/pii/S2405896322028622 —
   **verification: abstract-only, sourced secondhand** from the sibling research artifact
   `table1_legged_domainshift.md` (produced in this same review round by a different research pass); not
   independently re-fetched in this pass (ScienceDirect/ResearchGate both return HTTP 403 per that
   artifact's own note).
8. Background/general control-theory consensus on closed-loop identification bias (bias-correction and
   indirect-method literature surfaced in search: e.g. "Bias issues in closed loop identification with
   application to adaptive control," ResearchGate; "A bias-correction method for closed-loop
   identification of Linear Parameter-Varying systems," ScienceDirect S0005109817304843) —
   **verification: search-snippet/abstract level only**, cited as background textbook-consensus
   supporting Q1's general framing, not as specific evidence for the Koopman/EDMD case (items 1–2 above
   cover that).
9. General sim-to-real / domain-randomization survey: "A Survey of Sim-to-Real Methods in RL: Progress,
   Prospects and Challenges with Foundation Models," arXiv:2502.13187. https://arxiv.org/pdf/2502.13187
   — **verification: search-snippet only**, cited as background for the Q4 coverage-check argument
   (DR-support-as-sufficient-condition framing is standard in this literature), not independently
   full-text verified in this pass.

## GitHub repos

- **github.com/decargroup/closed_loop_koopman** — implements the closed-loop Koopman identification
  method from arXiv:2303.15318 (`cl_koopman_pipeline.py`). Reusable: this is the most directly relevant
  starting point if the project decides to pursue a closed-loop-aware `K_real`/`K_sim` fit — it is Python
  and extends `pykoop`, which is compatible with a PyTorch/rsl-rl stack as an offline analysis tool (not
  meant for in-the-loop training use). License not independently verified in this pass — check repo
  before adoption.
- **github.com/decargroup/pykoop** — general Koopman operator identification library (lifting functions +
  regressors: `pykoop.Edmd` with Tikhonov regularization, `pykoop.Dmdc`, `pykoop.Dmd`). Reusable as the
  base EDMD/DMDc fitting infrastructure for both `K_sim` and `K_real` fits, and as the dependency the
  closed-loop extension above builds on. License not independently verified — check repo before adoption.
- **github.com/dynamicslab/pykoopman** — the more widely known, actively maintained general-purpose
  Koopman/DMD Python package (companion to the JOSS paper arXiv:2306.12962). Reusable as an alternative
  or complementary EDMD backend; has broader dictionary/observable-function support out of the box,
  useful for the Q2 delay-embedding (Hankel-DMD) needs specifically. License: MIT (per the package's
  standard convention — not independently re-verified from the repo page in this pass, flag before
  reuse).
- **Note**: no repo was found implementing the specific "Spectral-Grassmann-Wasserstein" metric
  (arXiv:2509.24920) as reusable code; the paper references code availability but a public repository URL
  was not located in this search pass — would need direct author/OpenReview follow-up if that exact
  metric implementation is wanted.

## Implications for ALBC

1. **The meter is not "zero training-side risk."** Building a defensible version requires: adopting or
   adapting `decargroup/closed_loop_koopman` (nontrivial integration work, not a training-loop change but
   real engineering time), a delay-embedded subspace-restricted EDMD fit validated for observability
   (numerical rank check on the Hankel matrix before trusting it), a fault-injected sim-replay condition,
   and either continuous-time eigenvalue renormalization (S-G-W-style) or an explicit rate-matching study.
   None of this is currently built. The doc should downgrade the item's cost estimate accordingly.
2. **Axis attribution is a hypothesis, not a given.** Before any per-axis decision (DR recalibration,
   hydro-coefficient triage) is drawn from a spectral distance, the project needs to verify that the
   fitted operator's modes are physically interpretable for this dictionary choice — there is no
   literature precedent found that validates axis-attributable EDMD decomposition for an underwater
   vehicle at this project's scale. Treat any first result as exploratory, not as a number to act on
   directly.
3. **Do the coverage check first, and possibly instead.** A trajectory-statistics / physical-parameter
   DR-support check (is the measured real damping/added-mass/thrust-fault state inside the trained DR
   envelope?) answers the actual open question — "will sim-trained DR-robust policies transfer to this
   specific real plant" — more directly, more cheaply, and without any of the four confounds raised
   against the spectral meter. If that check already flags an out-of-support axis (e.g., the 2-fault
   thruster state, which is very plausibly outside a DR envelope not specifically designed around
   asymmetric 2-of-6 faults), the spectral meter's marginal information value is low, since the more
   basic and cheaper check already delivered an actionable finding.
4. **Fault-state mismatch is not optional to control for.** Even in the corrected protocol, `K_sim` must
   be fit on a sim replay with the same 2-of-6 thruster fault injected as the real vehicle currently has —
   this needs the DR/fault-injection machinery to support an explicit "hold this exact fault pattern for
   this replay" mode, which should be checked against the current DR config before this item is scheduled.
5. **Bottom line for planning**: reclassify from priority-1/applicable-now to a gated, deferred research
   item. Gate conditions: (a) confirm watertank data has synchronized ALBC thruster-command + IMU +
   pressure logs at usable rate (host-side check, currently unverified); (b) run and report the DR-support
   coverage check first; (c) only then, if coverage-check leaves open questions the spectral meter could
   plausibly resolve, scope the closed-loop+subspace+rate+fault-matched protocol as its own small project,
   not a training-loop add-on.
