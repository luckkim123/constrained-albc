# From-scratch re-diagnosis before Phase-1 rewrite: latency reconciled, FTC lever is sampler-shape, gates need 2 seeds, J1 soft-only

- id: handoff/302 · date: 2026-09-02 · author: mac-session
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: none
- summary: Fresh primary-source pass: obs staleness closed by firmware so the open gap is the untrained action delay; disturbance/fault weakness is a DORAEMON clamp+budget artifact whose naive severity-widening already backfired (lever=sampler shape); every gate needs >=2 seeds; J1 has a soft cost but no hard rail. PLAN banner stands, nothing launched.

From-scratch re-diagnosis of the retrain program is complete (Mac session 96be433c, 2026-09-02).
The PLAN's REVISION-PENDING banner stands; this handoff records what the fresh pass changed BEFORE
the Phase-1 rewrite, so the rewrite is grounded, not re-accreted. All facts re-verified against the
incumbent as-run config, the code inventory (25 files, file:symbol), and the posts cited inline.

FOUR CHANGES vs the accreted diagnosis (full re-diagnosis in the Mac scratchpad `rediagnosis-2026-09-02.md`):

1. LATENCY is reconciled, not open. finding/264's "obs 1.2–4.7 steps stale" was measured pre-firmware
   (IMU 20 Hz / joint 10 Hz, 2026-08-12); post-fix the robot serves IMU 100 Hz / joint 50 Hz, so obs
   age ≈0.5–1 step and matches vault finding/056. The obs-staleness side is closed by firmware. The real
   open gap is the untrained ACTION delay: `control_delay_steps` delays the action (not obs) and is
   trained (0,0). finding/264 stays `needs-apply-before-retrain` — it is a config edit, not a probe —
   but the one missing number is the real command→actuator response time (unmeasured in normal operation).

2. "DISTURBANCE/FAULT TOO WEAK" now has a mechanism AND a rejected naive fix. finding/273: the four
   nominal-0 DORAEMON dims (ocean_current, obs_noise, payload_xy_u, fault_severity) end at 6–8% of range
   because of the Beta clamp + shared kl_ub 0.12 budget, not because they are physically hard. E-ftc1
   already escaped the clamp on fault_severity (2.5× expansion, causally confirmed) and robustness got
   WORSE (2.9–5.5×). So the R6/R1 lever is the fault SAMPLER SHAPE (k∈{0,1,2} mask, dead-channel mass,
   vertical-pair-aware), NOT accelerating the severity curriculum.

3. SEED VARIANCE is a gate-design constraint, not a footnote. finding/266: two seeds of the incumbent's
   own config differ 0.13–0.19 deg (> 0.10 floor) at every level; from-scratch does not reproduce the
   incumbent's quality from its config alone. Every feasibility gate needs ≥2 seeds or a same-seed
   trajectory control; the retrain's baseline must be a same-config re-seed, not the deployed number.

4. The J1 cable-break axis EXISTS in sim as `joint1_position_cost(limit=4π, budget=.01)` but is a soft
   1%-budget cost with NO hard clamp in the integrator. That soft-only state is consistent with the real
   cable break — and locates the exact robot-damage-prevention lever the instruction sanctions (a hard J1
   rail), distinct from shaping.

UNCHANGED / re-confirmed: pitch no-response = deploy-config gap (thruster_scale=0 removes pitch's actuator;
TAM My=0.145 over-estimated, rows marked OPEN in code); attitude authority is NOT the gap (finding/136 N2
PASS) so retrain is justified by FTC-strengthening + deploy/TAM correction, not a sim-real authority gap;
policy obs excludes linear velocity so XY-position takeover is blocked (no DVL); the incumbent already trains
faults as a distribution (fixed dead plant was a regression); vertical m0/m3 is 1 motor/dual-ESC on the robot
so vertical kills manufacture fake pitch loss (decision/140) — FTC severity must be axis-aware.

NEXT: Phase-1 rewrite to the FTC-sampler-shape axis + hard J1 rail + control_delay apply-before-retrain +
vertical-TAM correction, with ≥2-seed gates. No gate has run, nothing launched, nothing approved.
## Comments
