---
title: "bias reward (bias_ema_penalty) theory review: conditionally sound; hidden-state-dependent non-Markov reward is the key flaw (expose _bias_ema as obs), squared form does not fill dead-zone, penalty is 175x smaller than tracking loss"
tags: ["albc", "envs-main", "reward", "bias-ema", "steady-state-error", "integral-action", "non-markovian", "pbrs", "observation-augmentation", "theory-review", "heavy-tail", "experiment-lead"]
created: 2026-07-11T06:52:57.946013
updated: 2026-07-16T06:36:48.834468
sources: []
links: ["leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r.md", "reward_penalty_terms_thruster_smoothness_bias_block_3_temporal_b.md", "yaw_command_is_rate_not_angle_inherited_design_defensible_only_i.md", "literature_map_how_rl_control_actually_handles_steady_state_erro.md"]
category: decision
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# bias reward (bias_ema_penalty) theory review: conditionally sound; hidden-state-dependent non-Markov reward is the key flaw (expose _bias_ema as obs), squared form does not fill dead-zone, penalty is 175x smaller than tracking loss

Theoretical review of the `bias` reward term (`bias_ema_penalty`, envs/main, `Isaac-ConstrainedALBC-TRPO-v0`). Code-verified 2026-07-11, independently checked (verifier PASS: code citations, quant recompute, literature grades, argument logic all reproduced). Full report: `/workspace/.sp/plans/REVIEW_bias_reward_theory.md`. This is a THEORY/LITERATURE review, not a run analysis — no training data, no code change.

WHAT THE TERM IS (code fact): `r_bias = sum_i w_i * bias_ema_i^2` (`rewards.py:173-181`), where `_bias_ema` is an UNGATED EMA of [roll_err(rad), pitch_err(rad), yaw_RATE_err(rad/s)] updated every step `bias_ema = a*bias_ema + (1-a)*err3`, a=0.99 (`albc_env.py:1131-1143`). Shipped `k_bias=-2.0` (`config.py:453`); `bias_ema_alpha=0.99`, `bias_weights=(1.5,1,1)` are rewards.py defaults (no override). tau = -dt/ln(a) = 1.99 s (~100 step window). A single guard `if k_bias != 0` toggles both the reward weight AND the EMA-update loop across two files.

VERDICT: CONDITIONALLY SOUND. It is a legitimate, intended reward-shaping approximation of integral action (the wiki already frames it as "EMA in env state lets a Markov reward express a non-Markov objective", same trick as cumulative_yaw). But it carries THREE structural tensions, none a bug — each a known-ceiling trade-off:

1. HIDDEN-STATE-DEPENDENT REWARD (most important). The reward depends on `_bias_ema`, which is ABSENT from both policy obs (69D) and privileged obs (28D) — verified by reading the full bodies of `compute_policy_obs`/`compute_privileged_obs`; `bias_ema` string appears nowhere in `mdp/observations.py` (only `_error_integral` is cat'd into obs). So the reward is Markov only in an augmented state the policy/critic cannot see -> to the policy it looks partially-observed / non-stationary, adding critic-regression noise and blurring credit assignment. The RL literature is consistent that a non-Markovian reward needs its history-summary state augmented into the OBSERVABLE MDP state for standard convergence guarantees (reward machines Toro Icarte arXiv:2010.03950; Gaon&Brafman AAAI 2020; PBRS invariance Ng-Harada-Russell 1999; the standard RL integral-action pattern is OBSERVATION augmentation, IASA arXiv:2201.13331 — not reward-only). This term meets that requirement only HALF-way (reward knows the non-Markov goal, policy does not observe its state variable). Contrast: `_error_integral` IS exposed as an obs channel; `_bias_ema` is not — an asymmetry with no documented rationale.

2. SQUARED FORM DOES NOT FILL THE DEAD-ZONE. Gradient d(w*ema^2)/d(ema) = 2*w*ema -> 0 as ema->0, so `ema^2` vanishes near zero exactly like the exp+quad kernel's "SS-error dead zone" (reward.md 2.2). The bias term catches LARGE sustained offsets (heavy-tail envs), NOT the dead-zone. A LINEAR form `w*|ema|` would have a finite near-zero gradient and would fill it; the squared choice is justified only by "hit big offsets hard, small ones weakly" (heavy-tail targeting), NOT by dead-zone mitigation.

3. QUANT: term is negligible vs tracking reward, NOT overpowering. At a sustained 5deg roll bias the bias-penalty contribution is 4.6e-4/step vs the att_rp reward LOSS of 8.0e-2/step from that same offset — ~175x smaller (att_rp @ zero-err = 0.18/step). At 1deg the bias contribution (1.8e-5/step) is effectively gone. So most of the offset-removal pressure still comes from the att_rp exp kernel. If the r11_emabias "strongest single intervention across 24 runs" provenance comment (config.py:448-452, INDEPENDENTLY UNVERIFIABLE, provenance only) is true, its effect is STRUCTURAL (a persistence filter targeting the direction-aligned offset of heavy-tail envs), not magnitude.

Secondary: DIMENSIONAL MISMATCH (C-6) — rad^2 (roll/pitch) and (rad/s)^2 (yaw-rate) are summed in one weighted sum, so `bias_weights` implicitly carries a unit conversion and tuning loses physical meaning. The yaw rate-bias PENALTY intent is itself defensible (sustained yaw-rate offset = heading drift), just not to be mixed with the angle terms. CARRY-OVER (A-2) — command resamples every 250 steps (`vel_cmd_resample_steps=250`) but `_bias_ema` is NOT reset at resample (only at env reset, `:1555`), so ~2s of old-command error residue carries into the new command; real but harm-unproven, self-correcting < the 250-step segment (see [[leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r]]). "EMA = integral action" is imprecise: EMA has FINITE DC gain (H(1)=1), so by the internal model principle it SUPPRESSES steady-state error but cannot force it to zero the way an infinite-gain integrator does — docstrings saying "eliminate/kill sustained offset" overstate; "penalize/suppress" is accurate.

RECOMMENDATIONS (proposals only, no code changed; all A/B-gated, harm/gain unproven by reasoning alone): R1 expose `_bias_ema` as an obs channel (like `_error_integral`) — most fundamental, needs from-scratch retrain, HIGH value. R3 reset `_bias_ema` at command resample — ALREADY designed with `_error_integral` (see carry-over card). R2 gate the EMA (|err|<sigma) or add a clamp — MEDIUM. R4 fix docstrings "eliminate"->"suppress" — doc-only. R5 squared->linear — CAUTION (linear was disabled for causing a dead-zone per reward.md 2.2; squared may be right for heavy-tail targeting; no A/B, not a recommendation). R6 separate yaw coefficient / document the dimensional mix. Priority R1 > R3 ~= R2 > R4/R6 > R5.

Literature grades (opened-source-only): [primary] EMA finite DC gain (Wikipedia exp-smoothing), IASA arXiv:2201.13331, reward machines arXiv:2010.03950, Gaon&Brafman AAAI 2020, arXiv:2410.12197 (non-Markov shaping can change optimal-policy set). [secondary, PDF unopened] Ng-Harada-Russell 1999, Fossen 2021 marine handbook (integral action is the marine-control standard for persistent-disturbance SS error), internal model principle. UNCONFIRMED: Hwangbo 2019 leaky-integrator precedent (paper real, arXiv:1901.08652, but the "leaky integrator observation" claim not found — honestly left unconfirmed). Related: [[reward_penalty_terms_thruster_smoothness_bias_block_3_temporal_b]] (mechanism), [[yaw_command_is_rate_not_angle_inherited_design_defensible_only_i]] (yaw-rate semantics).

---

## Update (2026-07-16T06:36:48.834468)

## Update (2026-07-16): Hwangbo precedent REFUTED by primary sources; 3 of this page's terms are not field terminology

Cross-domain literature research (5 parallel document-specialist agents, primary PDFs fetched and
quoted). This page's open items are now settled, and two of its own claims need correcting.

### 1. The "Hwangbo leaky-integrator precedent" is REFUTED, not merely unconfirmed

This page recorded: "UNCONFIRMED: Hwangbo 2019 leaky-integrator precedent (paper real, arXiv:1901.08652,
but the 'leaky integrator observation' claim not found -- honestly left unconfirmed)". Both papers have
now been read in full (20/20 and 8/8 pages, plus `pdftotext | grep` for integrat|leaky|accumulat).

[FINDING] Hwangbo et al. 2019 (Science Robotics, arXiv:1901.08652) does NOT use a leaky integrator
observation. Its observation is `o_k = <phi^g, r_z, v, omega, phi, phi_dot, Theta, a_{k-1}, C>` where
Theta is a SPARSELY SAMPLED FINITE HISTORY, quote: "The joint state history was sampled at t = t_k to
t = t_k - 0.02 s" -- a 20 ms stacked-frame history, not a first-order IIR recursion. "leaky" appears
ZERO times in the paper; the single "integrat*" hit is about discounted return ("integrated value over
time"), not an observation.
[EVIDENCE: arXiv:1901.08652 p.9 "Observation and action" section, quoted; full-text grep across 20 pages]
[CONFIDENCE: HIGH]

[FINDING] Hwangbo et al. 2017 (RA-L, arXiv:1707.05110) does NOT use an integral-error observation. Its
state is 18D, quote: "We used nine elements of the rotation matrix R_b to represent the rotation and the
rest of the states are trivially represented by position, linear velocity and angular velocity... we have
a 18-dimensional state vector". Its cost (Eq. 9) is instantaneous weighted norms with no accumulated
term. Full-text grep for "integral error"/"integrator"/"leaky"/"accumulat" -> zero relevant hits.
[EVIDENCE: arXiv:1707.05110 Sec. III-A quoted; Fig. 2 network input blocks 9+3+3+3=18D; Eq. 9]
[CONFIDENCE: HIGH]

CONSEQUENCE: `config.py`'s comment "Integral error observation (Hwangbo 2017 pattern, validated in R7/R8
experiments)" MIS-ATTRIBUTES the technique. The "validated in R7/R8" internal claim may still hold; the
paper citation backing it does not. Two other candidate origins were checked and excluded by full-text
grep: Molchanov "Sim-to-(Multi)-Real" (arXiv:1903.04628) and Koch "RL for UAV Attitude Control"
(arXiv:1804.04154).

TRUE closest precedent (verified, same recurrence + same domain family): Bohn, Coates, Reinhardt,
Johansen, "Data-Efficient Deep RL for Attitude Control of Fixed-Wing UAVs: Field Experiments", 2021,
arXiv:2111.04153 -- Eq.(7) `I_t = gamma^I * I_{t-1} + e_t, gamma^I = 0.99`, i.e. OUR recurrence, on
fixed-wing attitude control. Also relevant: Weber/Schenke/Wallscheid IASA, arXiv:2201.13331 (integral on
the ACTOR OUTPUT, inspired by MPC delta-input, not PID). WHO actually originated integral-as-observation
in RL remains an OPEN question -- it may simply be uncredited borrowing from classical PID with no RL
paper behind it. Do not fill this with a guess.

### 2. Three terms this page uses do NOT exist in the literature

[FINDING] "critic-regression noise", "blurred credit assignment", and "non-stationary (from the policy's
view)" are NOT field terminology for this hazard. Full-text search across the four core papers
(arXiv:2010.03950 reward machines; Gaon & Brafman AAAI-20; arXiv:2410.12197; arXiv:2201.13331) returned
ZERO hits for "non-stationar*" and "credit assign*". They are plausible informal restatements; this page
should not present them as literature claims.
[EVIDENCE: agent full-text grep across all four papers]
[CONFIDENCE: HIGH]

What IS literature-backed for the same hazard:
- The framing: reward is non-Markovian w.r.t. the observed state, Markovian w.r.t. the augmented state.
  Toro Icarte et al. arXiv:2010.03950 Observation 1: "the rewards the agent gets may be non-Markovian
  relative to the environment (the states of S), though they are Markovian relative to the elements in
  S x U... the agent should consider not just the current environment state s_t but also the current RM
  state u_t". Gaon & Brafman AAAI-20 independently: "A basic premise of MDPs is that the rewards depend
  on the last state and action only. Yet, many real-world rewards are non-Markovian."
- The empirical damage (vanilla = no augmentation, i.e. our pre-P-B1 setup), Gaon & Brafman: "vanilla
  Q-learning is very noisy and fails to converge"; "Vanilla is still noisy and converges to a sub-optimal
  policy after 25M steps with very high STD."
- The closest FORMAL mechanism, Baisero & Amato, AAMAS 2022, arXiv:2105.11674, Thm 4.1: "In partially
  observable control problems, a time-invariant state value function V^pi(s) is generally ill-defined."
  CAVEAT: proven for ASYMMETRIC actor-critic (privileged critic + partial-obs policy), NOT our
  symmetric-omission case -- mechanism-level grounding only, not a proof of our scenario.

### 3. R1 is now theory-backed, and P-B1 closed a formal hazard (not just a tracking gain)

[FINDING] R1 (expose _bias_ema as obs) is the TEXTBOOK prescription, and our case is its easiest
instance. Gaon & Brafman: "We can address non-Markovian rewards (NMRs) by augmenting the state with
information that makes the new model Markovian. Except for pathological cases, this is always possible."
Reward machines / automata-learning are NOT our tool -- they exist to DISCOVER an unknown non-Markov
structure from experience, while `_bias_ema` is already computed by the env. "Just put it in the
observation" is the correctly-scoped fix.
[CONFIDENCE: HIGH]

[FINDING] `r_bias = sum_i w_i * bias_ema_i^2` is NOT a potential difference, so by Ng-Harada-Russell
1999's Necessity Theorem (generalized to history-dependent potentials by Forbes et al. 2024,
arXiv:2410.12197) it is NOT guaranteed to preserve the optimal policy set. P-B1
(`use_bias_ema_obs=True`, 2026-07-16) removes this hazard entirely: once bias_ema is observed, r_bias is
Markov w.r.t. the augmented observed state and no potential-shaping argument is needed. Code-verified
that this covers the CRITIC too: `num_critic_obs = policy_obs_dim + privileged_dim`
(actor_critic_encoder.py:105-107), so the critic consumes o_t -- which P-B1 extended 69->72D. So P-B1
was correct for a deeper reason than its measured tracking gain.
[EVIDENCE: NHR99 Necessity Theorem: "If F is not potential-based, then there is an MDP M such that no
optimal policy in M is also optimal in M with F."; arXiv:2410.12197 Thm 1 + MiniGrid counterexample,
abstract: "These methods can often inadvertently change the set of optimal policies"; code
actor_critic_encoder.py:105-107, albc_env.py:1129]
[CONFIDENCE: HIGH]
SCOPE CAVEAT: NHR99/Forbes formally analyse an ADDED shaping term on a base reward; r_bias is a
base-reward component. The math does not require F to be "extra", but this application is our extension.

### 4. This page's quant claim (175x) is CONFIRMED as decisive -- and the fix is form, not weight

[FINDING] The math settles "is k_bias too small to matter": for `w*ema^2` the gradient is `2*w*ema`.
Scaling w scales the slope at any fixed ema but does NOT change the order of vanishing as ema->0. So
raising k_bias CANNOT fix a structurally vanishing gradient -- this page's "magnitude is not the
mechanism; structure is" and its R1 > R2 priority are mathematically correct.
[CONFIDENCE: HIGH]

[FINDING] R5 (squared -> linear), which this page marked CAUTION/not-a-recommendation, now HAS
literature evidence with measured numbers -- and it cuts both ways. Wang, Wu, Zheng, Lin,
arXiv:2402.09075 ("Steady-State Error Compensation for RL with Quadratic Rewards"): "Issues of
significant steady-state errors often manifest when quadratic reward functions are employed." Table III
(DDPG): ACC SS error quadratic 2.7e-1 m vs absolute-value 2.9e-3 m (~93x); lane-change 2.3e-2 vs 5.5e-5
(~418x). The documented COST: "Although absolute-value-type reward functions alleviate this problem,
they tend to induce substantial fluctuations in specific system states, leading to abrupt changes."
Our ss_jitter is currently healthy, so that is exactly what an L1 switch would spend.
[CONFIDENCE: HIGH]
NOTE the tension to resolve before acting: this page's R5 CAUTION cites reward.md 2.2 saying LINEAR was
disabled for causing a dead-zone -- the opposite of the literature's finding. Read reward.md 2.2 and
reconcile before any L1 probe; the internal note may concern att_rp's lin_ratio, not the bias term.

Also: "dead zone" is OUR coinage, not a field term (zero literature hits). And the field DISAGREES on
the cause of RL steady-state error: arXiv:2402.09075 blames "the discounting nature of rewards in RL
algorithms"; arXiv:2502.02265 blames "network approximation inaccuracies and inadequate sample quality".
Neither uses the vanishing-gradient story. The SYMPTOM is well-established; our causal account is one
candidate among several, not consensus.

### 5. The bigger context this page could not see

See [[literature_map_how_rl_control_actually_handles_steady_state_erro]]: NOBODY has eliminated
steady-state error in any domain -- Bohn 2021 tried a PURE integrator, 0.999 decay, learned integration
gains AND shaped rewards, and reports "none were successful in entirely eliminating it". That
empirically refutes the intuitive "we lack a true integrator, hence the residual bias" story. Also,
approach B (reward-penalizing the integral) is a SINGLE-PAPER idea while approach A (integral in obs) is
established -- so the reward half of this term is the rare half.

