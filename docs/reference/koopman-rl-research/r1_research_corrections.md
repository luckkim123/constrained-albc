# Corrections research — closing the evidence-critique's open verification items

Assignment: resolve 7 open verification items from `r1_critique_evidence.md` (§4, "Research questions
that would close the open items"), items 1–5, plus the KIPPO metadata fixes and two extra citation
checks named in the task prompt. This is a provenance-repair pass, not an editorial one — findings are
reported as they land, including where they support and where they complicate the doc's claims.

---

## 1. Bruder/Bombara/Wood IJRR 2025 — residual Koopman recipe (THEO-5)

**Source accessed**: NASA NTRS PDF (`ntrs.nasa.gov/api/citations/20250001907/downloads/ResidualKoopmanModel_IJRR.pdf`),
2.8MB. **Verification depth: FAILED — PDF is not machine-text-extractable through available tooling.**
Both the direct-fetch attempt and a repeat with a narrower prompt returned only "linearized PDF with
compressed object streams... not legible in this format" from the fetch tool's extraction layer. This is
the same corruption/extraction failure the original doc's sub-report already reported for a different
copy — so the "PDFs corrupted" ceiling named in the critique (THEO-5) is **not solved** by this pass. I
could not extract the exact recipe mechanics, the "<10% of the data" baseline, any real-data
sample-efficiency curve, or the update mechanism from full text.

What I can state from public metadata already surfaced in the critique and corroborated by search
snippets (title, DOI 10.1177/02783649241272114, IJRR 2025, open-access host confirmed reachable — HTTP
200, file downloads): the abstract-level claim that the method needs "only <10% of the data compared to
benchmarks" and performs "real-time recursive Koopman model updates" is genuine (this was independently
confirmed by the critique's own single search before my pass; I could not re-derive it myself because
the extraction layer failed identically here). I am **not** upgrading this beyond what the critique
already established — the caveat the critique flagged stands: Bruder's "sim" is an analytical physics
model, not a stochastic domain-randomized simulator, and the "<10%" comparison is against other
data-driven Koopman baselines fit purely on real data, not a sim-pretrain-then-real-residual curve. I did
**not** find any sim→real curve (percentage of real data vs. tracking error, or similar) in what was
extractable. **Verdict: the doc's claim "no real-data sample-efficiency curve exists for the sim-Koopman
+ real-residual recipe" survives this pass — not because the paper was read and confirmed absent, but
because the paper still could not be read at all.** The doc should say exactly that ("unread, extraction
failed twice") rather than implying the absence claim rests on read content. THEO-5's core complaint (a
"strongest template" designation resting on an unread paper) is not resolved — it is now doubly
confirmed unread.

**Recommendation**: if this citation is load-bearing, get a decompressed/OCR'd copy (Google Scholar
cache, sci-hub-style institutional access, or PDF repair tooling) rather than relying on WebFetch's PDF
layer, which fails consistently on this file across two independent attempts by two different agents.

---

## 2. Haseli & Cortés SSD/SSSD — reference resolution (THEO-2)

**Confirmed.** The paper is arXiv **1909.01419**, "Learning Koopman Eigenfunctions and Invariant
Subspaces from Data: Symmetric Subspace Decomposition," Masih Haseli and Jorge Cortés (v2, updated
2020-02-22) — this is the correct target for the survey's reference **[31]**, not [131] as the doc's
§14.2 mis-resolved it (search-confirmed title/author match; abstract corroborated by three independent
listings: arXiv abstract page, ADS, Papers with Code).

Per the abstract summary (search-snippet depth, not full-text-read — flagged accordingly): the paper
contributes (a) a necessary-and-sufficient condition for identifying Koopman eigenfunctions via
forward/backward-in-time EDMD, (b) the **SSD** algorithm (iterative, identifies the maximal
Koopman-invariant subspace + eigenfunctions within a fixed dictionary span), and (c) **SSSD** (Streaming
SSD) — described as "an online extension of SSD that only requires a small, fixed memory and incorporates
new data as [it] is received."

This substantiates the critique's THEO-2 finding on both counts: (1) [131] in the survey bibliography is
genuinely a different paper (Ordoñez-Apraez et al., L4DC 2024 — see §3 below), so the doc's accusation of
a survey citation error is unfounded and should be retracted; (2) the SSSD lead is real and correctly
characterized as a **fixed-memory, incremental/online subspace-update primitive** — which is exactly the
shape needed for a deployment-time observer update (bounded memory footprint, no need to store a growing
trajectory buffer, incorporates each new measurement without a full batch refit). I was not able to
verify the specific memory/compute cost (e.g., per-update FLOP count or update latency) at more than
abstract depth — the paper is from 2019/2020, pre-dating any GPU-batched implementation discussion, so an
implementation-cost claim beyond "small fixed memory" would need a full-text read.

**Verdict: SSSD exists, is a legitimate online primitive, and the lead survives — but the fix is
renumbering [131]→[31], not discarding the lead.** Update the doc's citation.

---

## 3. Ordoñez-Apraez et al., "Dynamics Harmonic Analysis of Robotic Systems" (L4DC 2024) — real [131]

**Source**: PMLR proceedings PDF failed extraction (same binary-stream failure as item 1); recovered via
arXiv abstract page (**arXiv:2312.07457**) full abstract (full-text-read of the abstract, not the paper
body) plus the project page `danfoa.github.io/DynamicsHarmonicsAnalysis/` (partial/summary depth).

**What it does**: decomposes the state space of a *symmetric* robotic system into orthogonal isotypic
subspaces via harmonic analysis; for linear dynamics this subdivides the dynamics into independent linear
systems, one per subspace ("dynamics harmonic analysis", DHA). Uses Koopman operator theory to build an
**equivariant deep-learning architecture** exploiting DHA to learn a global linear model. Reported
benefits: "enhanced generalization, sample efficiency, and interpretability, with fewer trainable
parameters and computational costs" (verbatim from the arXiv abstract).

**Evaluated on**: "synthetic systems and the dynamics of locomotion of a quadrupedal robot" (verbatim,
abstract) — the project page identifies this as a **Mini-Cheetah**, with real-hardware demonstrations
across gaits (trot/jump/pronk/gallop) and terrains; note the abstract itself does not specify
sim-vs-real, so the real-hardware attribution is at project-page depth only, not paper-body-confirmed.

**Symmetry group used**: the project page states the quadruped analysis uses **Klein-4 group** symmetry
(a richer structure than simple bilateral/mirror C2 symmetry — it captures the combination of
left-right and front-back symmetry axes present in a quadruped gait). The methodology is stated generally
("analytically compute this change of basis and apply it globally for any symmetric robotic system") but
**no manipulator, vehicle, or bilaterally-symmetric-only (C2) platform is evaluated** in what I could
access — the generalization claim is theoretical/architectural, not empirically demonstrated outside
quadruped locomotion.

**Relevance to a bilaterally-symmetric UUV+arm**: a 6-DOF UUV with a 2-DOF arm is closer to a **C2
(mirror) symmetry** case than the quadruped's Klein-4 case — the arm itself typically breaks the
mirror symmetry unless duplicated bilaterally, and thruster layouts are the more plausible symmetric
substructure (e.g., paired thrusters). The paper's architecture is *general* to any symmetry group
including C2, but the empirical evidence backing "enhanced generalization/sample efficiency" is
Klein-4-quadruped-specific; extrapolating that benefit magnitude to a C2 thruster-symmetric UUV is
untested. This is adjacent to SKooP conceptually (both use structural priors to shrink the Koopman
learning problem) but via a completely different mechanism (group-equivariant architecture vs.
critic-only Koopman prediction) — they are not substitutable citations for each other.

---

## 4. LC-SAC (arXiv 2602.04132) — calibrated restatement (THEO-3)

**Source**: arXiv HTML (`arxiv.org/html/2602.04132v4`), full-text-read depth for Table III and narrative
quotes.

**Seeds**: **5 random seeds per experiment**, 120 total runs (6 tasks × 4 algorithms × 5 seeds) — this
corrects the critique's own earlier "5 seeds" mention to a confirmed, sourced number (the critique had
said "5 seeds" without citing where; now confirmed at source).

**Full Table III** (point estimate ± std across seeds):

| Task | SAC | LC-SAC | LC-SAC-Mean | Lyap-RS-SAC (reward-shaping) |
|---|---|---|---|---|
| 2D quadrotor tracking | 195.6 ±11 | 180.5 ±14 | 188.7 ±7 | 45.9 ±41 |
| 2D quadrotor stabilization | 123.9 ±16 | 113.1 ±15 | 115.8 ±15 | 67.4 ±39 |
| Cartpole stabilization | 105.8 ±52 | 110.2 ±44 | **131.7 ±1** | **130.1 ±1** |
| Cartpole tracking | 112.9 ±52 | 115.8 ±43 | **140.5 ±1** | **137.1 ±3** |
| 3D quadrotor tracking | 147.3 ±10 | 125.5 ±7 | 135.9 ±14 | 8.2 ±2 |
| 3D quadrotor stabilization | 165.7 ±23 | 150.8 ±5 | 146.0 ±16 | 11.9 ±12 |

**Paper's own narrative** (quoted where the fetch tool reported direct quotation; treat as high-fidelity
but not independently re-verified against raw PDF bytes):
- Stabilization: "the constrained variants match or exceed vanilla SAC while dramatically reducing
  trial-to-trial variance" — illustrated most sharply on cartpole (σ drops from ±52 to ±1).
- Tracking: "constrained policies achieve monotonically decaying surrogate Lyapunov violations" but
  "incur a modest return cost in exchange for substantially reduced variance — a favorable stability
  performance trade-off."
- Reward-shaping collapse: "the shaping term overwhelms the task reward, destabilizing learning entirely"
  on quadrotor dynamics (93–94% collapse) — explicitly a failure of the *shaping* mechanism, not of
  Koopman-Lyapunov constraints per se.

**Calibrated restatement (no verdict flip)**: point estimates for the constrained variants are mixed
task-to-task — worse than SAC on both quadrotor tasks (2D and 3D, tracking and stabilization), better on
both cartpole tasks — with the 3D-quadrotor gap (147.3→125.5–135.9, roughly −8% to −15%) falling inside
one std of SAC's own reported spread in most cells, i.e. not clearly separable at n=5. The paper's own
framing (variance reduction as the sold benefit, not return improvement) is consistent across tasks and
is the mechanism the doc credits KIPPO with independently. This is a genuine tension for the doc: the
same paper it cites as "standing prohibition on actor-side Koopman-Lyapunov terms" also reports the
identical variance-reduction mechanism the doc treats as the *positive* case for KIPPO two sections
earlier — the two readings are not contradictory in mechanism (variance goes down either way), only in
whether the *return* cost is acceptable, and that appears task-dependent (favorable on stabilization,
"modest cost" on tracking, catastrophic only for the reward-shaping variant specifically). **A standing
prohibition on "Koopman-Lyapunov constraint terms on the actor" is not supported by this paper's own
narrative; a narrower prohibition on *reward-shaping-based* Lyapunov penalties in high-DOF underactuated
tracking is.**

---

## 5. arXiv 2603.03740 (Kinova KMPC) — compute-time confirmation (THEO-4)

**Source**: arXiv HTML (`arxiv.org/html/2603.03740v2`), full-text-read depth, Table II.

**Confirmed**: Table II reports **Avg. Comp. Time = 0.21913 s** per control step for KMPC (the
"Single Obstacle" 3D-space experiment column) — matching the critique's finding exactly. The paper states
"The proposed KMPC also achieves faster computation compared to NMPC (over 4.2× faster) by exploiting
linear Koopman dynamics, whereas shooting-based MPC becomes computationally impractical in these
scenarios" — no absolute Hz claim is made by the paper itself.

**Confirmed absent**: the figure **0.0389 s / 25 Hz does not appear anywhere in the paper** — corroborated
independently in this pass (separate fetch, separate session) from the critique's original finding. Two
independent extraction passes now agree: this number was fabricated somewhere upstream of the doc (most
likely a units/digit-transposition error, since 0.21913 and 0.0389 share no obvious derivation).

**Corrected figure and implication**: 0.21913 s/step = **~4.6 Hz**, not 25 Hz — roughly **5.6× slower**
than the doc's cited figure, and **~5.4× below** the stated 25 Hz obs-bus ceiling for this project. This
changes the character of the safety-filter blocker: the doc's original 25 Hz figure reads as "marginal,
right at our ceiling, might tune into range" — the corrected 4.6 Hz reads as "structurally far below the
bus rate, on a *simpler* plant (fixed-base 7-DoF arm, no floating base, no thruster/hydrodynamic coupling)
than a 6-DOF UUV+arm." If anything the corrected number **strengthens** the doc's caution about
Koopman-based MPC/safety-filter compute cost at this project's control rate, it just does so with an
accurate number instead of a fabricated one that happened to land near the threshold and understated the
gap by more than 5×.

---

## 6. KIPPO metadata fixes

**Source**: search-snippet confirmation of IJCAI proceedings listing + bibtex (`ijcai.org/proceedings/2025/556`,
`ijcai.org/proceedings/2025/bibtex/556`), and the UTK TRACE thesis repository page.

- **Page range**: confirmed **pp. 4994–5002** (not 4994–4997 as the doc states) — two independent
  listings (IJCAI proceedings entry #556 and its bibtex export) agree. This matches the critique's
  THEO-8(a) finding; the doc's citation should be corrected to 4994–5002.
- **"(one exception)" caveat**: not independently re-extractable in this pass — every attempt to fetch
  machine-readable full text of the KIPPO PDF (arxiv.org/pdf, arxiv.org/html, ar5iv) failed at the
  extraction layer in this session (arXiv HTML/ar5iv both 404'd for this ID; the raw PDF fetch returned
  only compressed-stream metadata). I could not re-verify this phrase myself. The critique's own
  provenance table marks this item as **F** (full text read at source, via local `pdftotext`) with a
  verbatim quote given ("reducing variance by 26.89-91.43% versus PPO... (one exception)") — that is a
  stronger verification method than anything available to me in this pass (I have no local PDF tooling
  access), so I am **not** downgrading it; I simply could not independently reproduce it. Treat it as
  standing on the critique's own local-pdftotext evidence, not on this pass.
- **MS-thesis provenance**: **confirmed real.** Andrei Cozma, "Koopman-Inspired Proximal Policy
  Optimization (KIPPO)," Master's thesis, University of Tennessee, Knoxville, 2024, hosted at
  `trace.tennessee.edu/utk_gradthes/11783` (TRACE — Tennessee Research and Creative Exchange, the
  university's institutional open-access repository). Title matches the arXiv/IJCAI paper exactly, same
  first author, consistent 2024 timing (IJCAI-25 submission would follow a 2024 thesis). This is a
  legitimate provenance chain (thesis → conference paper), not a red flag — MS-thesis-to-conference-paper
  is a standard academic pipeline. I could not fetch the thesis abstract itself (both direct URL attempts
  404'd/failed), so I cannot confirm whether the thesis and the IJCAI paper report identical numbers or
  whether the paper extended the thesis's results — flag this as unresolved if the exact figures depend
  on which document is cited.
- **4-runs-per-env compute note**: not independently re-extractable in this pass for the same
  extraction-layer-failure reason as the caveat above. The critique's own summary (§3, "What I checked
  and found clean") lists "its 4-seeds-per-env protocol" as independently verified clean at F-depth via
  local pdftotext. I have nothing that contradicts this and no better-depth source to add; treat it as
  standing on the critique's prior verification.

**Net**: 2 of 4 metadata items (page range, thesis provenance) newly confirmed in this pass; 2 (the
"(one exception)" caveat, 4-runs-per-env) remain resting on the critique's own prior local-pdftotext
read, which this pass's tooling could not reproduce or improve on. No metadata item was found to be
wrong beyond what the critique already flagged.

---

## 7. arXiv 2509.24920 (S-G-W metric) — validation-scope confirmation (THEO-10)

**Source**: arXiv abstract page (`arxiv.org/abs/2509.24920`), search-snippet + abstract depth.

**Confirmed**: the paper reports experiments "on **simulated and real-world datasets**, showing that the
approach outperforms standard operator-based distances in machine learning applications, including
dimensionality reduction and classification" — this directly corroborates the critique's THEO-10 finding
that the doc's "validated only on synthetic/fluid systems" description understates scope; "real-world
datasets" is explicitly claimed by the paper's own abstract, not just inferred.

What "real-world" means here was **not resolved to task-domain specificity** in this pass — the paper
(Germain, Flamary, Kostic, Lounici, arXiv 2509.24920) is a general operator-representation / optimal-transport
metric paper for dynamical-systems ML tasks (dimensionality reduction, classification of dynamical
systems by their operator spectra), not a robotics paper. "Real-world datasets" most plausibly refers to
benchmark time-series/dynamical-systems datasets used in the ML/dynamical-systems community (the kind
used for classification/clustering benchmarks), not robot trajectory data or any sim-to-real robot
experiment — I could not confirm the specific dataset names from abstract-depth alone. **Correction to
apply**: the critique's own more precise finding stands — "no robot, no sim-vs-real" is the part that
matters for the doc's APPLICABLE-NOW gap-meter framing, and that remains accurate; only "synthetic-only"
is the wording that needs fixing to "synthetic + non-robot real-world."

---

## Summary table

| # | Item | Resolution |
|---|---|---|
| 1 | Bruder IJRR 2025 full text | **Not resolved** — extraction failed again; "PDFs corrupted" ceiling persists, doc's claim it rests on is still evidentially unread |
| 2 | Haseli & Cortés SSD/SSSD | **Resolved** — arXiv 1909.01419 confirmed, is survey's [31]; SSSD is a real fixed-memory online-update primitive |
| 3 | Ordoñez-Apraez DHA (L4DC 2024, real [131]) | **Resolved** — Klein-4-symmetric quadruped locomotion (Mini-Cheetah), general architecture claim untested beyond quadrupeds; not a manipulator/UUV precedent |
| 4 | LC-SAC re-read | **Resolved (calibrated)** — task-dependent: worse on quadrotor (within-noise), better on cartpole; variance-reduction mechanism consistent with KIPPO's; standing prohibition should narrow to reward-shaping-specific |
| 5 | 2603.03740 Table II | **Resolved** — 0.21913 s/step confirmed, 0.0389/25Hz confirmed absent from paper; corrected figure is ~4.6 Hz, strengthens (does not weaken) the doc's caution |
| 6 | KIPPO metadata | **Partially resolved** — page range 4994–5002 confirmed, thesis provenance confirmed real; caveat text and seed-count note not independently re-derivable this pass, stand on critique's prior local-pdftotext read |
| 7 | 2509.24920 validation scope | **Resolved** — "simulated and real-world" confirmed verbatim in abstract; "real-world" is non-robot ML benchmark data, not robot/sim-to-real data |

---

## References

1. Bruder, D., Bombara, D., Wood, R. J. "A Koopman-based residual modeling approach for the control of a
   soft robot arm." *IJRR*, 2025. DOI: 10.1177/02783649241272114. Open-access:
   ntrs.nasa.gov/api/citations/20250001907/downloads/ResidualKoopmanModel_IJRR.pdf. **Verification
   depth: unreadable (PDF extraction failed, both this pass and the original doc's pass)** — file exists
   and downloads (HTTP 200, 2.8MB), but no full-text content could be extracted.
2. Haseli, M., Cortés, J. "Learning Koopman Eigenfunctions and Invariant Subspaces from Data: Symmetric
   Subspace Decomposition." arXiv:1909.01419 (v2, 2020-02-22). Verification depth: abstract/snippet
   (via arXiv abstract page, ADS, Papers with Code cross-listing).
3. Ordoñez-Apraez, D., Kostic, V., Turrisi, G., Novelli, P., Mastalli, C., Semini, C., Pontil, M.
   "Dynamics Harmonic Analysis of Robotic Systems: Application in Data-Driven Koopman Modelling." L4DC
   2024, PMLR v242. arXiv:2312.07457. Verification depth: full abstract text (arXiv abstract page) +
   project-page summary (danfoa.github.io/DynamicsHarmonicsAnalysis/, partial depth); full paper PDF
   extraction failed.
4. [Paper behind arXiv:2602.04132] "LC-SAC" (Lyapunov-constrained SAC), title/full author list not
   independently confirmed in this pass (fetch tool did not surface it). Verification depth: full-text
   (arXiv HTML v4, arxiv.org/html/2602.04132v4) for Table III and quoted narrative sentences.
5. Jung et al. "Whole-Body Safe Control of Robotic Systems with Koopman Neural Dynamics." arXiv:2603.03740
   (v2). Verification depth: full-text (arXiv HTML, arxiv.org/html/2603.03740v2), Table II confirmed.
6. Cozma, A., Harris, L., Qi, H. "KIPPO: Koopman-Inspired Proximal Policy Optimization." IJCAI-25,
   pp. 4994–5002. arXiv:2505.14566. Verification depth: proceedings metadata (ijcai.org/proceedings/2025/556
   and its bibtex export) — full-text depth NOT achieved in this pass (PDF/HTML/ar5iv all failed
   extraction); the "(one exception)" and seed-count claims rest on the original critique's local
   `pdftotext` read, not on this pass.
7. Cozma, A. "Koopman-Inspired Proximal Policy Optimization (KIPPO)." Master's thesis, University of
   Tennessee, Knoxville, 2024. trace.tennessee.edu/utk_gradthes/11783. Verification depth: repository
   listing page (title/author/repository metadata) — abstract not retrieved (fetch failed).
8. Germain, T., Flamary, R., Kostic, V. R., Lounici, K. "A Spectral-Grassmann Wasserstein metric for
   operator representations of dynamical systems." arXiv:2509.24920, submitted 2025-09-29. Verification
   depth: abstract (arXiv abstract page + corroborating search snippets).

## GitHub repos

No GitHub repository search was performed for this assignment — all seven items are literature/metadata
provenance checks on papers, not implementation surveys. One incidental repo surfaced in search results
while looking for the S-G-W metric paper: `github.com/thibaut-germain/SGOT` (appears related to optimal
transport for dynamical systems, likely the S-G-W paper's own or an adjacent author's implementation) —
**not verified**: I did not open this repo, cannot confirm license, contents, or whether it implements
the paper in item 7 above, or its reusability for a PyTorch/rsl-rl stack. Flagging as an unverified lead
only, not a finding.

## Implications for ALBC

1. **The Bruder residual-Koopman "strongest template" designation cannot be upgraded past unread.** Two
   independent extraction attempts (original doc's pass, this pass) both failed on the same NTRS PDF.
   Before this citation drives any design decision (e.g., adopting a physics-prior + residual-operator
   split for the teacher-to-real gap), get a readable copy through a different channel (Google Scholar
   HTML cache, institutional PDF-to-text service, or manual OCR) — do not let "abstract-level claims
   sound plausible" substitute for reading the method.

2. **SSSD (arXiv 1909.01419, correctly [31] not [131]) is a legitimate, cheap online-update primitive**
   for exactly the deployment-time observer-update use case named in the doc's medium-term shortlist:
   fixed memory, incremental incorporation of new measurements, no growing buffer. It is a 2019/2020
   algorithm, not GPU-native — a PyTorch port or reimplementation would be needed; there is no indication
   in what I could access of an existing maintained implementation to reuse. Treat it as an algorithm to
   reimplement, not a library to pull in.

3. **The real [131] (Ordoñez-Apraez DHA/L4DC 2024) is not a substitute citation for anything the doc
   currently uses SSSD for** — it is architecture-level (equivariant network exploiting symmetry
   subgroups), evaluated only on quadruped locomotion (Klein-4 symmetry), with no manipulator or vehicle
   validation. Its relevance to ALBC is speculative and would require ALBC's plant to actually be modeled
   as C2-symmetric (e.g., paired/mirrored thrusters) before the DHA construction applies — this is a new
   research direction, not a drop-in technique, and should not be conflated with the SSSD lead.

4. **The LC-SAC "standing prohibition" should be narrowed, not repealed.** The mechanism the paper
   reports (variance reduction via Lyapunov-structured constraints) is directionally consistent with what
   the doc credits KIPPO for — the paper's own narrative frames the return cost as favorable on
   stabilization-type tasks and only "modest" on tracking, with catastrophic failure isolated to the
   reward-shaping variant specifically. For ALBC's attitude-hold-plus-tracking task mix, this suggests
   Koopman-Lyapunov actor-side terms are not per se prohibited; if attempted, avoid the reward-shaping
   formulation and prefer whatever mechanism the paper's non-reward-shaping constrained variants use
   (hard/soft constraint vs. penalty — not resolved in this pass, needs a methods-section read before
   implementation).

5. **The corrected KMPC compute figure (4.6 Hz, not 25 Hz) makes the safety-filter-blocker case stronger,
   not weaker.** If a Koopman-based MPC/safety filter is ever considered for the real UUV+arm's ≤25 Hz
   bus, the reference precedent now shows ~5.6× headroom shortfall on a *simpler*, fixed-base 7-DoF
   platform with no thruster/hydrodynamic coupling — budget accordingly (expect the real plant's QP to be
   slower, not comparable, given added DOF and coupling terms), and do not treat 0.21913 s/step as
   "close enough to tune."

6. **KIPPO's provenance is legitimate (thesis → IJCAI paper, standard pipeline) and its citation is now
   correctable** (page range 4994–5002). This does not change any mechanism-level conclusion; it is a
   bibliographic fix only. The unresolved items (the exact "(one exception)" wording, the seed-count
   note) should not block use of KIPPO's core claims, since those two specific sub-claims were already
   verified at higher fidelity (local pdftotext) than anything available in this pass — re-verifying them
   would need the same tooling the original critique used, not a repeat web fetch.

7. **The S-G-W metric's "real-world" validation is not robot data** — it remains a legitimate
   APPLICABLE-NOW candidate for a generic sim-vs-real *gap-meter* primitive (operator-spectrum distance),
   but "validated on real-world data" should not be read as "validated on robot sim-to-real data." If
   adopted as a diagnostic for ALBC's teacher/student gap, it would be a first robotics application of
   the metric, not a precedent-backed one.
