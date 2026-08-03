# SSM-as-Koopman-Student Research Note (key: ssm_student)

## Q1 — MamKO: does it exist, what does it do, results?

**Yes, it exists and is exactly what the framing anticipates.** *MamKO: Mamba-based Koopman
operator for modeling and predictive control* (Zhaoyang Li, Minghao Han, Xunyuan Yin, Nanyang
Technological University), published at **ICLR 2025** (poster). Full text verified via
pdftotext of the camera-ready PDF.

**Exact mechanism.** MamKO targets *time-varying* nonlinear systems `x_{k+1}=f(x_k,u_k,k)`. It
lifts state to `z_k=ψ(x_k)` (a learned observable/encoder) and, instead of one fixed Koopman
triple `(A,B,C)`, generates a **time-varying** triple `(Ā_k, B̄_k, C_k)` at every step from a
window of `H` past lifted-state/input pairs. Concretely: 1D convolution over the historical
`[z_{k-H:k-1}, u_{k-H:k-1}]` window extracts features, which two FCNNs map to `B_k`, `C_k`, and a
per-step sampling-period sequence `T_k`; a **single trainable diagonal matrix `A`** is stabilized
via `Ã = −CELU(A)` (a *negative* CELU, not Mamba's negative-exponential, chosen specifically so
eigenvalues can still be non-negative for systems that aren't inherently stable, e.g. genetic
oscillators) and then discretized by **zero-order hold** (`Ā=e^{AT}`, `B̄=∫e^{At}dt·B`) using the
generated `T_k`. So `Ā_k` varies over time via the generated sampling period, `B̄_k`/`C_k` vary via
direct network generation — a genuine Mamba-style "matrices generated from data" scheme, but
explicitly **not** Mamba's own causal selective-scan recurrence: the paper states directly that
applying vanilla Mamba is "impractical" here because (a) Mamba's inputs are token-like with no
physical state, and (b) generating `B_k` from `u_k` itself would make the `B_k u_k` term bilinear
in the control input, breaking convexity of the downstream MPC — so MamKO generates matrices only
from *historical* (not current-step) data.

**Task and results.** Modeling + **MPC control**, not RL. Benchmarks: CartPole (a mechanical
system with an added time-varying-parameter variant), a gene regulatory network (GRN), and RSCP
(a chemical recycle-stream/separator process), each in time-invariant and time-varying form.
Baselines: DKO-based MPC (Lusch et al. 2018 deep Koopman), MLP-based MPC, and SAC. MamKO-based MPC
wins on steady-state error across all systems (e.g. cart-position steady-state error reductions of
98.38%/92.92%/… vs MLP/DKO/SAC baselines on the time-varying CartPole; 49–62% reductions on RSCP
variants) while keeping computation time close to DKO-MPC and far below MLP-MPC (Tables 2–3, 9,
10). An ablation on the discretization step (Table 1) and a lifting-dimension sweep (Table 7,
best at dim 8) are also reported.

**Fuzzy-match, Mamba+Koopman-bilinear at snippet depth**: found two directly relevant follow-ons,
both post-MamKO and both arXiv IDs consistent with 2026: (1) *Bilinear Mamba-Koopman Neural MPC
for Varying Dynamics* (Pagi & Sorek, arXiv 2605.04793) — extends the Koopman-Mamba line to a
**bilinear** control-dependent latent form (`B(u)` interaction, not just linear `Bu`), reported to
add <1% parameters via a low-rank structure; abstract/snippet depth only, not fetched full-text.
(2) *Bilinear Input Modulation for Mamba: Koopman Bilinear Forms for Memory Retention and
Multiplicative Computation* (arXiv 2604.17221) — argues the diagonal linear recurrence in vanilla
Mamba/S4/S5 "fundamentally limits representational power, as no multiplicative interaction
between the hidden state and the input can occur within the recurrence itself," and proposes a
Koopman-bilinear-form fix; snippet depth only.

## Q2 — Published SSM-class students in teacher-student distillation for robot control

**One directly on point, found and fetched in full: REAL** (*Robust Extreme Agility via
Spatio-Temporal Policy Learning and Physics-Guided Filtering*, arXiv 2603.17653, legged
locomotion). Privileged cross-modal-attention teacher → deployable student with a **FiLM-modulated
Mamba temporal backbone**. The student's Mamba module processes a **10-frame proprioceptive
sequence** (IMU + joint encoders) — a short window, comparable in order of magnitude to ALBC's
24–50-step student window. Reported numbers: full REAL (with Mamba) SR 0.78 / MEV 18.41 vs REAL
**without Mamba** SR 0.51 / MEV 89.96 (Table V) — a large ablation gap attributable to the temporal
backbone. Latency: Mamba backbone 13.14 ms/step vs a Transformer alternative at 23.07 ms/step,
which violates their 20 ms / 50 Hz real-time budget — the stated reason for choosing an SSM over
attention. **Caveat**: the paper does **not** report a GRU or TCN student baseline — only
no-Mamba and Transformer comparisons. So it demonstrates "SSM beats no-recurrence and beats
Transformer at this latency budget," not "SSM beats GRU," leaving the GRU-vs-SSM student question
open in the literature we could locate.

Adjacent but not privileged-distillation-shaped: **LocoMamba** (arXiv 2508.11849) uses Mamba
directly as the RL policy backbone (vision-driven quadruped locomotion, end-to-end DRL, not
teacher-student), reporting gains in return/safety/sample-efficiency over unspecified SOTA
baselines — relevant as further evidence SSMs work in real-time legged control loops, but it is
not a distillation setup and we did not verify its baseline list at full-text depth. **KD-Mamba**
(trajectory prediction, not control) and **Mamba Policy** (diffusion-policy manipulation, not
teacher-student RL distillation) surfaced but are off-target for this question and were not
pursued further.

**No paper found** doing exactly "privileged asymmetric-actor-critic teacher → GRU/TCN baseline vs
S4/S5/Mamba-class student, ablated head-to-head" for legged/manipulator RL. REAL is the closest
real precedent (Mamba-vs-none, Mamba-vs-Transformer) but leaves the GRU comparison as an open gap
that any ALBC SSM-student experiment would be filling, not confirming from prior art.

## Q3 — What the SSM literature already settles (would not need re-deriving)

Verified via full-text pdftotext of Lu et al., *Structured State Space Models for In-Context
Reinforcement Learning* (arXiv 2303.03982, NeurIPS 2023) — the canonical "S5 for RL" paper.

- **Stable diagonal parameterization + HiPPO-style init**: S5 uses a diagonalized HiPPO
  initialization for its state matrix (paper explicitly credits Gu et al.'s HiPPO for "a special
  matrix initialisation to better preserve sequence history"), inherited from the S4/S5 lineage —
  this is settled, off-the-shelf machinery, not something a from-scratch "Koopman student" needs
  to reinvent.
- **Discretization**: confirmed **zero-order hold**, matching the parenthetical hunch in the brief
  — `S5 Discretization: ZOH` appears explicitly in their hyperparameter table.
- **Parallel-scan training**: S5 replaces S4's convolution with an associative parallel scan
  (`O(log N)` depth), which is what makes long-context training tractable; this is a solved,
  reusable primitive, not new research.
- **Episode-boundary / reset handling — confirmed, and yes, this is exactly Lu et al.**: verbatim
  from the method section, S5's associative scan operator is extended with a binary "done" flag
  `d_k` folded into each scan element `e_k=(Ā, B̄u_k, d_k)`. The redefined operator `⊕` short-circuits
  accumulation whenever the right-hand element's done-flag is 1 (`a_j ⊕ a_i = (a_j) if a_j.c=1`),
  which the paper proves stays associative (so the `O(log N)` parallel scan still applies) and
  handles **multiple resets within one rollout** correctly (worked example in the text: resets at
  step n correctly zero out cross-episode memory even as the scan continues past it). This
  directly answers "handling of resets/episode boundaries" — it is a solved, published, provably-
  correct mechanism (their §3.1 "Resettable S5"), not something ALBC would need to derive from
  first principles for its own episode-per-env RL rollouts.
- **Baseline comparison, S5 vs GRU/LSTM**: on POPGym / bsuite memory-length tasks and Meta-RL
  settings, S5(+reset) is reported to **outperform GRU while running ~6x faster**, and to
  outperform LSTM in both performance and speed on DMControl-based generalization tasks; GRU was
  itself selected as "most performant" RNN baseline in prior work (Morad et al.) that this paper
  benchmarks against.

## Q4 — Honest counter-evidence: does the SSM advantage hold at ALBC's short-context regime?

Evidence is **mixed / thin, not a clean yes**.

- **Directly favorable, at comparable scale**: REAL's Mamba student uses a 10-step window (same
  order of magnitude as ALBC's 24–50-step, 25 Hz window) and shows a large ablation gap over
  no-recurrence — so short-context SSM students are not obviously starved for signal at this
  scale in a real control task. The S5-for-RL bsuite/POPGym tasks Lu et al. use also skew toward
  short-to-medium memory-length settings (the classic bsuite "memory length" suite spans short
  horizons, not book-length context), and S5 wins there too — so the "SSM advantage only shows up
  at long context" prior is **not obviously true for the RL literature specifically**; that framing
  comes more from NLP/long-range-arena results.
- **General architectural counter-evidence (not RL-specific, not context-length-specific)**:
  *Achilles' Heel of Mamba* (Chen et al., arXiv 2509.17514, NeurIPS 2025) shows Mamba has a
  structural **asymmetry bias** from its causal convolution stage — it favors compositional over
  symmetric solutions and struggles at tasks requiring matching/comparing a sequence against its
  own reverse. The authors attribute this to the pre-SSM causal convolution, not the SSM
  recurrence itself. This is a genuine, verified architectural limitation, but it is about
  symmetry/compositionality in synthetic sequence tasks, not a length- or scale-conditioned
  GRU>SSM result — we found **no paper reporting SSM-class models underperforming GRU specifically
  at short context / small scale** in a head-to-head RL or control benchmark. That specific
  comparison appears to be an open gap in the literature, not a settled negative result.
- **Net read for ALBC**: nothing found rules out an SSM student at a 24–50-step window; the
  closest real precedent (REAL) succeeds at a similar window. But because no paper runs the direct
  GRU-vs-SSM-student ablation at this scale, the claim "SSM will beat GRU as ALBC's student" is
  not something the literature already answers — it would be an empirical question for ALBC's own
  ablation, not a result importable from published work.

## References

1. Zhaoyang Li, Minghao Han, Xunyuan Yin. "MamKO: Mamba-based Koopman operator for modeling and
   predictive control." ICLR 2025 (poster). OpenReview: https://openreview.net/forum?id=hNjCVVm0EQ
   ; PDF: https://proceedings.iclr.cc/paper_files/paper/2025/file/e99847f8d8006806fd35d6f536136c0d-Paper-Conference.pdf
   — **verification: full-text-read** (pdftotext of camera-ready PDF, method §3, control §4, all
   result tables inspected).
2. Chris Lu, Yannick Schroecker, Albert Gu, Emilio Parisotto, Jakob Foerster, Satinder Singh, Feryal
   Behbahani. "Structured State Space Models for In-Context Reinforcement Learning." arXiv:2303.03982
   (NeurIPS 2023). https://arxiv.org/abs/2303.03982 — **verification: full-text-read** (pdftotext of
   arXiv PDF, §3.1 "Resettable S5" and hyperparameter/results tables inspected).
3. "REAL: Robust Extreme Agility via Spatio-Temporal Policy Learning and Physics-Guided Filtering."
   arXiv:2603.17653. https://arxiv.org/abs/2603.17653 — **verification: full-text-read** (WebFetch of
   arXiv HTML render; architecture, Table V ablation, and latency numbers extracted and quoted).
4. Tianyi Chen et al. "Achilles' Heel of Mamba: Essential difficulties of the Mamba architecture
   demonstrated by synthetic data." arXiv:2509.17514 (NeurIPS 2025 poster).
   https://arxiv.org/abs/2509.17514 — **verification: abstract/snippet only** (not fetched
   full-text; findings summarized from search-engine abstract synthesis).
5. Matan Pagi, Zohar Sorek. "Bilinear Mamba-Koopman Neural MPC for Varying Dynamics." arXiv:2605.04793.
   https://arxiv.org/abs/2605.04793 — **verification: snippet only**.
6. "Bilinear Input Modulation for Mamba: Koopman Bilinear Forms for Memory Retention and
   Multiplicative Computation." arXiv:2604.17221. https://arxiv.org/html/2604.17221v1 —
   **verification: snippet only**.
7. "LocoMamba: Vision-Driven Locomotion via End-to-End Deep Reinforcement Learning with Mamba."
   arXiv:2508.11849. https://arxiv.org/abs/2508.11849 — **verification: snippet only** (search-engine
   abstract synthesis; not fetched full-text, no baseline list verified).
8. Korda, M. & Mezić, I. (2018) and Lusch, Kutz, Brunton (2018) deep-Koopman-MPC baselines are cited
   inside MamKO (ref. #1) as its DKO-based-MPC comparator — not independently verified here, noted
   only as provenance for MamKO's baseline.

## GitHub repos

- S5-for-RL (Lu et al.): repository referenced in the paper's abstract-summary search result as
  `github.com/luchris429/s5rl` — **not independently browsed/verified**, cite with caution; confirm
  the URL by visiting the repo before relying on it for an implementation reference.
- No official MamKO or REAL GitHub link was surfaced in the search results retrieved; not claiming
  one exists or doesn't.

## Implications for ALBC

1. **The "Koopman-linear recurrent student is a deep SSM" framing is now doubly supported**: not
   only is S4/S5/Mamba mathematically a linear-recurrence-plus-input-map (per the original doc's
   framing), there is a **published paper (MamKO) that runs the reverse direction** — building a
   Koopman operator generator explicitly *from* the Mamba structure for control. That is strong
   corroboration that "Koopman student" and "SSM student" are the same design space, not an
   ALBC-specific analogy.
2. **MamKO's engineering choices are directly reusable/relevant**, not just conceptually adjacent:
   (a) its negative-CELU stabilization of the diagonal `A` (vs. Mamba's negative-exponential) is a
   concrete alternative to plain HiPPO-negative-real-part if ALBC's plant has any near-unstable
   modes; (b) its explicit reason for generating `B_k`/`C_k` from **historical**, not current-step,
   data (to avoid a bilinear `B_k u_k` term breaking downstream optimization) is a design
   constraint ALBC should keep in mind if any part of the pipeline (e.g. an MPC-style planner
   downstream of the student) needs convexity — pure behavior-cloning/RL distillation likely
   doesn't care, but it's worth flagging.
3. **Reset handling is not a research risk for an SSM student in ALBC's env-per-episode RL
   rollouts**: Lu et al.'s resettable associative-scan operator is a published, proven, drop-in
   mechanism (already open-source per S5-for-RL) — ALBC would adopt it, not invent it, for training
   an SSM student on rollouts that cross episode boundaries.
4. **Regime-relevance verdict for the 24–50-step/25 Hz window: cautiously supportive, not proven.**
   REAL succeeds with Mamba at a similar (10-step) window in a similarly latency-constrained
   real-time control loop, and the RL-specific S5 literature (bsuite/POPGym) already operates at
   short-to-medium horizons where S5 beats GRU — so there is no literature reason to expect the
   short window to void the SSM's advantage. But **no paper directly ablates GRU-vs-SSM-student at
   this scale**, so ALBC's own GRU-vs-SSM student ablation would be original evidence, not a
   replication of a known result — plan the experiment (and its write-up) accordingly, and don't
   claim literature support stronger than "no found counter-evidence, one favorable near-analog
   (REAL), general architectural caveats exist (Achilles' Heel) but aren't context-length-specific."
