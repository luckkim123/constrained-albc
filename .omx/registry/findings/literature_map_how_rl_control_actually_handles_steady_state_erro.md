---
title: "Literature map: how RL control actually handles steady-state error (cross-domain) -- nobody has eliminated it; our r_bias reward penalty is a single-paper idea, our encoder is the field's top-ranked mechanism with no UUV precedent"
tags: ["literature", "steady-state-error", "integral-action", "bias-ema", "reward-shaping", "policy-invariance", "rma", "encoder", "cross-domain", "citations"]
created: 2026-07-16T06:36:48.431486
updated: 2026-07-16T06:36:48.431486
sources: []
links: ["bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
---

# Literature map: how RL control actually handles steady-state error (cross-domain) -- nobody has eliminated it; our r_bias reward penalty is a single-paper idea, our encoder is the field's top-ranked mechanism with no UUV precedent

# Literature map: how RL control actually handles steady-state error, and where our stack sits

Cross-domain literature research, 2026-07-16, 5 parallel document-specialist agents (primary sources
fetched and quoted, not abstract-only). Domains covered: fixed-wing UAV, quadrotor, legged, automotive,
power electronics, motor drives, process control, aerial manipulation, marine. Triggered by the user
question "is our bias_ema approach standard? what do other studies do?"

# HEADLINE: nobody has eliminated steady-state error. It is an open problem, not our failure.

[FINDING] Every integral-family attempt in the fetched literature REDUCES but never ELIMINATES
steady-state error -- across four independent domains.
[EVIDENCE:
- Bohn, Coates, Reinhardt, Johansen, "Data-Efficient Deep RL for Attitude Control of Fixed-Wing UAVs:
  Field Experiments", 2021, arXiv:2111.04153 -- uses OUR EXACT recurrence, Eq.(7) `I_t = gamma^I * I_{t-1}
  + e_t, gamma^I = 0.99`. Quote: "We experimented with several techniques in order to address the
  steady-state error of the RL controller observed in flight experiments: pure integrator (no decay),
  higher decay factor (e.g. 0.999), having integration separate from the NN controller with learned
  integration gains, shaped rewards, and training with input disturbances. Whereas some of these
  measures reduced the steady-state error to some degree, NONE WERE SUCCESSFUL IN ENTIRELY ELIMINATING IT."
- Havenstrom, Sterud, Rasheed, San, "PID Controller Assisted RL for Path Following by AUVs", 2020,
  arXiv:2002.01022. Quote: "the agent has inferred that it must increase the control input in order to
  compensate for the current, but since it has not experienced this scenario during training, it is not
  able to compensate completely."
- Weber, Schenke, Wallscheid, IASA, 2022, arXiv:2201.13331 -- true integrator + anti-windup on the ACTOR
  OUTPUT: 52% (power grid) / 38% (motor) reduction vs DDPG. Reduction, not elimination.
- Hwangbo 2019 (legged) and Hwangbo 2017 (quadrotor) use NO integral action at all.]
[CONFIDENCE: HIGH]

CONSEQUENCE: our baseline's sub-degree mean + 100% survival is NOT a poor result in this context, and
"eliminate the DC bias" is not a solved target anyone has hit. Calibrate campaign expectations to
"reduce the tail", not "eliminate the bias".

[FINDING] Bohn 2021 already ran the experiment that refutes the intuitive "we have no true integrator,
that's why SS error persists" hypothesis: they tried a PURE (undecayed) integrator and it STILL did not
eliminate the error. They attribute the residual to sim-to-real / function-approximation gap and never
invoke DC-gain / internal-model-principle theory. So the leaky-vs-true-integrator distinction is
theoretically correct but has NO demonstrated predictive power.
[EVIDENCE: arXiv:2111.04153 quote above ("pure integrator (no decay)... none were successful")]
[CONFIDENCE: HIGH]

# Where our three mechanisms rank

| our mechanism | literature rank | standing |
|:--|:--|:--|
| encoder + student distillation (disturbance-as-latent) | **1st** (most mature) | **NO precedent in UUV RL** |
| `_error_integral` obs (leaky, gated) | 2nd | established; no paper shows full elimination |
| `r_bias` reward penalty | **6th** | **single-paper idea** + theoretically unsound (below) |

[FINDING] Approach (A) integral-in-OBSERVATION is established across multiple independent papers;
approach (B) reward-PENALTY on the integral is essentially a SINGLE-PAPER idea. A targeted attempt to
refute this (searching specifically for B) found exactly one clean instance. Half our design (the
reward penalty) is the rare half.
[EVIDENCE: (A) Bohn 2021 arXiv:2111.04153; Zhang/Mattsson/Wigren ACC 2023 arXiv:2304.10277 (true
accumulator z_t = z_{t-1} + eps_t, clipped [-25,25]); plus a PID-gain quadrotor cluster.
(B) Wang, Wu, Zheng, Lin, "Steady-State Error Compensation for Reinforcement Learning with Quadratic
Rewards", 2024, arXiv:2402.09075 -- the ONLY clean instance found. Other "integral reward" hits
(Lyapunov-descent reward, integral-TD-error, PI-Lagrangian) use "integral" in unrelated senses.]
[CONFIDENCE: HIGH]

[FINDING] Integral action of ANY kind is a niche technique in RL, not a general-RL standard -- it lives
only in control-engineering-adjacent RL (power electronics, motor drives, UAV attitude, process
control). MuJoCo/Atari/manipulation benchmarks essentially never use it.
[EVIDENCE: Zhang, Mattsson, Wigren, ACC 2023, arXiv:2304.10277, quote: "Using integrated errors is
however not standard in the RL field. Here it will therefore be explored how this idea can be
incorporated into the RL-framework."]
[CONFIDENCE: HIGH]

[FINDING] One paper explicitly REJECTS approach (A) on cost/benefit grounds.
[EVIDENCE: Chen et al., "Adviser-Actor-Critic: Eliminating Steady-State Error in RL Control", 2025,
arXiv:2502.02265, quote: "Integrating the integral of error as an observation element, inspired by PID
control, aims to compensate for past errors. However, this method increases the observation dimensions
and may not always enhance performance."]
[CONFIDENCE: HIGH]

# THEORY: r_bias is not guaranteed to preserve the optimal policy set -- but P-B1 already closed the hole

[FINDING] Ng-Harada-Russell 1999's Necessity Theorem plus its non-Markovian generalization say a
non-potential-based reward term can CHANGE the optimal policy set. `r_bias = sum_i w_i * bias_ema_i^2`
is a direct penalty, NOT a telescoping potential difference `gamma*Phi(s_{t+1}) - Phi(s_t)`, so it is
NOT guaranteed to preserve the optimal policy set of the task defined on the observed state.
[EVIDENCE: Ng, Harada, Russell, "Policy Invariance Under Reward Transformations", ICML 1999,
Necessity Theorem: "If F is not potential-based, then there is an MDP M such that no optimal policy in
M is also optimal in M with F."
Forbes, Villalobos-Arias, Wang, Jhala, Roberts, "Potential-Based Intrinsic Motivation: Preserving
Optimality With Complex, Non-Markovian Shaping Rewards", 2024, arXiv:2410.12197 -- generalizes NHR99 to
history-dependent/time-varying potentials Phi_t, with Theorem 1 (sufficient condition, Eq. 25) and a
worked MiniGrid counterexample. Quote: "These methods can often inadvertently change the set of optimal
policies in an environment, leading to suboptimal behavior."]
[CONFIDENCE: HIGH]
SCOPE CAVEAT (honest): both papers formally analyse an ADDED shaping term F on top of a base reward.
`r_bias` is a base-reward component. The math does not require F to be "extra", but applying the result
to a base component is an extension we are making, not something either paper states.

[FINDING] P-B1 (use_bias_ema_obs=True, adopted 2026-07-16) closes this hole completely, and for BOTH
actor and critic. Once `bias_ema` is observed, `r_bias` is Markov w.r.t. the augmented observed state
and no potential-based-shaping argument is needed at all. Code-verified: the critic input is
`num_critic_obs = policy_obs_dim + privileged_dim` (i.e. cat([o_t, p_t]), +z when critic_uses_z), so the
critic sees o_t -- and o_t is what P-B1 extended 69->72D. So P-B1 was right for a DEEPER reason than its
measured tracking gain: it removed a formal policy-invariance hazard.
[EVIDENCE: _core/encoder/actor_critic_encoder.py:105-107 num_critic_obs = policy_obs_dim +
privileged_dim (+ encoder_latent_dim if critic_uses_z); albc_env.py:1129 policy_obs cat _bias_ema;
Gaon & Brafman AAAI-20 quote below]
[CONFIDENCE: HIGH]

[FINDING] Observation augmentation IS the textbook prescription for a non-Markovian reward, and our
case is its EASIEST instance. Reward machines / automata learning are for DISCOVERING an unknown
non-Markov reward structure from experience; `bias_ema` is already computed by the env, so
"just put it in the observation" is the correctly-scoped fix -- reward machines would solve a harder
problem we do not have.
[EVIDENCE: Gaon & Brafman, "Reinforcement Learning with Non-Markovian Rewards", AAAI-20, quote: "We can
address non-Markovian rewards (NMRs) by augmenting the state with information that makes the new model
Markovian. Except for pathological cases, this is always possible."
Empirical damage from NOT augmenting, same paper: "vanilla Q-learning is very noisy and fails to
converge"; "Vanilla is still noisy and converges to a sub-optimal policy after 25M steps with very high
STD."
Toro Icarte, Klassen, Valenzano, McIlraith, "Reward Machines", arXiv:2010.03950 -- cross-product
baseline.]
[CONFIDENCE: HIGH]

# TERMINOLOGY CORRECTIONS (our own notes use non-existent terms)

[FINDING] Three phrases used in our wiki/analysis prose do NOT appear in the literature: "critic
regression noise", "blurred credit assignment", "non-stationary reward" (as a named framing for this
hazard). Full-text search of the four core papers returned ZERO hits for "non-stationar*" and "credit
assign*". They are plausible informal restatements, not field terminology. The closest FORMAL grounding
is Baisero & Amato, "Unbiased Asymmetric RL under Partial Observability", AAMAS 2022, arXiv:2105.11674,
Theorem 4.1: "In partially observable control problems, a time-invariant state value function V^pi(s)
is generally ill-defined" -- but that is proven for ASYMMETRIC actor-critic (privileged critic +
partial-obs policy), NOT our symmetric-omission case, so it is mechanism-level justification only.
[EVIDENCE: agent full-text grep across arXiv:2010.03950, Gaon&Brafman AAAI-20, arXiv:2410.12197,
arXiv:2201.13331 -- zero hits]
[CONFIDENCE: HIGH]
ACTION: fix [[bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h]], which uses these terms.

# The squared form is a bigger lever than the weight (settles the "is k_bias too small?" question)

[FINDING] Quadratic reward terms are DIRECTLY implicated in steady-state error, with measured numbers,
and L1 fixes it 93-418x at the cost of oscillation. Our stack is quadratic twice over: att_rp is
`exp(-e^2/sigma^2)` and r_bias is `w*ema^2`.
[EVIDENCE: Wang, Wu, Zheng, Lin, arXiv:2402.09075, quote: "Issues of significant steady-state errors
often manifest when quadratic reward functions are employed." Table III (DDPG): ACC quadratic SS error
2.7e-1 m vs absolute-value 2.9e-3 m (~93x); lane-change 2.3e-2 m vs 5.5e-5 m (~418x). Cost, same paper:
"Although absolute-value-type reward functions alleviate this problem, they tend to induce substantial
fluctuations in specific system states, leading to abrupt changes."]
[CONFIDENCE: HIGH]

[FINDING] Raising k_bias CANNOT fix a structurally vanishing gradient -- this settles the "the term is
175x too small to matter" question with math, not opinion. For `w*ema^2` the gradient is `2*w*ema`:
scaling w scales the slope at any FIXED ema, but the gradient still vanishes LINEARLY as ema->0
regardless of w. Magnitude does not change the order of vanishing. Corroborating (circumstantial): both
SS-error papers chose STRUCTURAL fixes (integral term / PID adviser) over weight tuning.
[CONFIDENCE: HIGH]
This mathematically backs the theory-review's R1(expose) > R2(weight) priority and its "magnitude is
not the mechanism; structure is" claim.

[FINDING] The exponential-kernel vanishing-gradient problem is named and FIXED in exactly one paper, via
a directly transferable two-scale superposition -- relevant to att_rp (sigma=0.1), not just r_bias.
[EVIDENCE: Singh, Ujjwal, Chaudhary, Vasudevan, Yadav, Roy, "RL with Inner-loop Dynamics Estimator for
Aerial Manipulation under Uncertainty", 2026, arXiv:2606.16621, `r = r1*e^(-r2*x^2) + r3*e^(-r4*x^2)`,
quote: "We superimpose two exponential functions, one of wider variance and another of lower variance.
The higher variance exponential prevents gradients from vanishing when the system is away from the
target, whereas the lower variance exponential maintains high reward gradients near the target
enforcing precision."]
[CONFIDENCE: HIGH]

[FINDING] Our exp-kernel convention's lineage NEVER analysed this limitation -- it is inherited
convention, not a justified choice. DeepMimic (arXiv:1804.02717, SIGGRAPH 2018) established
`exp[-2*sum||qhat-q||^2]` etc; legged_gym set `tracking_sigma = 0.25  # tracking reward =
exp(-error^2/sigma)`; our Isaac Lab project inherited it. Neither origin discusses near-zero gradient.
[CONFIDENCE: HIGH]

NOT the field's term: "dead zone" for this phenomenon appears NOWHERE in the searched literature -- it
is our team's coinage. Also, the field DISAGREES on the cause: arXiv:2402.09075 blames "the discounting
nature of rewards in RL algorithms"; arXiv:2502.02265 blames "network approximation inaccuracies and
inadequate sample quality". Neither uses the vanishing-local-gradient story. The SYMPTOM is
well-established; OUR causal explanation is one candidate, not consensus.

CAUTION: dm_control's `tolerance()` (arXiv:1801.00690) is the OPPOSITE tool -- it deliberately makes the
reward FLAT (zero gradient) inside the tolerance band. Do not adopt it by name-match.

# COULD NOT FIND EVIDENCE (do not fill these with guesses)

- **RMA-style privileged-encoder disturbance-latent estimation in UUV/AUV RL**: no precedent found. RMA
  (Kumar et al., arXiv:2107.04034) is legged-only. Closest is Tian et al. 2025 (Ocean Engineering,
  S0029801825006195), an LSTM+attention meta-RL glider that infers a "posterior distribution of the
  latent task representation" for buoyancy loss / current -- but it is glider-specific (buoyancy engine,
  not thruster-driven), a meta-RL context encoder rather than teacher-student privileged distillation,
  and never cites RMA. **We are doing this and the marine literature is silent on it.**
- **IMP / infinite-DC-gain framing in any deep-RL paper**: none found. If we want that argument we must
  derive it from classical control ourselves; the RL literature neither makes nor refutes it.
- **sigma-curriculum (annealing the tracking kernel's sigma)**: none found. Using it means inventing it.
- **log-barrier as a tracking-error shaping term**: none found (log-barrier exists only for CONSTRAINT
  satisfaction -- e.g. our own IPO -- a different application).
- **Recurrent policy as a demonstrated SS-error eliminator**: no dedicated demonstration.
- **Frame/history stacking as an SS-error killer**: no evidence; it is a partial-observability tool.

# Marine-specific context

Newest high-profile 6-DOF UUV RL papers do not treat steady-state error as a research question at all --
they claim robustness from domain randomization alone: MarineGym (arXiv:2503.09203), Learning to Swim
(arXiv:2410.00120, ICRA 2025), EasyUUV (arXiv:2510.22126), Ocean Diviner (arXiv:2507.11283), Fast Policy
Learning (arXiv:2512.13359). The most-repeated concrete mechanism in marine RL is ESO/ADRC
disturbance-observer + RL (Su 2018 glider DOI 10.1007/s00773-018-0582-y; Applied Sciences 15(8):4443
2025 ROV; Ocean Eng. 2023 S001600322300217X) -- though several of those may be one author lineage, so
"multiple independent groups" is weak. Fossen's integral prescription (Handbook, 2nd ed. 2021) is a
MINORITY position in marine RL; Fossen's own 2017 adaptive integral LOS work moved toward "a disturbance
observer designed for estimation and compensation of ocean currents".

# Decision / next experiment (lead)

r_bias (approach B) is the weakest link on four independent counts: single-paper in the literature,
not guaranteed policy-invariant, structurally vanishing gradient, 0.32% of total reward (e3 measured).
The `_bias_ema` BUFFER it maintains is, by contrast, textbook-correct as an observation -- and the
`if k_bias != 0` gate holds that buffer hostage to the reward term (config.py:626 raises if
use_bias_ema_obs=True with k_bias=0). Leads:
1. Decouple the EMA update from k_bias (`use_bias_ema_obs or k_bias != 0`) so the reward can be ablated
   without killing the observation -- a clean k_bias=0 vs -2.0 single-variable probe is impossible today.
2. Two-scale att_rp kernel per arXiv:2606.16621 -- the only precedented fix for our exact kernel, and it
   targets the DOMINANT reward term, not the 0.32% one.
3. L1/Huber form for r_bias per arXiv:2402.09075 -- 93-418x SS-error gain, but watch our currently-healthy
   ss_jitter for the documented oscillation cost.
4. Fix the mis-attribution: config.py's "Hwangbo 2017 pattern" is REFUTED (see
   [[bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h]]). Closest real match is Bohn 2021
   (arXiv:2111.04153) -- same recurrence, same domain family -- or IASA (arXiv:2201.13331).

