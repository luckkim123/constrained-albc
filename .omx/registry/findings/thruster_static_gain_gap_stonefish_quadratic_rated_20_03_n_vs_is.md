---
title: "Thruster static gain gap: Stonefish quadratic rated 20.03 N vs Isaac linear 40 N per unit command; 2.0x at full command and 4.65x in the policy operating band, with zero DR coverage; rotor time constant IS aligned"
tags: ["sim-to-real", "stonefish", "thruster", "actuator", "saturation", "domain-randomization", "cross-sim-measurement", "thrust-curve"]
created: 2026-07-29T08:41:33.091940
updated: 2026-07-29T08:41:33.091940
sources: ["p1-thrust-sweep-20260729"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "real T200 bench curve needed to decide WHICH side to align to (open lead thruster_nonlinear_curve, deferred 2026-07-27); alignment knobs already identified on both sides"
---

# Thruster static gain gap: Stonefish quadratic rated 20.03 N vs Isaac linear 40 N per unit command; 2.0x at full command and 4.65x in the policy operating band, with zero DR coverage; rotor time constant IS aligned

[MEASURED 2026-07-29] Stonefish and Isaac disagree on how much force a thruster command buys, by 2x
at full command and ~4.65x in the band the policy actually uses. The axis carries NO domain
randomization (max_thrust_scale = (1.0, 1.0)), so every deployed policy is off-distribution on
actuator authority. Rotor time constant, in contrast, IS aligned.

THE TWO MODELS.
- Isaac (constrained_albc/envs/main/config.py:138-142, ALBCThrusterCfg): thrust = command * 40.0 N,
  LINEAR, clamped at max_thrust 50.0 (never binds since the coefficient is 40). tau_up/down 0.1/0.05.
- Stonefish v1.3.0 (Library/src/actuators/Thruster.cpp): T = rho*D^3*|n|*(D*kT0*n + alpha*u) with
  alpha = -kT0 and n = omega/(2pi). At u=0 this is rho*D^4*kT0*n^2 -- QUADRATIC in command, since
  omega_cmd = setpoint * max_rpm. With the scn's D=0.076, kT=0.167, max_rpm=3600 the rated value is
  20.03 N.

MEASURED, not just derived. Swept setpoint 0.1..1.0 as 2 s pulses on the vertical pair m0+m3
(symmetric about x, so pitch moments cancel), logging the engine's own /albc/thruster_state
thrust[N] and rpm at 100 Hz. Recovering kT0 per setpoint from the measured (T, n, u) triple gives
0.1671-0.1672 across all ten points (spread 0.1%) against the declared 0.167, and rpm/setpoint lands
at 3605-3652 against the declared 3600. Equation and parameters both confirmed.

  setpoint   SF bollard [N]   Isaac [N]   Isaac/SF
     0.1          0.200          4.00      19.97x
     0.4          3.207         16.00       4.99x
     0.7          9.818         28.00       2.85x
     1.0         20.027         40.00       2.00x
The ratio is exactly 2.0/setpoint, because the two laws are 40*sp and 20.03*sp^2.

NO RESCALING ANYWHERE IN THE PATH. bridge_node.py:151,162-164 clamps the policy action to [-1,1] and
publishes action[2:8] UNMODIFIED to /albc/setpoint/pwm; ROS2SimulationManager.cpp:407 feeds that
straight into Thruster::setSetpoint(). The thruster_allocator node (Newton -> PWM with max_thrust
50.0) is on the wrench path and is NOT in the RL loop.

THIS EXPLAINS THE UNRESOLVED SATURATION. albc-vibration-rootcause recorded that after the H5b
normalization fix the m0/m3 saturation rate barely moved (60.7->57.4%, 63.9->68.0%) and called it
"the signature of a plant that does not respond to commands as much as expected", handing the
residual to H1/H6/H3b. Isaac's own training logs show util_max 0.43, unsaturated. The arithmetic
closes exactly: heave is 2 vertical thrusters, so Isaac Fz = 80*sp and Stonefish Fz = 40.06*sp^2.
The 34.4 N the policy learned to get at sp 0.43 requires sp 0.927 in Stonefish. A policy trained to
use 43% of its authority must go nearly hard-over to get the same force -- which is the 57-68%
saturation that was observed.
Yaw is the same story: TAM Mz coefficient 0.144 on 4 horizontal thrusters gives Isaac 23.04*sp and
Stonefish 11.54*sp^2 N.m. The >=5 N.m P2 ceiling needs sp 0.217 in Isaac but sp 0.659 in Stonefish;
a policy issuing 0.217 gets 0.54 N.m, 9.2x short.

WHAT IS ALIGNED: the rotor time constant. Step response sp 0->1.0 measured t63 = 0.121 s, t95 =
0.362 s against Isaac's tau_up 0.100 s, and DR time_constant_scale (0.7, 1.3) puts the band at
[0.070, 0.130] -- in-distribution. This matches the source: Stonefish integrates
omega += (kp*e + ki*integral + torque)*dt with kp=8, ki=3 hardcoded and NO inertia divisor, giving
poles at -7.606 and -0.394; the fast pole governs the rise at 1/7.606 = 0.131 s. The slow pole leaves
a ~5% residual decaying with tau 2.5 s, which is why the measured rpm settles slightly above 3600.
So audit item 14 splits: time constant ALIGNED, static gain GAP.

WHICH SIDE IS WRONG -- UNDECIDABLE HERE. Isaac has the wrong SHAPE (real propeller thrust goes as
omega^2; marinelab even ships the signed-square curve at core/thruster.py:161-183 but
enable_thrust_curve defaults False, and every saved training env.yaml:296 confirms `false`).
Stonefish has the low SCALE (its thruster params are stock bluerov2 values). Anchoring to the real
T200 needs the bench measurement held by the open `thruster_nonlinear_curve...` lead (deferred
2026-07-27), so no target number can be chosen yet. Both alignment knobs exist:
max_rpm = 3600*sqrt(T_target/20.03) on the Stonefish side, enable_thrust_curve=True on the Isaac
side. Applying only one leaves the other mismatch.

NOTHING WAS APPLIED. scn/plant unchanged, training-side changes remain behind the human gate.

CONSEQUENCE FOR HYDRORC. The HydroRC line rests on "it oscillates because damping is short". The
plant is also short 2-5x on control authority. The half-recenter that failed its Isaac paired gate
on 2026-07-28 was tuned against a plant with this defect present, so a HydroRC-v2 proposal should
either handle thruster scale in the same experiment or state explicitly which side was held fixed.

Full result: vault docs/thruster-scale-gap-2026-07-29.md. Raw sweep and scripts at
tools/p1_joint_swing/{thrust_sweep_260729.csv, run_thrust_sweep.sh, analyze_thrust.py}.
[SOURCE: p1-thrust-sweep-20260729] [CONFIDENCE: HIGH]

