---
title: "DORAEMON difficulty has 3 separable levers: kl_ub (step size), step_interval (dwell-time), max_iterations (number of expansions)"
tags: ["doraemon", "kl_ub", "step_interval", "max_iterations", "performance_lb", "alpha", "curriculum", "dwell-time", "lever", "mechanism", "calibration", "correction", "schedule-bound", "fair-comparison"]
created: 2026-06-14T04:21:12.692273
updated: 2026-07-21T07:57:55.617078
sources: ["diagnose-20260721-164331"]
links: ["kl_ub_0_12_trades_attitude_for_translation_e1_dr_harder.md", "kl_ub_up_and_per_difficulty_learning_are_antagonistic_the_dr_har.md", "curriculum_recalibration_protocol_widening_the_dr_box_requires_r.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
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

---

## Update (2026-07-07T18:59:50.923421)

## CORRECTION (2026-07-08): baseline v2 performance_lb calibration baseline is 68, NOT 90

The "performance_lb tuning note" above anchors the baseline v2 calibration as `lb 90 (legacy
dr_harder, E1 config) -> lb 250`. That baseline is WRONG. Verified against the code SSOT
(config.py:486-499, the live DoraemonCfg override comment, 2026-07-08):

- The attitude_only baseline v2 calibration was **68.0 -> 250.0**, NOT 90 -> 250.
- 90.0 is the performance_lb of a SEPARATE campaign (legacy dr_harder E1); it is not the
  calibration baseline for the shipped attitude_only default. Do not conflate the two.
- The 250 value is the **p25 of the recon run's actual episode-return distribution**
  (run `trpo_baseline_260608_160453`, lb=68, 1146 iter; DORAEMON buffer n=2000:
  min=81.9 / p5=227 / p25=250 / median=264 / p95=291).
- Why lb=68 failed: it sat BELOW the minimum observed return (81.9), so success=return>=68
  was always 1 -> the feasibility constraint Ghat>=alpha was inert -> the curriculum widened
  DR unconstrained (no self-pacing). lb=250 (p25) puts the STARTING success_rate at ~0.65
  (above alpha=0.5 so DR still expands, but the signal is live again instead of pinned at 1).
- Chosen BELOW the median (264) on purpose: so a reward plateau cannot drag success_rate to 0,
  which would shrink the DR range.
- Companion lever: kl_ub 0.06 -> 0.12 was moved TOGETHER with the lb raise by design (doubles
  the per-step trust region to compensate for the slower expansion the raised lb induces).
  lb alone makes DR easier; kl_ub alone leaves success_rate pinned at 1.

The "tune lb by whether success_rate settles at alpha" PRINCIPLE in the note remains correct;
only the numeric calibration baseline (90 -> 68) and the p25 provenance are corrected here.

VERIFIED: config.py:486-499 (live DoraemonCfg override + calibration comment with the full
return-distribution percentiles); doraemon.py:39 (engine default 80.0, stale for ALBC). The
code comment is the primary source for the 250 provenance.

---

## Update (2026-07-21T07:57:55.617078)


## EMPIRICAL CONFIRMATION 2026-07-21 (A3 vs anchor) — expansion is SCHEDULE-bound, not success-bound

[FINDING] In the `teacher_baseline_posttam` config every DORAEMON update SATURATES the kl_ub
trust region, so the three levers reduce to a fixed schedule in practice: 18 updates at iters
500..4750 in steps of 250, each with `DORAEMON/kl_step` == 0.1200 exactly (== kl_ub). The
success rate does NOT modulate the step once it clears the alpha floor.
[EVIDENCE: TB DORAEMON/kl_step nonzero at 18 identical iterations, value 0.12 at every one, in
BOTH trpo_minstdthr008_260721_064149 and trpo_biasema_260715_142543, despite terminal
success_rate 0.8138 vs 0.8773; analysis diagnose-20260721-164331 §doraemon]
[CONFIDENCE: HIGH]

[FINDING] Consequence 1 (USE THIS): runs in this campaign train in a BIT-FOR-BIT IDENTICAL DR
box, so cross-run eval deltas are attributable to the policy, never to a different curriculum.
Terminal Beta compared elementwise: max abs diff dist_a 5.0e-06, dist_b 4.7e-05 (np.allclose
True). This was independently reproduced by diffing the two runs' curriculum_trajectory.json.
[EVIDENCE: doraemon_state.pt dist_a/dist_b of both runs; analysis diagnose-20260721-164331 §doraemon]
[CONFIDENCE: HIGH]

[FINDING] Consequence 2 (STOP DOING THIS): "DORAEMON health" cannot discriminate runs in this
config. success_rate, ess_ratio and mode are READOUTS of an identical curriculum, not
per-run outcomes — a 7.2% success-rate gap changed nothing about the DR box. Reporting
DORAEMON health as a first-class per-run outcome is uninformative here.
[EVIDENCE: success_rate 0.8138 vs 0.8773 with identical terminal Beta; DORAEMON/entropy_before
== entropy_after == -22.7017 in both runs (static readout, not a per-update measurement)]
[CONFIDENCE: HIGH]

[FINDING] At 5000 iterations the box is NOT exhausted: 0 of 20 params at the Beta(1,1) ceiling
(17 params ~a=b=1.7-1.9, 3 params at a=1.0/b~6.2-6.6). Box exhaustion is an 8000-iter
phenomenon, not a 5000-iter one.
[EVIDENCE: doraemon_state.pt per-parameter Beta(a,b), both runs; cf the Z2 saturation table on
[[curriculum_recalibration_protocol_widening_the_dr_box_requires_r]]]
[CONFIDENCE: HIGH]

