---
title: "Action bounding is justified (raw Gaussian + external clamp) -- tanh ruled out, 3 experiment leads remain"
tags: ["action-clamp", "tanh", "exploration", "noise", "clip-fraction", "raw-gaussian", "constraint-trpo", "experiment-lead", "max-std", "init-noise-std", "ipo-barrier", "entropy-collapse", "entropy", "sigma", "A2", "D1", "lead3-closed", "min_std", "action_bounding"]
created: 2026-07-02T09:00:08.575699
updated: 2026-07-21T07:57:12.504932
sources: ["trpo_entcoefzero_260721_014731", "diagnose-20260721-164331"]
links: ["action_pipeline_behavior_walk_through_two_clamps_raw_gaussian_vs.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
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

---

## Update (2026-07-13T06:37:50.097930)

## Lead 2 status-correction (2026-07-13): max_std / init_noise_std revisit is DISSOLVED, not open

An earlier framing left "Lead 2: revisit max_std=2.0 / init_noise_std=0.7" as an open training
comparison gated only on data. That is superseded. The P4 batch added clip_fraction logging
(Lead 1) and the new baseline `trpo_baseline_260713_031325` measured clip_fraction ~0.0048 —
i.e. <0.5% of actions hit the |a|>=1 saturation boundary. The saturation motivation for raising
max_std/init_noise_std is therefore dissolved (there is almost no saturation to relieve). Do NOT
re-propose Lead 2 as a probe; it matches the PROMPT_next_experiment_planning §3 rejection. Lead 3
(entropy-IPO causal split) remains a separate open item; Lead 1 (clip_fraction logging) is done.

---

## Update (2026-07-20T07:54:39.404966)

STATUS PROMOTION (2026-07-20 wiki sweep): Lead 3 (entropy-IPO causal split: comparison training run with entropy_coef_per_dim=0 vs shipped per-dim values, to isolate whether the IPO barrier causally drives entropy collapse) is a live training-run lead; page promoted to needs-experiment so it surfaces in the status backlog alongside the other exploration leads.

---

## Update (2026-07-20T21:40:49.535452)

# D1 RECORD (2026-07-21) -- A2 result and A3's pre-registered band

[FINDING] A2 ANSWERS the lead: the ENTROPY BONUS -- not the IPO barrier -- is what holds
sigma. With `entropy_coef_per_dim` set to all-zero, all THREE unclamped dims departed
>=10% below the anchor path from iter 500 and stayed there for the whole run (4500 iters
sustained, vs the >=500 required). arm1, which never floors in any prior posttam run,
was pinned to its 0.10 floor by iter 1000.

| iter | arm1 A2/anchor (dev) | thr0 A2/anchor (dev) | thr3 A2/anchor (dev) |
|---|---|---|---|
| 500 | 0.1014 / 0.1896 (-46.5%) | 0.1868 / 0.2221 (-15.9%) | 0.2199 / 0.2554 (-13.9%) |
| 1000 | 0.1000 / 0.1632 (-38.7%) | 0.1558 / 0.1789 (-12.9%) | 0.1671 / 0.1890 (-11.6%) |
| 2500 | 0.1000 / 0.1357 (-26.3%) | 0.1217 / 0.1453 (-16.2%) | 0.1299 / 0.1524 (-14.8%) |
| 4999 | 0.1000 / 0.1303 (-23.3%) | 0.1036 / 0.1271 (-18.5%) | 0.1080 / 0.1306 (-17.3%) |

[EVIDENCE: exp(log_std) per dim from model_<it>.pt of trpo_entcoefzero_260721_014731 vs trpo_biasema_260715_142543 at matched iterations; free-dim set {arm1, thr0, thr3} established by Z1]
[CONFIDENCE: HIGH]

[FINDING] The kill-criterion did NOT fire and the April 2026 result does NOT replicate in
its consequence. April 04-10 (coef=0) was recorded as a collapse to noise_std 0.12 vs
0.55; here removing the bonus costs sigma but NOT return -- A2's reward is slightly HIGHER
than the anchor. So on this plant, with per-dim floors in place, the entropy bonus buys
exploration that the objective does not need at 5000 iters. The divergence from April is
itself the finding: the April campaign's dramatic collapse was on a configuration without
today's per-dim floor structure.
[EVIDENCE: TB reward last-200-iter mean -- A2 276.82 vs anchor 272.08 (+1.7%); final 277.68 vs 272.46; kill-criterion was 'sustained >=200-iter drop >15% below the anchor band']
[CONFIDENCE: HIGH]

[FINDING] D1 DECISION -- A3 = raise `min_std_per_dim` THRUSTER leg 0.05 -> 0.08. The
plan's D1 rule branches on whether A2 showed IPO-barrier causality; it did NOT (it showed
bonus causality), so the 'otherwise' branch applies, which offers the arm leg or the
thruster leg. The thruster leg is chosen because Z1 shows it lifts FOUR currently-floored
dims (thr1/thr2/thr4/thr5) while the arm leg would lift only arm0 (arm1 is already free
at ~0.13 under the normal bonus). One run, no sweep, 5000 iters, vs the biasema 5k anchor.
[EVIDENCE: Z1 per-dim table -- floored set {arm0, thr1, thr2, thr4, thr5}, free set {arm1, thr0, thr3}; campaign plan D1 rule]
[CONFIDENCE: HIGH]

# A3 PRE-REGISTERED VERDICT BAND (declared BEFORE launch, revisable only before results)

- MANIPULATION CHECK (precondition): at iter 5000 the four lifted dims must read exactly
  0.0800 (the clamp still binds at the new floor, proving the intervention is active), and
  the three free dims {arm1, thr0, thr3} must be within +/-10% of the anchor path (proving
  the change did not act through them). FAIL on either -> the run does not isolate the
  floor lever and must not be read as evidence.
- PRIMARY (benefit): `none`-level roll `os_env_mean` vs the anchor's 17.022. Adopt-worthy
  = a reduction of >=10% (i.e. <=15.3) OR a >=10% reduction in `hard`-level AttErr vs the
  anchor, with no cost breach below.
- GUARD (cost): `none`-level roll AND pitch `ss_error` must not worsen by more than 5%
  (anchor roll 0.215 -> ceiling 0.226; pitch 0.195 -> ceiling 0.205). A breach means the
  extra exploration bought robustness by paying tracking -> do not adopt.
- NULL is a real outcome: within +/-5% on both primary and guard = the floor is not the
  binding constraint on exploration, and the exploration lead resolves as 'floors are not
  the lever' rather than staying open.
- KILL: sustained >=200-iter reward drop >15% below the anchor band, or a constraint
  violation spike -> stop early and report.
- DORAEMON health reported as a first-class outcome (mode, success vs alpha=0.5, achieved
  expansion count, terminal Beta b), per the campaign convention.

[EVIDENCE: anchor values from trpo_biasema_260715_142543/eval/static_260716_160156/summary.json none/roll and none/pitch]
[CONFIDENCE: HIGH]

---

## Update (2026-07-21T07:57:12.504932)


# A3 RESULT (2026-07-21) — DISCARD, and it CLOSES the exploration lead

[FINDING] A3 (`trpo_minstdthr008_260721_064149`, min_std_per_dim thruster leg 0.05 -> 0.08,
5000 iters) FAILS the pre-registered primary in the ADVERSE direction: `none`-level roll
`os_env_mean` = 21.4858 against the anchor's 17.0215 (+26.2%), where adoption required
<= 15.3. The alternative `hard`-AttErr branch also failed (att_norm ss_error -1.5%, needed
-10%). Manipulation check PASSED (thr1/thr2/thr4/thr5 exactly 0.08000; free dims arm1 +3.8%,
thr0 -0.7%, thr3 -6.1%, all inside +/-10%), so the verdict is attributable to the floor lever.
[EVIDENCE: summary.json none/roll/os_env_mean, A3 eval static_260721_113503 vs anchor
trpo_biasema_260715_142543 eval static_260716_160156; per-dim exp(log_std) from model_4999.pt
of both runs; analysis diagnose-20260721-164331 §verdict]
[CONFIDENCE: HIGH]

[FINDING] The lead resolves STRONGER than a NULL: the per-dim sigma floor is not an
under-exploration bottleneck — raising it ACTIVELY DEGRADES the nominal plant. The lever
engaged exactly as designed (Noise/std_min 0.05 -> 0.08, mean sigma +16.8%, entropy +20.4%),
so the failure is not "the knob did nothing".
[EVIDENCE: TB last-200-iter means both runs; analysis diagnose-20260721-164331 §trpo]
[CONFIDENCE: HIGH]

[FINDING] REUSABLE TRADE: raising the action sigma floor buys steady-state DC accuracy and
pays transient overshoot plus per-env spread. ss_error improved on roll AND pitch at every DR
level (pitch -47% at `none`) while roll os_env_mean degraded at every level and pitch CV
roughly doubled at every level (none 10->21, soft 18->43, medium 35->92, hard 116->197).
Expect this shape from any future sigma/dither-side intervention.
[EVIDENCE: summary.json all 4 DR levels x roll/pitch; analysis diagnose-20260721-164331 §tracking]
[CONFIDENCE: HIGH]

[FINDING] The cost of added action noise scales INVERSELY with DR: roll os_env_mean penalty
decays monotonically +26.2% (none) -> +13.1% (soft) -> +8.2% (medium) -> +3.9% (hard). Dither
is pure disturbance against a known plant and only becomes comparatively cheap once model
uncertainty already dominates. Corollary: an exploration-side intervention must be judged at
`none`, where it is most expensive — judging it at `hard` would have looked nearly free.
[EVIDENCE: summary.json roll os_env_mean across 4 levels, both runs; analysis
diagnose-20260721-164331 §generalization]
[CONFIDENCE: HIGH]

[FINDING] BAND-DESIGN LESSON: the A3 guard did NOT catch the regression. Both guarded
quantities (`none` roll/pitch ss_error) IMPROVED (-5.8%, -47.2%) while the damage landed in
os_env_mean and n_gt20. A band for a sigma/exploration-side intervention MUST guard the
transient (os_env_mean) and the tail (n_gt20), not only the DC error.
[EVIDENCE: A3 band on this page vs measured guard values; analysis diagnose-20260721-164331 §verdict]
[CONFIDENCE: HIGH]

