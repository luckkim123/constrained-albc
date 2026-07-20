---
title: "Cross-run DR comparability: eval.py --doraemon-dr-from already provides a common test distribution; p7_tail knew and declined, judging a robustness campaign on nominal-only"
tags: ["eval", "comparability", "doraemon-dr-from", "common-exam", "confound", "methodology", "p7-tail", "e4", "demonstrated"]
created: 2026-07-16T06:00:00.285512
updated: 2026-07-20T03:15:55.206233
sources: ["diagnose-20260716-164016"]
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-experiment
---

# Cross-run DR comparability: eval.py --doraemon-dr-from already provides a common test distribution; p7_tail knew and declined, judging a robustness campaign on nominal-only

# Cross-run DR comparability: `--doraemon-dr-from` ALREADY EXISTS; p7_tail chose not to use it

User challenge (2026-07-16): "each run's final DORAEMON DR differs so cross-run comparison is called
impossible -- we need to build a comparable methodology; you can't judge on `none` alone."

Correct on both counts. The methodology does not need building -- it was built for an earlier campaign
and then not used.

[FINDING] `eval.py` already ships `--doraemon-dr-from <run_dir>`, which loads the DORAEMON DR from a
DIFFERENT run and grades the evaluated policy on it, giving every variant a COMMON test distribution.
Its own help text states the purpose verbatim: "Used to evaluate all ablation variants on the r13_A
baseline's learned DR distribution (common test distribution)"; the call-site comment adds "so
cross-variant comparisons are not confounded by per-variant curriculum drift".
[EVIDENCE: eval.py:124-131 (arg def), eval.py:1113-1130 (override branch: load_doraemon_dr(dr_source)
-> _DORAEMON_FULL_DR/_DORAEMON_RAW, "Hard DR = DORAEMON-learned distribution from override
(mean +/- 2*std)"); raises FileNotFoundError on a bad path and RuntimeError if the source dir has no
DORAEMON TB tags]
[CONFIDENCE: HIGH]

[FINDING] The p7_tail campaign KNEW about it and declined. e3's report section 3 writes: "A
shared-distribution re-eval (`--doraemon-dr-from baseline`) could quantify the hard-exam tail exactly,
but is not needed for the verdict". Instead the campaign wrote README section 2 -- a prose
comparability gate cataloguing per-run confound DIRECTIONS (e1 inflates, e2/e4 understate, e3 shrinks
its deficit) -- and anchored every verdict to `none`. Cost of the alternative: one extra 64-env eval
per run.
[EVIDENCE: e3 report diagnose-20260714-084409 section 3 FINDING; teacher_baseline_opt/README.md
section 2 confound-direction table]
[CONFIDENCE: HIGH]

# Why `none`-only judging is the deeper defect

[FINDING] `none` is fixed NOMINAL physics. Anchoring a DR-ROBUSTNESS campaign's verdicts to `none`
judges the campaign on the one condition it does not deploy in, discarding every robustness
measurement. This plausibly mis-judged e4: e4 shrank the hard-DR roll tail 23.2x -> 10.5x (top-6
48.7% -> 29.4%) AND did it on a HARDER self-exam, yet was DISCARDED on a 1.34x `none` att_norm
regression. A common-exam re-eval could flip that verdict; it was never run.
[EVIDENCE: teacher_baseline_opt/README.md section 3 e4 row (roll H1 success / pitch H2 load-bearing
/ 판정 SPLIT, 폐기); README section 2 lists e4's confound as "이득을 과소평가"]
[CONFIDENCE: MED]

# Gaps to close before adopting the flag as the standard (do NOT just turn it on)

[FINDING] The flag's anchor is a LIVE artifact, not a frozen spec: it points at a run dir and reads
`DORAEMON/mean/*` from that run's TB event file. Anchoring to "the baseline's final DR" therefore
MOVES the exam whenever the baseline is retrained -- and a post-TAM baseline retrain is exactly what is
pending, which would silently re-break comparability against every eval taken against the old anchor.
[EVIDENCE: eval.py:1117-1130 dr_source = args_cli.doraemon_dr_from -> load_doraemon_dr(dr_source),
requires a TB event file with DORAEMON/mean/* scalars in that dir]
[CONFIDENCE: HIGH]

Requirements for a durable common-exam methodology:
1. FREEZE the reference DR as a static, version-controlled spec (JSON/config), not a run-dir pointer,
   so the exam is reproducible and survives baseline retrains.
2. The anchor SHOULD be a deployment-realistic fixed DR, not any run's learned DR -- a run's final DR
   is just where that run happened to land, so anchoring to it is arbitrary. BLOCKED: no defensible DR
   band exists yet -- see [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]]
   (blocked_on: "source a defensible TAM moment-arm / max_thrust DR band (no load cell to measure)").
3. Record the DR SOURCE as provenance in the eval output, or a later reader cannot tell which exam a
   given `hard` number came from.

[FINDING] SCOPE LIMIT -- a common exam fixes the MEASUREMENT confound only. The compared policies are
still optima of DIFFERENT training distributions (the TRAINING confound), which no eval flag can
remove; that one is fixed at design time by holding the training DR fixed and moving one variable.
This distinction is what teacher_baseline_opt README section 2 misses: it treats "only `none` is a fair
exam" as if it made the two POLICIES a same-config/different-budget pair, which it does not.
[EVIDENCE: e3 report section 0 (e3 end-DR 4.7x wider on ocean_current than baseline) -- the two
policies optimised different objectives, so a fair exam still compares unlike candidates]
[CONFIDENCE: HIGH]

# Decision / next experiment (lead)

LEAD: adopt `--doraemon-dr-from` + a FROZEN reference-DR spec as the campaign-standard eval for any
cross-run comparison, replacing the prose confound-direction gate. Cheapest first probe: re-eval the
existing e2/e4 checkpoints on the baseline's DR (one 64-env eval each, no retrain, checkpoints already
on disk) and check whether e4's roll-tail win survives a common exam -- that is the campaign's only
proven tail lever and it was discarded on a `none`-only verdict.
Sequencing note: do this BEFORE the post-TAM baseline retrain moves the natural anchor, or freeze the
anchor spec first.

---

## Update (2026-07-16T06:54:18.179347)

## Update (2026-07-16): the e4 re-eval probe is RETIRED (user closed the prune direction); the methodology lead survives

[DECISION] User (2026-07-16) FULLY rejected e4 and the entire xy-offset prune direction, including the
`_y`-only refinement — see [[xy_offset_dr_is_load_bearing_for_pitch_not_free_ndims_dilution_e]].
Rationale: the manufacturing tolerance those DR dims model is physically real on the hardware, so there
is no reason to delete them; NDIMS economy does not justify un-modelling a real disturbance.
[CONFIDENCE: HIGH — user domain judgment]

CONSEQUENCE for this page: its "cheapest first probe" — re-eval the e4 (and e2) checkpoints on the
baseline's DR to test whether e4's roll-tail win survives a common exam — is RETIRED **as an
e4-motivated probe**. That probe existed to answer "was e4 mis-discarded on a `none`-only verdict?"; with
the prune direction closed by decision, its answer cannot change what we do. Do not queue it as the
methodology's first demonstration.

WHAT REMAINS VALID AND UNCHANGED (do not let the e4 retirement take these with it):
- The core defect this page identifies — anchoring a DR-ROBUSTNESS campaign's verdicts to `none` (fixed
  nominal physics) judges the campaign on the one condition it does not deploy in — is INDEPENDENT of
  e4. e4 was the illustration, not the argument.
- The three durable-methodology requirements still stand: (1) FREEZE the reference DR as a static,
  version-controlled spec rather than a live run-dir pointer; (2) the anchor should be a
  deployment-realistic fixed DR, not any run's learned DR (still BLOCKED on a defensible DR band, see
  [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]]); (3) record the DR source as
  provenance in the eval output.
- The SCOPE LIMIT still stands: a common exam fixes the MEASUREMENT confound only, never the TRAINING
  confound (compared policies remain optima of different training distributions).

NEW FIRST DEMONSTRATION NEEDED: this lead now lacks a cheap, decision-relevant first probe. Whatever
replaces it must be a comparison we would actually act on. Keep `status: needs-experiment`, but note the
motivating probe changed — do not re-inherit the e4 framing when this lead is next picked up.

---

## Update (2026-07-16T07:48:29.230002)

## Update (diagnose-20260716-164016): the NEW FIRST DEMONSTRATION this lead needed now EXISTS.

P-B1 (trpo_biasema_260715_142543) was graded on the REFERENCE trpo_baseline_260714_192020 learned DR via --doraemon-dr-from (eval static_260716_160156) -- the first shared-exam eval in the workspace. Anchor verified directly: data_hard.npz dr_* box matches the reference eval exactly (mismatch 0.00000) and differs from the self-DR eval (7.90261) -- proving the anchor moved, which the none sanity gate alone (anchor-invariant) cannot.

RESULT: P-B1's self-exam hard-roll regression (0.717->0.928) was a MEASUREMENT artifact -- on the common exam P-B1 scores 0.5950 vs REF 0.7167 (17% better). Only the transient peak survives (hard roll n_gt20 8.667 vs 6.667). This demonstrates exactly the defect this page names: a self-anchored hard number can invert under a fair exam.

SCOPE LIMIT re-confirmed empirically: the training confound is REAL and large -- P-B1's learned DR is wider on 20/20 params (variance ratio mean 2.23x). So the common exam fixed measurement, not training-distribution difference, exactly as this page states. Full detail: page p_b1_shared_exam_on_reference_dr_hard_roll_floor_was_exam_artifa and report diagnose-20260716-164016. status stays needs-experiment: the curriculum-replay arm (hold training DR fixed, move only observation) is the remaining probe to assign causation.

---

## Update (2026-07-20T03:15:55.206233)

## Audit re-scope (2026-07-20, backlog audit)

The ORIGINAL ask is DONE: the shared-exam methodology was demonstrated. P-B1
(`trpo_biasema_260715_142543`) was evaluated on the reference run's learned DR via `--doraemon-dr-from`
(eval `static_260716_160156`, report `diagnose-20260716-164016`), showing a self-anchored hard-number
can INVERT under a fair exam (P-B1 hard-roll 0.5950 vs REF 0.7167 on the common exam, against a
0.717->0.928 self-exam reading).

REMAINING SCOPE -- this page stays open ONLY for the narrower follow-on: the curriculum-replay arm
(hold training DR fixed, move only the observation) to assign causation between measurement-confound and
training-confound. The tooling already exists and is unused for this purpose: `CurriculumReplayer` +
`--replay_curriculum_path` in `marinelab/algorithms/doraemon.py` (commits ecc5c88/ff7c0bc/b1b76db,
2026-06-05, built for an earlier purpose); no run dir or report uses it for this discrimination.

WATCH: this page's own warning still stands -- a post-TAM baseline retrain moves the DR anchor and
silently re-breaks comparability.
