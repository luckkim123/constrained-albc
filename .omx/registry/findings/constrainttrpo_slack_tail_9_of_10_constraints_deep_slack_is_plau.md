---
title: "ConstraintTRPO slack tail: 9 of 10 constraints deep-slack is plausibly healthy complementary slackness (UNVERIFIED) -- confirm via training-time trajectory + loosening ablation before tuning budgets"
tags: ["constraint", "CMDP", "complementary-slackness", "thruster_util", "slack-tail", "inertness", "loosening-ablation", "budget-tuning", "next-experiment", "ConstraintTRPO"]
created: 2026-07-12T10:04:32.803449
updated: 2026-07-13T05:31:34.247747
sources: ["diagnose-20260606-194621", "diagnose-20260607-113942"]
links: ["constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md", "constraint_budget_x0_5_binds_only_thruster_util_authority_starva.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# ConstraintTRPO slack tail: 9 of 10 constraints deep-slack is plausibly healthy complementary slackness (UNVERIFIED) -- confirm via training-time trajectory + loosening ablation before tuning budgets

STATUS: WORKING INTERPRETATION, not a settled rule. Recorded provisionally; confirm via the experiments below before treating as verified or tuning any budget.

WHAT IS OBSERVED (teacher run trpo_main_teacher_260525_232805, final-window J_C/d_k): the CMDP binds through ONE channel only -- thruster_util J_C/d_k=0.87 -- while the other 9 sit in slack (5 deep; cumul_yaw ~0 "fully inert"). See [[constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli]] for the table + normalization.

LEADING INTERPRETATION (PLAUSIBLE, NOT YET CONFIRMED): this is a HEALTHY constrained optimum (KKT complementary slackness), NOT a defect to fix. But this is inferred from a FINAL-window snapshot; it is NOT experimentally confirmed that the 9 never influenced learning. Do not treat "the 9 are inert / the state is healthy" as settled, and do not tune budgets, until the OPEN QUESTION below is closed.

WHY THE HEALTHY READ IS PLAUSIBLE (these parts ARE verified -- theory + mechanics):
- Complementary slackness: at a constrained optimum an inactive constraint (J_C<d_k) has dual multiplier ~0 and adds ~no first-order gradient to the policy. In this IPO/barrier form the soft multiplier is 1/(t*margin_k) (barrier=-sum log(margin_k)/t, constraint_trpo.py:470); slack => large margin => pull ~0.
- Double suppression of the 9: their cost term rarely fires => standardized cost-advantage ~0, AND the std floor clamp(min=1.0) at constraint_trpo.py:437 deliberately does NOT amplify near-constant binary constraints. Net influence ~0 by design.
- A slack SAFETY margin is SUPPOSED to be slack in the common case -- that is the definition of a margin. If all 10 bound you would have an over-constrained, reward-starved policy: exactly what E6 produced by tightening (see [[constraint_budget_x0_5_binds_only_thruster_util_authority_starva]]: -54% reward, negative lin_vel, entropy collapse).
- Literature: inactive-constraint => multiplier 0 is standard CMDP/KKT; safe-RL threshold guidance notes a too-loose limit makes a constraint "vacuous", so slack-vs-loose depends on constraint intent (guardrail vs regulator).

HYPOTHESIZED PER-CONSTRAINT BUCKETS (from cost-function semantics + teacher J_C/d_k; the behavioral-regulator bucket especially is a hypothesis the ablation tests):
- Authority cap (1, BINDING): thruster_util 0.870 -- the one genuine reward<->cost tradeoff (authority vs tracking); ~13% slack, 0 violation.
- Pure safety/catastrophe rails (6, slack looks correct): attitude 0.003 (80deg tilt), cumul_yaw 0.000 (+-8pi tether ~3.3x peak), joint1_pos 0.005 (+-4pi cable-wrap), manipulability 0.038 (singularity floor), arm_joint_vel 0.031, arm_torque 0.407. Slack likely = policy lives inside the physical envelope; would activate under drift / harder DR.
- Intended behavioral regulators (3, benign design-intent gap): rp_rate 0.319, yaw_rate 0.138, rp_vel_settling 0.455 -- meant to actively cap rates/settling but out-competed by the reward's rate-tracking terms. Only a "problem" IF a GUARANTEED rate/settling envelope is required (e.g. under DR) that the reward cannot promise.

OPEN QUESTION (why this is NOT settled): final-window slack does NOT prove a constraint never influenced learning. J_C/d_k=0.003 is consistent with three training histories -- (a) never mattered (flat deep-slack from init; cumul_yaw the strongest candidate, physically unreachable); (b) mattered early then satisfied (bound during early exploration, bent the trajectory, decayed to slack -- "the fence you never touch still shaped where you walked"); (c) latent counterfactual (never bound on this trajectory but holds the policy in a safe basin; remove it and it drifts, esp. under DR). A snapshot cannot separate these.

NEXT EXPERIMENTS TO CONFIRM (do the free one first):
1. FREE, zero-GPU, existing data -- settles (a) vs (b): the training-time trajectory already exists in TB (constraint_encoder_runner.py:317 logs Constraint/margin/<name> every iter; :316 Constraint/viol/<name>; :320 barrier_penalty). Read J_C/d_k(iter) for the 9: any approaching 1.0 early then settling => (b) it shaped; flat-slack from iter 0 => (a) it never mattered. CAVEAT: derive J_C/d_k from margin ONLY in the slack regime (J_C=d_k-margin); in the binding regime margin freezes at alpha*d_k so margin-derived ratio saturates at 1-alpha=0.95 -- there use Constraint/viol crossing 0 to detect early binding (this is the same saturation corrected in the margin-normalization page). Corroborate with early barrier_penalty spikes >0.1 that later subside.
2. LOOSENING ABLATION -- settles the counterfactual (c), needs 1 run: multiply the 9 non-thruster budgets by x100 (config.py:57-69), keep thruster_util=0.40 EXACTLY, everything else (reward/DR/seed/iters/encoder/hparams) byte-identical. Loosen, do NOT delete: deleting changes num_constraints => cost-critic head count + per-constraint standardization + barrier-sum dim (several variables at once); loosening keeps the code path identical and moves only the feasible boundary (minimum-change, one-variable). Control = teacher (same seed). Discriminator: eval_dr static attitude ss_error (roll/pitch) + per-env CV across 4 DR levels; thruster final J_C/d_k; the 3 shapers' J_C/d_k; Reward/total + lin_vel + entropy.
   Outcome interpretation: (i) identical policy/metrics (seed noise), thruster ~0.87, attitude unchanged => CONFIRMED passive safety envelope; treat as a 1-constraint (thruster) problem + 9 dormant rails. (ii) rate/settling degrade => the 3 shapers WERE contributing; reward alone insufficient for smooth rates; keep them. (iii) safety envelope violated though nominal fine => case (c) latent guardrail was holding a safe basin; keep it. (iv) thruster binds harder / entropy collapses => the 9 were indirectly relieving thruster (coupling); unlikely given deep slack.

PROVISIONAL RECOMMENDATION (pending confirmation): lean toward accepting the state as healthy, but (i) back it with the FREE step-1 diagnostic before declaring it, and (ii) do NOT tune any budget until verified. IF later you want the CONSTRAINT (not the reward) to enforce a tighter attitude/rate envelope, the tuning asymmetry is: tightening thruster OR all-budgets-globally = DESTRUCTIVE (E6-proven); tightening a deep-slack behavioral channel (e.g. attitude) by co-tuning (limit, budget) toward the operating point, one variable vs baseline = the SAFE documented lever (docs section 3.4; budget-alone tuning of a far-threshold constraint is a near-no-op until the threshold moves toward the operating point). Never tighten toward a non-physical value (kills the soft-bites-before-hard-cap layering).

SOURCE / VERIFICATION STATUS: OMC architect analysis (opus) + web research (KKT complementary slackness; safe-RL "loose limit -> vacuous" threshold guidance), 2026-07-12. VERIFIED: per-iter margin/viol/barrier logging (constraint_encoder_runner.py:316-320), std floor (constraint_trpo.py:437), adaptive floor engages only at J_C/d_k>0.95 so thruster 0.87 is exact-regime. UNVERIFIED (pending the experiments above): whether the 9 slack constraints empirically influenced learning; the behavioral-regulator bucketing; the healthy verdict itself.

---

## Update (2026-07-13T05:31:34.247747)

STEP 1 (free training-time trajectory check) DONE — 2026-07-13 post-p7_tail planning session, on baseline trpo_baseline_260713_031325 TB (5000 iters, EventAccumulator over Constraint/margin/*). Verdict: the deep slack at convergence is NOT 'never mattered' — 8/10 constraints were near-binding during early exploration and then relaxed (= 'shaped training then relaxed', healthy complementary slackness): attitude min 0.05@it4, joint1_pos 0.05@it498, cumul_yaw 0.05@it0, arm_joint_vel 0.10@it1, yaw_rate 0.50@it0, rp_rate 0.50@it1, arm_torque 0.40@it5, thruster_util 2.00@it14. Only TWO never came close at ANY point: rp_vel_settling (min 8.30@it3781) and manipulability (min 3.09@it153) — the genuinely-inert candidates. CONSEQUENCE: the loosening ablation (budgets x100 on the 9 non-thruster constraints) is DEPRIORITIZED — most budgets demonstrably shaped early training, so loosening is not a safe no-op and the 'inert' hypothesis is already largely refuted for 8/10 without a GPU run. If a loosening probe is ever wanted, scope it to rp_vel_settling + manipulability only. Data: margin trajectories at iters 0/50/100/200/400/800/1600/3200/4999 extracted this session (evidence in the p7_tail planning notes).
