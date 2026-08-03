# Research Report: priv_critic_ppg_spr

Key: `priv_critic_ppg_spr` — two independent halves for the Koopman-lifting research doc
(`/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md`, §17-19 context, not re-surveyed here).

---

## HALF A — Auxiliary features added to an ALREADY-PRIVILEGED (asymmetric) critic

### Question
Does any published result test adding auxiliary dynamics/model-derived features to a critic that
already has privileged (asymmetric) access, in teacher-student or sim-to-real RL? Does the
"Informed Asymmetric Actor-Critic" paper (arXiv 2509.26000) bear on the marginal value of extra
critic information? Any RMA/HORA-lineage ablation varying critic input richness?

### Finding 1 — Informed Asymmetric Actor-Critic (Ebi, Ernst, Böhm, Lambrechts; ICML 2026; arXiv 2509.26000)
is the closest direct evidence, and it is about exactly this question, though not phrased as
"dynamics features." **Fetched and read at full-text depth** (PDF → `pdftotext`, all of §4-5 and
Appendix G).

Setup: the critic in an asymmetric actor-critic is conditioned on `V(h_t, i_t)`, where `i_t` is an
arbitrary state-dependent privileged signal (not necessarily the full state `s_t`). The paper's
core empirical question is exactly "does more/richer privileged information given to an already-
informed critic help or not," tested by systematically varying which privileged signal `i_t` a
critic receives — including combinations that stack multiple privileged sources on top of a
baseline one (e.g., Higher-Lower: `previous-card` vs `both-cards` [current+previous] vs `full-state`
vs `expert`; Repeat-First: `hand` vs `dealt` vs `full-state` [hand+dealt combined]; Concentration:
`first-card`/`second-card` vs `flipped-cards` [both jointly] vs `all-values`).

**Result (Table 6, Appendix G.1, 20 seeds/run):** combining more privileged signals does **not**
monotonically improve performance, and is sometimes actively worse:
- Higher-Lower: `both-cards` (4.81e-01) < `previous-card` alone (5.02e-01) < `expert` (4.92e-01) ≈
  `full-state` (4.90e-01) — the richer combined signal underperforms a single well-chosen one.
- Repeat-First: `full-state` (0.900) nominally highest mean but with the largest AUC variance in
  the table; `dealt` alone (0.876) is close behind with far lower AUC variance; `NONE` (no
  privileged signal at all, 0.829) is competitive with several privileged variants under this
  noisy-scoring regime.
- Concentration: `all-values` (full privileged state) actually *underperforms* `NONE` (no
  privileged info) — 0.145 vs 0.238 mean final return.
- Explicit statement (Appendix G.2, verbatim): *"the full-state signal `i_t = s_t` does not always
  yield the highest episodic return gains, further highlighting the practical relevance of the
  informed asymmetric actor-critic framework, which can exploit any state-dependent privileged
  information beyond full-state access."*

So this paper is direct evidence that **stacking more privileged/auxiliary information onto an
already-privileged critic has no guaranteed marginal value and can hurt** — the paper's whole
motivation is to select an informative subset rather than assume "more privileged info = better
critic." It is not phrased in terms of dynamics/model-derived auxiliary features specifically, but
the mechanism (critic conditioned on `V(h,i)` vs `V(h,i')` where `i'` is `i` plus more state-derived
components) is structurally the same experiment as adding a dynamics-auxiliary feature to an
existing privileged critic.

Caveat on relevance ceiling: environments are toy POMDPs (grid navigation, POPGym card/memory
tasks), on-policy A2C, not a TRPO/PPO-scale continuous-control robotics setting. No teacher-student
distillation stage. This constrains how far the transfer to ALBC's ConstraintTRPO+IPO asymmetric
critic (28D params + 9D latent z) can be pushed — it is evidence about the *shape* of the effect
(diminishing/negative marginal returns to piling on privileged features), not a quantitative
transferable number.

### Finding 2 — No direct evidence located for "auxiliary dynamics/model-derived features added to
an already-privileged critic" in teacher-student / sim-to-real legged/manipulation RL specifically.
Searched: "asymmetric critic auxiliary task privileged information reinforcement learning ablation",
"RMA rapid motor adaptation privileged critic ablation extra privileged information", "asymmetric
actor critic critic input richness ablation sim-to-real teacher student more privileged features
hurts helps." Results surfaced RMA (Kumar et al.), DreamWaQ, and general asymmetric-actor-critic
background (Pinto et al. 2018, Baisero & Amato 2022) but no ablation in that lineage that varies
*how much or what kind* of privileged information the critic receives while holding the actor fixed
and reports a resulting performance comparison. RMA's own ablations concern the extrinsics
vector/adaptation module (student side), not critic-input richness on the teacher side.

**Honest gap**: no RMA/HORA-lineage ablation on critic input richness was found. The IAAC paper
(Finding 1) is the only located result that directly manipulates privileged-signal richness for an
asymmetric critic and reports the performance consequence; it stands alone as evidence for this
question, not corroborated by a second independent source.

---

## HALF B — Full-text verification of PPG and SPR

Both fetched and verified at **full-text depth** via `pdftotext -layout` on the arXiv PDFs (page-
image route was not needed — `pdftotext` extraction was clean and complete for both).

### PPG — Cobbe, Hilton, Klimov, Schulman, "Phasic Policy Gradient," arXiv 2009.04416 (ICML 2021)

**Exact protocol** (§2, Algorithm 1, verified against extracted text):
- Two alternating phases per "phase" iteration: **policy phase** (`N_π` iterations of standard PPO
  updates, disjoint policy network `θ_π` and value network `θ_V`, `E_π` policy epochs + `E_V` value
  epochs per iteration) followed by one **auxiliary phase** (`E_aux` epochs over all buffered data
  `B`).
- Auxiliary-phase joint objective: `L_joint = L_aux + β_clone · E_t[KL[π_θold(·|s_t), π_θ(·|s_t)]]`,
  where `π_θold` is frozen at the phase's start and `β_clone` trades off distillation strength
  against preserving the current policy. This **is** the behavior-cloning term the brief asked to
  verify — it is a KL-to-old-policy penalty, not a literal action-matching BC loss, applied during
  the auxiliary phase only.
- `L_aux` is, in the paper's implementation, simply the value-function loss `L_value` computed on an auxiliary
  value head attached to the *policy* network (shares all parameters with the policy except final
  linear layers): `L_aux = ½ E_t[(V^π_θ(s_t) − V̂_t^targ)²]`. This is literally distillation of value
  information into the policy trunk via a shared-feature auxiliary value head — confirms the
  brief's description exactly.
- Targets `V̂^targ` are computed once during the policy phase and held fixed through the auxiliary
  phase; `L_value` and `L_joint` share no parameter dependencies so can be optimized independently.

**Stated reasons for phase separation / interference (§1, §3.4, verified):**
- Motivating premise (Introduction): *"Interference between policy and value function optimization
  can negatively impact performance when parameters are shared between the policy and the value
  function networks."* Value function optimization also "tolerates a significantly higher level of
  sample reuse than policy optimization" — the two objectives want different training regimes, not
  just different gradients.
- §3.4 (auxiliary phase frequency ablation, varying `N_π` from 2 to 32): *"performance suffers when
  we perform auxiliary phases too frequently. We conjecture that each auxiliary phase interferes
  with policy optimization, and that performing frequent auxiliary phases exacerbates this
  effect... relatively infrequent auxiliary phases are critical to success."*
- Appendix (value-function gradient detachment, referenced at line ~299-310 of extracted text): PPG
  detaches the value-function gradient at the last shared layer during the *policy* phase to prevent
  the value objective from influencing shared parameters mid-policy-phase, while allowing the full
  gradient through only during the auxiliary phase — an explicit mechanism for controlling
  *when* interference is allowed to occur, not just gating it off entirely.

**Bears directly on transfer to hard-KL TRPO:** PPG's phase separation is motivated by shared-
parameter interference and differing sample-reuse-optimality between value and policy objectives.
For a hard-KL-constrained TRPO (ALBC's setting), the analogous risk is that any auxiliary/distillation
update competes with the trust-region constraint's implicit assumption that the policy network's
representation is stable within a step; PPG's own conjecture (frequent auxiliary phases interfere
with policy optimization) supports keeping any encoder-distillation or auxiliary-critic update on an
infrequent cadence relative to policy updates, consistent with a freeze-cadence design. PPG does not
itself use TRPO or discuss KL-constrained trust regions — this is an inference, not a stated result.

### SPR — Schwarzer, Anand, Goel, Hjelm, Courville, Bachman, "Self-Predictive Representations,"
arXiv 2007.05929 (ICLR 2021)

**EMA target encoder ablation (Table 2, Table 7, Figure 5, §5 and Appendix C — verified full text):**
- "No Stopgradient" variant (target = online encoder, gradients allowed to flow into it, i.e.
  *removing* the EMA target and letting the same network generate its own future-prediction
  targets) causes **large performance drops**, attributed to representational collapse:
  - With augmentation: median human-normalized 0.415 (SPR) → 0.278 (no stopgradient); DQN@50M
    median 0.361 → 0.231.
  - Without augmentation: median human-normalized 0.307 (SPR) → 0.208 (no stopgradient); DQN@50M
    median 0.225 → 0.233 (roughly flat here, but mean drops 0.336→0.301).
  - Paper's verbatim conclusion: *"We find that using a separate target encoder is vital in all
    cases."*
- **Momentum coefficient (τ) sweep** (Appendix C, Figure 5, 9 values log-interpolated between 0.999
  and 0, tested on a 10-game subset, 10 seeds/value):
  - τ ∈ {0.999, 0.9976, 0.9944, 0.9867, 0.9684, 0.925, 0.8222, 0.5783, 0}.
  - **With data augmentation:** performance peaks at **τ = 0** (i.e., the target encoder equals the
    online encoder at every step with a stop-gradient only — no actual EMA smoothing needed once
    augmentation is present). Used τ=0 as the reported main-result setting.
  - **Without augmentation:** the method is much less sensitive to τ, and the paper adopts **τ =
    0.99** for consistency with prior work (BYOL/Grill et al. 2020), not because it measurably beat
    other values in this setting.
  - Paper's hypothesis for the τ=0 result with augmentation: augmentation itself provides the
    stabilizing effect that an EMA target network is normally used for (citing Grill et al. 2020;
    Tarvainen & Valpola 2017 on mean-teacher), making the EMA "redundant" once augmentation is
    present — but an EMA target network can *slow down* early learning in the RL setting because a
    lagging target implies acting with an inferior policy for longer, which does not apply in the
    non-RL BYOL-style setting SPR is drawing the comparison from.
- **Representation-drift/stability rationale (verbatim, §5 + Appendix C):** the "No Stopgradient"
  ablation — letting online and target collapse to the same network — is explicitly linked to
  "representational collapse," i.e., the target must not be able to be pulled by the same gradient
  that is being matched against it, or the trivial solution (constant/collapsed representation)
  becomes reachable. Stopgradient alone (τ=0, target frozen per step) is sufficient to prevent
  collapse when augmentation forces distinct views; a slower EMA (higher τ) becomes helpful mainly
  when there's no other source of representation diversity, and its downside is slowing early
  learning by leaving the acting policy's data collection anchored to a stale target longer.

**Bears directly on freeze-cadence/EMA design for ALBC's encoder:** SPR's ablation is unambiguous
that *some* form of gradient-decoupling (stopgradient at minimum) between an online-updated encoder
and its own self-supervised/distillation target is necessary to avoid collapse — directly supports
having a frozen or EMA target for ALBC's encoder if it is trained against its own outputs
(reconstruction-style or self-prediction auxiliary). However, note the CLAUDE.md project rule that
ALBC has already tried and rejected encoder auxiliary losses (reconstruction, z_bounds, contrastive)
due to z-collapse — SPR's finding that the *cause* of collapse in their setting was the No-Stopgradient
variant is a plausible partial explanatory match (if ALBC's rejected reconstruction auxiliary lacked
a proper stopgradient/EMA-target mechanism, that would independently predict the observed collapse),
but this report does not verify what mechanism ALBC's prior attempt used — flagging as a testable
hypothesis, not a confirmed diagnosis.

---

## References

1. Cobbe, K., Hilton, J., Klimov, O., Schulman, J. "Phasic Policy Gradient." arXiv:2009.04416
   (ICML 2021). https://arxiv.org/abs/2009.04416 — **verification depth: full-text-read** (PDF
   downloaded, `pdftotext -layout` extraction, §1-3.5 + relevant Appendix references read in full).

2. Schwarzer, M., Anand, A., Goel, R., Hjelm, R.D., Courville, A., Bachman, P. "Data-Efficient
   Reinforcement Learning with Self-Predictive Representations." arXiv:2007.05929 (ICLR 2021).
   https://arxiv.org/abs/2007.05929 — **verification depth: full-text-read** (PDF downloaded,
   `pdftotext -layout` extraction, abstract, §5 Analysis, and Appendix C "The Role of the Target
   Encoder in SPR" read in full, including Table 2, Table 7, Figure 5).

3. Ebi, D., Ernst, D., Böhm, K., Lambrechts, G. "Informed Asymmetric Actor-Critic: Leveraging
   Privileged Signals Beyond Full-State Access." arXiv:2509.26000 (ICML 2026, poster).
   https://arxiv.org/abs/2509.26000 — **verification depth: full-text-read** (PDF downloaded,
   `pdftotext -layout` extraction, §1-5 and Appendix D, G read; Table 6 and Appendix G.1-G.2
   quoted directly). Prior investigation (R1, per brief) had this at abstract-only depth; now
   upgraded to full-text.

4. Baisero, A., Amato, C. (2022) — cited within IAAC as the source of the asymmetric policy-gradient
   theorem and navigation-task baselines; not independently fetched (secondary citation only).
   **verification depth: not verified independently** (referenced via IAAC's citation, not fetched).

5. Pinto, L. et al. (2018) — cited within IAAC as an early asymmetric actor-critic paper (image-
   based robot learning). **verification depth: not verified independently** — noted in search
   results (alphaXiv overview of arXiv:1710.06542) but not fetched at full-text depth; flagged here
   only because it recurred across searches as the canonical asymmetric-actor-critic reference.

6. RMA (Kumar et al., "RMA: Rapid Motor Adaptation for Legged Robots") and DreamWaQ — surfaced by
   search as the standard RMA-lineage references; **verification depth: snippet-only** via
   WebSearch summaries, not fetched. No ablation varying critic-input richness was found in the
   available snippets; this is reported as a gap, not a verified absence.

## GitHub repos

- PPG reference implementation: https://github.com/openai/phasic-policy-gradient (cited in paper,
  not cloned/inspected in this pass).
- IAAC reference implementation: https://github.com/EbiDa/informed-asymmetric-a2c (cited in paper,
  not cloned/inspected in this pass).

## Implications for ALBC

- **Half A → critic design**: ALBC's asymmetric critic already carries 28D privileged params + 9D
  latent z. The IAAC evidence (Finding 1) argues against assuming that adding further
  auxiliary/dynamics-derived features to this critic is free value — in the one paper that directly
  tests this, richer combined privileged signals sometimes underperformed a single well-chosen
  signal, and in one environment even underperformed no privileged signal at all. If a Koopman-
  lifted dynamics feature is added to the critic, this motivates treating it as a signal to be
  validated (e.g., via an informativeness/ablation check analogous to IAAC's residual/prediction
  tests) rather than assumed beneficial by construction — directly consonant with the project's
  existing "No Generic Solutions Without Evidence" rule (`.claude/rules/03-analysis-quality.md`).
- **Half B → update-protocol design**: PPG supports a freeze-cadence argument — infrequent,
  isolated auxiliary/distillation phases outperform frequent interleaving because interference
  scales with frequency, and detaching gradients from shared parameters during the primary
  (policy/TRPO) phase while allowing them during the isolated auxiliary phase is PPG's concrete
  mechanism for this. SPR supports an EMA/stopgradient-target argument specifically for self-
  predictive/auxiliary encoder objectives — at minimum a stopgradient is required to prevent
  collapse, and the *degree* of EMA smoothing needed depends on whether another source of
  representational diversity (SPR's data augmentation; ALBC would need an analogous source, e.g.
  DR-induced diversity) is already present. Neither paper was run in a TRPO/hard-KL-constraint
  setting, so applying either recipe to ConstraintTRPO+IPO is an extrapolation, not a verified
  transfer — flag explicitly in the design doc rather than presenting as settled.
