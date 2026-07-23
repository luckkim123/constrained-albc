---
title: "DORAEMON _optimize_entropy accept can leak the success floor (latent divergence from reference, dead path so far)"
tags: ["doraemon", "floor-leak", "optimize-entropy", "impl-vs-ref", "latent-bug", "teacher"]
created: 2026-07-06T02:12:16.207679
updated: 2026-07-23T07:42:44.174065
sources: ["trpo_main_teacher_260525_232805"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
---

# DORAEMON _optimize_entropy accept can leak the success floor (latent divergence from reference, dead path so far)

Our marinelab DORAEMON `_optimize_entropy` accept condition is a LATENT divergence from the reference implementation: it can accept a distribution with success < alpha (a floor leak), where the reference never does. Not a bug that has bitten yet — a dead path under normal (success >> alpha) conditions — but a real risk for FUTURE harder runs that push success near alpha.

MECHANISM (code read 2026-05-27):
- ours (`marinelab/marinelab/algorithms/doraemon.py:637`): `if result.success or (result.fun < init_obj and kl_val <= kl_ub): accept`. The OR-branch accepts a NON-converged SLSQP result on "entropy improved + KL ok" WITHOUT re-verifying the perf constraint success >= alpha.
- reference (`references/doraemon/doraemon/doraemon.py:920`): `if not (all(constraints_satisfied) and result.fun < old_f): keep old`. Ref requires ALL constraints (incl. perf_ineq) satisfied AND improvement, else rollback. Ref therefore never accepts a perf-violating distribution; ours can via the OR-tail.
- RISK: a dist with success < alpha can be accepted through the OR-branch. When success >> alpha (feasible regime, mode=0) the first branch `if result.success` accepts immediately and the risky OR-tail is never reached — so it only matters when SLSQP fails to converge AND success is near alpha.

WHY IT DID NOT BITE (teacher 260525_232805, verified via doraemon_state.pt replay + TB step-level):
- 20 DORAEMON optimization events (every 250 iter): 19 updates mode=0 (feasible-expand) + 1 mode=-3 (init, no dist accepted). mode=1/-2 (infeasible/inverted) NEVER fired. Every accepted update had success_rate 0.66 (step250) then 0.96-0.99 — 0 accepts below alpha=0.5.
- REPLAY: reconstructed `_optimize_entropy` from final Beta a/b + 2000-ep ring buffer, ran SLSQP -> result.success=TRUE, perf@sol=+0.95, KL=0.06 (full budget), entropy improved. So the normal regime converges cleanly and takes the first (safe) branch; our code == ref there. LIMITATION: only the final snapshot was replayable, not each of the 19 updates.

FIX CANDIDATE (cheap safety belt, NOT urgent): tighten `doraemon.py:637` accept to also re-verify `perf_ineq >= 0` (mirror ref's all-constraints-satisfied gate). This closes the leak for future high-alpha / high-kl_ub runs where success sits near the floor.

RELATED harmless diffs found in the same 2026-05-27 impl-vs-ref comparison:
- DIFF1 [HARMLESS]: ours objective = `max H(phi)` vs ref `min KL(phi||uniform)` — mathematically EQUIVALENT when target=uniform (see wiki `our_doraemon_original_*`). Ours hardcodes target=uniform, drops ref's prior_constraint. Fine.
- DIFF3 [LOW, guarded]: IS denominator = prev_dist over ring buffer (ours l.425/489) vs ref fresh data on current_distr (l.598). Justified (ring buffer ~ prev_dist, IS weights ~1) + ESS gate reverts on low estimator quality (l.460). This run ess_ratio min 0.865 -> no reverts, bias did not materialize.

VERIFIED: code read 2026-05-27 (ours l.637/425/489/460; ref l.920/598); doraemon_state.pt SLSQP replay; TB step-level leak-check (0/19 sub-floor accepts). Source run: trpo_main_teacher_260525_232805.

---

## Update (2026-07-13T05:19:13.182854)

[STATUS] already-fixed (verified 2026-07-13, post-p7_tail planning session). The proposed 1-line fix IS in the code: marinelab commit ef46cb7 ('fix(doraemon): re-verify perf floor in _optimize_entropy accept condition', 2026-05-27) gates the OR-accept branch on perf_ok = perf_ineq(result.x) >= 0.0 (marinelab/algorithms/doraemon.py:653-654), an ancestor of current HEAD. Combined with the earlier replay evidence (0/19 sub-floor accepts on the teacher run), this item is CLOSED — drop it from candidate rosters. The page's 'FIX CANDIDATE ... NOT urgent' phrasing predates the fix landing.

---

## Update (2026-07-23T07:42:44.174065)

2026-07-23 curation: status set to resolved -- body states this item is CLOSED/already-fixed (verified 2026-07-13); body kept as durable design-history.
