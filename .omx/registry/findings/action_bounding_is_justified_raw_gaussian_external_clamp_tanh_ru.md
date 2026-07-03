---
title: "Action bounding is justified (raw Gaussian + external clamp) -- tanh ruled out, 3 experiment leads remain"
tags: ["action-clamp", "tanh", "exploration", "noise", "clip-fraction", "raw-gaussian", "constraint-trpo", "experiment-lead", "max-std", "init-noise-std", "ipo-barrier", "entropy-collapse"]
created: 2026-07-02T09:00:08.575699
updated: 2026-07-02T09:00:08.575699
sources: []
links: ["action_pipeline_behavior_walk_through_two_clamps_raw_gaussian_vs.md"]
category: convention
confidence: high
schemaVersion: 1
---

# Action bounding is justified (raw Gaussian + external clamp) -- tanh ruled out, 3 experiment leads remain

Scope: envs/main (Isaac-ConstrainedALBC-TRPO-v0) exploration/action-noise. 2026-07-02 review conclusion, NO code changed. Literature + current code cross-checked. Companion to the mechanics card [[action_pipeline_behavior_walk_through_two_clamps_raw_gaussian_vs]] (that card = how the two clamps / raw-Gaussian-vs-tanh behave; THIS card = the clamp-justification VERDICT + the experiment leads to check before planning a noise experiment). Full prose ref: docs/reference/exploration-and-noise{.ko,}.md sect.11.

VERDICT. The current raw Gaussian + [-1,1] hard clamp is JUSTIFIED and STANDARD. Do NOT switch to tanh-squashing -- it moves the problem, it does not improve it. Three tanh-free experiment leads remain; the tanh comparison run is discarded.

WHY THE CLAMP IS JUSTIFIED (code-confirmed). Action sample is raw Gaussian, no clamp: actor_critic_encoder.py:277 distribution.sample() ("no action clamping"). Only active clamp is the env buffer albc_env.py:452 self._actions = actions.clone().clamp(-1.0, 1.0); vecenv clip_actions (Clamp#0/#1) unset -> isaaclab default None -> no-op. log-prob is computed on the PRE-clamp raw sample (constraint_trpo.py:459); the clamp touches only env dynamics. Density and executed action are each internally consistent = standard on-policy PPO/TRPO convention (clamp = part of env, not policy).

WHY TANH IS RULED OUT -- and note the "arm freeze" reasoning is WRONG for this task.
1. Optimum is at action-space CENTER here, so tanh saturation (1-tanh^2(u)->0 at boundary) barely applies. arm = delta integrator (albc_env.py:567-578 q_des += 0.10*a) -> idle (a~0) optimal, no boundary attractor; thrusters = hover -> small-command equilibrium near 0. CAUTION: the OLD EE-position ABSOLUTE mode had the optimum at the workspace BOUNDARY, where tanh/clamp DID cause gradient freeze (project memory delta-ee-decision, 97-day-old). That failure mechanism is ABSENT in the current joint-space delta mode -- do not carry "tanh = arm freeze" forward, it is stale.
2. on-policy TRPO + tanh is NOT a validated combination. tanh-squash is SAC-family (off-policy, reparameterization, entropy-in-objective) where the Jacobian correction -sum log(1-tanh^2(u_i)) is natural. TRPO's KL trust region is over the policy distribution; tanh changes that geometry. No literature validates squashed-Gaussian TRPO (no source found). = a full ConstraintTRPO+IPO+FVP redesign with no upside per point 1.
3. Dropping the Jacobian correction makes log-prob use the wrong density -> entropy bonus systematically wrong near the boundary -> breaks the collapse-defense math (entropy bonus + per-dim min_std floor).

THE ONE UNMEASURED VALUE. Clipping's known defect is NOT vanishing gradient but log-prob BIAS for out-of-bound samples (Fujita & Maeda 2018, CAPG), which grows with saturation frequency. With center-optimum + small std (floor 0.05~0.10) saturation is PRESUMED rare -> bias likely small in practice, but this is NOT measured (no clip_fraction logging exists today).

EXPERIMENT LEADS (check before planning; nothing implemented yet).
Lead 1 -- Add clip_fraction logging (abs(a)>=1 rate). Rationale: not logged (code-confirmed); must measure saturation to judge the clip-bias; literature says measure before changing the pipeline. Nature: CODE CHANGE (a few log lines, algorithm unchanged, NO training gate). Top priority -- it gates lead 2.
Lead 2 -- Revisit max_std=2.0 / init_noise_std=0.7. Rationale: only these two knobs have ZERO justification comments = inertia (other knobs -- entropy_coef 0.003, per-dim coef, arm floor -- have empirical backing). Nature: comparison TRAINING run (USER training gate). Depends on lead 1.
Lead 3 -- Isolate the IPO barrier->entropy causality (entropy_coef_per_dim=0 vs current). Rationale: exploration-and-noise sect.6 self-admits this is "inferred, not isolated"; the referenced plan file docs/plans/2026-06-30-entropy-collapse-ipo-barrier-experiment.md is ABSENT. Nature: comparison TRAINING run (USER training gate). tanh-independent, can run any time.
DISCARDED: tanh vs raw+clamp comparison run (ruled out above).

LITERATURE (verified, no fabrication). Haarnoja et al. 2018 SAC arXiv:1801.01290 App.C (tanh Jacobian correction). Fujita & Maeda 2018 Clipped Action Policy Gradient ICML arXiv:1802.07564 (clip-bias theory + CAPG fix). Schulman 2015 TRPO arXiv:1502.05477 / 2017 PPO arXiv:1707.06347 (plain-Gaussian convention). Chou et al. 2017 ICML Beta-policy (both clip and squash have boundary artifacts). NO-SOURCE-FOUND (flagged gaps, not claims): squashed-Gaussian TRPO validation; direct tanh-vs-clip comparison at boundary optima.

