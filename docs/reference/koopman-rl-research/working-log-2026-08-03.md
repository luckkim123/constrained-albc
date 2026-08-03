# Koopman Operators in Robot Learning — Paper/Code Analysis and Proposal Review

Date: 2026-08-03
Sources: `/workspace/references/Koopman Operators in Robot Learning.pdf` (Shi, Haseli, Mamakoukas,
Bruder, Abraham, Murphey, Cortes, Karydis, IEEE T-RO vol. 42, 2026, 20 pp.),
`/workspace/references/KoopmanRobo/` (companion tutorial, cloned 2026-08-03),
`/workspace/constrained-albc` (input-path map, file:line verified), omx wiki queries.
Method: 6 parallel readers (4 paper page-ranges, 1 code, 1 ALBC map) + main-context synthesis.

> NOTE (durable copy): PART II (§17-20) SUPERSEDES PART I (§1-16) wherever they conflict; each
> round records its verdict changes in §18.8 / §19.4 / §20. Report pointers below are
> sibling-relative in this copy (originals lived in job scratch).

Reviewed proposals (user, 2026-08-03):
1. Lift ALL network inputs (policy obs, privileged obs, proprio history, commands) into a Koopman
   observable space before feeding the encoder + base policy, to improve implicit system identification.
2. Drop the encoder (and student distillation); feed Koopman-lifted obs to the base policy alone, on
   the theory that Koopman itself performs system identification.
Comparison plan under review: {baseline, koopman+encoder+base, koopman+base} at ~2000 iters on a
separate experiment track.

---

## 1. What the paper is

A survey (not a method paper). Structure: II fundamentals (Koopman operator, EDMD, HVOK, input
handling), III pipeline (data collection, lifting-function design, MPC/LQR/active learning, state
estimation, planning, robustness), IV per-platform survey (manipulation, ground, soft, aerial,
underwater, multiagent), V advanced theory (continuous time, Koopman Control Family,
invariant-subspace search: consistency index, SSD/T-SSD), VI open challenges.

Core math:
- Koopman operator `K g = g ∘ T` acts on observable functions of a SPECIFIC dynamics map
  `x_{t+1} = T(x_t)`. Lifted linear dynamics `Ψ(x_{t+1}) = K Ψ(x_t)` hold exactly only on a
  Koopman-invariant subspace `span(Ψ)` (eqs. 1–5, p.1090–1091).
- EDMD: batch least squares `K = Ψ(Y) Ψ(X)^+` from paired transition data (eqs. 6–7).
- Inputs are structurally second-class: three approximation schemes (joint lifting, affine
  `g(x+) ≈ K g(x) + B u`, control-coherent). The input-state separable model (Sec. V.B) is
  *linear in the lifted state but nonlinear in the input* (p.1101). Joint lifting "does not
  generalize well when the input varies arbitrarily" (p.1092).
- Lifting quality = invariance, not size. Explicit counterexamples: a larger dictionary gives
  WORSE prediction (`x+ = 0.5x` with `[x, sin x]`, p.1091); EDMD residual error can be driven to ~0
  on a NON-invariant subspace by basis choice alone (Fig. 3, p.1101). Even as lifted dim → ∞,
  lifted linear predictors with inputs do not provably converge to the true trajectories (p.1100,
  after eq. 24).
- NN-based ("deep Koopman") lifting: flagged for OOD-generalization risk, overfitting,
  interpretability loss (p.1094); reduces active-learning data efficiency (p.1096); dictionary
  optimization is data-hungry and "typically only applicable to offline precomputation" (p.1102).

Koopman × RL in the survey — exactly three roles, none of which is "lift the policy's input":
1. Koopman model as surrogate ENVIRONMENT for training RL policies (soft robots, [67], p.1098).
2. Koopman assisting CRITIC design ([103], p.1095).
3. Koopman-encoded human intent for REWARD shaping ([128], p.1097).
Plus imitation-learning latents ([40],[41],[42]) and latent planning (DeepKoCo [116], title-only).
Underwater entries are vehicle-only hydrodynamics modeling / MPC / LQR ([87]–[90],[150]); no UVMS,
no RL, no encoder-replacement claim anywhere.

"System identification" in the paper's sense = fitting the dynamics operator `K` (one regime) from
transition pairs, or adapting it ONLINE from streaming data (recursive updates, disturbance
observers, episodic eigenfunction learning). It is never per-episode inference of latent plant
parameters from a single observation. The closest analogues (EVOLVER disturbance observer [80],
population-level uncertainty [114]) are estimation loops over data history — structurally what the
student TCN/GRU already is.

## 2. What the companion code is

`KoopmanRobo/demo.ipynb` (409 code lines, numpy/scipy/cvxpy, CPU only):
- 3-state unicycle (`[x, y, θ]`, hand-coded kinematics), 10k transition triples from random excitation.
- 11-D manual dictionary (identity + degree-1 monomials (duplicated) + cos/sin θ + pairwise cross
  terms); EDMD via one `pinv` call; affine-input split `K_phi (11×11)`, `K_u (11×2)`.
- Linear decoder `C = X Φ(X)^+`; open-loop rollout error ~0.016.
- Koopman-MPC: cvxpy QP per step, horizon 15, ~95 ms/step, 38 s for 400 steps.
- No torch, no NN lifting (explicitly deferred to other work), no DR, no batching, no online update.
Reusable for our stack: the EDMD formula and affine-input factorization as concepts only. The
gap to "lift a 72D obs inside a 4096-env GPU policy forward pass" is categorical, not incremental.

## 3. Current ALBC input interface (facts, file:line in the mapper report)

- Policy obs `o_t`: runtime 72D = 20D current proprio (3D cmd, 6D body, 5D arm, 6D thruster)
  + 30D tracking history (10D × 3) + 16D action history (8D × 2) + 3D integral error
  + 3D bias-EMA. NOTE: 46D of this is already a time-delay embedding — i.e., the obs already
  contains an HVOK-style temporal lifting, and the actor MLP's first layer is a learned lifting.
- Privileged `p_t`: 28D physical parameters (hydro, payload, actuator, current, buoy, latency,
  measured lin-vel), constant-per-episode except current/measured-vel; static min-max normalized
  with per-dimension DR-derived bounds.
- Encoder: `p_t → MLP[256,128,64] elu → LayerNorm → softsign → z(9D)`; actor input
  `cat([EmpNorm(o_t), z])`; student (TCN H=9 / GRU) maps `o_t` history → ẑ, supervised by teacher z
  and action match; student reuses the teacher's frozen `EmpiricalNormalization` instance.
- Any dim-changing transform breaks 4 independent consistency checks + checkpoint geometry
  inference (fine for a fresh track, but no checkpoint reuse).
- Registered ablation `Isaac-ConstrainedALBC-NoEncoder-v0` already exists (actor sees raw `o_t`).
- omx wiki: "feed o_t into encoder" open lead already flags z-collapse/redundancy risks; the
  No-Encoder-Auxiliary-Losses rule records the empirically failed reconstruction path (decoder
  ignores z, z collapses). Wiki "system identification" pages are all physical plant calibration —
  no Koopman precedent in this codebase.

## 4. Review of Proposal 1 (lift all inputs, keep encoder + base)

Verdict: NOT SUPPORTED by the paper; as stated, partially a category error.

1. Koopman linearity is a property of TIME EVOLUTION under a fixed dynamics map, not of the
   obs→action mapping. No result in the survey says `Ψ(obs)` makes an optimal policy or an
   encoder's parameter-inference more linear/learnable. The claimed mechanism ("make data–action
   relations more linear") is not what the theory provides.
2. Lifting `p_t` is meaningless under the paper's own formalism: within an episode
   `p_{t+1} = p_t` (trivial identity dynamics), so every function of `p_t` is a Koopman
   eigenfunction with eigenvalue 1. There is nothing to linearize.
3. Lifting commands/actions contradicts the paper directly: inputs enter NONLINEARLY even after
   lifting (input-state separable model, p.1101); joint lifting fails for arbitrarily varying
   inputs (p.1092) — an RL policy's actions vary arbitrarily by construction.
4. For `o_t` itself, two implementation families:
   - Fixed dictionary (poly/RBF/trig): 72D obs → combinatorial blowup (order-2 cross terms alone
     ≈ 2.6k dims); no invariance guarantee; the paper explicitly warns bigger dictionaries can
     HURT (p.1091) and that required dimension is unboundable without a model (p.1092). A fixed
     nonlinear expansion feeding a universal-approximator MLP adds no capacity the MLP lacks.
   - Learned (deep Koopman) lifting: requires a dynamics-prediction auxiliary objective
     `Ψ(o_{t+1}) ≈ K Ψ(o_t) + B a_t`. (i) This is an auxiliary representation loss — the exact
     family the project's settled rule bans after the reconstruction failure; (ii) lifted-space
     prediction alone has trivial optima (constant Ψ) — the standard fixes are reconstruction
     (the failed path) or identity-inclusion; (iii) under DR there is no single K: the operator is
     K(θ_env) per episode. One shared K averages over plants and the residual carries exactly the
     env information the encoder exists to capture — so the lift either discards the adaptation
     signal or must be conditioned on θ_env, reintroducing the encoder's job.
5. Redundancy: the 72D obs already embeds 46D of time-delay history (HVOK-style lifting) and euler
   angles; a learned first layer already is a lifting. The proposal adds a second, unlearned or
   aux-loss-trained lifting in front of a learned one.

Steelman (the only defensible fragment): the paper's "physics-informed lifting" category maps to
classical feature engineering — e.g., appending `sin/cos` of roll/pitch or quadratic-damping-shaped
terms (`ω|ω|`) to `o_t`. Cheap, rule-compliant (input change, not aux loss). But the paper's own
criterion (invariance under the true dynamics) would remain unverified, and its warning that naive
dictionary growth can hurt applies. Expected effect: small; MLPs learn such features readily.

## 5. Review of Proposal 2 (drop encoder + student; Koopman + base only)

Verdict: NOT SUPPORTED; the core premise conflates two different objects.

1. The paper's Koopman "system identification" = estimating a global (bi)linear DYNAMICS MODEL of
   one regime from transition data, for model-based control (MPC/LQR). The encoder's job =
   per-episode inference of latent plant parameters under DR so a model-free policy can adapt.
   Different problem, different object. No passage supports substituting one for the other; the
   pages that come closest (active learning, disturbance observers, online re-estimation) all
   REQUIRE an online data-driven adaptation loop — structurally the student, not a stateless lift.
2. Information argument (decisive): any fixed pointwise transform `Ψ(o_t)` carries exactly the
   information of `o_t`. A memoryless base policy on `Ψ(o_t)` cannot infer episode-specific
   parameters absent from `o_t` — removing encoder (privileged access) and student (history
   integration) removes the only channels that carry that information. If Ψ is given history to
   fix this, it has become a history encoder — the student under another name.
3. The honest control for this proposal already exists: `Isaac-ConstrainedALBC-NoEncoder-v0`.
   "koopman+base vs baseline" without it is confounded; the informative comparison would be
   NoEncoder vs NoEncoder+lift, isolating the lift's contribution — which by (2) is a fixed
   re-parameterization of the same information.
4. If the real intent is Koopman-as-adaptive-controller (online EDMD + MPC replacing the RL
   policy), that is the paper's actual use case but a different research program — it would replace
   ConstraintTRPO+IPO entirely (settled question) and the tutorial's 95 ms/step cvxpy loop shows
   the compute regime is nowhere near 4096-env RL training.

## 6. Experiment-value assessment

- As proposed, both arms test a mechanism the theory does not predict; the paper itself supplies
  the counterarguments (invariance ≠ size, inputs not linearizable, no per-episode parameter
  inference). Prior local evidence (reconstruction z-collapse; o_t-into-encoder lead's redundancy
  warnings) points the same way. Recommendation: do not run as proposed.
- Minimal falsifiable variant IF an empirical token is still wanted (cheap, 2000-iter track):
  physics-informed feature augmentation of `o_t` only (e.g., +sin/cos roll/pitch, +ω|ω| terms;
  ~+6–8 dims), arms {TRPO baseline, TRPO+features, NoEncoder, NoEncoder+features} at 2000 iters.
  This tests the only defensible fragment of Proposal 1 without aux losses; expectation from
  theory and prior evidence is a null-to-small effect.
- The genuinely Koopman-native directions for this project would be (out of current scope, not
  proposed for the campaign): Koopman surrogate dynamics for model-based rollouts/critic assist
  ([67],[103]-style), or offline EDMD/HVOK analysis of logged trajectories as a diagnostic
  (spectral comparison across DR arms) — analysis-only, no training-path change.

## 7. Decision log

- 2026-08-03: analysis + review delivered; experiment decision deferred to user. No plan authored
  (per instruction). If user proceeds despite the recommendation, use the minimal variant in §6
  and the NoEncoder controls; record the lead + verdict in omx wiki at decision time.
- 2026-08-03 (later): user challenged breadth of the review; web-searched beyond the survey's
  reference window. VERDICT PARTIALLY REVISED — see §8.

## 8. REVISION (2026-08-03, after user push-back): variants re-examined + newer literature

The survey's bibliography window predates two directly relevant works found by web search:

### 8.1 KIPPO — Koopman-Inspired Proximal Policy Optimization (Cozma, Harris, Qi, IJCAI 2025)

Read in full (pp. 4994–4997). This IS the user's variant "keep the pipeline, lift the final obs
fed to the policy":
- State autoencoder `phi_x: S → R^m` with m = 2–4× state dim (EXPANSIVE latent, not compressive),
  decoder `phi_x^{-1}`, action encoder `phi_u`; linear latent dynamics
  `phi_x(x_{t+1}) ≈ K phi_x(x_t) + B phi_u(u_t)` enforced as a SOFT constraint along
  policy-explored trajectories (local, not global linearization).
- Losses: reconstruction `L_rec`, latent-space prediction `L_pred-ls`, state-space prediction
  `L_pred-ss` over horizon H. Trained alongside PPO but DECOUPLED from the policy objective
  ("without altering the core policy or value function architecture").
- Crucially: "The policy optimization algorithm operates on the encoded states y_t = phi_x(x_t)"
  — the actor and critic DO consume the lifted representation.
- Results: MuJoCo/Box2D, +6–60% mean return, 26–91% variance reduction vs PPO (4 trials/env).
- Claimed mechanism: NOT system identification — "reduces gradient variance specifically in
  critical regions... simplifies underlying dynamics while preserving essential features for
  policy learning." Related work it cites (verified in its text): DKRL (Song et al. 2021, local
  Koopman operators for data efficiency), KFC / Koopman Q-learning (Weissenbacher et al. 2022,
  offline RL via dynamics symmetries).

### 8.2 SKooP (arXiv 2607.11624, 2026) — quadruped RL

Controlled Koopman autoencoder (reconstruction + H-step latent prediction losses) trained
concurrently with PPO; the Koopman one-step prediction `z_{k+1} = A f(x_k) + B u_k` is fed to the
CRITIC ONLY as privileged information; "the actor only requires x_k as input." Faster convergence,
higher reward, better symmetry generalization on Cyberdog 2 bipedal tasks. No RMA-style encoder,
no env-parameter inference.

### 8.3 What the revision changes — and what it does not

REVISED: Proposal 1 in its "keep encoder, lift the policy's obs" form (user variant B) HAS
published precedent with positive results (KIPPO), plus a critic-side sibling (SKooP). A
2000-iter screening arm is defensible. The honest mechanism hypothesis must change from
"improves implicit system identification" to "locally-linear latent dynamics as an inductive
bias → smoother/lower-variance policy-gradient optimization."

UNCHANGED:
- Proposal 2 (drop encoder+student): still unsupported. KIPPO/SKooP have no privileged encoder to
  remove and claim no parameter inference; the information argument stands (pointwise phi adds no
  env info; history-consuming phi = a student by another name).
- Variant A (replace the p_t encoder with a "Koopman encoder"): unsupported. The two encoders
  share an architectural slot but differ in input and objective (privileged-parameter compression
  with ground truth available vs dynamics-linearizing obs embedding). Both new papers ADD a
  Koopman module; neither REPLACES an information source. Discarding free ground-truth p_t in sim
  is strictly worse.
- Theoretical steelman worth recording: constant-per-episode DR parameters ARE Koopman
  eigenfunctions (eigenvalue 1) of the episode's extended system, so "Koopman can express
  parameter inference from history" is formally true — but extracting lambda≈1 eigenfunctions from
  history IS the student's job, and supervised distillation (z targets available in sim)
  dominates unsupervised spectral discovery. This supports keeping the student, not removing it.

### 8.4 Design cautions for a KIPPO-style arm on ALBC (facts to carry into any proposal)

1. Aux-loss rule scope: the No-Encoder-Auxiliary-Losses rule targets the p_t→z encoder. A separate
   obs-side lifting module phi_x with its own rec+prediction losses is a NEW module, not covered by
   the rule's letter; the prior failure (decoder ignores 9D compressive z) differs from KIPPO's
   expansive (m > n) autoencoder where reconstruction is easy and collapse-unlikely. Still, flag it
   to the user explicitly as adjacent to a settled rule.
2. DR-single-K tension remains: one (K,B) fit across 4096 randomized plants averages dynamics; as a
   soft regularizer this may just weaken (KIPPO frames linearity as inductive bias, not exact
   model). Optional stretch: condition K on z (parameter-varying lifted dynamics) — novel work.
3. KIPPO was PPO on MuJoCo without DR/constraints/asymmetric critic. Interactions to watch on our
   stack: ConstraintTRPO trust region + IPO cost critics now ride on a drifting representation
   y_t = phi_x(o_t); EmpiricalNormalization placement (normalize o_t before phi_x, keep actor-side
   normalizer identity or re-fit); checkpoint geometry (new track, no reuse).
4. Fair arm set for a 2000-iter screening: {TRPO baseline, TRPO+phi_x (KIPPO-style),
   NoEncoder, NoEncoder+phi_x}, single seed per screening convention; primary metrics: gradient
   variance / KL health / convergence speed at fixed iter + eval static, not just final reward.

## 9. Alternative integration points beyond input lifting (7-category survey, 2026-08-03)

User asked what OTHER Koopman x RL integration perspectives exist beyond their proposals. 7 parallel
researchers with web verification. Full per-category reports: survey_*.md
(job-scoped; key content summarized here). Verdicts use APPLICABLE-NOW / STRETCH / NOT-APPLICABLE.

| # | Category | Key works (verified) | Verdict for ALBC |
|---|---|---|---|
| 1 | Critic/value-side | KARL (NeurIPS AI4Sci 23, replaces critic w/ linear-in-dictionary — authors admit no MuJoCo scale); KEEC (no actor at all); LC-SAC (arXiv 2602.04132) | Critic-concat of Koopman prediction = STRETCH; critic replacement = NOT-APPLICABLE. **LC-SAC negative signal: on 3D quadrotor (closest analog) ALL Koopman-Lyapunov variants underperform vanilla SAC (-8~-15%), reward-shaping variant collapses (-93%)** |
| 2 | Model-based surrogate | Mayfrank eNMPC (CCE 2024); Dyna-Koopman Rayleigh-Benard (25.6x faster rollouts, >40% wall-clock cut); Ji Real2Sim2Real continuum (= survey ref [67], TIE 2025); DeepKoCo | NOT-APPLICABLE: every method replaces an EXPENSIVE generator; our 4096-env GPU sim is already the cheap side. DR family blocks single K |
| 3 | Residual/hybrid control | KORR (arXiv 2509.12562, Koopman-predicted-latent conditions residual head, +~6pt under disturbance); RK-MPC (Unitree Go1 hardware, 500 Hz QP); Residual KMPC (F1TENTH hardware, lateral err -11.7~22.1%, 20% of training data); Esfahani CSL 2024 (RL tunes KMPC params) | STRETCH: pattern hardware-validated in adjacent domains, but thruster faults change B structurally (bounded-mismatch premise broken), IPO constraint ownership unsolved, zero UUV precedent |
| 4 | Offline RL/symmetry | KFC/KFC++ (ICML 22 spotlight, D4RL: hopper-medium 58->94.2, walker2d 79->108 vs CQL); KATS (OpenReview, unverified maturity) | NOT-APPLICABLE (no offline dataset; teacher is on-policy). KATS for DAgger buffer = STRETCH but we are not data-scarce. NOTE: no on-policy Koopman-symmetry augmentation paper exists — open gap |
| 5 | Deployment observer / online adaptation | EVOLVER (T-RO 2024, real quadrotor, **STM32F7 @ 100 Hz** — embedded-feasible); K-ESKF (IROS 24, -60% attitude propagation err); **OM-Koop (2025/26, field-validated on REAL USV/AUV, eigenvalue-constrained online Koopman = stability-safe recursive update)**; CR-RKL (recursive EDMD covariance-divergence fixes) | STRETCH — most deployment-relevant category. Koopman disturbance/current observer output as student extra-obs channel composes with obs4 (ZOH-2, 25 Hz). Gaps: no paper feeds observer into a distilled policy; train/deploy channel consistency needed (obs4-style); fault regimes untested |
| 6 | Imitation/distillation latents | KODex (CoRL 23 oral, analytic per-task — N/A); KOROL (CoRL 24, multi-step rollout-consistency loss trains Koopman-friendly features, ADROIT 86-100%, real robot); KOAP (arXiv 2410.07584, LSTM-over-history latent-action + Koopman consistency + recon, wins at 1% action labels) | STRETCH, most concrete training-side candidate: add a SUPERVISED linear-consistency term on the student — `||K*z_hat_t - z_hat_{t+1}||^2` against already-logged teacher z-sequences (KOROL/KOAP minus the banned reconstruction term). No new label source/loss class; single-K-under-DR is the untested central risk |
| 7 | Safety/constraints lifted-space | Folkestad Koopman-CBF (CSL 2021, seed paper); Neural Koopman CBF (ACC 23, bilinear + provable l2 bound); Robust Koopman CBF filter for actor-critic (arXiv 2605.26452, zero violations CartPole, mixed on locomotion); **Jung whole-body KMPC (arXiv 2603.03740, real Kinova 7-DoF, QP ~0.0389 s/step = ~25 Hz on desktop, 2.8% residual infeasibility)**; KTMPC constraint tightening (recursive feasibility + ISS proofs); conformal Koopman reachability (arXiv 2601.01076) | STRETCH — additive to IPO (deployment-time action wrapper, not a training change). Blockers: 25 Hz on DESKTOP for a simpler plant = caution at our bus rate on embedded; needs a forward Koopman plant model we do not have; fault-range validity unproven; filter itself can go infeasible |

Cross-cutting blocker (every category): a single Koopman operator K assumes one dynamics regime;
our 28D DR + discrete thruster faults make the true operator per-episode K(theta_env). Any adoption
must either condition on p_t/z (reintroducing encoder-like machinery) or be robustified/tightened —
and no surveyed paper validates under actuator-fault-scale regime switching.

Priority ranking (my synthesis):
1. NEAR-TERM training-side probe: student Koopman-consistency term (cat 6, supervised-only) —
   smallest diff, rides existing distillation targets; pairs naturally with the queued observability
   retrain roster. KIPPO obs-lifting arm (Sec 8) remains the other near-term candidate.
2. MEDIUM-TERM deployment-side: online Koopman disturbance/current observer as a student extra-obs
   channel (cat 5) — OM-Koop gives real-marine precedent, EVOLVER gives embedded feasibility;
   requires obs4-style sim-consistent channel design; fault-regime validation mandatory.
3. LONG-TERM: Koopman-CBF/KMPC deployment safety filter (cat 7) — only after a validated forward
   Koopman model of the coupled vehicle+arm exists; additive to IPO.
4. DROP: critic replacement (cat 1), sim surrogate (cat 2), offline symmetry augmentation (cat 4).
5. NEGATIVE EVIDENCE to remember: LC-SAC quadrotor degradation — do not bolt Koopman-Lyapunov
   constraint terms onto the actor in high-DOF underactuated settings.

## 10. History/delay-embedding and partial-lifting variants (3-axis survey, 2026-08-03)

Triggered by user questions: teacher history availability, HVOK option, partial lifting option.
Fact base: teacher o_t already embeds 52D of temporal features (30D tracking hist stride-3 x3 +
16D action hist x2 + 3D integral + 3D bias-EMA); bias-EMA is itself a crude eigenvalue-near-1
slow-mode filter. Reports: axis_*.md.

AXIS A — HVOK/time-delay Koopman: STRETCH. Hidden-STATE recovery via delay embedding is
established theory (HAVOK Nat.Comm 2017; Kamb/Kaiser/Brunton/Kutz SIADS 2020; deep delay
autoencoders ProcRoySoc 2023). Slow-PARAMETER recovery from delay embedding ALONE is NOT
established — the eigenvalue-1 trick in the literature uses an explicit parameter channel
(arXiv 2304.00147, 2607.07594); treating it as given would be our own unverified inference.
No precedent wires delay-Koopman features into an RL actor (all found work is LQR/MPC:
arXiv 2507.14455, 2408.06607; Hankel-DMDc ship sys-ID 2502.15782). Window selection guidance
is ad hoc everywhere. Key mechanism distinction: HVOK = Hankel + SVD low-rank extraction, not
"more delayed channels"; a fair test needs windows matched to parameter timescales (currents
~O(10s), faults episode-long) — orders longer than the current 9-physical-step embedded history,
i.e. new infrastructure, not a drop-in arm.

AXIS B — partial/structured lifting: STRETCH, sharpens the phi_x design. Precedents: Koopman-DFL
causal observables (Selby-Asada RA-L 2021: causality filter excludes g(x,u) anti-causal
observables; ~8-20x ISE gains in excavation sim), Koehler arXiv 2207.12132 (lifting state-only
provably yields LPV input matrix — justifies keeping u raw), SE(3)-structured dictionaries
(2103.03363), wind-farm physics-vs-AE lifting (2409.06523: physics lifting wins nominal, loses
under model drift — caution under DR). No precedent for partial lifting of an RL policy's obs
(the T-RO survey itself has no such taxonomy — open gap). Design: lift the 20D dynamic block
(attitude/rate/arm/ESC — do NOT narrow to 9D core; arm+ESC carry the fault/coupling
nonlinearities), pass command/integral/bias-EMA/history through identity; prediction targets
exclude the command block (exogenous; user-flagged joint-lifting caveat) — action-history is a
known shift register given a_t, integral/EMA have known linear updates. Ablation needed:
full-72D lift vs 20D-block vs no-lift.

AXIS C — teacher-side history window: NOT-APPLICABLE. RMA/HORA/Distillation-PPO teachers consume
privileged + current obs only; history is the STUDENT'S SUBSTITUTE for privileged access, never a
teacher complement (RMA base policy = x_t + a_{t-1} + z only; adapter alone sees 50-step history).
No precedent keeps full p_t access AND adds teacher history windows. CTS (2405.10830) blurs the
split by sharing the trunk, not by teacher history. phi_x(o_{t-H:t}) on the teacher would add a
third temporal encoder competing with z, with no deployment payoff (student GRU already integrates
history). Adjacent actionable: DRKO (IEEE TII 2024, deep recurrent Koopman on delay windows for
robust MPC) is real precedent for a Koopman-linear recurrent STUDENT encoder — reinforces the
cat-6 student-consistency/SSM direction; MAKO (2510.09042) meta-adapts lifting per system
parameters (MPC-side analog of z-conditioned K).

Clarification recorded (user question): past control inputs inside o_t are NOT the survey's
joint-lifting hazard. The hazard is asking a PREDICTIVE operator to advance u (no dynamics law);
o_t's action history serves a POLICY-INPUT role with no prediction duty — and under actuation
delay + ESC filter dynamics (both in our plant/DR), past inputs are rigorously part of the true
state (delay-system state augmentation), so the design is theoretically sound, not a hack. The
caveat only re-enters for a predictive aux model, where shift-register/exogenous handling
(Sec 10 Axis B) resolves it.

Updated shortlist after Sec 9-10: (1) KIPPO-style instantaneous o_t lift with BLOCK-PARTITIONED
prediction targets (Axis B design) — near-term screening arm; (2) student-side Koopman-linear
consistency / recurrent-linear encoder (cat 6 + DRKO) — rides observability retrain;
(3) deployment observer (cat 5) — medium-term; HVOK-infrastructure and teacher-history-window
variants dropped.

## 11. Conversation-state addendum (2026-08-03, persisted pre-compaction)

Decisions/answers reached in discussion, not yet captured above:

1. **phi_x design settled points (user-agreed direction, not yet a proposal):** input = o_t only
   (z BYPASSES phi_x, concatenated raw as today). Rationale: single-variable screening discipline,
   z-hat error propagation surface at deployment, z_sweep diagnostic interpretability. z-into-phi_x
   is NOT fundamentally wrong (extended-state Koopman is the principled fix for the DR family) but is
   staged BEHIND the safer scaffold-side alternative K(z) (z conditions only the training-time
   operator; deployed phi_x stays o-only). Order: bypass -> K(z) -> phi_x(o,z), data-gated.
2. **Normalization**: lifting does not remove input normalization (it relocates it to phi_x's input);
   the real win is replacing running-stat EmpiricalNorm non-stationarity with static DR-derived
   min-max at phi_x input + bounded (tanh) output — the same remedy already applied to the p_t
   encoder after the z-drift KL-spike incident.
3. **Latent budget m**: empirical (KIPPO rule-of-thumb 2-4x state dim is itself empirical). Cheap
   pre-estimation: offline supervised training of phi_x+K+decoder on logged rollouts at several m,
   pick the plateau of recon/prediction curves; note our 72D obs is partially pre-lifted (52D
   temporal), so try smaller m first. Screening keeps ONE m; sweep only if the arm shows promise.
4. **Joint-lifting caveat (survey p.1092) vs our obs**: the hazard = asking a predictive operator to
   advance u (no dynamics law). Our action history inside o_t is a POLICY input (no prediction duty)
   and, under control-latency DR + ESC filter dynamics, past inputs are rigorously part of the true
   state (delay-system augmentation). The caveat only bites a predictive aux model at the command
   block -> excluded from prediction targets (Sec 10 Axis B block table).
5. **Control-coherent Koopman [37] preliminary calibration** (final verdict pending cluster read):
   the survey's "input variation" = generalization over new input VALUES/sequences (fits our
   arm-vehicle coupling axis); our thruster-fault DR = structural change of the input CHANNEL
   (B-matrix column loss) which is KCF [36]/switched-model/K(z) territory, not CCK's headline claim.
   Do not conflate the two when the deep-read returns.
6. **Sim-to-real strategy verdict** (user's research focus): phi_x = sim-trained + frozen ->
   zero-shot valid (deployment never uses linearity; only obs-coverage matters, same surface as the
   existing actor; NEVER re-fit phi_x on real data post-deployment — moving-target at deploy).
   Model-role K (observer/safety filter) = sim-pretrain + REAL-data refit (cheap least squares) /
   online update; sim-fit K inherits the analytical-hydro model error (wiki:
   sim_hydro_nominal_is_analytical_not_measured). Third option with direct thesis value: K_sim vs
   K_real spectral comparison on existing watertank datasets (data/ 1_hero_lab, 2_kiro, 7_ucrc...)
   as a QUANTITATIVE per-axis sim-to-real gap meter — offline analysis only. (Note: data/ is
   host-side, not visible in-container; plan the analysis for a host session or exported logs.)

## 12. PENDING WORK LEDGER (running workflows — resume here after compaction)

> **STATUS 2026-08-03 (post-compaction): ALL THREE WORKFLOWS COMPLETE AND SYNTHESIZED.**
> Split reports live at  as cluster_{separable_theory,coherent_bilinear,
> underwater_row}.md (w580hqgii), table1_{aerial_disturbance,legged_domainshift}.md (wfekof8bg),
> s2r_{policy_transfer,model_correction}.md (wt6v1pp4q). Syntheses: Sec 13 (input handling),
> Sec 14 (Table I rows), Sec 15 (sim-to-real), Sec 16 (training staging / excitation).

Three background workflows were in flight at persist time. Their outputs land at
/tmp/claude-0/-workspace/add36792-5228-49ca-a6e5-ffa3c915bb4e/tasks/<taskId>.output
(JSON; result under key "result", one sub-key per cluster). Journals (per-agent full returns):
/root/.claude/projects/-workspace/add36792-5228-49ca-a6e5-ffa3c915bb4e/subagents/workflows/<runId>/journal.jsonl

| taskId | runId | Covers | Owed synthesis |
|---|---|---|---|
| w580hqgii | wf_6ee68324-6a9 | Sec II-C/V-B citation deep-read: cluster1 = [36] input-state separable/KCF + [105] infinite-input + [161]/[162]; cluster2 = [37] control-coherent + [43]/[97] bilinear; cluster3 = Table I underwater row [87]/[88]/[89]/[90]/[150] | (a) affine vs bilinear vs control-coherent choice for the phi_x aux model given ESC-filter + quadratic thrust + fault DR; (b) final verdict on user's "CCK fits my system" question (see Sec 11.5); (c) marine dictionary-design hints |
| wfekof8bg | wf_33ac14c9-ffb | Table I relevant rows: clusterA = aerial disturbance [78] episodic eigenfunctions, [84] hierarchical disturbance model, [86] online NN+Koopman bilinear; clusterB = legged [50] incremental domain-shift-robust embedding refinement (+[53],[131] skim) | (a) online-adaptation mechanics transferable to the deployment observer item; (b) whether [50]'s domain-shift refinement translates to per-episode DR or only slow deployment drift |
| wt6v1pp4q | wf_08675905-a52 | Koopman x sim-to-real targeted survey: axis1 = policy-transfer (zero-shot, domain alignment in lifted space); axis2 = model correction (sim-pretrain + real-refit recipes, digital-twin calibration, Koopman spectra as gap metric precedent) | (a) does the exact "Koopman for policy sim2real" framing exist (thin-literature answer acceptable); (b) precedent + data requirements for the K-refit recipe; (c) precedent for the gap-meter idea (Sec 11.6) |

On each completion: split result JSON into <name>.md files, read, synthesize in
chat, and append findings to this doc (Sec 13+). Per-cluster reports from COMPLETED earlier rounds
already live at : paper_p*.md (survey read), code_report.md, albc_report.md,
survey_{critic_value,model_based,residual_hybrid,offline_symmetry,observer_adaptation,
imitation_distill,safety_constraints}.md (7-category round), axis_{hvok_delay,partial_lift,
history_window}.md (3-axis round).

Standing user-context for synthesis: research focus = sim-to-real gap reduction; experiment decision
still user-gated (no proposal authored yet — exp-design when user green-lights); screening convention
= single-seed, ~2000 iters, separate track; launch only via omx queue-launch (human gate).

## 13. Input-handling deep-read synthesis (w580hqgii, 2026-08-03)

Full reports: cluster_separable_theory.md ([36][105][161][162]), cluster_coherent_bilinear.md
([37][97][43]), cluster_underwater_row.md ([87]-[90][150]).

### 13.1 The affine-vs-bilinear question — resolved AGAINST pure affine

The two theory clusters initially appear to disagree; they reconcile as follows.

- Theory cluster reading: `phi_x(o+) = K phi_x(o) + B phi_u(a)` with nonlinear phi_u looked like
  KCF Th 4.3's general input-state separable form. **Correction on cross-check**: the additive form
  equals `Psi+ = A(u) Psi` only with input-dependence confined to the inhomogeneous column
  (Lemma 4.5's affine special case). Th 4.3's general form has EVERY entry of A(u) varying with u —
  i.e., multiplicative state x input coupling. [97]'s taxonomy makes the same point operationally:
  `B phi_u(a)` is still a "linear realization" no matter how rich phi_u is; the missing ingredient
  is STATE-dependence of the input's effect, not input-encoding richness.
- [97] Theorem II.1 + Corollary: control-affine plant with state-dependent input gain (our drag /
  added-mass / fault-scaled thruster effectiveness) admits a bilinear realization over generic
  dictionaries, but NO linear realization at any dictionary size. Empirical signature: linear error
  flat ~0.55-0.60 from 10 to 927 basis fns; bilinear drops to ~0.03-0.05. MPC: 74.3 cm (affine) vs
  2.03 cm (bilinear) vs 1.92 cm (full nonlinear, 500x compute).
- [43] is the on-point worked example: input-SCALED disturbance (structurally the shape of thruster
  fault DR) breaks standard NMPC (80-100% failure) while bilinear Koopman-NMPC survives (60-100%);
  validated sim -> Gazebo -> hardware (88%).
- Underwater cluster: [90] hand-derived nonlinear action reparametrization restored affine structure
  (validates the phi_u premise) but needed ONLINE (A,B) refit to survive real disturbance; [150]
  states verbatim that affine-in-raw-control is only "locally accurate" once actuation is nonlinear,
  and names state-dependent actuation as open future work; [87] achieves de facto bilinearity via
  dictionary cross-terms (state x action x flow) inside one lift — hardware-validated, and the
  cheapest implementation route.

**Design update (supersedes the plain-affine sketch in Sec 8/11)**: aux model becomes
`phi_x(o+) ~ K phi_x(o) + B phi_u(a) + H (phi_u(a) (x) phi_x(o))` — [97]/[43]'s bilinear form, with
H scoped/sparsified to lifted components plausibly carrying hydro/fault information (CCK's
"no phantom pathway" discipline applied as a structural constraint). Equally valid cheaper route:
[87]-style explicit cross-term features inside phi_x's dictionary. phi_u alone handles only the
static command nonlinearity (deadband/quadratic in a); it structurally cannot represent
state- or fault-dependent thrust effectiveness.

### 13.2 Two gaps the survey citations do NOT cover (and what to do)

1. **Fault DR = family of dynamics.** [36]/[105]/[161]/[162] all fix T(x,u) as one known map. A
   single fixed (K,B,H) assumes one lifted subspace jointly invariant across the ENTIRE DR
   distribution — stronger than any cited theorem guarantees, plausibly false across fault regimes.
   Actionable: condition the scaffold on the privileged latent — K(z), B(z) via small hypernetwork
   (training-only, scaffold asymmetry principle of Sec 11 preserved). phi_u only sees a_t, never the
   fault parameter — it structurally cannot absorb theta-dependence.
2. **ESC filter + latency = Markovity problem, not a form problem.** One-step lifted recursion
   requires phi_x's input to already carry actuator memory. o_t's action history (16D) partially
   covers this; verify the ESC-state block (6D in the 20D proprio block) suffices before blaming
   the model form for prediction error.

Switched/mixture forms ([161], Lemma 4.4): right tool ONLY if fault DR is categorical
(nominal/stuck/reversed); for continuous DR sweeps, z-conditioned (K,B) is the correct
generalization, not a matrix bank.

### 13.3 CCK final verdict (user's "fits my system perfectly?" question — answer: NO, partially useful)

- [37]'s exactness precondition — actuation subsystem EXACTLY linear in u in local coordinates —
  holds at most for the ESC filter's internal LTI state, NOT the full chain: the quadratic thrust
  map and fault DR sit strictly between filter and rigid body. CCK's exact-B construction cannot
  cover a phi_u spanning the whole actuation chain.
- The survey's gloss ("particularly useful for manipulation tasks and underactuated systems",
  "generalization to new control sequences") overstates the paper: [37] is a sim-only 2-link arm
  MPC result about B's causal sparsity; no input-variability generalization experiment exists in it.
- What IS transferable: the failure mode it exposes (regression-fit B invents physically impossible
  instantaneous control->state pathways, invisible in one-step prediction error, catastrophic under
  closed-loop exploitation — 8-22x worse tracking with IDENTICAL prediction-error histograms; the
  B-swap ablation isolates it) and the discipline of structurally constraining B/H sparsity to true
  actuator causality. Our RL actor reading phi_x could exploit a phantom pathway exactly the way
  their MPC did — the aux-model's B/H should not connect action encodings to obs blocks the real
  actuation path cannot touch in one step.
- Fault DR remains uncovered by CCK (fixed known dynamics, same as the rest of the theory cluster).

### 13.4 Marine dictionary-design hints (underwater row)

- Signed-quadratic velocity v|v| per DOF recurs in both physics-informed marine papers ([90][150]).
- Angle-of-attack-like ratio terms (arctan(vy/vx), [90]) — directional hydro cue, not just magnitude.
- Added-mass belongs as a coefficient the encoder infers (via z), not as an explicit input feature.
- Current should enter as MULTIPLICATIVE cross-terms with state ([87]: baseline degrades 4.8x vs
  FARM 2.7x from static to 0.46 m/s flow), not only as our additive bias-EMA channel.
- Caution: a noisy/estimated disturbance input costs accuracy exactly where the disturbance is absent
  ([87] zero-flow regression) — bias/variance budget for fault/current conditioning features.

## 14. Table I relevant-rows synthesis (wfekof8bg, 2026-08-03)

Full reports: table1_aerial_disturbance.md ([78][84][86]), table1_legged_domainshift.md ([50]+[53][131]).

### 14.1 Three distinct adaptation cadences (aerial trio)

| Ref | Cadence | Mechanism | Deployment relevance |
|---|---|---|---|
| [78] KEEDMD | Episodic (between-trial batch refit) | NN eigenfunctions warm-start re-trained per episode, cumulative data, confidence-weighted additive controller blending; hardware, 19.3% tracking gain in 3 episodes; compute grows per episode (capped at 5) | Blending pattern reusable; wrong shape for within-episode observation |
| [86] KoopNet | Offline-train, FROZEN at deployment | Joint dictionary + bilinear model from 4 min PID data; recon loss DISABLED (raw state carried in z); survives z<=0.05 m ground effect where nominal NMPC crashes | **Survey's "online update" phrasing is WRONG** — verified against the paper: runtime is ordinary re-encoding of a fixed phi, no parameter adaptation. Evidence for zero-shot within training regime, NOT for online adaptation |
| [84] DHC | Genuinely online, per-step recursive DMDc | Reference-space re-identification; rank-conditioned freeze safeguard; Lyapunov proof the wrapper cannot destabilize a stable inner loop; 720 hardware trials; per-trial randomized mass/inertia (structurally per-episode DR); "disturbance embedded in the learned model" | Strongest template for the deployment-time observer item: (a) freeze-on-rank-deficiency guard, (b) correction must vanish at nominal to inherit the non-destabilization argument |

None of the three factors disturbance into an explicit conditioning variable like our z — all absorb
it into observables/operator. No precedent either way on explicit-factoring vs implicit-absorption.

### 14.2 [50] Incremental Koopman — "domain-shift" does NOT mean DR

Load-bearing correction: [50]'s refinement loop is an OFFLINE, single-fixed-domain data-coverage
curriculum (harvest failed MPC rollouts -> append data -> grow latent dim -> retrain; each of the 7
robot x terrain suites trained SEPARATELY; nothing updates after training). It transfers to neither
per-episode DR nor deployment drift. Do not port its trigger loop for either. Transferable nuggets:

- Anti-collapse guard: z = [x, g'(x)] (concat raw state) makes A=B=0, g=0 degenerate solution
  impossible — adopt for phi_x regardless.
- Light reconstruction weight (alpha=0.1) empirically beats heavier weighting — consistent with our
  decoupled-aux plan.
- Theorem 1 sizing heuristic: m = Omega(n ln n) samples vs latent dim, error
  O(sqrt(ln n / m)) + O(1/sqrt(n)) — grow n and m together (informs the empirical-m budget, Sec 11).
- Ablation: dataset-coverage increment mattered more than dimension increment (8.4x vs 4.8x error
  inflation when removed).

Side-finds: [131] contains Streaming SSD (SSSD) — online fixed-memory Koopman subspace update; lead
for the deployment observer. [53] (abstract-level only): Koopman generator spectrum differs per
terrain type, used for sensor-free terrain classification — independent support for the spectral
gap-meter / regime-detection idea. Note: survey's in-text claim that [131] is a legged-robot
modeling study is a citation error (it is general SSD theory).

## 15. Koopman x sim-to-real synthesis (wt6v1pp4q, 2026-08-03)

Full reports: s2r_policy_transfer.md, s2r_model_correction.md.

### 15.1 Confirmed white space

The survey (arXiv:2408.04200 full text) contains ZERO occurrences of sim-to-real / reality gap /
domain randomization / domain adaptation. No published work: (a) trains an RL policy in sim with a
Koopman component and attributes zero-shot real transfer to it; (b) does Koopman-space
adversarial/moment-matching alignment of sim-vs-real trajectory distributions; (c) computes a
spectral distance between K_sim and K_real as an explicit gap score; (d) claims Koopman structure
permits REDUCING DR breadth. Marine Koopman beyond OM-Koop is all simulation-only (three candidates
verified; one search-snippet "towing-tank validation" claim was a hallucination caught by direct
abstract fetch).

### 15.2 The recurring published pattern: freeze lifting, refit operator on small real data

- Whole-Body Safe Control w/ Koopman Neural Dynamics (arXiv:2603.03740, Kinova Gen3 hardware):
  "collect hardware data and fine-tune only the A and B matrices; embedding frozen." No DR at all.
- Digital Twins Meet Koopman (arXiv:2409.10347, 1:5 vehicle hardware): quoted sim2real gap number
  (0.1539 -> 0.1458 m, -5.2%) tied to Koopman modeling.
- Bruder residual Koopman (IJRR 2025, real soft-robot arm): physics-Koopman prior + data-driven
  residual operator — structurally identical to our K_real = K_sim + Delta sketch (their "sim" =
  analytical physics model, mapping onto our analytical hydro nominals vs watertank telemetry).
  Strongest template for the refit half. (Number-level claims unverified — PDFs corrupted.)
- Non-Koopman nearest neighbor FADA (arXiv:2606.28476, real humanoid): freeze teacher/planner,
  fine-tune only the inverse-dynamics module on ~2 min real rollouts — the sample-efficiency
  benchmark for the "small real dataset" claim.
- No real-data sample-efficiency curve exists for the sim-Koopman + real-residual recipe; Split
  Koopman (arXiv:2502.00162, sim-only) saturating past ~4096 samples is the only proxy.

This validates Sec 11.6's staging verdict: phi_x sim-trained + frozen (zero-shot valid, deployment
never uses linearity); model-role K refit on real data; the two roles decouple cleanly.

### 15.3 Gap meter: APPLICABLE-NOW and apparently novel

Spectral-Grassmann Wasserstein metric (arXiv:2509.24920) is exactly the mathematical primitive for a
K_sim-vs-K_real distance (spectral decomposition + Grassmann geometry + OT), validated only on
synthetic/fluid systems — pointing it at a robot sim-vs-real comparison would be a novel
contribution, not a reproduction. DMD-GEN (arXiv:2412.11292) is cross-field precedent that
"compare DMD modes between two data sources as a fidelity score" is established. Caution: Koopman
spectral estimates are themselves approximation-error-prone — validate the meter's own noise floor
(e.g., K_sim-vs-K_sim across seeds/data splits) before trusting sim-vs-real deltas. [53]'s
per-terrain spectral signatures independently support regime discrimination via spectra.

### 15.4 Updated shortlist standing (verdicts after all three deep-reads)

1. KIPPO-style phi_x on o_t with block-partitioned targets + bilinear H term + z-conditioned scaffold
   — screening arm candidate (mechanism precedent solid; RL-policy application is ours to test).
2. K_sim vs K_real watertank spectral gap meter — APPLICABLE-NOW, novel, zero training-side risk;
   needs only logged trajectories + EDMD fits + the S-G-W metric with a noise-floor control.
3. Deployment-time online observer — DHC's guard/vanishing-correction patterns + SSSD as the online
   update primitive; deferred until student-side work is scheduled.
4. Koopman-as-DR-replacement — NOT SUPPORTED anywhere; drop this framing. Koopman components
   complement DR at most.

## 16. Training staging: excitation data vs RL (user question, 2026-08-03)

Question: Koopman fitting reportedly needs excitation-rich/random data, which conflicts with RL
training data; pre-train then freeze, or tune during RL, or an episodic/iterative scheme like
[78]/[100]?

([78] = episodic KEEDMD; [100] = Abraham & Murphey active-learning line — survey III-C.2 credits
linear-dictionary Koopman with a data-efficiency advantage via active learning, and notes deep-NN
observables REDUCE active-learning effectiveness.)

### 16.1 The conflict dissolves under the role decomposition (Sec 11)

- **Representation role (phi_x as policy input, KIPPO)**: persistent excitation is NOT required.
  PE is a least-squares system-ID requirement for identifying a global K; the representation role
  only needs coverage of the state distribution the policy visits — which is exactly what on-policy
  rollouts provide. KIPPO trains phi_x concurrently on PPO rollouts with a decoupled optimizer and
  no excitation injection. Additionally: early-training policy is near-random (natural excitation),
  and DR at 4096 envs (payload/current/fault) supplies plant diversity no excitation signal on real
  hardware could match.
- **Model role (scaffold K/B/H, gap meter, sysID)**: excitation-rich data IS required — but its
  collection needs not touch the RL loop at all. In sim, a dedicated data-collection pass (random +
  scripted chirp/PRBS-style actions across 4096 envs) costs minutes of wall clock; the RL policy
  never trains on those trajectories. The perceived conflict assumes excitation and RL must share
  one rollout stream; in simulation they don't.

### 16.2 Recommended staging (pre-train -> concurrent-decoupled -> freeze)

1. Stage 0 (cheap, optional but recommended): offline pre-train phi_x on a mixed corpus of
   random-policy + scripted-excitation sim rollouts. Precedent [86]: 4 min of PID data sufficed for
   a quadrotor bilinear Koopman model; our simulator gives orders of magnitude more for free. Gives
   a warm start and stabilizes early aux training.
2. Stage 1: concurrent DECOUPLED training during RL (KIPPO recipe) — necessary because the visited
   state distribution shifts as the policy improves; a purely pre-trained frozen phi_x goes stale
   for late-policy states. TRPO's KL constraint already bounds per-update policy shift against
   representation drift (Sec 11 homework item 2).
3. Stage 2: freeze after a warmup window (or drop to a slow LR). Freeze-vs-continue is itself a
   cheap ablation, not a design commitment.

### 16.3 What the episodic/iterative papers actually contribute

- [78]'s episodic loop exists because REAL data is expensive and sequential. In sim RL, every
  TRPO iteration already IS an episode batch — KIPPO's concurrent recipe IS the [78] pattern with
  episode = rollout batch. Two reusable details: (a) warm-start refits on CUMULATIVE data — argues
  for a small replay buffer for aux training so phi_x doesn't forget early-policy states;
  (b) confidence-weighted blending of newer models (deployment-side pattern).
- [50]'s incremental loop (closest sim-side precedent): alternate collect-with-current-controller /
  retrain, grow latent dim, harvest failure cases — its anti-collapse guard and light recon weight
  transfer (Sec 14.2); its loop itself is an offline curriculum, not an in-RL mechanism.
- [100]'s active learning does NOT transfer to RL training: it chooses actions to maximize model
  information, and hijacking the policy's actions for model learning is precisely what WOULD hurt
  RL. It becomes relevant at the real-data stage: the survey's data-efficiency point (linear
  dictionary + active learning beats deep NN) is an argument for freezing the deep phi_x and
  refitting only the LINEAR operator on real data — which is exactly the Sec 15.2 recipe.

---

# PART II — ADVERSARIAL ITERATION ROUNDS (2026-08-03, later session)

User directive: iterate {critique the existing survey → targeted research to repair/extend} up to 4
rounds. Sections 17+ record each round. Where a later section contradicts an earlier one, THE LATER
SECTION GOVERNS; superseded claims are listed explicitly in the round's "verdict changes".

## 17. ROUND 1 — adversarial critique record

Method: 4 independent adversarial reviewers (lenses: theory rigor / evidence-citation integrity /
codebase system-fit / epistemic process + blind spots), symmetric skepticism mandated (negative
verdicts attacked as hard as positive ones). Full reports:
`r1_critique_{theory,evidence,systemfit,epistemic}.md`.

### 17.1 Confirmed defects (cross-lens, load-bearing)

1. **Trust-region drift reassurance FALSE (triple-confirmed: theory THEO-7, systemfit THEO-1,
   epistemic THEO-3).** §16.2's "TRPO's KL constraint already bounds representation drift" is wrong
   three ways: (i) the KL is conditional on inputs — an out-of-band phi_x step changes pi(.|o) with
   zero KL budget consumed, and stored old_mu/old_logp become stale (biased surrogate BEFORE the
   trust region applies); (ii) code: `constraint_trpo.py` groups params by name prefix (:161-184) —
   a phi_x submodule on the policy is silently swept into `_policy_params` AND stepped by the aux
   Adam (double-owned); K/B/H used only in the aux loss crash `_flat_grad(allow_unused=False)`
   (:354-366); `storage.clear()` (:526) runs before the only runner hook, so the aux step must be
   inserted inside `ConstraintTRPO.update()`; (iii) literature: Moalla et al., NeurIPS 2024
   (arXiv 2405.00662) shows representation collapse BREAKS trust-region guarantees — the opposite
   of the doc's claim.
2. **Brand-vs-mechanism framing hole (epistemic THEO-2).** KIPPO = OFENet (ICML 2020,
   arXiv 2003.01629: expansive aux-dynamics-prediction features consumed by the agent) + a LINEARITY
   restriction on the latent transition. The linearity restriction is the only Koopman-specific
   testable content, and no proposed arm isolates it. Decisive control arm: identical phi_x trained
   with an UNCONSTRAINED (nonlinear MLP) latent predictor.
3. **§9 priority-1 (student Koopman-consistency term) near-vacuous (theory THEO-4 + systemfit
   THEO-3, independently).** 22 of 28 p_t dims are constant within episode → teacher z-sequences are
   dominated by constants → global minimizer K ≈ I; the term degenerates to a temporal-smoothness
   penalty that (a) contains no Koopman content, (b) injects irreducible-residual noise on the 6-7
   time-varying dims (OU current, measured lin-vel — not autonomous functions of z), (c) directly
   opposes the episode-start identification transient the student campaign is trying to improve.
4. **Single-K under DR is an INVARIANCE PRESSURE, not neutral noise (theory THEO-9).** A shared
   operator's aux loss penalizes exactly the phi_x features whose one-step evolution depends on
   theta_env → the minimizer prefers plant-invariant features → the aux objective is a domain-
   invariance regularizer on the policy's input representation. For a sim-to-real-adaptation
   project this is a directional risk, and the most plausible mechanism by which a KIPPO arm HURTS
   here while helping on un-randomized MuJoCo.
5. **Gap meter (§15.3/§15.4 #2) not as-stated (theory THEO-12 + epistemic THEO-4).** EDMD spectra
   depend on dictionary AND sampling measure (closed-loop policy-driven data); the proposed
   noise-floor control doesn't cover distribution mismatch. Project-wiki facts defeat
   "APPLICABLE-NOW": real vehicle = IMU+pressure only (no DVL → surge/sway unobservable), <=25 Hz
   ZOH / 10 Hz joints, 2/6 thrusters currently faulted; K_sim is undefined under DR (a family
   K(theta)); decision-relevance never argued.
6. **Verdict-flip adjudication (§4/5 → §8) (epistemic THEO-1).** Score: ~1/3 genuine new evidence
   (KIPPO/SKooP existence defeats "nobody feeds lifted obs to an RL actor"), ~1/3 rule-
   reinterpretation-after-push-back (the No-Aux-Losses scope re-reading needed zero new evidence;
   the codebase's own precedent axis is input-change-vs-aux-loss, under which phi_x+rec+pred lands
   on the banned side — systemfit THEO-9), ~1/3 unresolved-but-endorsed (DR-single-K conceded and
   endorsed anyway). Also: §4/5 issued "NOT SUPPORTED / decisive" from a single survey with NO
   literature search — the survey even self-declares its RL coverage truncated (p.1094, evidence
   THEO-1); the process defect was the review's, not the survey's window. KIPPO's real weight: one
   MS-thesis-derived 4-seed/env MuJoCo paper, PPO, no DR/constraints. SKooP is partially COUNTER-
   evidence for actor-side lifting (they built the machinery and fed the critic only).
7. **Compound-arm violation (epistemic THEO-5).** The "screening arm" accreted 4 simultaneous
   deltas (phi_x lift + block-partitioned targets + bilinear H + K(z) scaffold) vs the single
   precedent, on a different algorithm, under DR the precedent lacked, at single seed — while
   §11.1 used single-variable discipline to exclude the user's z-into-phi_x variant. Asymmetric
   standards confirmed (epistemic THEO-10 catalogues 4 matched pairs).
8. **§13.1 "resolved AGAINST pure affine" demoted (theory THEO-2).** [97] Cor II.1 proves bilinear
   existence + NO GUARANTEE for linear — not non-existence; the KCF Lemma 4.5 attribution is wrong
   (the additive form is the inhomogeneous-column sub-family, neither Lemma 4.5 nor Th 4.3-general);
   the source cluster report's own bottom line (affine adequate as engineering default) was silently
   overridden; and every cited number is a MODEL-FIDELITY-for-MPC number — for the aux/representation
   role (model never rolled out) exact-realizability does not resolve the design; a harder-to-satisfy
   affine constraint is if anything a STRONGER inductive bias. Affine-vs-bilinear = follow-up
   ablation, not a prerequisite. ([97]'s decimal figures are figure-reads, not stated in text —
   evidence THEO-11.)
9. **Normalization plan withdrawn (systemfit THEO-2).** o_t bounds are not DR-derivable (integral/
   bias-EMA are policy-dependent accumulators); swapping the normalizer breaks 6 consumers incl.
   the just-closed deploy-parity contract; EmpiricalNorm drift is 1/k-annealing and the constructor
   already takes `until=N` (one-kwarg hard freeze). The p_t-incident analogy transplants a remedy
   without its diagnosis.
10. **Evidence corrections (evidence lens).** (a) [131] mis-resolved: SSD/SSSD is survey ref [31]
    (Haseli & Cortes); the "survey citation error" accusation is withdrawn — the real [131]
    (Ordonez-Apraez, L4DC 2024, Dynamics Harmonic Analysis) is a defensible legged citation and was
    never read; (b) the "QP ~0.0389 s ≈ 25 Hz" figure for arXiv 2603.03740 is fabricated — Table II
    says 0.21913 s/step ≈ 4.6 Hz (safety-filter blocker is WORSE, structurally not marginally);
    (c) KIPPO pages are 4994-5002 and its variance claim carries a "(one exception)" caveat the doc
    dropped; (d) §15.1's "ZERO sim-to-real occurrences" needs scoping to body text ([67]'s title
    contains Real2Sim2Real); (e) identity-inclusion guard (§14.2 "adopt regardless") is the design
    KIPPO §3.1 EXPLICITLY REJECTS for multi-fixed-point systems (Draeger 1995 topological
    conjugacy) — our multi-equilibrium plant is exactly the case named; the two anti-collapse
    designs are mutually exclusive; (f) LC-SAC hardening: 5 seeds, overlapping sigma bands, paper's
    own narrative reads favorably for stabilization + variance — the blanket actor-side prohibition
    is narrowed to reward-shaping variants; (g) NoEncoder is a REGISTERED TASK, not an existing
    baseline — no run exists on the current plant (the only noenc artifact is April full-DOF,
    pre-TAM/pre-buoyfix), so the 4-arm screen is 4 new runs, not 2; (h) "Dyna-Koopman" is an
    invented name (Plotzki & Peitz, arXiv 2603.28074); (i) no hallucinated arXiv IDs anywhere —
    all 10 nonstandard-looking IDs resolve; KIPPO/SKooP/OM-Koop quotes verbatim-accurate.
11. **Other reasoning repairs (theory lens).** §5.2's "information argument (decisive)" restated in
    its correct narrow form: DPI only bars ADDING privileged info; it says nothing about
    optimization geometry/sample complexity (the same error class as §4.4's UAT non-sequitur,
    THEO-5); and phi_x(o_t) on our o_t (46-52D embedded history) IS a short-window history encoder,
    so the "fixed pointwise vs history encoder" dichotomy collapses. §4.2/§8.3's p_t-constancy
    claims corrected (6-7 of 28 dims time-varying in-episode; eigenvalue-1 steelman is a tautology —
    recoverability is an observability question, not spectral). §16.1's PE dissolution restated
    (plant diversity ≠ input excitation; under-identified scaffold = weakly-defined bias = null-risk).
    §10 Axis A's window-length premise is a non-sequitur (constant params have no timescale;
    window is set by excitation/observability — RMA's 50-step adapter is the counterexample);
    the HVOK-drop survives only on the no-precedent + student-already-integrates-history grounds.

### 17.2 What survived all four lenses

§4.1 (Koopman linearity is about time evolution, not the obs→action map); §13.2 item 2 (ESC filter +
latency = Markovity, not model form); §13.3 CCK verdict incl. phantom-pathway discipline; §14.2
([50] domain-shift ≠ DR); §14.1 [86] frozen-at-deployment finding (though the accusation against the
survey's wording was overreach — evidence THEO-9); §15.4 item 4 (Koopman-as-DR-replacement: drop);
§16.3 ([100] active learning would hijack policy actions). The student-reuses-frozen-normalizer-
instance and NoEncoder-registration facts verified at code level.

## 18. ROUND 1 — targeted research record

Method: 7 researchers (web + GitHub), each closing a confirmed critique cluster. Full reports:
`r1_research_{selfpred_class,trustregion_drift,invariance_dr,degeneracy_guard,
corrections,gapmeter,critic_side}.md` (each with full reference lists + verification depth).

### 18.1 Mechanism class (selfpred_class)

- OFENet (arXiv 2003.01629, ICML 2020): predicts next RAW observation (not latent), DenseNet
  expansive features concatenated to raw state. PPO evidence = ONE task (HalfCheetah +39.2%) vs
  5-task SAC/TD3 coverage. No independent replication found. Repos: merlresearch/OFENet, BY571/OFENet.
- Voelcker et al. (arXiv 2406.17718): the strongest available theory for latent self-prediction —
  but proven under linear function approximation + FIXED-POLICY EVALUATION, empirics DQN/TD3 only.
  Latent self-prediction → top-k eigenvectors of P^pi; reconstruction better STANDALONE; self-pred
  stronger as AUXILIARY under distraction, with Prop 7's eigenvalue condition (not automatic).
  Its distraction model is NOT DR — extrapolating to per-episode dynamics variation is ours, not citable.
- On-policy evidence for the whole aux-dynamics class is SPARSE, not negative (PBL/IMPALA closest;
  no PPO/TRPO-scale negative results found either). KIPPO is actually the largest on-policy data point.
- **No published work isolates the linearity constraint** (KIPPO's own ablations vary loss
  components, never swap K for a nonlinear MLP; verified in its PDF). TD-MPC2 (arXiv 2310.16828) is
  existence-proof that UNCONSTRAINED latent-consistency scales (104 tasks) without linearity.
  → The nonlinear-latent control arm is mandatory for any Koopman attribution. Ni et al. survey
  correct ID: arXiv 2401.08898. Unofficial KIPPO reimplementation exists:
  github.com/Bluehorse-hub/KIPPO-PyTorch-Unofficial (unverified; Round-1b inspects it).

### 18.2 Trust-region protocol (trustregion_drift)

- PFO (arXiv 2405.00662): aux loss E[(phi(s)-phi_old(s))^2] on penultimate PRE-ACTIVATIONS, every
  gradient step, coefficient power-of-10-matched to the PPO loss; raises feature rank, reduces clip
  violations. Mechanism is PPO-per-sample-clip-specific; TRPO/NPG explicitly not studied.
  Repo: CLAIRE-Labo/no-representation-no-trust.
- **No published pairing of aux representation learning with TRPO/NPG-family optimizers exists at
  all** (genuine gap, searched hard). Nobody solves stale-old_logp-under-phi-drift.
- Four mitigation options ranked (all unvalidated under hard-KL): (1) freeze phi during rollout +
  TRPO inner loop, step on fixed cadence between iterations (PPG-pattern); (2) EMA/target encoder
  feeding the actor (SPR-pattern, wrong optimizer family); (3) re-anchor old_mu/old_logp/z_old
  after each phi step (weakest precedent, but directly repairs the surrogate-bias defect);
  (4) PFO-style representation penalty added to the objective. Best-supported = hybrid of (1)+(4),
  itself unpublished → any ALBC arm is de facto novel-method territory, not recipe application.
- KIPPO's own update schedule could NOT be extracted this round (no official repo; PDF text layer
  unreadable) → Round-1b image-read in flight.

### 18.3 Invariance vs adaptation under DR (invariance_dr)

- No paper runs the exact strip-the-env-info ablation, but three convergent adjacent results
  support THEO-9's mechanism: CaDM (arXiv 2005.06800) — non-conditioned dynamics model loses 4-7x
  to context-conditioned under randomized dynamics; IB-sim-to-real (arXiv 2305.18464) — compression
  without an env-info-preserving term "almost fails"; IIDA (arXiv 2203.05549) — a CONDITIONED
  dynamics loss spontaneously clusters env identity (implying the unconditioned case lacks the
  retention mechanism). Verdict: plausible + well-supported, not directly proven.
- K(z) has NO exact precedent: MAKO (arXiv 2510.09042) fits per-task discrete operators (not a
  continuous function of an inferred latent); PVKO (arXiv 2309.10278) conditions on KNOWN params;
  PrivilegedDreamer (arXiv 2502.11377) is the closest full match (inferred-context-conditioned
  latent dynamics feeding policy) but non-Koopman and UN-gated (no stop-grad), while WMR
  (arXiv 2502.16230) deliberately CUTS the same gradient — the stop-grad question is literature-
  disputed → A/B it, don't assume. Under the settled rule, z.detach() into any hypernetwork is
  mandatory regardless (systemfit THEO-5: without it the aux loss reaches the p_t encoder — a
  letter violation, plus an ordering-dependent silent-gradient bug vs value_optimizer.zero_grad()).
- Repos: younggyoseo/CaDM (TF1.15, not reusable — reimplement), younggyoseo/trajectory_mcl.

### 18.4 Degeneracy guards (degeneracy_guard)

- Identity-inclusion vs KIPPO-reconstruction are MUTUALLY EXCLUSIVE anti-collapse designs; KIPPO's
  §3.1 rejection (Draeger 1995) targets multi-equilibrium plants = ours. Additionally identity-
  inclusion re-imports the raw state's nonlinearity into the K-fit block (degrades the gradient
  signal even in the regularizer role). Neither design certifies the learned part g' is non-INERT
  (the project's actual decoder-shortcut failure mode) — loss health is not function.
- Adopted proposal: 4-part falsifiable phi_x health gate (analog of the z_sweep rule):
  (1) per-dim variance floor on g' only (VICReg-style, arXiv 2105.04906); (2) effective-rank /
  capacity check on g' (2405.00662 framing); (3) linear probe g' → the 6-7 time-varying p_t channels
  with a degenerate-baseline R^2 floor; (4) PRE-TRAINING closed-form check: fit K = argmin
  ||K z_t - z_{t+1}|| on already-logged teacher z and test distinguishability from I — falsifies the
  student-consistency idea for ~zero cost before any GPU spend.
- Latent-size evidence: no source reports active harm from over-expansion (saturation only);
  both RL-representation precedents (KIPPO, OFENet) run counter to §11.3's "try smaller m first"
  instinct — that line is downgraded to untested-inference.
- Repos: BethanyL/DeepKoopman, intelligent-control-lab/Incremental-Koopman ([50] official).

### 18.5 Corrections batch (corrections)

- SSD/SSSD confirmed real at survey ref [31] (arXiv 1909.01419, streaming variant with fixed
  memory); [131] = Ordonez-Apraez L4DC 2024 (DHA): symmetry-equivariant Koopman via isotypic
  decomposition, validated on Mini-Cheetah (Klein-4 group); relevance to our C2-ish symmetries
  plausible-untested → recorded as NEW LEAD, not a technique.
- LC-SAC recalibrated (5 seeds, 120 runs): quadrotor point-estimates below SAC but within ~1σ;
  cartpole variance σ52→1 IMPROVEMENTS; only reward-shaping variants collapse (−93/94%).
  Standing prohibition NARROWED to: no reward-shaping-based Koopman-Lyapunov terms.
- 2603.03740: 0.21913 s/step (~4.6 Hz) confirmed; no Hz claim in paper; 0.0389/25 Hz confirmed
  absent. Safety-filter compute blocker strengthened.
- KIPPO: pp. 4994-5002 (bibtex-confirmed); MS-thesis provenance real (standard pipeline, not a red
  flag per se); "(one exception)" caveat + seeds note pending Round-1b image-read.
- S-G-W (arXiv 2509.24920): "simulated AND real-world datasets" — but real-world = generic
  dynamical-systems ML benchmarks, no robots, no sim-vs-real. Doc wording fixed; critique's sharper
  point stands.
- Bruder IJRR: NTRS PDF downloads but text-extraction failed a SECOND time → the "strongest
  template" designation still rests on an unread source (Round-1b image-read in flight).

### 18.6 Gap meter (gapmeter)

- Closed-loop identification bias is real and studied (arXiv 2303.15318; 2605.17966: single-policy
  data can leave the control channel unidentifiable in BOTH fits — replay converts a confound into
  a shared identifiability weakness, it does not remove risk). No replay-matched sim-vs-real
  spectral comparison exists anywhere (the idea remains novel — and unvalidated).
- The doc's own Hankel-DMDc "precedent" (arXiv 2502.15782) uses FULL state, not partial obs — it is
  not the precedent §10 implied. Partial-obs (IMU+pressure) delay-embedding EDMD for a comparably
  under-observed marine vehicle: no validating literature found.
- Rate-mismatch has a clean fix (continuous-time renormalization log(mu)/dt, validated in
  2509.24920); ZOH STALENESS does not — it must be matched at the sim-replay stage.
- Decision-relevance: per-axis attribution requires physically-interpretable EDMD modes
  (unvalidated); the DR-support coverage check answers the operative question (is the real plant
  inside the trained envelope) more directly and cheaply, with none of the confounds.
- VERDICT: reclassified priority-1 → GATED/DEFERRED. A defensible protocol exists on paper
  (closed-loop-aware estimator + subspace-restricted delay embedding + CT renormalization +
  fault-matched replay + noise-floor controls incl. K_sim-vs-K_sim across DR draws) but is real
  engineering with unvalidated attribution. Repos: decargroup/closed_loop_koopman, decargroup/pykoop,
  dynamicslab/pykoopman.

### 18.7 Critic-side variant (critic_side)

- SKooP deep-read: critic receives ONE-STEP privileged Koopman prediction; motivation is
  deployment-cost avoidance, NOT a documented actor-side failure (no actor-side ablation exists).
  Decoupled optimizer, PER buffer, no policy gradient into the AE. SKooP-NoPred ablation (lifted
  state instead of prediction) is worse late-stage. Repo: evelyd/SymmetricKoopmanPredictions.
- The crux for us: OUR critic is already privileged (28D p_t + 9D z) — SKooP's was not. Closest
  evidence, "Diminishing Return of Value Expansion Methods" (arXiv 2412.20537): model-derived value
  information gives shrinking gains once the critic already knows the world (even an ORACLE model
  barely helps). FCSRL (arXiv 2405.11718): value-consistency aux on a COST critic underperformed
  (sparse-signal attribution; our IPO costs are dense — transfer unclear either way).
- Code-verified: critic-side input changes live entirely in the Adam-owned value_prefixes group —
  no trust-region contact, no deploy-export contact, no student-distillation contact. Structurally
  the SAFEST Koopman arm, with an honestly SMALL/NULL expected effect. Rank: cheap screening probe,
  null-expected prior.

### 18.8 Round 1 verdict changes (supersedes the listed earlier claims)

| # | Superseded claim (section) | New standing |
|---|---|---|
| 1 | §16.2 "KL bounds representation drift" | WITHDRAWN. Concurrent phi_x under ConstraintTRPO = unsolved novel-method territory; if pursued: freeze-phase cadence + re-anchored old stats + PFO-style penalty, EACH a design decision with cost (§18.2), + `constraint_trpo.py` edit + param-ownership decision (value_prefixes) required |
| 2 | §15.4 #1 "mechanism precedent solid" (actor-side KIPPO arm) | DOWNGRADED: one 4-seed PPO no-DR precedent; arm must be UNBUNDLED (plain phi_x first; bilinear H, K(z), block-partition = separate later ablations); MANDATORY controls: nonlinear-latent predictor arm + (if attribution to expansion is in question) frozen-random-expansion arm; NoEncoder baseline must be TRAINED (does not exist on current plant); invariance-pressure risk (§17.1-4) predicts null-to-negative under DR — record the prediction before launch |
| 3 | §15.4 #2 gap meter "APPLICABLE-NOW" | GATED/DEFERRED (§18.6 protocol + confounds; DR-coverage check is the cheaper, more decision-relevant instrument) |
| 4 | §9/§10 student Koopman-consistency (was priority-1) | REJECTED as Koopman item (K≈I). Salvage path only via §18.4 gate item 4 (pre-check on logged z, ~zero cost): if K distinguishable from I → revisit; else closed. If temporal smoothing of z_hat is independently wanted, propose it AS a smoothness prior with done-masking, GRU-only — different item, honest name |
| 5 | §14.2 identity-inclusion "adopt regardless" | WITHDRAWN (mutually exclusive with KIPPO design; wrong for multi-equilibrium plant per KIPPO's own §3.1). Anti-collapse = expansive AE + reconstruction (KIPPO branch) + the 4-part health gate (§18.4) |
| 6 | §11.2 normalization swap | WITHDRAWN (systemfit THEO-2; if freeze is wanted: `EmpiricalNormalization(until=N)` one-kwarg) |
| 7 | §11.3 "try smaller m first" | DOWNGRADED to untested inference; precedents point larger-is-better up to saturation |
| 8 | §9 ranking 5 LC-SAC blanket prohibition | NARROWED to reward-shaping Koopman-Lyapunov variants |
| 9 | §14.2 "[131] survey citation error" + SSSD attribution | WITHDRAWN; SSSD = [31]; real [131] = DHA (new symmetry lead, untested) |
| 10 | §9 cat 7 "25 Hz on desktop" | CORRECTED to 4.6 Hz — blocker strengthened |
| 11 | §5.2 "information argument (decisive)" | RESTATED narrow (DPI bars added privileged info only; o_t is already a 46-52D delay embedding, so phi_x(o_t) IS a short-history encoder; NoEncoder vs NoEncoder+phi_x is the empirical test) |
| 12 | §13.1 "resolved AGAINST pure affine" + H-term in screening arm | DEMOTED to model-role result; representation-role form choice = later ablation; Lemma 4.5 attribution corrected; open question recorded: no paper evaluates affine-vs-bilinear for a pure representation-shaping loss |

### 18.9 New candidate ranking after Round 1 (supersedes §15.4)

1. **Critic-side Koopman prediction probe (SKooP-adapted)** — structurally safest (code-verified
   zero contact with trust region / deploy / student), null-expected prior stated honestly
   (already-privileged critic + diminishing-returns analog). Cheapest true Koopman arm.
2. **Actor-side phi_x screening arm (KIPPO-adapted), UNBUNDLED + controlled** — only with: (a) the
   §18.2 update protocol decided; (b) nonlinear-latent control arm; (c) 4-part health gate;
   (d) trained NoEncoder baseline; (e) pre-registered invariance-pressure prediction. This is
   novel-method work (TRPO+aux gap), not recipe application — cost accordingly.
3. **Offline pre-analysis (no training risk): K-vs-I check on logged teacher z** (§18.4 item 4) —
   closes/reopens the student-consistency question for free; plus optional offline phi_x+K fit on
   logged rollouts to sanity-check m and loss scales before any arm.
4. **Deployment-observer line (cat 5) unchanged** — medium-term; SSSD ([31]) + DHC guard patterns;
   composes with obs4 channels; export-spec cost noted.
5. **Gap meter — gated/deferred** (§18.6). DR-coverage check first if the sim-fidelity question
   becomes operative.
6. **New leads recorded, no action**: DHA symmetry-structured observables ([131] real content);
   OFENet-style raw-obs prediction as the non-Koopman comparator family; PrivilegedDreamer/WMR for
   the stop-grad A/B if K(z) is ever pursued.

Open items for Round 2: spot-verification of Round-1 researchers' new load-bearing citations
(CaDM 4-7x, 2412.20537, 2605.17966, IIDA, PrivilegedDreamer/WMR); exact p_t time-varying slice
(theory said [19:22]+[25:28]=6, systemfit said 24/28 constant — pin against observations.py);
whether any Round-1 verdict itself overreaches (Round 2 critique).

### 18.10 Round 1b — page-image reads of the two unreadable PDFs (technique: pdftoppm 150dpi + vision)

Both previously-unreadable sources were fully read via page-image rendering. Full reports:
`r1b_{kippo,bruder}_imageread.md` (rendered pages kept alongside).

**KIPPO (22 pp, arXiv 2505.14566) — corrects our own earlier description:**
- **"Decoupled" = stop-gradient only, NOT a separate optimizer.** Algorithm 3 (p.19): ONE joint loss
  `L_KIPPO = L_KI + L_PPO`, one combined backward/step per minibatch per epoch (10 epochs/cycle,
  32 minibatches), single shared Adam (3e-4, LR-annealed, grad-clip 0.5). A stop-grad marker keeps
  PPO gradients out of phi_x ("state representations are optimized independently of the PPO loss",
  App F.3). phi_x therefore DRIFTS DURING the PPO epoch loop — KIPPO has no between-iteration safe
  cadence to borrow; PPO's clip tolerance is the only thing absorbing the drift. §8.1's "trained
  alongside PPO but DECOUPLED from the policy objective" stands, but §18.2's option (1)
  (freeze-phase cadence) has NO KIPPO precedent — every protocol option for ConstraintTRPO is ours.
- Losses: L_KI = 0.75*L_rec + 0.1*L_pred-ls + 0.5*L_pred-ss (Table B.2); horizon sweeps cover only
  H∈{1,3,5,10} while the text claims "8-32 effective" — internal inconsistency in the paper.
- Defaults derive from a 300-config x 4-seed x 6-env = **7,200-model hyperparameter search**
  (App E) — the "cheap screening arm" framing must budget for tuning sensitivity we cannot afford
  to replicate; main results are 4 seeds x 6 envs, ~15h vs ~13h (PPO) on one V100S.
- Variance-reduction caveat verbatim (p.7): "reducing variance by 26.89-91.43% versus PPO (one
  exception)" — the exception is HalfCheetah-v4 (+16.76% variance). vs RPO: two exceptions.
- Actor AND critic consume ONLY y_t = phi_x(x_t) (Alg 1, p.18) — no raw-x concat anywhere; phi_x is
  never frozen; NO input normalization before phi_x is stated in the paper (the unofficial repo's
  clamp(state,-10,10) is its own addition). Identity-concat rejection quote confirmed, located in
  App G (not §3.1 as earlier recorded).
- Unofficial repo (Bluehorse-hub/KIPPO-PyTorch-Unofficial) STRUCTURALLY DIVERGES from Algorithm 3
  (two separate Adams, sequential 10-epoch Koopman-then-PPO passes, no shared clip/anneal) —
  disqualified as an implementation reference; loss weights match, nothing else verified.

**Bruder IJRR 2025 (17 pp, NTRS copy) — resolves §15.2's open item, and corrects the R1 critique itself:**
- The R1 evidence-critique's claim that the abstract contains "<10% of the data" and "real-time
  recursive Koopman model updates" is NOT in the published text — neither phrase/number appears
  anywhere (search-snippet contamination inside the critique; the critique's process point about
  unread sources stands, its content was wrong). All identification is OFFLINE batch least squares;
  online refinement is explicitly future work.
- §15.2's white-space claim "no real-data sample-efficiency curve exists for the sim-Koopman +
  real-residual recipe" is now CONFIRMED TRUE by direct reading: efficiency curves exist only for
  simulated toys (Figs. 4-5); the real arm uses one fixed dataset (K=30000), no sweep.
- "Strongest template" NARROWED: the prior is an ANALYTICAL ODE algebraically projected onto a
  Hermite basis (matrix-exponentiated) — never a simulator. The transferable mechanism is:
  K_residual := K_EDMD - K_physics, combined additively in lifted space as K_p + gamma*K_r with
  scalar gamma in [0,1] fit on held-out data. Hardware (3-segment soft arm, mocap): prediction RMSE
  0.07 m (combined) vs 0.14 (physics) vs 0.21 (data-only); tracking 67-73 mm vs 167-192 mm
  (physics); PURE DATA-DRIVEN MPC FAILED OUTRIGHT (zero control output) — negative evidence for
  pure-data recipes, positive for physics-prior + residual. No controlled generalization study.

## 19. ROUND 2 — critique of Round-1 outputs (record)

Method: 3 adversarial reviewers over the Round-1-updated doc + all Round-1 reports: citation
spot-check (citecheck), synthesis attack (synthattack), completeness-vs-owner's-bar (completeness).
Full reports: `r2_critique_{citecheck,synthattack,completeness}.md`.
Round 1's own failure mode (search-snippet contamination) RECURRED inside Round 1: five load-bearing
R1 characterizations failed primary-source checks, one R1 reference carries a fabricated author name
("T. M. Dawson" on arXiv 2303.15318 — real authors Dahdah & Forbes), and one report cited a sibling
R1 artifact as a source. All arXiv IDs (including 2605.17966, flagged possibly-fabricated in R1)
resolve to real papers; zero hallucinated identifiers across the whole investigation.

### 19.1 Citation spot-check results (citecheck)

FAILED against primary text (doc corrected accordingly):
- CaDM "4-7x": cross-family comparison (Vanilla MLP vs PE-TS ensemble + CaDM). Matched ablations:
  1.1-3.5x, median ~1.5x, metric = MPC return on held-out dynamics (Table 1 pairs verified).
- IB-sim-to-real "compression without preservation almost fails": ablation misread — HIB-w/o-ib
  removes the ENTIRE IB objective (it is the plain-RNN baseline). Paper supports "explicit
  privileged-alignment helps", not "compression pressure damages adaptation".
- CaDM context-encoder "not isolated from policy": REVERSED — Alg 1 L20 trains the encoder by
  prediction loss only, and the official PPO arm feeds context as a NumPy array from a pretrained
  frozen model (stronger than stop-grad). CaDM is precedent FOR gating.
- PrivilegedDreamer "un-gated": most likely wrong (R1 depth was abstract-only) — estimator/HIP head
  are world-model components under L(phi) (no return term); actor/critic train against a FIXED world
  model. WMR's "gradient intentionally cut off" verbatim-confirmed AND ablation-backed (cutoff
  necessary). => The "stop-grad is literature-disputed" framing DISSOLVES: all three checked
  precedents gate the context/estimation path. Combined with the settled rule (z.detach()
  mandatory), the K(z)/context gating question is CLOSED: gate it.
- OFENet "PPO on ONE task": contradicted — Table 1 has PPO on all five tasks, PPO(OFE) wins 5/5
  (Hopper +44.0%, HalfCheetah +39.2%, others +1.8/+6.2/+2.7% = within seed noise). Correction cuts
  IN FAVOR of the actor-side arm; recorded per symmetric skepticism.

SCOPED/CALIBRATED:
- Moalla/PFO leg of §17.1-1: mechanism verified exactly, but the demonstrated breakdown is
  PPO-Clip's per-sample heuristic ("heuristic trust region"); hard batch-KL + line search is not
  studied (grep TRPO/NPG = 0). Legs (i) math and (ii) code stand on their own; "triple-confirmed"
  reduced to double + one adjacent-mechanism warning.
- arXiv 2605.17966 UPGRADED snippet→confirmed, and its remedy matters for §18.6: the control-channel
  identifiability certificate vanishes only under DETERMINISTIC feedback; information grows
  quadratically with dither amplitude — a stochastic-policy rollout provides natural dither. Gap-
  meter replay protocol should record this as its identifiability escape hatch.
- SGOT rate-renormalization: real, but demonstrated on one synthetic linear system over a 1.5x rate
  span; GOT equally robust. "Validated across sample rates" downgraded to "demonstrated in principle".
- 2412.20537 (diminishing returns): quote OK; causal transfer to "one-step prediction appended to a
  privileged critic's input" is the doc's analogy, not the paper's claim (its lever is multi-step
  TD-target construction). Keep as directional prior only.
- FCSRL: "underperformed" misplaced — VC is one of the paper's STRONGER baselines; supportable
  statement: "cost-value-consistency is workable but comparatively weak", a weaker null argument.
- SSD/SSSD in 1909.01419: confirmed incl. fixed memory + Thm 6.3 equivalence (depth caveat cleared).
- IIDA / TD-MPC2 / Voelcker characterizations: verified OK with scope notes (IIDA = supervised
  offline predictor, object-identity latent; TD-MPC2 latent feeds MPPI planning — weaker analogy).
- Remaining snippet-depth items carrying §18.2's recommended options: PPG (2009.04416) and SPR
  (2007.05929) — Round-3 verification required before the update-protocol options are citable.

### 19.2 Synthesis attack results (synthattack) — accepted findings

- S1 (critical): §18.9 #1 (critic-side probe) demoted. A null-expected arm at single-seed screening
  cannot distinguish null from underpowered (uninformative in both branches); it is NOT the cheapest
  build (full phi_x+K+B+decoder+aux-loop still required — only the trust-region protocol is saved);
  and it silently dropped the unconstrained-latent control its own source report mandates.
- S2 (critical): the ranking lacked its best rung — **frozen pre-trained phi_x**: pretrain offline
  on logged/excitation sim rollouts (§16.2 Stage 0, never withdrawn), FREEZE, train ConstraintTRPO
  on the frozen lift. Zero trust-region contact, no aux loss during RL (input change under the
  codebase's own rule axis), no constraint_trpo.py edit, no param-ownership question, single-variable.
  Round-3 question: does any published work use a frozen pretrained lifting as RL policy input?
- S3 (major): p_t time-variance PINNED BY CODE (main-context grep confirmed synthattack, corrected
  both R1 lenses AND R2-completeness): `ou_enable: bool = False` (config.py:556, both variants),
  `payload_toggle_steps: int = 0`, and NO `ou_enable=True` override exists anywhere in the repo →
  ocean current p_t[19:22] is CONSTANT per episode as shipped; the only within-episode time-varying
  dims are p_t[25:28] measured body lin-vel (3 of 28; water density p_t[18] constant; 34D fault
  variant adds 6 more constants). K≈I argument strengthened; §18.4 gate item 3's probe target must
  be redesigned (the 3 varying dims are policy-driven state, not parameters).
- S4 (major): "unbundle the arm" is scoped: unbundle ARCHITECTURE add-ons (bilinear H, K(z)), keep
  the LOSS TRIPLE intact — KIPPO's own Fig D.1/D.2 + App E.3 show subsets are the negative cells
  (rec+pred-ls without state-space prediction negative on ~4/6 envs; omega_3<0.25 loses the benefit).
- S5 (major): THEO-9 must acknowledge the 0.75-weighted reconstruction term as a counter-pressure
  (approximately injective expansive AE cannot DESTROY theta-signal, only re-weight it), and that on
  the teacher the actor keeps z regardless — "strips exactly the env information" softened to a
  re-weighting risk, pre-registered prediction retained in weakened form.
- S6 (major): identity-inclusion withdrawal was an over-correction — KIPPO's App-G objection is an
  exact-realizability argument, the same class §18.8 row 12 rules out for the representation role.
  REOPENED as undecided-but-disfavored; the surviving argument against it is §18.4's (identity block
  re-imports raw-state nonlinearity into the K-fit block), vs two working practices ([50],[86]).
- S7 (major): §6's physics-informed feature arm (sin/cos, omega|omega|, ~+6-8 dims) was ORPHANED,
  never rejected. RESTORED to the candidate list: cheapest possible arm, rule-compliant, and the
  natural low-anchor control for the whole program.
- S8 (major): proposal-level verdicts must be stated in one place (done in §21 of the final doc).
- S9 (major): KIPPO per-env curves (Fig C.1, page-image read): behind PPO for most of training on
  Walker2d + BipedalWalker ("surpasses the baseline towards the end"); +6-60% is an end-of-training
  aggregate. A 2000-iter screen sits in the regime where KIPPO LOSES on 2/6 envs — screening-length
  risk recorded for any actor-side arm.
- S11 (minor): LC-SAC final wording: "no evidence of benefit on the closest analog; clear harm for
  the reward-shaping variant; not a supported direction absent a mechanism argument."
- S12 (minor): supersession table additions: §11.6 (gap meter as endorsed plan) and §15.2 ("<10%
  data" / "recursive updates" characterizations) are superseded by §18.6/§18.10. r1b page
  attributions corrected (7,200-model sentence = PDF p.11/App E).

### 19.3 Completeness results — accepted findings + two NEW leads

- C-2 (critical, EMPIRICAL CLOSURE): the K-vs-I pre-check was specified AND RUN during review on
  logged student-eval z (the only place teacher z exists on disk — eval.py student-mode
  latent_*.npz; there is no teacher-training z log): fitted K is NOT distinguishable from I at any
  stride or DR level (split-half refit spread exceeds ||K-I|| everywhere). The student
  Koopman-consistency line is EMPIRICALLY DEAD at zero GPU cost. (§18.8 row 4 salvage path: closed.)
- C-3/C-4 (major): the critic-side probe's "zero structural contact" is CONDITIONAL — name-prefix
  param grouping, evaluate()/evaluate_costs() take obs only (no action argument → SKooP's
  a_t-conditioned prediction needs an API change at 3+ call sites), critic obs are recomputed (not
  stored) so added channels change num_critic_obs → normalizer geometry + _init_base assertions;
  and NO Koopman aux loss can ride the existing value loop — `_update_values` shuffles
  torch.randperm over the flattened (T*E) batch, destroying temporal adjacency; a pair-preserving
  sampler over unflattened storage with dones-masking (+ last-step bootstrap gap) must be built
  inside update() before storage.clear().
- C-5 (major): launch-grade decision rules (thresholds, budgets, branch/tag, wandb group, plant sha)
  are ABSENT — deliberately: the user excluded experiment planning from this stage. Recorded as the
  first task of the NEXT stage (exp-design), not of this doc.
- C-6 (major, NEW LEAD): a 2026 Ocean Engineering paper (Ocean Eng. 348, art. 123965) appears to do
  Koopman-observer-based actuator fault detection/isolation + controller reconfiguration on an
  8-thruster underwater vehicle with injected faults — would narrow the doc's most-repeated blocker
  (single-K under fault-scale regime change) on our exact platform class. Snippet-depth only
  (ScienceDirect 403) → Round-3 verification, could flip a standing verdict.
- C-7 (major, NEW FRAMING): a Koopman-linear recurrent student IS a deep SSM (S4/S5/Mamba class) —
  that literature already answers stability parameterization, initialization, and training questions
  the doc treats as open; MamKO (Mamba-generated time-varying Koopman operator) is structurally the
  K(z) idea with a mature architecture. Snippet-depth → Round-3 verification. Dominates §18.9-2 on
  every risk axis the doc uses (no aux loss, no trust-region contact, rides the observability retrain).
- C-8 (major): §6's SIM-vs-SIM offline spectral diagnostic (compare EDMD spectra across DR arms on
  logged sim rollouts) was dropped by attrition — none of the gap-meter defeaters (partial obs, ZOH,
  closed-loop sim-vs-real mismatch) applies sim-vs-sim. RESTORED as the cheapest zero-risk lane
  (C-2 is a live instance of exactly this pattern producing a decision-grade result in minutes).
- C-9 (minor): plant symmetry CODE-CHECKED: the 6-thruster allocation matrix is exactly
  C2-equivariant under port-starboard reflection with thruster permutation (12)(34)(56); the planar
  2-link arm preserves it; per-episode DR draws break it per-realization but preserve it in
  distribution. DHA lead gated behind a cheap offline C2-equivariance probe on existing eval logs.
- C-1/C-10/C-11 (hygiene, accepted for the final deliverable): move the evidentiary base out of
  ephemeral job-tmp into a durable store next to the final doc; state verification depth per
  reference IN the final doc; annotate superseded Part-I claims in place; dedup the control-arm
  items (§18.1 nonlinear-latent control == §18.9-6 OFENet comparator); rank arms against the
  non-Koopman comparator delivering the same mechanism, not only against other Koopman arms.

### 19.4 Round 2 verdict changes (supersedes the listed items)

| # | Superseded claim | New standing |
|---|---|---|
| 1 | §18.3/§17.1-4 THEO-9 "well-supported" | Hypothesis with ONE adjacent supporting result (IIDA, scope-noted) + an unmodeled counter-pressure (0.75 recon term). Pre-registered prediction kept in weakened "re-weighting risk" form |
| 2 | §18.3 "stop-grad literature-disputed → A/B it" | RESOLVED: gate the context path (CaDM frozen-numpy, PrivilegedDreamer fixed-WM, WMR ablation-backed cutoff — all three gate; settled rule requires z.detach() anyway) |
| 3 | §18.9 #1 critic-side probe | DEMOTED: conditional safety (C-3), needs its own control arm, null-expected AND uninformative at screening convention. Stays on the list only with an informative-outcome redesign |
| 4 | §18.8 row 4 salvage path (K-vs-I pre-check) | EXECUTED — K ≈ I confirmed on logged z. Student Koopman-consistency CLOSED EMPIRICALLY |
| 5 | §17.1-3/§18.4 "6-7 time-varying p_t dims" | 3 of 28 ([25:28] measured lin-vel only; ou_enable=False shipped, no override in repo; [19:22] varies ONLY if OU enabled) |
| 6 | §17.1-1 "triple-confirmed" | Legs (i) math + (ii) code confirmed; leg (iii) literature scoped to PPO-Clip (adjacent warning, not proof for hard-KL) |
| 7 | §18.1 OFENet "PPO = one task" | PPO on 5/5 tasks, wins 5/5 (2 large, 3 within noise) — on-policy evidence better than R1 stated |
| 8 | §18.8 row 5 identity-inclusion "withdrawn" | REOPENED undecided-disfavored (KIPPO's objection is exact-realizability class; surviving argument = §18.4 nonlinearity re-import; [50]/[86] working practice on the other side) |
| 9 | §18.8 row 8 LC-SAC narrowed prohibition | Final wording per S11 (not-supported-absent-mechanism, harm proven only for reward-shaping) |
| 10 | §18.9 ranking as a whole | REBUILT in §21 (final doc): offline zero-risk analyses first; frozen-phi_x middle rung added; physics-feature arm restored; every arm paired with its non-Koopman control |
| 11 | §18.8 supersession table | += §11.6 (gap-meter plan), §15.2 (Bruder mischaracterizations) |

Round-3 residue (small, targeted): (R3-1) verify Ocean Eng 123965 fault-tolerant Koopman; (R3-2)
verify MamKO + SSM-student framing; (R3-3) frozen-pretrained-lifting-as-RL-input precedent; (R3-4)
aux dynamics features on an already-privileged critic + PPG/SPR full verification; (R3-5)
reconstruction-as-context-preservation evidence. Everything else = specification/consolidation work.

## 20. ROUND 3 — final targeted verification (record) + EARLY-STOP decision

Five narrow researchers closed the Round-2 residue. Full reports:
`r3_research_{fault_koopman,ssm_student,frozen_lift,priv_critic_ppg_spr,recon_context}.md`.

1. **Ocean Eng fault paper (fault_koopman)**: EXISTS — Akumalla, Kadiyam, Jain (IIT Mandi), "Actuator
   fault-tolerant control of underwater vehicle using koopman framework", Ocean Engineering 348
   (2026) 123965 [abstract depth only; ScienceDirect blocked all full-text routes]. It SIDESTEPS our
   single-K blocker rather than refuting it: a single K fit on NOMINAL dynamics only generates FDI
   residuals for unknown-fault detection/isolation; fault COMPENSATION is a separately reconfigured
   backstepping controller. The blocker stands for model/policy roles; the paper contributes a
   structural precedent (nominal-K-for-detection + separate compensator) that maps directly onto our
   deployment-observer line, on our exact platform class (8-thruster UV).
2. **SSM student (ssm_student)**: MamKO confirmed real (ICLR 2025): Mamba generates a time-varying
   Koopman triple per step (diagonal A, negative-CELU stabilized, ZOH-discretized) for MPC — the
   K(z)-with-mature-architecture precedent (MPC-side, not RL). S5-for-RL (Lu et al., NeurIPS 2023,
   arXiv 2303.03982, full-text): HiPPO init, ZOH discretization, parallel scan, and RL episode
   RESETS are all solved ("Resettable S5" with proof); S5 beats GRU ~6x faster on memory tasks.
   REAL (arXiv 2603.17653, full-text): Mamba student in privileged distillation at a 10-frame
   window (our scale), large ablation win vs no-Mamba, chosen over Transformer for latency — but NO
   GRU/TCN student baseline anywhere in the literature: a GRU-vs-SSM student head-to-head at ALBC
   scale would be ORIGINAL EVIDENCE, not replication. Counter-evidence: Mamba causal-conv asymmetry
   bias (arXiv 2509.17514, snippet). => the "Koopman-linear recurrent student" question is best
   pursued AS an SSM-student question, riding the observability retrain.
3. **Frozen lift (frozen_lift)**: the frozen-pretrained-phi_x arm is SEMI-NOVEL as a combination; each
   piece precedented separately (ATC pretrain+freeze [visual analogy]; DeepKoopman offline AE fit on
   logged trajectories; RMA phase-2 freezing). The staleness failure mode is REAL and published:
   A-RMA's third phase exists precisely because frozen phase-1 components degrade against the
   consuming module's actual distribution — the arm's health gate must monitor late-policy
   reconstruction/prediction error drift. Identifiability cluster (arXiv 2605.09545, 2511.03734,
   2605.17966): offline fits are well-identified only along directions the logging policy excited —
   scripted-excitation data in the pretrain corpus is load-bearing, not optional.
4. **Privileged critic + protocol sources (priv_critic_ppg_spr)**: IAAC (arXiv 2509.26000, ICML 2026,
   full-text) is direct-but-narrow evidence that stacking MORE privileged signal onto an
   already-informed critic has no guaranteed marginal value and can HURT (Table 6: full-state signal
   underperforms no-signal on one env; "does not always yield the highest performance"). This
   further supports the critic-side demotion. PPG full-verified: alternating N_pi policy phases + 1
   aux phase, L_joint = L_aux + beta_clone*KL[pi_old, pi] (KL-to-frozen-policy, not literal BC);
   "infrequent auxiliary phases are critical to success". SPR full-verified: target/stop-gradient is
   VITAL (0.415 -> 0.278 without), tau sweep peaks at tau=0 WITH augmentation (stop-grad alone
   suffices when data diversity is high — relevant: 4096-env DR is high-diversity). Both remain
   PPO/off-policy; the TRPO gap stands.
5. **Reconstruction-as-context-preservation (recon_context)**: NEGATIVE-to-fragile. Theory
   (reconstruction -> top singular vectors = variance-driven selection) + direct probe study
   (arXiv 2607.27017: recon- AND prediction-trained latents both fail to encode a low-variance drag
   parameter, R^2 ~ 0.12-0.13 vs 0.89 raw-data ceiling) + PrivilegedDreamer's own motivation/ablation
   (vanilla reconstruction-only RSSM is the WORST at hidden-parameter recovery; explicit estimation
   head required). => S5's "0.75 recon counter-pressure protects theta" is NOT supported. Net effect
   on the actor-side arm: phi_x will likely encode theta poorly REGARDLESS of the invariance-pressure
   question — which simultaneously (a) removes the "better implicit system identification" upside
   story, and (b) softens the catastrophic-stripping downside (the explicit theta channel z exists
   separately and bypasses phi_x by design). The arm's honest hypothesis is optimization-geometry
   only, exactly what KIPPO claims and nothing more.

**EARLY-STOP DECISION**: iterate loop ends at 3 rounds (user allowed <=4). Grounds: Round-2's three
lenses each declared their axis converged except the five targeted questions above, all five now
answered; no remaining open item is closable by further literature research — the residue is either
specification work (owner-bar) or experiments (known-unknowns register). Final deliverable:
`constrained-albc/docs/reference/koopman-rl-research.md` (+ evidence reports copied alongside),
verified by an independent review pass before commit.
