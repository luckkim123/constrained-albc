# RETRACTED: the 2026-08-25 headline that 100 Hz IMU observations closed the yaw divergence (240 -> 1.26 deg) was a radians-labelled-as-degrees error (57.3x) on top of a raw-IMU-frame read; true numbers are 240 -> 71.9 deg yaw and roll std 5.2 deg, so only accelerating divergence -> bounded drift (19 -> 1.15 deg/s) survives

- id: finding/224 · date: 2026-08-24 · author: wiki-form-conversion
- to: all
- subject: retracted-the-2026-08-25-headline-that-100-hz-imu-observatio · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: 2026-08-25 · keywords: albc, units, frame, imu, analysis-trap, 0825
- summary: RETRACTED: the 2026-08-25 headline that 100 Hz IMU observations closed the yaw divergence (240 -> 1.26 deg) was a radians-labelled-as-degrees error (57.3x) on top of a raw-IMU-frame read; true numbers are 240 -> 71.9 deg yaw and roll std 5.2 deg, so only accelerating divergence -> bounded drift (19 -> 1.15 deg/s) survives

The night session of 2026-08-25 (vault appendix H, commit b7e80ef2) analysed the 50 Hz run with analyze_rl_bag.py / analyze_rl_osc.py / analyze_step.py from ~/albc_diag on agent-jetson. Those scripts print radians under a (deg) label and read /hero_agent/sensors ROLL/PITCH, which is the raw IMU mounting frame (102 deg off body; body frame = build_proprio.rotate_imu). Re-analysis in body frame with unit sanity checks: yaw span after the firmware IMU-rate fix is 71.9 deg not 1.26; roll std 5.18 deg not 0.11; the attitude moved roll +-15 / pitch -29 deg during the 35 s window. What still holds from that night: firmware IMU publish rate 22.6 -> 100.4 Hz (commit 80ab138, pub_sensors was stuck inside the depth-sensor state machine) and the qualitative change from accelerating divergence to bounded drift. The retraction memo of that session (2026-08-25-session-retraction-and-handoff.md) itself over-retracted appendix F (which was copied from node eul lines and is clean) and under-retracted the unit error. Rule: attitude numbers come only from the node log eul(deg) line or an offline rotate_imu transform validated against it; check invariants first (yaw and sqrt(roll^2+pitch^2) are frame-invariant, a uniform 57.3x is units). Do not reuse the four scripts above. Source: vault note section 0 item 3; campaign finding/002 A12; auto-memory feedback_unit_and_frame_invariants.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["vault 0_Project/in_progress/albc/notes/2026-08-25-night-reanalysis.md", "campaign 2026-albc-0825-night-reanalysis finding/001", "finding/002", "finding/003"]
- qualityScore: 80
- qualityReasons: ["no-source-marker"]
## Comments
