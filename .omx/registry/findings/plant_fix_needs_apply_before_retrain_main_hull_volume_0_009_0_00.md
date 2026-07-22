---
title: "PLANT FIX (needs-apply-before-retrain): main hull volume 0.009 -> 0.00790 recenters sim net buoyancy +10.25 N -> neutral, matching 2026-07-06 onboard measurement"
tags: ["buoyancy", "plant-fix", "sim-to-real", "net-buoyancy", "hull-volume", "pre-retrain-gate", "marinelab", "teacher-baseline", "user-decision", "partial-correction", "launch-gate", "measured", "applied", "buoyfix"]
created: 2026-07-16T12:13:44.284365
updated: 2026-07-22T04:52:11.692425
sources: ["onboard_measured_2026_07_06", "albc.py:64", "paper-spec-table"]
links: ["onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7.md", "open_actionable_ledger_read_before_any_sim_plant_code_change_or_.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "UNBLOCKED 2026-07-21: both user questions closed (buoy-net reading settled via URDF geometry; operated dry mass MEASURED 10.592 kg with buoy attached, no ballast -> mass model correct within 0.22%, so the fix is volume-only as scoped). Remaining is SEQUENCING, not information: apply only AFTER the last Stage-A eval (A4, then A5), because marinelab is a shared editable install and a mid-Stage-A swap would eval old-plant policies on the new plant. Still to decide: new run_group/wandb purpose vs teacher_baseline_posttam."
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
- Implication: every teacher_baseline_posttam run trained so far (incl. the currently-running trpo_biasema_extend8k_260716_162849) carries the +10.25 N wrong buoyancy. If that campaign is meant as the corrected-plant reference baseline, this repeats the 2026-07-14 teacher_baseline_opt known-wrong-plant incident. See [[open_actionable_ledger_read_before_any_sim_plant_code_change_or__]].

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

---

## Update (2026-07-21T03:36:25.873280)

## RESOLVED 2026-07-21: user measurement confirms the volume-only fix; both open user questions are now closed

[FINDING] The real vehicle's operated dry mass is 10.592 kg, measured by the user 2026-07-21
with the buoy ATTACHED (weighed in the as-deployed configuration) and with NO ballast fitted.
[EVIDENCE: user measurement 2026-07-21, compared against this page's own sim weight budget]
- sim total weight = main 90.06 N + buoy 9.12 N + arm 4.92 N = 104.10 N = 10.615 kg
- measured                                                              = 10.592 kg
- delta = -0.023 kg = **-0.22%**
[CONFIDENCE: HIGH -- single arithmetic comparison of a measured scalar against code-sourced weights]

[FINDING] The sim's MASS model is therefore correct, and the +10.25 N (+1.045 kgf) positive
net buoyancy is attributable ENTIRELY to hull volume -- the fix scoped on this page stands
unchanged.
[EVIDENCE: the two candidate branches were designed to be far apart, and the measurement
lands cleanly on one of them]
- volume-error branch (mass correct): predicted total 10.615 kg -- measured is 0.22% off it
- mass-error branch (neutrality from extra mass): would have required ~11.5-12 kg, i.e. the
  measurement would have had to sit ~+9% above the sim's main+arm figure
[CONFIDENCE: HIGH]

### Both blockers on this page are now closed

1. `||F_bu|| = 1.835 kgf` interpretation -- SETTLED 2026-07-21 as the BUOY net-buoyancy
   reading, on URDF geometry (the modelled R=0.085 / H=0.118 cylinder = 0.00268 m^3 matches
   NET's 0.00277 and contradicts TOTAL's 0.00184). So the error is the hull's.
2. Operated dry mass -- MEASURED, this update. 10.592 kg, buoy included, no ballast.

Ballast: the user confirms **none is fitted**, so the "unmodelled ballast" concern raised
when this page was written does not apply. Nothing is missing from the mass budget.

### The fix, unchanged from the original scope

- `marinelab/marinelab/assets/albc/albc.py:64` -- `ALBCHydrodynamicsCfg.volume` 0.009 -> 0.00790
- `albc.py:120` -- `ALBCBuoyHydrodynamicsCfg.volume` stays 0.00268 (buoy already correct)
- `constrained-albc envs/main/config.py` volume_scale 0.75~1.25 DR range -- unchanged
- constrained-albc needs no code change; this is marinelab-only

### SEQUENCING HAZARD -- do not apply while Stage A is still being evaluated

marinelab is an editable install shared by every run on this machine. Applying the volume
change to the working tree while Stage-A runs are still awaiting eval would make those evals
execute on the NEW plant while the policies were TRAINED on the OLD one, silently invalidating
their verdicts. The change therefore lands only AFTER the last Stage-A run has been evaluated
(A4 `trpo_privslim24d_260721_114717`, then A5). Prepare it on `exp/buoyancy-recenter` off tag
`baseline-260716-buoyancy`, and leave the working tree on main until then.

Still-open decision before the first Stage-B launch: whether the refreshed plant runs under
the existing `teacher_baseline_posttam` purpose or a NEW run_group/wandb-project name. The
plant change breaks `none`-level comparability with the posttam series, which argues for a
new purpose.

---

## Update (2026-07-21T03:37:54.802930)

(status refresh only -- the measurement, the arithmetic, and the sequencing hazard are in the 2026-07-21 RESOLVED section above)

---

## Update (2026-07-22T04:52:11.692425)


## APPLIED 2026-07-22 (apply-gate CLOSED, status -> resolved)

Applied after ALL Stage-A evals completed (A1-A5 done, seed floor done). Change:
`marinelab/marinelab/assets/albc/albc.py` `ALBCHydrodynamicsCfg.volume` 0.009 -> 0.00790.
- marinelab branch `exp/buoyancy-recenter`, commit **7d45c2c**; pre-fix baseline tag
  `baseline-260716-buoyancy` (rule-02 isolation, main untouched).
- Verified: net-neutral hull 0.00790 + buoy 0.00268 = 0.01058 m^3 -> 103.6 N ~= weight
  104.10 N; live-run `DR/buoyancy_force_mean` reads ~78 N (was ~88).
- Corrected-plant campaign LAUNCHED under wandb purpose **`teacher_baseline_buoyfix`**
  (user decision 2026-07-22: NEW name, since the plant change breaks none-level
  comparability with the `teacher_baseline_posttam` series). 3-seed paired-seed anchor
  (seeds 30/31/32) started on the workstation.
- DGX must HAND-REPLICATE the one-line fix (workstation<->DGX transfer is artifacts-only);
  see `/workspace/.sp/plans/2026-07-22-DGX-handoff-e3-scaleup.md`.

PHYSICAL NOTE (open sub-thread): 0.00790 < the earlier geometric "pure cylinder 0.00827"
estimate, so that geometric figure is suspect (likely over-estimated). This value is
EMPIRICAL (measurement-matched net buoyancy), not derived. Upgrade path: a real hull
displacement measurement to reconcile the geometric estimate.

