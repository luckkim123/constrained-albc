---
title: "IMU 45deg mounting offset + pitch negation is sim-uncompensated (2026-07-05)"
tags: []
created: 2026-07-05T15:24:24
updated: 2026-07-05T15:24:24
sources: []
links: ["tam_columns_must_match_robot_firmware_esc_channel_order_reorder_.md"]
category: reference
confidence: medium
schemaVersion: 1
---

# IMU 45deg mounting offset + pitch negation is sim-uncompensated (2026-07-05)

Scope: firmware IMU handling (3DM-GX5) vs sim policy observation construction. Session 3 tracer analysis (4 tracers + 1 scientist), 2026-07-05. Companion to [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]].

FIRMWARE FACT: the real IMU (3DM-GX5) is mounted with a 45-degree yaw offset relative to the robot body frame (`imu_yaw_offset_deg = 45`, applied in `imu_rotation.h` / `build_proprio.py`), plus a sign negation applied ONLY to pitch (`raw_pitch = -PITCH`); roll and yaw are not negated.

SIM FACT: the sim policy's observation pipeline consumes `root_ang_vel_b` (Isaac Lab ground-truth body-frame angular velocity) directly -- it does NOT apply any 45-degree rotation or any axis negation. The sim policy is therefore trained under an implicit assumption of perfect IMU-to-body-frame alignment, which does not match the real sensor mounting.

MITIGATING FINDING (reduces regression-risk from this asymmetry): firmware `control_law.h` (TDC/attitude control law) and sim `build_proprio.py` (policy observation construction) were checked byte-identical for the SIGN CONVENTION of roll/pitch that actually reaches the policy/controller -- i.e. despite the raw-sensor-level 45-degree offset + pitch negation upstream, the firmware's own downstream correction produces attitude signs that match sim's assumption. This lowers the likelihood that this offset is the root cause of the relay/attitude regressions investigated elsewhere in this session (see project memory `project_albc_attitude_regression_2026_07_02`) -- the sign convention that reaches control is already reconciled in firmware.

OPEN QUESTION (cannot be resolved from code alone): whether the pitch-only negation is (a) a body-frame convention correction (e.g. reconciling an NED vs FLU handedness difference between sensor output and control frame), or (b) a chip-native quirk specific to the 3DM-GX5 (e.g. its internal axis convention), is NOT determinable from source code -- it requires the 3DM-GX5 datasheet to confirm the sensor's native output convention. Do not assume either interpretation without checking the datasheet.

STATUS: unverified (confidence=medium). The 45-degree offset and pitch-negation are confirmed present in firmware code (high confidence on the code fact itself); the interpretation of WHY (FLU/NED handedness vs chip quirk) and whether it fully explains any observed sim-to-real attitude discrepancy is open, pending datasheet review.
