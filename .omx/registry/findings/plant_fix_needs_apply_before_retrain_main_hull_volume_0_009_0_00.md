---
title: "PLANT FIX (needs-apply-before-retrain): main hull volume 0.009 -> 0.00790 recenters sim net buoyancy +10.25 N -> neutral, matching 2026-07-06 onboard measurement"
tags: ["buoyancy", "plant-fix", "sim-to-real", "net-buoyancy", "hull-volume", "pre-retrain-gate", "marinelab", "teacher-baseline", "user-decision", "partial-correction", "launch-gate"]
created: 2026-07-16T12:13:44.284365
updated: 2026-07-16T12:16:54.623772
sources: ["onboard_measured_2026_07_06", "albc.py:64", "paper-spec-table"]
links: ["onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7.md", "open_actionable_ledger_read_before_any_sim_plant_code_change_or.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: needs-apply-before-retrain
blocked-on: "user must (1) confirm paper ||F_bu||=1.835 kgf is buoy-net vs total-displacement interpretation, (2) decide run_group naming; DEFERRED to next-gen plant refresh -- does NOT block posttam continuation (user decision 2026-07-16)"
---

# PLANT FIX (needs-apply-before-retrain): main hull volume 0.009 -> 0.00790 recenters sim net buoyancy +10.25 N -> neutral, matching 2026-07-06 onboard measurement

PLANT FIX registered for the next-experiment stack (handed off from another session 2026-07-16, code-verified here). Sim system net buoyancy nominal is +10.25 N (+1.045 kgf positive) but the real vehicle is NEUTRAL (onboard measured). Single-variable root cause: main hull volume too large.

## Evidence
- Sim system net buoyancy nominal = +10.25 N (+1.045 kgf positive) = main(B 88.1, W 90.06) + buoy(B 26.2, W 9.12) - arm(W 4.92).
- Real system net buoyancy = NEUTRAL, onboard measured 2026-07-06 (agent-jetson edd735c), |F_net| <= 3 mN = 0.011% of buoy buoyancy. See [[onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7]].
- Paper spec table: Mini-ROV weight-in-water 1.30 kgf, ALBC ||F_bu|| 1.835 kgf.
- Discriminating check (single-variable confirmation): sim buoy net buoyancy 17.1 N = 1.745 kgf already matches paper ||F_bu|| 1.835 within 5%. Fixing hull ONLY to weight-in-water 1.30 kgf (V 0.009 -> 0.00790) moves system net +10.25 -> -0.56 N ~= NEUTRAL, matching the measurement. So the +10 N error is entirely main hull volume; the buoy is already correct.

## Code verification (this session, against CODE not manifest)
- marinelab/marinelab/assets/albc/albc.py:64 `ALBCHydrodynamicsCfg.volume = 0.009` -- CONFIRMED present (the wrong value).
- marinelab/marinelab/assets/albc/albc.py:120 `ALBCBuoyHydrodynamicsCfg.volume = 0.00268` -- CONFIRMED present (the correct value, keep).
- Implication: every teacher_baseline_posttam run trained so far (incl. the currently-running trpo_biasema_extend8k_260716_162849) carries the +10.25 N wrong buoyancy. If that campaign is meant as the corrected-plant reference baseline, this repeats the 2026-07-14 teacher_baseline_opt known-wrong-plant incident. See [[open_actionable_ledger_read_before_any_sim_plant_code_change_or_]].

## FIX (single variable, minimum-change)
- File: marinelab/marinelab/assets/albc/albc.py
- `ALBCHydrodynamicsCfg.volume`: 0.009 -> 0.00790 (m^3; grounded in paper weight-in-water 1.30 kgf).
- `ALBCBuoyHydrodynamicsCfg.volume`: DO NOT change (keep 0.00268 -- buoy net buoyancy already correct).
- DR range (constrained-albc envs/main/config.py volume_scale 0.75~1.25): DO NOT change. Recentering nominal alone makes the DR box straddle neutral instead of +1.2 kgf.
- Update the buoyancy numbers in albc.py:62-64 and :119 comments to the new value.
- Code change is marinelab-only (constrained-albc unchanged).

## Isolation procedure (rules/02, comparison experiment)
- Baseline tag FIRST: `git -C marinelab tag -a baseline-260716-buoyancy -m "pre buoyancy-recenter; compares vs measured-neutral"`.
- Exp branch: `git -C marinelab checkout -b exp/buoyancy-recenter` (never edit main directly).

## Verification (completion criteria)
1. After load, compute system net buoyancy -> |net| < a few N (neutral), compare against the 2026-07-06 onboard measurement.
2. ONE clarification required from the user before apply: is paper ||F_bu|| 1.835 kgf the BUOY net buoyancy (correct, this fix stands) or the TOTAL displacement buoyancy (then the buoy also needs a fix + there is an unmodeled arm-buoyancy gap)? The measured-neutral result supports the net-buoyancy reading, but final call is user domain knowledge.

## Naming (user decision, do not choose arbitrarily)
- run_group = log_project_name (same string). Currently-open purpose = teacher_baseline_posttam. User must decide whether the buoyancy fix is the SAME corrected-plant teacher baseline purpose or a NEW purpose before launch.

## Launch gate
- No auto-launch. Queue only via `omx queue-launch` (human approval gate).
- 3 other needs-apply-before-retrain HARD gates still open (tam_vertical, imu_45deg_offset, sim_hydro TAM/max_thrust DR band); omx queue-launch refuses until each is applied or `--ack-gate <slug>`.

---

## Update (2026-07-16T12:16:54.623772)

## Update (2026-07-16): user decision -- posttam campaign INTENTIONALLY continues on the pre-buoyancy plant

[DECISION] User (2026-07-16): let the running ITEM 1 (trpo_biasema_extend8k_260716_162849) finish AND keep proceeding with subsequent teacher_baseline_posttam launches on the current plant. Rationale: "too many variables is a problem" -- the posttam series (P-A8 -> P-B1 -> extend -> P-B7 ...) is a within-plant comparison chain; injecting a buoyancy plant change mid-series would break its comparability. The buoyancy fix therefore stays REGISTERED here but does NOT block the posttam campaign's continuation.
[CONFIDENCE: HIGH -- user domain decision]

CONSEQUENCE for the launch gate: a running/continuing teacher_baseline_posttam launch WITH this buoyancy lead still open is EXPECTED and user-approved -- it is a DOCUMENTED partial-correction posture, NOT the 2026-07-14 silent-wrong-plant incident. Do not treat posttam continuation as a gate violation. The buoyancy fix (and the same-posture TAM/IMU/sim_hydro gates) apply to a DELIBERATE next-generation plant refresh, not to the in-flight posttam series. The within-plant comparison is valid because the buoyancy error is common-mode across every posttam run.

