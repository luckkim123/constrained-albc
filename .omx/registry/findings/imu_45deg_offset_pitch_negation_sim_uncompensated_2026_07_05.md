---
title: "IMU 45deg mounting offset + pitch negation is sim-uncompensated (2026-07-05)"
tags: ["imu", "3dm-gx5", "mounting-offset", "sim-to-real", "deployment-prep", "deferred", "user-decision"]
created: 2026-07-05T15:24:24
updated: 2026-07-20T07:24:09.722345
sources: ["control_law.h", "build_proprio.py"]
links: ["tam_columns_must_match_robot_firmware_esc_channel_order_reorder_.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-apply-before-retrain
blocked-on: "DEFERRED by user decision 2026-07-20: will be applied to sim AFTER a real-robot measurement settles the pitch-negation convention (measurement preferred over datasheet interpretation). Zero sim-side impact meanwhile; firmware already reconciles the signs reaching control. NOT part of the batch experiment pass -- deployment prep, sequenced with robot bring-up."
---

# IMU 45deg mounting offset + pitch negation is sim-uncompensated (2026-07-05)

Scope: firmware IMU handling (3DM-GX5) vs sim policy observation construction. Session 3 tracer analysis (4 tracers + 1 scientist), 2026-07-05. Companion to [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]].

FIRMWARE FACT: the real IMU (3DM-GX5) is mounted with a 45-degree yaw offset relative to the robot body frame (`imu_yaw_offset_deg = 45`, applied in `imu_rotation.h` / `build_proprio.py`), plus a sign negation applied ONLY to pitch (`raw_pitch = -PITCH`); roll and yaw are not negated.

SIM FACT: the sim policy's observation pipeline consumes `root_ang_vel_b` (Isaac Lab ground-truth body-frame angular velocity) directly -- it does NOT apply any 45-degree rotation or any axis negation. The sim policy is therefore trained under an implicit assumption of perfect IMU-to-body-frame alignment, which does not match the real sensor mounting.

MITIGATING FINDING (reduces regression-risk from this asymmetry): firmware `control_law.h` (TDC/attitude control law) and sim `build_proprio.py` (policy observation construction) were checked byte-identical for the SIGN CONVENTION of roll/pitch that actually reaches the policy/controller -- i.e. despite the raw-sensor-level 45-degree offset + pitch negation upstream, the firmware's own downstream correction produces attitude signs that match sim's assumption. This lowers the likelihood that this offset is the root cause of the relay/attitude regressions investigated elsewhere in this session (see project memory `project_albc_attitude_regression_2026_07_02`) -- the sign convention that reaches control is already reconciled in firmware.

OPEN QUESTION (cannot be resolved from code alone): whether the pitch-only negation is (a) a body-frame convention correction (e.g. reconciling an NED vs FLU handedness difference between sensor output and control frame), or (b) a chip-native quirk specific to the 3DM-GX5 (e.g. its internal axis convention), is NOT determinable from source code -- it requires the 3DM-GX5 datasheet to confirm the sensor's native output convention. Do not assume either interpretation without checking the datasheet.

STATUS: unverified (confidence=medium). The 45-degree offset and pitch-negation are confirmed present in firmware code (high confidence on the code fact itself); the interpretation of WHY (FLU/NED handedness vs chip quirk) and whether it fully explains any observed sim-to-real attitude discrepancy is open, pending datasheet review.

---

## Update (2026-07-14T09:55:53.590020)

Flagged needs-apply-before-retrain 2026-07-14. Verified sim-UNCOMPENSATED: grep of envs/main/ finds no IMU mounting-offset frame correction in the observation pipeline (constraints.py:166 is an attitude COMMAND +-45deg range, unrelated). The 45deg mount offset + pitch negation is not applied in obs. Decide + (maybe) apply frame correction before a reference retrain, or record pre-IMU-frame.

---

## Update (2026-07-20T07:24:09.722345)

## DECISION (2026-07-20, user): DEFERRED pending real-robot measurement -- NOT rejected

Explicit user position: the frame correction WILL be applied to sim; it is simply not being decided
now. The intended sequence is **measure on the real robot first, then apply**, which is later but
not too late -- nothing downstream is blocked by waiting.

The reasoning that makes deferral safe (verified, not assumed):

- **Zero effect on sim-side results.** Sim consumes Isaac Lab ground-truth attitude and applies no
  mounting rotation and no axis negation, so no training curve, no eval number, and no verdict in
  any campaign to date is contaminated by this. This is a sim-to-real ALIGNMENT item, not a
  performance item. Do not let it appear in a results-regression discussion.
- **The signs that reach control are already reconciled.** Firmware `control_law.h` and sim
  `build_proprio.py` were checked byte-identical for the roll/pitch SIGN CONVENTION arriving at the
  controller/policy, so the raw-level 45deg offset + pitch negation is corrected downstream in
  firmware. Nothing is actively broken today.
- **The open question cannot be closed from code.** Whether the pitch-only negation is a body-frame
  handedness correction (NED vs FLU) or a 3DM-GX5 chip-native convention needs the datasheet, or --
  the user's preferred route -- a direct measurement on the robot, which settles it empirically
  without needing to interpret the datasheet at all.

CONSEQUENCE for planning: this item does NOT belong in the batch experiment pass. It is deployment
prep, sequenced with real-robot bring-up, and its cost is one retrain whenever it lands. Keep the
`needs-apply-before-retrain` flag so a reference retrain cannot silently skip it, but do not treat
it as a blocker on any sim-side campaign.

