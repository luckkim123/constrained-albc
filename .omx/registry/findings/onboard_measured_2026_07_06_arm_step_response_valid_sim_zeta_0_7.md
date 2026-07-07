---
title: "Onboard measured 2026-07-06: arm step-response (VALID, sim zeta~0.7 matches) + net buoyancy (NEUTRAL confirmed, sign unresolvable at 1cm depth quantization)"
tags: ["sim-to-real", "arm", "step-response", "buoyancy", "actuator", "measurement", "baseline"]
created: 2026-07-06T04:58:39.169684
updated: 2026-07-06T05:02:21.929898
sources: []
links: ["actuator_hardware_identification_arm_xw540_t260_board_measured_p.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Onboard measured 2026-07-06: arm step-response (VALID, sim zeta~0.7 matches) + net buoyancy (NEUTRAL confirmed, sign unresolvable at 1cm depth quantization)

Board-measured 2026-07-06 on agent-jetson (edd735c). Companion RESULT card to the two prereq cards that predicted these: [[actuator_hardware_identification_arm_xw540_t260_board_measured_p]] (predicted measurement 1) and [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]] (predicted measurement 2 as "unforced vertical drift z(t), simplest anchor"). Raw CSV lives in the user's vault (0_Project/.../data/20260706_onboard_measurement/), NOT in the ksm-ubuntu container -- these figures are trusted from the note's own raw-CSV computation, cross-checked here against sim live code (marinelab/assets/albc/albc.py).

## MEASUREMENT 1 -- arm step-response (VALID for tuning)
joint1 (Dynamixel ID 11), air/no-buoy, deploy gains P800/I1/D40 re-written before stepping (CSV IS deploy-gain response; README's D=0/I=0 is a pre-measurement snapshot, not the measured gains -- do not misread). Steps 0/+30/+60/0/-30 deg x3, logged at 484 Hz (>>200 Hz target), Operating Mode 4 (Extended Position, harmless at +-60 deg, no wrap).

Measured (raw CSV): +30deg -> rise(10-90%) 0.15s, overshoot 3.0%, settle(2%) 0.32s, ss-err <0.05deg. -60deg -> rise 0.27s, OS 1.5%, settle 0.36s. High 3-repeat reproducibility.

### KEY SIM-TO-REAL FINDINGS (use for baseline/comparison-group design)
1. **Measured overshoot 2-3% <-> sim already assumes zeta~0.7.** sim arm ImplicitActuatorCfg (albc.py:196) has stiffness=100 damping=3 with the design comment "w_n=57.7 rad/s, J~0.15, damping ratio ~0.7". 2-3% OS maps to zeta~0.74-0.78. So the real arm's effective damping ratio ALREADY MATCHES sim's assumed zeta. sim small-signal gains (w_n, zeta) are in the right regime -- do NOT re-tune Kp/Kd blindly.

2. **The +30deg step is NOT the linear/small-signal regime -- it is velocity/effort SATURATED.** The note's section 1.2 said "linear region, not velocity saturation" -- that is BACKWARDS and must be corrected. Proof: sim w_n=57.7 rad/s predicts small-signal rise ~1.4/w_n ~ 0.024s, but measured rise is 0.15s (6x slower), AND rise scales WITH step size (0.15s@30 -> 0.27s@60). A linear 2nd-order system's rise is INDEPENDENT of step size; rise growing with amplitude is the signature of saturation. So the large-step rise is a saturation datum, not a linear-PD datum.

3. **What to match next in sim: the saturation point, not the small-signal gains.** sim arm hard caps: velocity_limit_sim=6.28 rad/s (2pi) and effort_limit_sim=13.0 Nm (albc.py:200-201). The 6x rise gap is more likely effort/torque saturation + underwater load than the velocity cap (6.28 is already near XW540-T260 no-load speed). Deploy operating point is a 50 Hz delta command stream (action +-1 -> +-5.7 deg), a DIFFERENT physical regime from the +-30 deg step -- a dedicated delta-command injection (arm_delta_sysid.py, unbuilt) reproduces deploy better than the big-step data. Use the step data as a PD sanity check (small-signal PASS) + a saturation anchor, not as deploy-point ground truth.

## MEASUREMENT 2 -- net buoyancy (NEUTRAL confirmed, SIGN unresolved)
neutral-buoy, 5 trials x 8s, /hero_agent/state Depth (MS5837), thruster uninvolved (verified no depth-control node). 22.6 Hz.

**Depth is quantized ~1 cm.** Whole CSV has only 3 distinct depth eigenvalues (0.4193 / 0.4296 / 0.4398 m), spacing exactly 0.01024 m = 1 cm = MS5837 pressure LSB in this condition (WORSE than the ~2mm the prereq plan assumed). Over 8s free-float depth only flickered among these 3 values, total excursion 1-2 cm; 4/5 trials Delta-z exactly 0, trial 5 = +1 quantization step.

### FINDINGS
1. **NEUTRAL is a QUANTITATIVE upper bound, not just qualitative.** Free-float moved <1 quantization step (1cm) in 8s -> accel upper bound ~ 2*Deltaz/t^2 ~ 2*0.01/64 ~ 3e-4 m/s^2. With sim body_mass=9.18 kg (albc.py:80): |F_net| <~ 9.18 * 3e-4 ~ 3 mN ~ 0.011% of buoy buoyancy F_bu~26.24 N. Usable as a sanity check on sim volume/body_mass/water_density DR center values (the net buoyancy center is ~exactly neutral).
2. **SIGN (float vs sink) is NOT resolvable** with this method + this sensor resolution -- 1 trial of +1 LSB is indistinguishable from noise. This is on top of the method's inherent limit (added-mass not separated, so no absolute F_net).
3. **Re-measure order**: longer logging (30-60s) accumulates drift past the 1cm boundary while quantization noise stays fixed -> sign emerges. BUT do the IMU accel_z firmware exposure FIRST ([[actuator_hardware_identification_arm_xw540_t260_board_measured_p]] companion handoff): direct z-double-dot measurement beats depth-drift integration for buoyancy precision.

## MISSING (reproducibility, user to fill in vault note): depth sign convention (down = +?), robot total weight, buoy mass/volume/attach-point, water temperature.

---

## Update (2026-07-06T05:02:21.929898)

## CORRECTION 2026-07-06 (raw CSV re-verified in-container -- supersedes two claims above)

The raw CSVs ARE in the ksm-ubuntu container at /workspace/data/20260706_onboard_measurement/ (armstep/step_air_nobuoy_j1.csv 10895 rows, buoyancy/*.csv 5x181). Re-parsed directly; the "raw lives only in vault" caveat in the header is WRONG for this container. All measurement-1 and measurement-2 quantitative figures REPRODUCE from raw (rise/OS/settle/ss-err within rounding; +30 rise 0.152s, OS 3.1%, -60 rise 0.267s, OS 1.3%; buoyancy 3 depth eigenvalues 0.4193/0.4296/0.4398 spacing 0.01023m; F_net<=3mN=0.011% Fbu all 5 trials). The note is VALID.

But raw velocity data OVERTURNS finding #3's velocity-cap judgement:

1. **VELOCITY SATURATION IS DIRECTLY VISIBLE and the saturation speed is ~3.1 rad/s, NOT the linear regime.** peak|joint velocity| (from present_vel_raw x 0.229rpm LSB) plateaus at ~3.0-3.6 rad/s ACROSS BOTH 30deg and 60deg steps -- doubling the step does NOT raise peak velocity => hard velocity saturation confirmed from raw (not just inferred from rise-vs-amplitude). This nails finding #2 (saturation, note's "linear region" backwards) with a direct velocity plateau.

2. **CORRECTS finding #3: the measured saturation speed ~3.1 rad/s is HALF of sim velocity_limit_sim=6.28 rad/s.** The earlier card said "6.28 is already near XW540-T260 no-load speed, so the velocity cap is not the culprit." That is WRONG. Real arm saturates at ~3.1 rad/s (which happens to equal XW540-T260 ~30rpm=3.14 rad/s no-load spec), so sim at 6.28 lets the sim arm rotate TWICE as fast as the real arm. => sim velocity_limit_sim should be LOWERED to ~3.1 rad/s (measured no-load speed). This is a concrete sim-to-real fix for the next from-scratch baseline retrain. current also plateaus ~3.7-3.8 A (secondary effort/profile-accel saturation).

3. **Gain-in-effect (deploy P800/I1/D40) is NOT directly confirmable from the CSV** -- the file logs no gains. Register readout showed I=0/D=0 (a torque-off snapshot). Data is CONSISTENT with active D>0 (damped 3% overshoot, small ~0.4deg settle ripple, ~29mA residual holding current), which argues the deploy gains WERE re-applied as the note claims, but this is indirect. Treat "measured with deploy gains" as very-likely-but-not-CSV-proven.

NET for next baseline: (a) lower sim arm velocity_limit_sim 6.28 -> ~3.1 rad/s [measured]; (b) keep Kp/Kd (zeta~0.7 matches); (c) the big-step data is a saturation anchor, deploy-point still needs a delta-command sysid. Measurement 2 (buoyancy neutral, |F_net|<0.011% Fbu, sign unresolved at 1cm quantization) stands unchanged.

