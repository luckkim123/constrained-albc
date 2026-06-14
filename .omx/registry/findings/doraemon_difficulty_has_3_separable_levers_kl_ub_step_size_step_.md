---
title: "DORAEMON difficulty has 3 separable levers: kl_ub (step size), step_interval (dwell-time), max_iterations (number of expansions)"
tags: ["doraemon", "kl_ub", "step_interval", "max_iterations", "performance_lb", "alpha", "curriculum", "dwell-time", "lever", "mechanism"]
created: 2026-06-14T04:21:12.692273
updated: 2026-06-14T04:21:12.692273
sources: []
links: ["kl_ub_0_12_trades_attitude_for_translation_e1_dr_harder.md", "kl_ub_up_and_per_difficulty_learning_are_antagonistic_the_dr_har.md"]
category: reference
confidence: high
schemaVersion: 1
---

# DORAEMON difficulty has 3 separable levers: kl_ub (step size), step_interval (dwell-time), max_iterations (number of expansions)

# DORAEMON difficulty has 3 separable levers: kl_ub (step size), step_interval (dwell-time), max_iterations (number of expansions)

Code-verified mechanism of how DORAEMON curriculum difficulty is driven, from a user mental-model check (2026-06-14). SSOT = marinelab/marinelab/algorithms/doraemon.py:38-49 (DoraemonCfg) + :406-420 (update gate). All four user-named concepts map to real cfg fields; verified by direct code read.

## The cfg fields (doraemon.py:38-49)
- `performance_lb` (:39, default 80.0) = "episode return threshold for binary success". An episode counts as success iff episode_return >= performance_lb (:306). This is the ABSOLUTE-return difficulty gate, NOT normalized -- so its effect depends on the reward ceiling.
- `alpha` (:40, default 0.5) = desired IS-estimated success rate; the feasibility floor `Ghat >= alpha` (:616). DORAEMON widens only while success stays above alpha.
- `kl_ub` (:41, default 0.5; teacher/legacy ran 0.06) = "Trust region KL upper bound PER STEP". Caps how far the Beta(a,b) distribution can move in ONE update. = expansion STEP SIZE.
- `step_interval` (:43, default 250) = "RL iterations BETWEEN DORAEMON updates". Between updates the policy trains on the frozen current DR distribution (:406-408 comment: "matches the reference's train-for-N-steps-then-update structure"). = per-difficulty DWELL-TIME.
- `max_iterations` (train arg, all dr_harder runs locked at 5000) = total RL iterations.

## The update gate (doraemon.py:416)
`if self._step_count % self.cfg.step_interval != 0: return`  -- the distribution is widened ONLY once every step_interval iterations. So over a whole run the number of expansions is:

    n_expansions = max_iterations / step_interval     (e.g. 5000/250 = 20)

and the reachable final difficulty is roughly:

    final_difficulty ~= (max_iterations / step_interval) * (per-step width, capped by kl_ub)

This is exactly the user's formula "update_time = max_iter / iter_per_step" -- where the user's unnamed "iter per step" IS step_interval.

## Why this matters: 3 INDEPENDENT levers to raise final difficulty, different side-effects
| lever | raising it does | side-effect |
|---|---|---|
| kl_ub UP | bigger jump per expansion | under-trains each difficulty -> attitude collapse (E1 proved this, see [[kl_ub_0_12_trades_attitude_for_translation_e1_dr_harder]]) |
| max_iterations UP | more expansions (n_expansions rises) | none on the curriculum itself; only wall-clock cost. Reaches farther WITHOUT touching dwell-time |
| step_interval UP | longer training per difficulty | at fixed max_iter, FEWER expansions -> LOWER final difficulty (trades reach for thoroughness) |

CORRECTION to [[kl_ub_up_and_per_difficulty_learning_are_antagonistic_the_dr_har]]: that page said "kl_ub-up SHRINKS dwell-time per difficulty". More precisely: DWELL-TIME is owned by step_interval, not kl_ub. kl_ub is step SIZE, step_interval is dwell-TIME -- they are SEPARATE fields. kl_ub-up doesn't literally shorten step_interval; it makes each expansion bigger so the policy faces a larger distribution jump within the same (unchanged) dwell window -> effectively under-trained relative to the harder distribution. The antagonism conclusion stands; the mechanism is "bigger jump per fixed dwell", not "shorter dwell".

## performance_lb tuning note
performance_lb is an absolute return threshold (:39), so lb 90 (legacy dr_harder, E1 config) -> lb 250 (attitude_only baseline v2) is non-linear in "how hard it is to be counted success" because it interacts with the reward ceiling. Symptom of a WELL-tuned lb: success_rate converges to alpha=0.5 (the env is genuinely stressed). Symptom of TOO-LOW lb: success ~0.97 >> alpha (teacher) -> DORAEMON thinks it has slack -> expands endlessly (the legacy dr_harder failure mode the user described). So tune lb by the criterion "does success_rate settle at alpha at convergence", not by the absolute value.

VERIFIED: doraemon.py:38-49 (cfg fields + defaults), :306 (binary success = return>=lb), :406-420 (step_interval update gate), :616 (Ghat>=alpha floor); E1 config/agent.yaml (kl_ub 0.12, performance_lb 90.0, max_iterations 5000); attitude_only baseline lb=250. Source: user mental-model check 2026-06-14.

