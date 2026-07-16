---
title: "Cross-run DR comparability: eval.py --doraemon-dr-from already provides a common test distribution; p7_tail knew and declined, judging a robustness campaign on nominal-only"
tags: ["eval", "comparability", "doraemon-dr-from", "common-exam", "confound", "methodology", "p7-tail", "e4"]
created: 2026-07-16T06:00:00.285512
updated: 2026-07-16T06:00:00.285512
sources: []
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
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

