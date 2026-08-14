---
title: "Sigma decay under an expanding DR curriculum: literature verdict and the projection-not-clamp correction"
tags: ["exploration", "entropy", "doraemon", "curriculum", "literature", "gsde", "sigma", "M2", "closed", "arm-w"]
created: 2026-08-10T01:20:25.614865
updated: 2026-08-14T07:48:46.944411
sources: ["arXiv:2311.01885", "arXiv:1912.06680", "arXiv:1810.02541", "arXiv:2212.07536", "arXiv:1908.00261", "arXiv:2509.10771", "arXiv:2405.19153", "arXiv:2005.05719", "arXiv:2510.10959", "arXiv:2601.19624", "wiki-backlog-20260814"]
links: ["exploration_is_not_coupled_to_curriculum_width_dr_grew_10_29x_wh.md", "where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# Sigma decay under an expanding DR curriculum: literature verdict and the projection-not-clamp correction

Literature (13-agent survey + independent citation audit, 2026-08-10) settles three things about the sigma decay seen in Arm W, and refutes one natural assumption about our own code.

1) NOT AN ANOMALY. Monotonic action-std decay to a floor is the documented standard behaviour of on-policy Gaussian policy gradients. PPO-CMA (arXiv:1810.02541, 2018) already stated "the exploration variance can shrink prematurely" and that the entropy-loss weight "can be difficult to finetune". RPO (arXiv:2212.07536) measured the decline on DMC and IsaacGym. The rsl_rl family assumes it: static entropy_coef=0.01, static std clamp, adaptive schedule touches learning rate only. rl_games' IsaacGymEnvs continuous-control default is entropy_coef 0.0.

2) NOT YET A DEFECT. The optimal policy of a fixed MDP is deterministic (arXiv:1908.00261), so std -> floor is the textbook endpoint of convergence. The burden of proof is on "the collapse is harmful", and that burden is currently unmet. Raising entropy uniformly is refuted here (roll 9.77 -> 13.59 deg) AND in the largest published run: OpenAI Five scheduled entropy DOWN 1e-2 -> 1e-3 and its ablation reports "higher entropy performs much worse because the actions are too random" (arXiv:1912.06680).

3) NO PRECEDENT for coupling exploration to curriculum state, anywhere. Six independent survey angles found zero continuous-control papers doing it. Decisive evidence: a full-PDF grep of the DORAEMON paper (arXiv:2311.01885) returns "policy entropy", "action noise" and "std" ZERO times in the body, and "exploration" twice (one inside a bibliography title) - confirmed independently by two auditors. The axis is unexplored in the source paper of our own curriculum, not merely untried in our fork. Nearest neighbours are all outside our setting: AER (arXiv:2510.10959, GRPO/LLM only), AES (arXiv:2601.19624, PPO only, unrefereed), axPPO (arXiv:2405.04664, PPO only).

REFUTED ASSUMPTION ABOUT OUR CODE: it is tempting to reason from upstream rsl_rl, where GaussianDistribution applies std_param.clamp() every forward pass - which would zero the entropy gradient outside the bound and make entropy_coef structurally powerless at the floor. Our fork does NOT do this. In constraint_trpo.py the entropy bonus sits INSIDE the TRPO surrogate (:495, so it participates in the line search), and the floor is applied AFTER the step as an in-place projection on the parameter: log_std.data = torch.max(log_std.data, log_min_std) (:507-509). No gradient is cut. Entropy pressure is live at the floor and simply out-voted by the task gradient. The k=2 probe raising sigma 0.1307 -> 0.17405 is the empirical proof. Do not explain past entropy-intervention failures by "the clamp blocked it".

ARITHMETIC THAT NARROWS THE DIAGNOSIS: with min_std_per_dim = (0.10, 0.10, 0.05 x6), an all-dims-at-floor state would read std_mean = 0.0625. Arm W measured 0.0811, i.e. 30% above that, so the collapse is NOT total. If only the 6 thruster dims are pinned, the 2 arm dims average (0.0811*8 - 0.30)/2 = 0.174, i.e. 1.7x their own 0.10 floor and in free equilibrium. That picture - thrusters bound by the projection, arm bound by the task gradient - is exactly consistent with a uniform entropy raise perturbing only the arm and degrading roll tracking.

CHEAPEST DECISIVE TEST (M2, free, existing logs): compare the std trajectory of the reference run that DID saturate (return 252-262) against Arm W. If the reference also pins std_min at 0.0500 around it 5000 and its it-15000 std_mean is within +-10% of Arm W's 0.0829, then sigma is NOT the variable separating the two runs and the "is it a defect" question closes as NO. Only a reference std_mean >=1.5x higher, or a markedly later pinning, promotes exploration to a candidate cause.

ALSO USABLE NOW: the DORAEMON authors report our exact failure pattern themselves (Walker2D/Swimmer, "degradation in performance over time... due to the agent's exposure to harder/infeasible parameters") and their remedy was not an exploration change but tracking the best-performing checkpoint (arXiv:2311.01885 section 5.2). Their Eq. 6 backup optimisation means the widen-violate-contract limit cycle at the ceiling is designed behaviour, not a bug.

Untried remedies that transfer to on-policy TRPO without touching the trust region: RND intrinsic reward (native to rsl_rl, arXiv:2509.10771), L2-Init / regenerative regularization (the only family that passed consistently on on-policy PPO under distribution shift, arXiv:2405.19153), gSDE state-dependent correlated noise (arXiv:2005.05719). Structurally excluded: Clip-Higher / Clip-Cov / KL-Cov - TRPO has no clip ratio to widen.

Audit: 58 citations, 0 fabricated ids, 1 MISATTRIBUTED (Wasserstein content belongs to arXiv:2312.00246, not 2308.11958), 10 OVERSTATED (mostly paraphrase presented as verbatim quotation). Notable: arXiv:1808.04355's Roboschool/Ant runs discretized the action space, so it is not continuous-action evidence. Full note: vault 0_Project/in_progress/albc/notes/2026-08-10-entropy-collapse-literature.md

---

## Update (2026-08-10T02:38:19.621710)

ADDENDUM 2026-08-10, from reading our own config against our own encoder.

Two config keys in `envs/main/agents/rsl_rl_ppo_cfg.py` and `envs/full_dof/agents/rsl_rl_ppo_cfg.py` are DEAD - declared but consumed nowhere in the repository: `noise_std_type` (default "log") and `state_dependent_std`. Both are dropped by `ActorCriticEncoder.__init__`, which logs `ActorCriticEncoder ignoring unexpected kwargs: ['noise_std_type', 'state_dependent_std']`.

Two consequences.

1) The warning is benign, and the proof is that it appears identically in TRAINING, not only in eval. The Arm D training run on the DGX logs it at 11:27:21, the eval selection pass logs it at 11:31:58. Same construction path, same policy. Seeing it only in an eval log would naturally read as "eval is silently ignoring a saved policy setting and therefore scoring a different network" - that reading is wrong. Check the training log before acting on it.

2) `state_dependent_std` being a dead key means gSDE-style state-dependent correlated exploration (arXiv:2005.05719), listed among the untried remedies, is NOT a flag to switch on. There is no implementation behind the key - only a config field. Costing that lead as "toggle a setting" understates it by an implementation.

This also sharpens the projection-not-clamp finding recorded above: the std parameterisation in this fork is entirely the encoder's own, so upstream rsl_rl's `noise_std_type` semantics do not describe our policy at all. Reason about `constraint_trpo.py` and the encoder, never about upstream defaults.

---

## Update (2026-08-14T07:48:46.944411)

M2 EXECUTED IN ITS COMPARATIVE FORM, 2026-08-14 -- and this page's own pre-registered rule closes the
"is it a defect" question as NO.

WHY THIS WAS STILL OPEN. The M2 work recorded in
[[exploration_is_not_coupled_to_curriculum_width_dr_grew_10_29x_wh]] measured ARM W ONLY. It settled
that exploration is not coupled to curriculum width, which is a different question. The test THIS page
names -- "compare the std trajectory of the reference run that DID saturate against Arm W" -- had
never been run, because it needs both runs side by side.

MEASURED (`Policy/mean_noise_std` and `Noise/std_min`, 2500-iteration buckets, both event files):

| iters | reference `trpo_iterbudget_s30` (saturated, locked 21/21 at 7748) | Arm W `trpo_rampw_kl006_s30` | Arm W / ref |
|:--|--:|--:|--:|
| 2500-4999 | 0.0881 | 0.0933 | 1.06x |
| 5000-7499 | 0.0864 | 0.0870 | **1.01x** |
| 7500-9999 | 0.0844 | 0.0851 | **1.01x** |

`Noise/std_min` is 0.0500 in EVERY bucket of the reference, including its earliest; Arm W reads 0.0510
at 2500-4999 and 0.0500 from 5000 on. The reference therefore pins **at least as early** as Arm W, not
"markedly later".

VERDICT AGAINST THE PRE-REGISTERED RULE. The rule was: reference also pins std_min at 0.0500 around
5000 AND its std_mean within +-10% of Arm W's => sigma is not the separating variable, question closes
NO; only a reference std_mean >=1.5x higher, or markedly later pinning, promotes exploration to a
candidate cause. Both conditions are met with room to spare -- 1.01x against a 1.5x promotion
threshold, and equal-or-earlier pinning. **Exploration is not the variable separating the run that
saturated from the run that did not.**

THE REFUTATION IS ACTUALLY STRONGER THAN THE RULE ASKED. At every overlapping window Arm W carries
MARGINALLY MORE action noise than the reference (+0.7 to +0.8%), and it is the one that failed. The
failing arm explores at least as much as the succeeding one, so "collapsed exploration" cannot be what
costs Arm W its 8 points of return.

LETTER-VS-PURPOSE, STATED EXPLICITLY. The rule names "its it-15000 std_mean". That exact comparison is
NOT EXECUTABLE: the reference run ends at model_9998 while Arm W ran to model_19999, so there is no
reference value at 15,000. What is executable is the same comparison at all three overlapping windows,
and the answer there is unambiguous. Read the verdict as "answered at matched iterations up to 9,999",
not as "answered at 15,000". Arm W's further decline past the reference's end (0.0851 -> 0.0808 over
10,000 more iterations, -5%) has no counterpart to compare against and is not part of this verdict.

WHAT THIS DOES NOT CLOSE. Everything else on this page stands: the literature verdict (sigma decay is
standard on-policy behaviour, not an anomaly), the projection-not-clamp correction to our own code,
the dead `state_dependent_std` / `noise_std_type` keys, and the untried-remedy roster (RND, L2-Init,
gSDE -- the last needing an implementation, not a flag). Those are reference material, not open probes.
The remaining question about Arm W's deficit is WHERE the return is lost, which is
[[where_is_arm_w_losing_the_8_points_of_return_per_dr_dimension_qu]] and is blocked on two engine-gaps.

EVIDENCE: `.omx/scratch/wiki-backlog-20260814/py/tb_traj.py`, tags `Policy/mean_noise_std` and
`Noise/std_min`, bucket 2500, over
`logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813` and
`logs/rsl_rl/albc_trpo_teacher/teacher_final_ramp/trpo_rampw_kl006_s30_260809_161913`.

