---
title: "Real ALBC deployment state-estimation rates measured from code: attitude+gyro at most ~25 Hz (loop_speed/4, self-telemetered in the sensors DEPTH field), joints 10 Hz, control 50 Hz -- the real policy runs on zero-order-held stale observations, so 50 Hz Stonefish odom is already faster than reality"
tags: ["rates", "deployment", "agent-jetson", "staleness", "aliasing"]
created: 2026-08-03T06:21:41.365125
updated: 2026-08-03T06:21:41.365125
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Real ALBC deployment state-estimation rates measured from code: attitude+gyro at most ~25 Hz (loop_speed/4, self-telemetered in the sensors DEPTH field), joints 10 Hz, control 50 Hz -- the real policy runs on zero-order-held stale observations, so 50 Hz Stonefish odom is already faster than reality

Real ALBC deployment state-estimation rates, read from the deployed agent-jetson code (vault clone @08e326f 2026-06-15; board additionally carries the 2026-06-29 pack_B file swap, which replaced models/pack, not loop structure -- board git is authoritative, re-check at the next board session).

MEASURED CHAIN:
- attitude roll/pitch/yaw + gyro p,q,r on /hero_agent/sensors: AT MOST ~25 Hz. firmware/agent/agent.ino main loop is a 4-phase state machine, each phase ends in delay(9); pub_sensors.publish() fires only in the last phase, so period >= 4x9 ms. The exact rate is SELF-TELEMETERED: the firmware stuffs loop_speed (loops/sec) into sensors_msg.DEPTH, so true publish rate = loop_speed/4, readable from any field bag or board log in one minute.
- joint states on /albc/joint_states: 10 Hz (joint_angle_command.patched.cpp LOOP_HZ=10.0, velocity differentiated with measured dt).
- policy control loop: 50 Hz (rl_inference_node control_hz=50, CONTROL_DT=0.02).
- angvel obs[6:9] is the firmware gyro true value via rotate_gyro (obs[8] yaw rate = raw GYRO_Z); euler-differencing+LPF is only the no-gyro fallback.

CONSEQUENCES:
1. The real policy consumes zero-order-held STALE observations: attitude refreshes every ~2 control ticks, joints every 5. Stonefish's deployed 50 Hz odom is already FASTER than the real stack -- raising it to 100 Hz to kill the measured +40% yaw-rate aliasing bias would move away from deployment reality; the smoke bench stays at 50 Hz, and a real-faithful mode would LOWER rates (~25 Hz attitude ZOH + 10 Hz joints), not raise them.
2. The 50 Hz aliasing finding is reclassified from simulator artifact to REAL DEPLOYMENT CONDITION the policy must tolerate.
3. The remaining open half of the rate question belongs to the training side: what obs freshness the policy was trained to expect. If Isaac serves fresh state every control step, the train-deploy gap is STALENESS, not rate -- it lands in the open latency/transport-delay DR lead.

Vault SSOT: 0_Project/in_progress/albc/sim_validation/docs/real-state-rate-2026-08-03.md

