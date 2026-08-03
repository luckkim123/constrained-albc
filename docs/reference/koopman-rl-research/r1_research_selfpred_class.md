# Research Report: Self-Predictive Auxiliary Latent-Dynamics Prediction — Mechanism-Class Comparison

**Assignment key:** `selfpred_class`
**Addresses:** epistemic critique THEO-2 — the design doc frames its proposal around the "Koopman" brand while the
actual mechanism (auxiliary latent-dynamics prediction trained jointly with a policy) has a 5-year literature that
was never surveyed. This report surveys that literature and evaluates whether the doc's proposed Koopman arms can
be attributed to "Koopman-ness" specifically, or to the more generic mechanism class.

---

## Q1 — OFENet (Ota, Oiki, Jha, Miyoshi, Sasaki; arXiv 2003.01629; ICML 2020)

**Title:** "Can Increasing Input Dimensionality Improve Deep Reinforcement Learning?"

**Architecture (verified via ar5iv HTML full text).** OFENet ("Online Feature Extractor Network") is not a
Koopman/linear-dynamics model. It is a pair of **DenseNet-style MLP towers**: one takes the raw state `s` and
produces an expanded feature `z_s`, the other takes `[s, a]` and produces `z_{s,a}`. Each DenseNet block computes
`y = [x, σ(W₁x)]` — i.e. every layer's output is concatenated (not replaced) with its input, so representation
dimensionality *grows* with depth (the paper's central claim: bigger, denser features help, contrary to the usual
bottleneck-encoder intuition). Depth/width is task-tuned (6 layers for Hopper/Walker2d/Ant, 8 layers for
HalfCheetah/Humanoid, Swish activation, feature-dim increment 240/layer). The auxiliary task is **predicting the
next raw observation** (and, in the state-action tower, predicting the next state from `[s,a]`) — this is
observation-space prediction, not a linear-operator/eigenstructure objective. `z_s`/`z_{s,a}` are concatenated onto
the *original* low-dim state and fed to the RL algorithm's actor/critic as an *augmented input*, not substituted for
it and not compressed into a small bottleneck like the ALBC encoder's 9D `z`.

**Algorithms tested and gains (Table 1, MuJoCo-v2 suite, verified).**

| Task | Algo | Baseline | +OFE | Gain |
|---|---|---|---|---|
| Hopper | SAC | 3316.6 | 3511.6 | +5.9% |
| Walker2d | SAC | 3401.5 | 5237.0 | +53.9% |
| HalfCheetah | SAC | 14116.1 | 16964.1 | +20.2% |
| Ant | SAC | 5953.1 | 8086.2 | +35.8% |
| Humanoid | SAC | 6092.6 | 9560.5 | +56.9% |
| Walker2d | TD3 | 4515.6 | 4915.1 | +8.8% |
| Ant | TD3 | 6148.6 | 8472.4 | +37.8% |
| HalfCheetah | PPO | 2860.4 | 3981.8 | +39.2% |

Off-policy algorithms (SAC, TD3) were evaluated across most/all of the 5 MuJoCo tasks; the **on-policy PPO
comparison in the main table is reported for only one environment (HalfCheetah)**, not the full 5-task suite that
SAC/TD3 got. This is a genuine asymmetry in the paper's own evidence, not something the paper explains away — PPO
gets one data point, off-policy methods get five. One data point (+39%, comparable in magnitude to the SAC/TD3
gains) is suggestive that on-policy also benefits, but it is not the same weight of evidence. I could not verify
from the fetched text whether PPO was tested more broadly in the appendix; treat the on-policy claim as
**weakly supported**, not established at the same confidence as the off-policy result.

**Follow-ups.** The direct follow-up by the same lab is Ota, Jha et al., "Training Larger Networks for Deep
Reinforcement Learning" (arXiv 2102.07920, 2021) — extends OFENet's premise (wider/denser networks help RL) with
decoupled representation-learning and distributed training. I did not find an independent (non-author) replication
or a paper specifically re-testing OFENet's on-policy (PPO) claim at wider scale.

## Q2 — Voelcker, Kastner, Gilitschenski, Farahmand, "When does Self-Prediction help? Understanding Auxiliary
Tasks in Reinforcement Learning" (arXiv 2406.17718, published as RLC 2024)

**This is the single most decision-relevant paper for the project**, and full-text extraction (via ar5iv HTML +
locally parsed PDF) surfaced findings materially more specific than the abstract alone.

**Theoretical setting — read the fine print.** The theory is derived under **linear function approximation and
fixed-policy evaluation** ("on-policy" here means the *data-collection policy for evaluating a single fixed policy*
does not shift under estimation — this is the classical linear-TD sense of "on-policy," **not** "on-policy
algorithm" in the PPO/TRPO sense). The paper is explicit that this is "a restrictive assumption... limiting
applicability to online [policy-improvement] RL," and lists it as an acknowledged limitation in its own
Limitations section (verified verbatim: *"We also conduct all of our theoretical work in the on-policy policy
evaluation regime, while our empirical study includes both off-policy policy estimation and policy improvement...
we consider this an acceptable limitation, but studying the impact of off-policy samples and shifting policies is
an important step for future work."*).

**Three objectives compared under a shared two-layer-linear-network model:**
- **Observation reconstruction** converges to the top-k *singular vectors* of the policy's transition operator
  `P^π` (Proposition 2) — optimal low-rank linear features *without* reward information.
- **Latent self-prediction** (predict the encoder's own next-latent, stop-gradient target — this is the mechanism
  class the doc's Koopman-lifting proposal belongs to, minus the explicit linearity constraint on the *transition*
  itself) converges to the top-k *eigenvectors* of `P^π` (Proposition 1).
- **TD learning** alone pursues reward-aligned subspaces only.

**Key Insight 1 (verified verbatim intent):** *used in isolation*, observation reconstruction is superior to latent
self-prediction — singular vectors are optimal low-rank features with no reward assumption, while pure latent
self-prediction "fails to learn any relevant features in several cases" empirically (MinAtar).

**Key Insight 3 (the load-bearing finding):** latent self-prediction is a stronger **auxiliary** task than
reconstruction *when combined with TD learning*, and **specifically more so in environments with distracting
processes** — i.e. task-irrelevant dynamics coexisting with task-relevant dynamics. Mechanistically: reconstruction
must spend representational capacity encoding the distractor (because distractors are visible in the raw
observation and get equal weight in a reconstruction loss), while a TD-anchored latent self-prediction loss can, in
principle, let the value/policy gradient pull the shared representation toward reward-relevant eigenvectors instead
— **but this is explicitly conditional**: Proposition 7 proves that if the distractor's eigenvalues are *larger*
than the task-relevant process's second eigenvalue, the top-k eigenspace the latent objective would converge to
**still gets contaminated by distractor eigenvectors** — the auxiliary task does not automatically filter
distraction, it only does so when the task-relevant signal's eigenspectrum dominates.

**No domain-randomization / multi-dynamics framing.** The paper's distraction formalism is a factored MDP
(Kronecker product of a task-relevant chain and an independent, reward-irrelevant chain) — this models **an
irrelevant co-occurring process within one fixed environment**, not **the same task's dynamics changing across
episodes/domains** (which is what DR does to ALBC: thruster gains, ocean current, latency all vary per rollout
under one fixed reward/task structure). This is an important mismatch: the paper's theory does not model, and
its authors do not claim to model, a setting where `P^π` itself is a *different operator per episode* (DR). The
practical inference for a DR setting has to be an extrapolation, not a citation: if latent self-prediction
converges toward the eigenstructure of *the* transition operator, and DR forces the effective transition
operator to vary across rollouts (28D randomized: thruster faults, current, latency, ESC filter), then either (a)
the encoder must learn an eigenstructure that is *shared/robust* across the DR distribution, which is a harder,
underspecified fitting target than the paper's single-environment result, or (b) the aux loss pushes the encoder to
track per-rollout eigenstructure, which is closer to what the ALBC design doc actually wants (a DR-conditioning
signal) but is **not what this paper studied or validated**. State this as an extrapolation, not a proven claim.

**Empirical algorithms used — decisively answers the on-policy question for this paper.** Verified from the
appendix (locally parsed PDF, lines ~1641 and ~1697-1704): MinAtar experiments use **Double DQN**; DMC experiments
use **TD3**. **No PPO or TRPO experiment appears anywhere in this paper.** Both algorithms tested are off-policy
(replay-buffer-based). The paper's own stated future-work item is exactly the gap the ALBC doc needs filled
(on-policy, policy-improvement regime) and this paper does not fill it.

**Observation-function distortion result (relevant to "does it survive perturbation"):** all three objectives
degraded under a random linear transform of the observation space; latent self-prediction retained relatively more
performance than reconstruction on 2/5 MinAtar games, but the paper states plainly that its claimed theoretical
invariance property "does not fully translate to the more complex test setting" — i.e. even the authors flag their
own theory as only partially confirmed empirically.

## Q3 — Broader self-predictive-representation family: on-policy (PPO/TRPO) evidence hunt

| Method | Base algorithm | On/off-policy | Notes (verified) |
|---|---|---|---|
| **SPR** (Schwarzer et al., ICLR 2021, arXiv 2007.05929) | Rainbow-DQN (Atari-100k) | Off-policy, discrete | Multi-step latent self-prediction + augmentation-consistency; the headline "self-predictive representations" result. Never tested with an on-policy actor-critic algorithm in the original paper. |
| **SAC-AE** (Yarats et al., AAAI 2021) | SAC | Off-policy | Reconstruction-based (not latent self-prediction), included here as the standard aux-recon baseline the field compares latent-prediction methods against. |
| **TD-MPC2** (Hansen et al., ICLR 2024, arXiv 2310.16828) | Model-based, replay-buffer TD-MPC (MPPI planning + Q-learning) | Off-policy (data-reuse via replay buffer; not on-policy PPO/TRPO) | Uses an **unconstrained nonlinear MLP** latent-dynamics/consistency loss (joint-embedding prediction across multi-step rollouts, no explicit linearity constraint) and scales to 104 tasks — direct evidence that *nonlinear* latent self-prediction works well at scale without any Koopman-style linear restriction. |
| **PBL** (Guo et al., ICML 2020, "Bootstrap Latent-Predictive Representations for Multitask RL") | IMPALA (V-trace-corrected, near-on-policy actor-critic) | Closest thing found to an on-policy-family test of latent self-prediction, on DMLab-30 multitask. Bidirectional (forward+reverse) latent bootstrapped prediction, BYOL-style stop-gradient target network. Reports across-the-board gains over SOTA DMLab-30 agents. This is the best available (imperfect) on-policy-adjacent positive result for the mechanism class. |
| **Ni et al., "Bridging State and History Representations"** (ICLR 2024, arXiv 2401.08898 — note: this is the correct arXiv ID; the assignment brief's "2406.17718" ID actually belongs to the Voelcker paper covered in Q2, the two were conflated in the brief) | Unifying theory paper; validates a "minimalist" self-predictive algorithm on standard MDPs, MDPs-with-distractors, and POMDPs with sparse reward | Provides theoretical unification of self-predictive objectives (shows many published variants share one core mechanism) and studies the stop-gradient technique's role in avoiding representation collapse. Official code: `twni2016/self-predictive-rl`. |

**Direct search for a documented on-policy (PPO/TRPO-family) *negative* result for latent self-prediction turned
up nothing conclusive** — I found no paper stating "we tried this auxiliary latent-dynamics loss with PPO/TRPO and
it did not help or hurt." The honest state of the evidence is: **on-policy testing of this mechanism class is
sparse, not negative.** OFENet's single-environment PPO result and PBL's IMPALA (off-policy-corrected but
near-on-policy) result are the two closest positive data points; neither is a rigorous PPO/TRPO ablation at the
scale the field applies to SAC/TD3/DQN. This is itself the finding: the doc's central mechanism has a real, mostly
positive off-policy literature, and a thin, unreplicated on-policy literature — which matters directly because
ConstraintTRPO is on-policy.

## Q4 — Does any published work isolate the LINEARITY constraint (Koopman-style linear latent dynamics vs.
unconstrained nonlinear latent dynamics, architecture held fixed)?

**Short answer: no, not found, and I looked specifically.**

**KIPPO (Cozma, Harris, Qi; arXiv 2505.14566, IJCAI 2025) — read the full ablation table via local PDF text
extraction.** KIPPO's ablation (Section 4.3 / Appendix D, Table 3 / Table D.1) varies **which loss components are
included**: reconstruction loss (`L_rec`), latent-space prediction loss (`L_pred-ls`), state-space prediction loss
(`L_pred-ss`), and combinations of the three, always summed with the PPO objective. **Every arm in the ablation
uses the same linear transition matrix `K` for the latent-dynamics prediction — there is no arm that swaps `K` for
an unconstrained nonlinear MLP predicting the next latent while holding the encoder/decoder architecture fixed.**
I grepped the full extracted text for "nonlinear latent" / "non-linear latent-dynamics" comparisons and found only
narrative discussion of *why* linearity is a useful inductive bias (reduced gradient variance in policy
optimization), never an empirical arm testing the counterfactual. KIPPO's own text acknowledges the mechanism's
limits — performance gains "diminish in environments with highly discontinuous transitions... as the linear latent
dynamics struggle with abrupt changes" — which is itself evidence the authors know linearity is a real constraint,
just one they never ablate against a nonlinear latent-predictor control.

**DKRL — "Deep Learning of Koopman Representation for Control" (Han, Hao, Vaidya; arXiv 2010.07546, 2020).**
Confirmed via full-text extraction: this is a **model-based** method (learns a DNN-parameterized basis function for
a finite Koopman operator, then does LQR in the lifted linear space) tested on two classic OpenAI Gym control
problems. It is not combined with PPO/TRPO/SAC and does not run a linear-vs-nonlinear latent-dynamics ablation
either — the entire point of the method is the linear lift, so there is no nonlinear-latent control arm by design.

**"KFC" (Koopman Feature Control):** targeted search found no paper matching this name/acronym in the RL auxiliary-
task literature. Either the doc's citation is to an obscure/unpublished source I could not locate, or the acronym
is misremembered — flagging this as **unverifiable**, not confirming or denying its existence.

**Adjacent Koopman-RL work surveyed for a possible hidden ablation** (Koopman-Assisted RL, arXiv 2403.02290;
"Course Correcting Koopman Representations," arXiv 2310.15386; Koopman Dreamer, arXiv 2607.19719; DeepKoCo, arXiv
2011.12690; "Scaling Law of Neural Koopman Operators," arXiv 2602.19943) — none of these, per their abstracts/search
snippets, run the specific linear-vs-nonlinear-latent-dynamics-prediction ablation with architecture held fixed.
"Scaling Law of Neural Koopman Operators" does something adjacent (ablates *auxiliary losses* — covariance and
inverse-control regularizers — for a Koopman operator, finding they barely change open-loop prediction error but
help closed-loop control) but that's an ablation *within* the linear-Koopman family, not linear-vs-nonlinear.

**Conclusion for Q4, stated plainly for the doc's authors:** the literature search, including the design doc's own
named prior work (KIPPO, DKRL), does not contain a study that isolates whether the *linearity* of the latent
transition is what earns Koopman-branded methods their reported gains, versus the gains coming from the more
generic "predict your own future latent as an auxiliary signal" mechanism that Q1–Q3 show already helps broadly
across SAC/TD3/DQN/IMPALA and, more thinly, PPO. **This means: any experiment the ALBC project runs that only
compares "Koopman-lifted linear latent dynamics + PPO/TRPO" against "no auxiliary task" cannot attribute a result to
Koopman/linearity specifically** — an improvement could equally be explained by the generic self-predictive
mechanism (per Q2's Insight 3, expected to help most under DR-induced distraction-like variance).

### The minimal missing control arm

To make any ALBC Koopman experiment interpretable, the arms must include, at minimum:
1. **No auxiliary latent prediction** (current baseline: ConstraintTRPO + IPO, no aux task).
2. **Koopman/linear-latent-dynamics prediction** (the doc's proposed arm: encoder `z`, linear operator `K`,
   predict `z_{t+1} = Kz_t (+ Bu_t)`, auxiliary MSE loss).
3. **Unconstrained nonlinear latent-dynamics prediction** — *same* encoder architecture, *same* loss weight,
   *same* auxiliary-loss placement, but replace the linear operator `K` with a small MLP predicting `z_{t+1}`
   from `(z_t, a_t)`. This is the control KIPPO itself never ran.
4. (Optional, cheap) **Observation-space next-step prediction** (OFENet-style) as an alternative non-latent
   auxiliary baseline, since Voelcker et al.'s Insight 1 says this can be the stronger *standalone* feature learner.

If arm 2 beats arm 1 but does **not** clearly beat arm 3 (holding train iterations/wall-clock roughly fixed), the
gain is attributable to "predicting your own dynamics," not to "Koopman" — and the paper/report language should say
so. If arm 2 clearly beats arm 3, that would be the first published isolation of the linearity effect in this
literature, and would be a genuinely novel contribution worth writing up on its own, independent of the encoder
work.

---

## Implications for ALBC (mechanism-level, not hand-waving)

1. **The generic mechanism (predict-your-own-future-latent as an auxiliary task) has real, mostly-positive support
   across SAC/TD3/DQN and a thinner but real positive OFENet PPO data point** — so adding *some* form of auxiliary
   latent-dynamics prediction to the ALBC encoder is not an unreasonable thing to try. The `_core/encoder` module
   already trains `z` (9D) via the actor/critic gradient only (no aux loss); adding a next-`z` prediction head is a
   small, bounded-risk architectural change (one linear or small-MLP head, one added loss term) relative to the
   encoder's existing `elu`+LayerNorm+softsign stack.
2. **ConstraintTRPO is on-policy** — and the literature's on-policy evidence for this exact mechanism (auxiliary
   latent-dynamics prediction) is the thinnest part of the whole survey (Q1/Q3). This is the honest gap: nothing
   here proves the mechanism transfers cleanly to TRPO-family updates at the scale ALBC trains at (4096 envs). The
   project should treat a first Koopman/self-predictive experiment as **exploratory**, not as implementing an
   established recipe.
3. **Voelcker et al.'s Insight 3 (latent self-prediction as auxiliary task helps most under distraction) is the
   most on-target piece of theory available, but it was proven for a single fixed environment with an independent
   irrelevant sub-process, not for DR-induced dynamics variation across rollouts.** ALBC's 28D DR (thruster faults,
   current, latency, ESC filter) changes the *effective transition operator itself* per rollout, which is a
   different and harder setting than the paper's factored-MDP distraction model. Do not cite Voelcker et al. as
   proof that this helps under DR — cite it as the closest available theory, with an explicit note that DR-style
   non-stationary dynamics is outside what was proven.
4. **No published work has isolated whether Koopman's linearity constraint (vs. a plain nonlinear latent-dynamics
   predictor) is what earns the reported gains** (Q4). Any ALBC ablation intended to credit "Koopman" needs the
   nonlinear-MLP control arm described above, or the resulting report will overclaim exactly the way KIPPO's own
   ablation does (varies loss *components*, never varies the *linearity* of the transition model itself).
5. **Practical warning from KIPPO's own text**, worth carrying into ALBC's design: KIPPO's authors report
   diminishing returns "in environments with highly discontinuous transitions (e.g., collisions), contact-rich
   interactions, or multi-modal behaviors" — this describes underwater vehicle-manipulator contact/collision
   dynamics (arm-hull contact, thruster saturation nonlinearities, ocean-current-driven regime shifts) reasonably
   well. This is a specific, mechanism-grounded reason (not a generic "it might not work" hedge) to expect a
   linear-Koopman auxiliary loss to underperform on the more contact/nonlinearity-heavy ALBC scenarios even if it
   helps on smoother attitude-hold segments — worth stratifying results by DR level / contact-episode frequency
   rather than reporting one aggregate number.
6. **TD-MPC2 is existence-proof that *nonlinear* latent-dynamics consistency losses scale well** (104 tasks,
   large-scale, still stable) — so if the ALBC team wants the safest version of this mechanism rather than the
   Koopman-branded one, a TD-MPC2-style nonlinear latent-consistency auxiliary head, without any linear-operator
   claim, has stronger scale-tested precedent than the Koopman-specific arms in the current design doc.

---

## References

| # | Citation | Identifier | Verification depth |
|---|---|---|---|
| 1 | Ota, K., Oiki, T., Jha, D., Mariyama, T., Nikovski, D. "Can Increasing Input Dimensionality Improve Deep Reinforcement Learning?" ICML 2020. | arXiv:2003.01629 | Full-text (ar5iv HTML) |
| 2 | Voelcker, C., Kastner, T., Gilitschenski, I., Farahmand, A. "When does Self-Prediction help? Understanding Auxiliary Tasks in Reinforcement Learning." RLC 2024. | arXiv:2406.17718 | Full-text (ar5iv HTML + locally downloaded/parsed PDF, `pdftotext -layout`) |
| 3 | Schwarzer, M., Anand, A., Goel, R., Hjelm, R.D., Courville, A., Bachman, P. "Data-Efficient Reinforcement Learning with Self-Predictive Representations." ICLR 2021. | arXiv:2007.05929 | Abstract/snippet |
| 4 | Yarats, D., Zhang, A., Kostrikov, I., Amos, B., Pineau, J., Fergus, R. "Improving Sample Efficiency in Model-Free Reinforcement Learning from Images" (SAC-AE). AAAI 2021. | arXiv:1910.01741 | Not directly fetched this session — cited from established background knowledge; flagged as **not independently re-verified in this pass** |
| 5 | Hansen, N., Su, H., Wang, X. "TD-MPC2: Scalable, Robust World Models for Continuous Control." ICLR 2024. | arXiv:2310.16828 | Snippet/search-result level; abstract content, not full PDF |
| 6 | Guo, Z.D., Pires, B.A., Piot, B., Grill, J.B., Altché, F., Munos, R., Azar, M.G. "Bootstrap Latent-Predictive Representations for Multitask Reinforcement Learning" (PBL). ICML 2020. | PMLR v119, also arXiv:2004.14646 | Abstract/snippet |
| 7 | Ni, T., Eysenbach, B., Seyedsalehi, E., Ma, M., Gehring, C., Mahajan, A., Bacon, P.L. "Bridging State and History Representations: Understanding Self-Predictive RL." ICLR 2024. | arXiv:2401.08898 | Abstract/snippet (title/authors/venue verified; theoretical content not full-text read this session) |
| 8 | Cozma, A., Harris, L., Qi, H. "KIPPO: Koopman-Inspired Proximal Policy Optimization." IJCAI 2025. | arXiv:2505.14566 | Full-text (locally downloaded PDF, `pdftotext -layout`, ablation section directly grepped and quoted) |
| 9 | Han, Y., Hao, W., Vaidya, U. "Deep Learning of Koopman Representation for Control" (DKRL). 2020. | arXiv:2010.07546 | Full-text (locally downloaded PDF, `pdftotext -layout`) |
| 10 | "Scaling Law of Neural Koopman Operators." | arXiv:2602.19943 | Snippet only |
| 11 | Nauman, M., et al. "Koopman-Assisted Reinforcement Learning." | arXiv:2403.02290 | Snippet only |
| 12 | "Course Correcting Koopman Representations." | arXiv:2310.15386 | Snippet only |
| 13 | "Koopman Dreamer: Spectrally Constrained Latent Dynamics for Stable World-Model Imagination." | arXiv:2607.19719 | Snippet only |
| 14 | "DeepKoCo" — model-based agent, latent Koopman representation from images. | arXiv:2011.12690 | Snippet only |
| 15 | Ota, K., Jha, D., Kanezaki, A. "Training Larger Networks for Deep Reinforcement Learning." (OFENet follow-up, same lab) | arXiv:2102.07920 | Snippet only |

**Note on the assignment brief's arXiv IDs:** the brief lists "Voelcker et al. arXiv 2406.17718" for "When does
Self-Prediction help?" and separately mentions "Ni et al. 2024 'Bridging State and History Representations'" without
an ID. I confirmed 2406.17718 is indeed Voelcker et al. (correct), and separately found Ni et al.'s correct ID is
**2401.08898** (not 2406.17718 — that number belongs only to Voelcker et al.). No conflict once disambiguated, just
noting it for the record since the brief's phrasing could be read as implying overlap.

## GitHub repos

| Repo | What it implements | License (if visible) | Reusable for a PyTorch/rsl-rl stack? |
|---|---|---|---|
| [merlresearch/OFENet](https://github.com/merlresearch/OFENet) | Official OFENet (Mitsubishi Electric Research Labs) — DenseNet feature-expansion + next-obs prediction, combined with SAC/TD3/PPO on MuJoCo | Visible on repo (MERL standard research license — check before any redistribution) | TensorFlow-based (original); architecture (DenseNet expansion blocks + concat-based aux prediction head) is simple enough to port to PyTorch directly, but not a drop-in for rsl-rl — would need re-implementing the two towers as PyTorch `nn.Module`s and wiring the aux loss into rsl-rl's `OnPolicyRunner` update step |
| [BY571/OFENet](https://github.com/BY571/OFENet) | Independent (non-official) PyTorch port of OFENet | Not verified | More directly reusable for a PyTorch stack than the TF original if it's a faithful port — **verify correctness against the official repo's numbers before trusting it**, this is an unofficial reimplementation |
| [twni2016/self-predictive-rl](https://github.com/twni2016/self-predictive-rl) | Official code for Ni et al. 2024, "Bridging State and History Representations" — minimalist self-predictive representation learning for MDPs/POMDPs | Not verified | PyTorch (standard for this line of work); useful as a reference for a *minimal, correctly-regularized* (stop-gradient, no-collapse) self-predictive loss implementation, independent of the Koopman framing |
| [Bluehorse-hub/KIPPO-PyTorch-Unofficial](https://github.com/Bluehorse-hub/KIPPO-PyTorch-Unofficial) | Unofficial PyTorch reimplementation of KIPPO | Not verified | Directly relevant as a reference implementation of the Koopman-auxiliary-network-on-PPO pattern the ALBC doc proposes, but it is **unofficial and unverified against the paper's numbers** — treat as a structural reference only, not a validated baseline |
| No official KIPPO repo found | — | — | The paper (arXiv 2505.14566, IJCAI 2025) does not appear to have a linked official code release as of this search; only the unofficial reimplementation above was found |
| No repo found for Voelcker et al. 2024 ("When does Self-Prediction help?") | — | — | Targeted search of the author's GitHub (`cvoelcker`) and web search did not surface a released repo for this specific paper — flagging as **not found**, not confirmed absent |
