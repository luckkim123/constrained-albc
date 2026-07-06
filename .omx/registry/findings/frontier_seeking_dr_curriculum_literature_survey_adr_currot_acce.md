---
title: "Frontier-seeking DR curriculum literature survey (ADR/CURROT/ACCEL) and why naive success-oscillation is unsound"
tags: ["doraemon", "curriculum", "literature", "ADR", "CURROT", "ACCEL", "frontier", "UED"]
created: 2026-07-06T02:12:16.581631
updated: 2026-07-06T02:12:16.581631
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Frontier-seeking DR curriculum literature survey (ADR/CURROT/ACCEL) and why naive success-oscillation is unsound

Literature survey (2026-05-27, verified arXiv sources) on frontier-seeking / feasibility-frontier DR curricula, prompted by the user's idea of MODIFYING DORAEMON into a balance-seeking limit-finder (expand-and-contract to discover the robot's realistic physical feasibility frontier, instead of DORAEMON's monotone march to a fixed uniform target). Verdict: the user's INSTINCT is correct and live research; the naive "oscillate at 50% success" IMPLEMENTATION is the exact strawman DORAEMON/PAIRED/ACCEL were written to fix.

SIMILAR ALGORITHMS:
- ADR (Akkaya/OpenAI 2019, arXiv:1910.07113) = CLOSEST match to the user's idea. Algorithm 1: per-parameter `if p_bar>=t_H: bound+=Delta; elif p_bar<=t_L: bound-=Delta`. Two-sided thresholds, each DR-param boundary oscillates independently at the competence frontier — exactly "expand/contract to find the limit". (Confirmed via ar5iv HTML, not memory.)
- GoalGAN (Florensa 2018, arXiv:1705.06366): keeps goals in a success band [R_min,R_max] (~0.1-0.9). Band-tracking, bidirectional, but goal-space not DR-param-space.
- CURROT (Klink ICML2022): `min W2(p, target) s.t. J(pi,c)>=delta`. Restricts support to feasible-frontier tasks; most principled formal frontier-tracking.
- SPDL (Klink NeurIPS2020, arXiv:2004.11812): adaptive alpha tether to target; implicit contraction.
- PAIRED/UED (Dennis 2020, arXiv:2012.02096) + ACCEL (Parker-Holder ICML2022, arXiv:2203.01302): regret/learnability-based frontier in ENV STRUCTURE (level design).
- DORAEMON itself HAS a backup contraction (when success<alpha) but it is a recovery subroutine, NOT a t_H-style voluntary contract-to-probe. No t_H analog -> never voluntarily contracts to test the boundary.

THEORY VERDICT (RL soundness of "find physical-limit range" curriculum):
- Naive form ("oscillate around a success band to settle at the frontier") is NOT well-posed: a two-sided set-point CONTROLLER on a non-stationary plant -> no fixed objective, no convergence guarantee, prone to LIMIT CYCLES / hunting (policy slow+noisy, controller reacts to a noisy success estimate). DORAEMON avoids exactly this: fixed objective (max entropy), success as a ONE-SIDED floor (not a two-sided band), + KL trust region D_KL(nu_{i+1}||nu_i)<eps as the damping the naive version lacks.
- CRITICAL conceptual error in the framing: it conflates (a) TRUE physical controllability limit (property of dynamics + actuator authority, policy-INDEPENDENT, fixed) with (b) CURRENT policy competence boundary (policy-DEPENDENT, moves outward as the policy improves). A success-thresholded curriculum measures (b), NOT (a). The "frontier" it settles at is a snapshot of where LEARNING stalled, confounded by exploration noise/capacity/reward shaping — not a fixed property of the robot. To characterize (a): reachability / actuator-saturation analysis or a converged-grid slope test, with the policy removed from the loop.
- Intermediate difficulty (success~50%) is good as a SAMPLING heuristic (Florensa) but WRONG as a termination/deployment criterion: a deployable robust policy needs HIGH success across the WHOLE range, not a policy parked at 50% on a self-narrowing range.
- The sound version EXISTS and is SOTA-aligned: regret/learnability-GATED (ACCEL: prefer "solved-sometimes-not-always" = learnable regret, auto-excludes both trivial AND physically-impossible regions) + monotone + trust-region-bounded coverage expansion. Pure success-pushing = minimax/worst-case search -> drives toward uncontrollable regions where 0% is correct and gradients vanish (RARL failure mode, Pinto 2017 arXiv:1703.02702).

RECOMMENDATION if pursued: add ACCEL-style learnability gating ON TOP of DORAEMON's one-sided-floor + KL-trust-region, NOT replace it with a two-sided success oscillator. This is a real design change -> separate planning pass.

VERIFIED: arXiv sources checked 2026-05-27 (IDs above). Source run/analysis: teacher 260525_232805 live-analysis log. Related: `our_doraemon_original_*`, `doraemon_alpha_is_a_feasibility_floor_*`.

