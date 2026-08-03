# Adversarial Critique — Lens: EVIDENCE / citation integrity & provenance

Target: `/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md` (639 lines, Sec. 1–16)
Reviewer stance: adversarial, symmetric skepticism (negative verdicts attacked as hard as positive ones).
Method: (a) provenance table for every load-bearing citation, built by diffing the doc against the 23
`$CLAUDE_JOB_DIR/tmp/*.md` sub-reports it compresses; (b) direct web/PDF spot-check of 12 of the most
load-bearing items; (c) local `pdftotext` of the source survey and of KIPPO / Bruder-bilinear to check
quotes and numbers at source; (d) internal-contradiction sweep across revisions.

---

## 0. Headline

The doc's *reasoning* is mostly better than its *sourcing*. Three quantitative or attributional errors
survive into load-bearing positions (a fabricated QP-rate, a mis-resolved reference number carrying a
false accusation against the source survey, and an over-hardened negative result), and one design
recommendation contradicts the flagship precedent the doc itself relies on. Separately, the doc's
original NOT-SUPPORTED verdicts were built on an absence-of-evidence argument over a survey that
*explicitly declares it does not cover RL* — a fact the doc never records, even though §8's own
revision proves that argument failed once already.

Verified-clean and worth stating (no manufactured complaints here): KIPPO exists, its two most
load-bearing quotes are verbatim-accurate, and its headline numbers are right; SKooP exists and its
critic-only claim is verbatim-accurate; OM-Koop's real USV/AUV field validation is real; every
"nonstandard-looking" arXiv ID checked (2607.11624, 2602.04132, 2606.28476, 2603.03740, 2605.26452,
2601.01076, 2509.24920, 2409.10347, 2509.12562, 2410.07584) resolves to the claimed paper. No
hallucinated identifiers were found.

---

## 1. Provenance table (load-bearing citations only)

Depth key: **F** = full text read at source (by a sub-agent or by me); **P** = partial / abstract or HTML
section; **S** = search-snippet only; **U** = admitted unverified; **X** = not fetched / mis-resolved.
"Checked" = I independently re-verified during this critique.

| # | Item (doc section) | Claimed by doc | Sub-report basis | Depth | Checked | Verdict |
|---|---|---|---|---|---|---|
| 1 | T-RO survey 2408.04200 / TRO 42:1088–1107 (§1,4,5,10) | full read, page cites | `paper_p*.md` ×4 | F | yes | Page cites correct (0.5x/sin x → 1091; "does not generalize well" → 1092; vol/pages correct). But see THEO-1. |
| 2 | KoopmanRobo tutorial (§2) | 409 code lines, ~95 ms/step | `code_report.md` | F | no | Not load-bearing for any verdict; not re-checked. |
| 3 | ALBC input map (§3) | file:line verified | `albc_report.md` | F | no | Out of this lens. |
| 4 | **KIPPO** (Cozma/Harris/Qi, IJCAI-25) (§8.1, 11.3, 16.1) | precedent that makes Proposal 1 defensible | **none — main-context web read, no tmp file** | F (by me now) | **yes** | Quotes verbatim-accurate; numbers accurate; page range wrong; one caveat dropped (THEO-8). |
| 5 | **SKooP** arXiv 2607.11624 (§8.2) | critic-only Koopman prediction | none (main context) | F (by me now) | **yes** | Accurate. "the actor only requires xk as input" is verbatim; Cyberdog 2 bipedal confirmed. |
| 6 | **LC-SAC** arXiv 2602.04132 (§9 cat 1, §9 ranking 5) | negative signal, standing prohibition | `survey_critic_value.md` (HTML) | F | **yes** | Numbers right, framing overstated (THEO-3). |
| 7 | [97] Bruder/Fu/Vasudevan arXiv 2010.09961 (§13.1) | affine-vs-bilinear resolved | `cluster_coherent_bilinear.md` | F | **yes** | Theorems real; the decimal numbers are figure-digitized, not stated in the paper (THEO-6). |
| 8 | [37] CCK arXiv 2403.16306 (§13.3) | CCK verdict = NO | `cluster_coherent_bilinear.md` | F | no | Mechanism description internally consistent; not re-fetched. |
| 9 | [43] arXiv 2504.21215 (§13.1) | 80–100% NMPC failure | `cluster_coherent_bilinear.md` | F | no | Doc↔report numbers match. |
| 10 | [86] KoopNet ICRA 2022 (§14.1) | "survey's online-update phrasing is WRONG" | `table1_aerial_disturbance.md` | F | **yes (survey side)** | Overreach (THEO-9). |
| 11 | [50] arXiv 2411.14321 (§14.2) | domain-shift ≠ DR | `table1_legged_domainshift.md` | F | no | Doc↔report consistent. |
| 12 | **[131]** (§14.2 side-find) | "survey citation error"; SSSD lead | `table1_legged_domainshift.md` | **X (mis-resolved)** | **yes** | **Wrong reference entirely** (THEO-2). |
| 13 | **arXiv 2603.03740** Kinova (§9 cat 7, §15.2) | 25 Hz QP; A,B-only fine-tune | `survey_safety_constraints.md`, `s2r_*` | F | **yes** | Quote ✓, 2.8% ✓, **QP rate fabricated** (THEO-4). |
| 14 | arXiv 2509.24920 S-G-W metric (§15.3) | gap-meter primitive, novel to point at robots | `s2r_model_correction.md` | P | **yes** | Exists; "synthetic/fluid only" understates its validation (THEO-10). |
| 15 | arXiv 2409.10347 digital twin (§15.2) | −5.2% sim2real | `s2r_model_correction.md` | P | **yes** | 5.2% confirmed in abstract; the 0.1539→0.1458 m pair remains P. |
| 16 | **Bruder residual Koopman IJRR 2025** (§15.2) | "strongest template"; numbers "unverified — PDFs corrupted" | `s2r_model_correction.md` | **U** | **yes** | Free full text exists at NASA NTRS; abstract bears on a claim §15.2 declares absent (THEO-5). |
| 17 | FADA arXiv 2606.28476 (§15.2) | freeze planner, ~2 min real | `s2r_policy_transfer.md` | P | **yes** | Accurate ("finetunes only the IDM using approximately 2 minutes"). |
| 18 | arXiv 2605.26452 CBF filter (§9 cat 7) | zero violations CartPole, mixed locomotion | `survey_safety_constraints.md` | F | **yes** | Accurate. |
| 19 | arXiv 2601.01076 conformal reachability (§9 cat 7) | exists | `survey_safety_constraints.md` | P | **yes** | Accurate. |
| 20 | OM-Koop (IEEE, doc 11123429) (§9 cat 5, §15.1) | field-validated real USV/AUV | `survey_observer_adaptation.md` | P | **yes** | Accurate. Note it is *steering* dynamics + LSTM-augmented. |
| 21 | KOROL 2407.00548 / KOAP 2410.07584 (§9 cat 6) | rollout-consistency; 1% action labels | `survey_imitation_distill.md` | F | partial | Numbers match report; KOAP's diffusion-planner half is dropped by the doc's compression. |
| 22 | KATS (§9 cat 4) | "unverified maturity" | `survey_offline_symmetry.md` | **U** | no | Correctly flagged by the doc. |
| 23 | DeepKoCo [116] (§1, §9 cat 2) | latent planning | survey bib | **S/title-only** | no | Correctly flagged by the doc. |
| 24 | KODex CoRL 2023 (§9 cat 6) | analytic per-task | `survey_imitation_distill.md` (numbers **S**, self-flagged) | S | no | Doc uses no numbers from it — OK. |
| 25 | Dyna-Koopman R-B (§9 cat 2) | 25.6×, >40% | `survey_model_based.md` (arXiv 2603.28074) | F | no | Numbers match; the *name* "Dyna-Koopman" is the doc's invention (THEO-14). |
| 26 | KFC/KFC++ ICML 22 (§9 cat 4) | D4RL 58→94.2, 79→108 | `survey_offline_symmetry.md` | F | no | Matches report exactly. |
| 27 | KORR 2509.12562, RK-MPC, RKMPC F1TENTH (§9 cat 3) | ~6 pt; 500 Hz; −11.7~22.1% | `survey_residual_hybrid.md` | F | no | All three match the report verbatim. No drift. |

**Provenance summary**: 27 load-bearing items. 1 mis-resolved (12), 1 with a fabricated number (13),
2 admitted-unverified but still cited as templates/leads (16, 22), 1 title-only (23), 1 snippet-only
but unused (24). The two items the doc leans on hardest for its *positive* revision (KIPPO, SKooP)
have **no sub-report at all** — they were read only in main context, which is exactly the material
most likely to be lost to compaction. I re-verified both; they hold.

---

## 2. Findings

### THEO-1 — MAJOR — §1 / §4: the "exactly three roles" absence argument omits that the survey says it does not cover RL

Doc (§1, l.46): "Koopman × RL in the survey — exactly three roles, none of which is 'lift the policy's
input'", used to ground §4's "Verdict: NOT SUPPORTED by the paper" and §5's "No passage supports
substituting one for the other."

Source (`pdftotext` of the local PDF, p.1094): "…and RL, where Koopman models are used to either
approximate environment dynamics [67] or support the design of critic networks [103]. **Due to space
limitations, we do not expand on these additional topics here**, but representative examples can be
found in Table I."

The survey self-declares its Koopman×RL coverage is non-exhaustive by editorial choice. An
absence-of-evidence verdict over an admittedly-truncated section is not evidence of absence — and §8
proves it empirically: one web search produced KIPPO, a directly on-point precedent published *before*
the doc's analysis. The doc revised the verdict but never revised the *epistemic claim* that generated
it; §1 still reads as an exhaustive index of Koopman×RL. Any future reader re-deriving a verdict from
§1 will repeat the same mistake.

### THEO-2 — MAJOR — §14.2: reference [131] is mis-resolved; both the "survey citation error" accusation and the SSSD lead are wrong

Doc (§14.2): "[131] contains Streaming SSD (SSSD) — online fixed-memory Koopman subspace update; lead
for the deployment observer… Note: survey's in-text claim that [131] is a legged-robot modeling study
is a citation error (it is general SSD theory)." The SSSD lead is then carried into §9 priority item 3
("SSSD as the online update primitive").

Source (survey bibliography, p.1107): `[131] D. Ordoñez-Apraez et al., "Dynamics harmonic analysis of
robotic systems: Application in data-driven Koopman modelling," L4DC 2024.` The Haseli & Cortés
SSD/SSSD paper the sub-report actually read is **[31]** (`M. Haseli and J. Cortés, "Learning Koopman
eigenfunctions and invariant subspaces from data…"`), not [131]. `table1_legged_domainshift.md` l.20
lists [131] as Haseli & Cortés — an off-by-100 bibliography lookup that the doc inherited without
re-checking.

Consequences: (a) the doc records a **false citation error against the source survey** — [131]
(symmetry-based Koopman modeling of robotic systems, evaluated on legged platforms) is a defensible
citation for "modeling the full-body or local leg dynamics of legged robots"; (b) the SSSD lead — a
named primitive in the medium-term shortlist — is attached to a paper that does not contain it. The
lead itself survives under the correct number [31]; the accusation does not.

### THEO-3 — MAJOR — §9 cat 1 / ranking item 5: the LC-SAC negative result is hardened past what the paper supports

Doc: "**LC-SAC negative signal: on 3D quadrotor (closest analog) ALL Koopman-Lyapunov variants
underperform vanilla SAC (-8~-15%), reward-shaping variant collapses (-93%)**", promoted to standing
policy in ranking item 5: "do not bolt Koopman-Lyapunov constraint terms onto the actor in high-DOF
underactuated settings."

Source (arXiv 2602.04132, Table III, fetched): tracking 125.5±7 / 135.9±14 / 8.2±2 vs SAC 147.3±10;
stabilization 150.8±5 / 146.0±16 / 11.9±12 vs SAC 165.7±23. The point estimates do go the doc's way,
but (i) the ±σ bands overlap for every non-collapsing variant (147.3±10 vs 135.9±14 is not a
distinguishable difference at 5 seeds); (ii) the paper's own narrative reads the opposite way — "On
stabilization tasks where the reference is a fixed setpoint, the constrained variants match or exceed
SAC" and "the constrained methods substantially reduce trial-to-trial variance" — a variance benefit
the doc's compression deletes entirely, which is notable given that variance reduction is the exact
benefit the doc credits KIPPO with two sections earlier; (iii) the collapse figure is −94% (tracking) /
−93% (stabilization), and it belongs to the *reward-shaping* variant, i.e. it is evidence against
reward shaping, not against constraint terms. A single 5-seed simulation paper with overlapping error
bars should not become a durable prohibition — the doc's own `.claude/rules/03` standard ("sign
consistency is not magnitude", "no premature assertions") applies to negative verdicts too.

Bonus: the doc files LC-SAC under category 1 "Critic/value-side", while its own sub-report says the
Lyapunov constraint "keeps it entirely on the actor side" — and the doc's own ranking item 5 says
"actor". Self-inconsistent taxonomy in the same section.

### THEO-4 — MAJOR — §9 cat 7: the "QP ~0.0389 s/step ≈ 25 Hz" figure for arXiv 2603.03740 does not exist in the paper

Doc (§9 cat 7): "**Jung whole-body KMPC (arXiv 2603.03740, real Kinova 7-DoF, QP ~0.0389 s/step = ~25 Hz
on desktop, 2.8% residual infeasibility)**", and the blocker it drives: "25 Hz on DESKTOP for a simpler
plant = caution at our bus rate on embedded".

Source (arXiv 2603.03740, Table II, fetched twice, plus an explicit string search): the number 0.0389
(or 0.039) **does not appear anywhere in the paper**. Table II reports `KMPC (Ours): Avg. Comp. Time
0.21913 s` per control step. The paper claims "over 4.2× faster" than NMPC and states no Hz figure at
all. Verified-correct in the same citation: the frozen-embedding quote ("we collect hardware data and
fine-tune only the A and B matrices of the lifted linear dynamics") and the 113/4000 ≈ 2.83%
infeasibility.

Impact: 0.21913 s/step is **4.6 Hz**, 5.6× slower than the doc's figure. The doc's conclusion direction
is unchanged (still a caution) but its magnitude is wrong in the dangerous direction — a reader sees
"lands exactly at our 25 Hz bus ceiling" (marginal, tune-able) rather than "5× below the bus rate on
desktop hardware for a fixed-base 7-DoF arm" (structurally out of reach for a coupled vehicle+arm on
embedded). The error originates in `survey_safety_constraints.md` l.24/48, which presents it as
"fetched directly"; the doc amplified it into the section's single quantitative gate.

### THEO-5 — MAJOR — §15.1/§15.2: "confirmed white space" is declared partly on the strength of a paper the doc admits it never read, whose abstract is freely available and bears on the missing claim

Doc (§15.2): "Bruder residual Koopman (IJRR 2025, real soft-robot arm)… **Strongest template for the
refit half.** (Number-level claims unverified — PDFs corrupted.)" followed by "No real-data
sample-efficiency curve exists for the sim-Koopman + real-residual recipe".

Source (one search): the paper is Bruder, Bombara, Wood, "A Koopman-based residual modeling approach
for the control of a soft robot arm", IJRR (doi 10.1177/02783649241272114) — and an **open-access full
text is hosted at NASA NTRS** (`ntrs.nasa.gov/api/citations/20250001907/downloads/ResidualKoopmanModel_IJRR.pdf`).
Its abstract already states the method requires "only <10% of the data compared to benchmarks" and uses
"real-time recursive Koopman model updates" — i.e. it reports a data-efficiency figure for exactly the
physics-prior + data-residual Koopman recipe the doc labels the strongest template and simultaneously
declares has no sample-efficiency evidence.

Two defects: (a) "PDFs corrupted" is a solvable obstacle, not a provenance ceiling — the doc's
strongest-template designation rests on an unread paper when a free copy is one search away; (b) the
"no sample-efficiency curve exists" statement in the same paragraph is at minimum unsafe until that
paper is read. (Caveat in the doc's favour: Bruder's "sim" is an analytical physics model, not a
simulator, and <10% is relative to data-driven Koopman baselines rather than a sim→real curve — so the
white-space claim may survive. It has not been *shown* to survive.)

### THEO-6 — MAJOR — §14.2 vs §8.1: the recommended anti-collapse guard is the design KIPPO explicitly rejects, and the doc never notices

Doc (§14.2): "Anti-collapse guard: z = [x, g'(x)] (concat raw state) makes A=B=0, g=0 degenerate
solution impossible — **adopt for phi_x regardless**." Doc (§4.4.ii) makes the same move: the fixes for
trivial optima are "reconstruction (the failed path) or identity-inclusion". Doc (§14.1, [86]) reuses
it a third time: "recon loss DISABLED (raw state carried in z)".

Source (KIPPO, IJCAI-25, §3.1, extracted locally): "Unlike [Song et al., 2021], **we do not concatenate
the original state with the encoded state, as this restricts the set of systems where linearization is
possible.** Specifically, finding a linear representation of a non-linear system that includes the
original state becomes impossible when the system has multiple fixed points or general attractors…
linear systems (with a single fixed point at the origin) are not topologically conjugate to non-linear
systems with multiple fixed points [Draeger et al., 1995]."

The doc's flagship precedent — the one paper that makes its top shortlist item defensible at all —
deliberately rejects the guard the doc says to "adopt regardless", and gives a theoretical reason that
applies directly to a 6-DOF UUV+arm (a plant with multiple equilibria: hover attitudes, arm
configurations, fault regimes). This is not a small conflict: it is the difference between KIPPO's
architecture (expansive AE + reconstruction) and [50]/[86]'s (identity-inclusion, no reconstruction),
and the doc's §8.4 collapse-risk argument ("expansive AE where reconstruction is easy and
collapse-unlikely") silently assumes KIPPO's branch while §14.2 mandates the other. One of them must be
dropped before a proposal is authored.

### THEO-7 — MINOR — §11.3: "try smaller m first" runs against KIPPO's own reported trend

Doc (§11.3): "note our 72D obs is partially pre-lifted (52D temporal), so try smaller m first."

Source (KIPPO §E, extracted): latent dims swept over {16, 32, 48}; "Overall, dimensions of 32 or higher
tend to boost returns and reduce variance"; "Larger dimensions generally yield higher returns and lower
variability." The doc's 2–4× rule-of-thumb attribution is **correct** (the paper does state "typically
set to 2-4 times the state dimension") — no complaint there — but the empirical guidance is
larger-is-better, and the doc's inference to the contrary is its own extrapolation from a premise
(pre-lifted obs) with no cited support. State it as an untested inference, not as a reading of KIPPO.

### THEO-8 — MINOR — §8.1: KIPPO citation details and one dropped caveat

(a) Page range: doc says "IJCAI 2025, pp.4994–4997" and "Read in full (pp. 4994–4997)". Actual:
**pp. 4994–5002** (IJCAI proceedings entry 556). Claiming a full read while citing a page range that
covers roughly half the paper is a provenance smell — in this case the read was in fact adequate (I
verified both quotes at source), but the citation is wrong and should be fixed.
(b) Numbers: "+6–60% mean return" ✓ (paper: 6.36%–60.26%); "26–91% variance reduction" ✓ (paper:
"reducing variance by 26.89-91.43% versus PPO") — but the paper appends "**(one exception)**", which
the doc drops. Given the doc uses variance reduction as the mechanism hypothesis for the whole arm,
the exception belongs in the record.
(c) Verified-clean and worth keeping: "The policy optimization algorithm operates on the encoded states
y_t = φx(xt)" is **verbatim** (§3, p.4996), and the appendix repeats "The actor and critic networks
operate on the encoded states." The single most load-bearing quote in the document is accurate.

### THEO-9 — MINOR — §14.1: "the survey's 'online update' phrasing is WRONG" overreaches

Doc (§14.1, bolded): "**Survey's 'online update' phrasing is WRONG** — verified against the paper:
runtime is ordinary re-encoding of a fixed phi, no parameter adaptation."

Source (survey p.1099): "An NN is combined with the Koopman operator **to update both the lifted states
and inputs** of the robot with online measurements." The survey says the *lifted states* are updated
with online measurements — which is precisely re-encoding, and therefore literally true. The doc's
paper-level conclusion (KoopNet is frozen-at-deployment evidence, not online-adaptation evidence) is
sound and useful; the accusation against the survey's wording is not supported by the wording.

### THEO-10 — MINOR — §15.3: the S-G-W metric's validation scope is understated

Doc (§15.3): "Spectral-Grassmann Wasserstein metric (arXiv:2509.24920)… **validated only on
synthetic/fluid systems**".

Source (abstract, fetched): the paper reports evaluation on "simulated **and real-world** datasets",
on ML tasks including dimensionality reduction and classification. The sub-report
(`s2r_model_correction.md` l.24) says "1D systems and fluid-dynamics numerical experiments… no robot,
no sim-vs-real" — the "no robot / no sim-vs-real" part is what actually matters for the novelty claim
and appears correct; "synthetic only" is not. Minor, but it is the doc's own evidence for the
APPLICABLE-NOW gap-meter item, so the scope should be stated accurately.

### THEO-11 — MINOR — §13.1: the [97] decimals are digitized from log-scale figures, not stated in the paper

Doc (§13.1): "Empirical signature: linear error flat ~0.55-0.60 from 10 to 927 basis fns; bilinear drops
to ~0.03-0.05. MPC: 74.3 cm (affine) vs 2.03 cm (bilinear) vs 1.92 cm (full nonlinear, 500x compute)."

Source (arXiv 2010.09961v3, extracted locally): none of `74.3`, `2.03`, `1.92`, `0.55`, `0.60`,
`0.03`, `0.05` appear in the text. Results are presented as Fig. 2 and Fig. 4 (both log-scale plots);
the paper's *textual* claims are the weaker "its mean tracking error is more than 15×" and "the mean
computation time for K-NMPC is more than 500×". `927` appears (basis-function count) ✓, and the "500×"
in the doc is correct — note this contradicts the sub-report's own table (1160 ms / 9.6 ms = 121×),
so the doc happened to pick the right claim from an internally inconsistent report.
The §13.1 verdict ("resolved AGAINST pure affine") rests on Theorem II.1 / Corollary II.1, which are
real, so the verdict survives — but three-significant-figure centimetre values presented as measured
results are figure-reads and should be marked as such.

### THEO-12 — MINOR — §15.1 contradicts §9 cat 2 on the survey's sim-to-real content

Doc (§15.1): "The survey (arXiv:2408.04200 full text) contains **ZERO occurrences** of sim-to-real /
reality gap / domain randomization / domain adaptation."
Doc (§9 cat 2): "Ji **Real2Sim2Real** continuum (= survey ref [67], TIE 2025)".

Source (my `pdftotext` + grep of the local PDF): exactly one match in the whole document — reference
[67]'s title, "Efficient **Real2Sim2Real** of continuum robots…". The body-text claim is otherwise
correct and the finding (Koopman literature does not frame itself in sim-to-real terms) is genuinely
useful; scope it to body text so it stops contradicting the doc's own citation two sections earlier.

### THEO-13 — MINOR — §6 was never amended after §8/§10 superseded it

§6 still reads "Recommendation: do not run as proposed" and proposes the physics-informed feature
augmentation arm set `{TRPO, TRPO+features, NoEncoder, NoEncoder+features}` as *the* minimal variant.
§8.4 then proposes a different arm set (`{TRPO, TRPO+phi_x, NoEncoder, NoEncoder+phi_x}`), and §10/§15.4
supersede that again with block-partitioned targets + bilinear H + z-conditioned scaffold. §7 carries a
"see §8" pointer, but a reader landing on §6 gets a stale experiment design. In an accreted document
this is how a superseded arm set gets launched.

### THEO-14 — MINOR — §9 cat 2 gives a paper a name it does not have

"Dyna-Koopman Rayleigh-Benard (25.6x faster rollouts, >40% wall-clock cut)". The numbers are faithful to
`survey_model_based.md`, but the underlying work is Plotzki & Peitz, "Koopman-based surrogate modeling
for reinforcement-learning-control of Rayleigh-Bénard convection" (arXiv:2603.28074) — "Dyna-Koopman"
appears nowhere. Invented shorthands become unresolvable citations once the sub-reports are garbage-collected.

### THEO-15 — MINOR — §9 cat 6 compression drops KOAP's planner half and the untested-stripped-variant caveat

Doc: "KOAP (arXiv 2410.07584, LSTM-over-history latent-action + Koopman consistency + recon, wins at 1%
action labels)" → priority item 1: "add a SUPERVISED linear-consistency term on the student…
(KOROL/KOAP minus the banned reconstruction term). No new label source/loss class".

`survey_imitation_distill.md` is more careful in two ways the doc drops: (a) KOAP is a "plan-then-control"
system whose Koopman controller only exists to track a **diffusion planner's** output — the doc's
compression makes it read as a pure distillation architecture; (b) the report explicitly warns "only a
reconstruction-stripped, consistency-only variant is admissible under the settled decision, **and that
stripped variant is untested — neither in KOAP's own ablations nor here**". The doc's top-ranked
near-term probe therefore rests on an ablation nobody has run, which the doc mentions only obliquely
("single-K-under-DR is the untested central risk").

---

## 3. What I checked and found clean (stated so it is not re-litigated)

- All 10 "nonstandard-looking" arXiv IDs resolve to the claimed papers. No hallucinated identifiers.
- KIPPO's two load-bearing quotes, its +6–60% / 26–91% numbers, its 4-seeds-per-env protocol, its
  MuJoCo/Box2D suite, its decoupled-optimizer design, and its 2–4× latent rule of thumb: all accurate.
- SKooP's "the actor only requires xk as input" and Cyberdog 2 bipedal tasks: verbatim accurate.
- OM-Koop's real USV/AUV field validation: real (IEEE Xplore 11123429).
- 2603.03740's frozen-embedding quote and 2.8% infeasibility: accurate (only the QP rate is wrong).
- FADA (2606.28476) ~2-min IDM fine-tune, 2409.10347's 5.2% figure, 2605.26452's CartPole/locomotion
  split, 2601.01076's identity: all accurate.
- KORR ~6 pt, RK-MPC 500 Hz, RKMPC F1TENTH −11.7~22.1% / 20% data, Dyna-Koopman 25.6× / >40%, KFC
  hopper-medium 58.0→94.2 and walker2d 79.2→108.0: zero numeric drift between doc and sub-reports.
- Survey page cites (1091, 1092, 1094, 1099, 1101) and vol/page metadata: correct.

## 4. Research questions that would close the open items

1. Read the free NTRS copy of Bruder/Bombara/Wood IJRR 2025 and re-test §15.2's "no real-data
   sample-efficiency curve exists" against it (THEO-5).
2. Re-run the §14.2 legged cluster against reference **[31]** (Haseli & Cortés, SSD/SSSD) and drop the
   [131] citation-error claim; separately re-read [131] (Ordoñez-Apraez, L4DC 2024, symmetry/DHA) since
   symmetry-structured Koopman modeling is adjacent to SKooP and was never actually read (THEO-2).
3. Recover the real compute figure for a Koopman safety filter at our plant scale — 2603.03740's
   0.21913 s/step is desktop, fixed-base, 7-DoF; the cat-7 blocker needs a scaled estimate, not a
   borrowed Hz number (THEO-4).
4. Decide the phi_x degeneracy guard on evidence: KIPPO's reconstruction-only expansive AE vs
   [50]/[86]'s identity-inclusion, given a plant with multiple equilibria. KIPPO's topological-conjugacy
   objection is checkable against our attitude/arm/fault equilibrium structure (THEO-6).
5. Re-read LC-SAC's seed protocol and variance columns before letting it stand as a prohibition; the
   variance-reduction result may actually *support* the KIPPO mechanism hypothesis (THEO-3).
