# albc field 2026-08-25 night: arm-only attitude tracking reaches the command (cmd 30 deg gives body roll +28.7 deg); the fold singularity does not amplify jitter (+12 pct) but kills the signal (attainable/ripple 3.4 vs 10.7; cmd (30,30) held 58 s at theta2 = fold-13 deg gave +2.8 deg)

- id: finding/018 · date: 2026-08-24 · author: wiki-form-conversion
- to: all
- subject: albc-field-2026-08-25-night-arm-only-attitude-tracking-reach · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: 2026-08-25 · keywords: albc, sim2real, attitude, singularity, 0825
- summary: albc field 2026-08-25 night: arm-only attitude tracking reaches the command (cmd 30 deg gives body roll +28.7 deg); the fold singularity does not amplify jitter (+12 pct) but kills the signal (attainable/ripple 3.4 vs 10.7; cmd (30,30) held 58 s at theta2 = fold-13 deg gave +2.8 deg)

FIELD-MEASURED 2026-08-25 (bag rl_20hz_target_0825 + full-session bag, body frame via offline rotate_imu validated against node eul(deg) lines: 372 lines, residual max roll 0.678 / pitch 0.348 / yaw 0.505 deg, bias < 0.004 deg). All RL runs that night had thruster_scale=0, so every attitude response is the arm alone. Staircase cmd 5/10/15/20/25/30 deg -> body roll +6.59/+9.57/+14.24/+19.03/+24.08/+28.68 deg (steady-state mean over 18 steps, 100 Hz). Inside 25 deg of the fold the closed-loop ripple std is 5.56 vs 4.97 deg outside (+12 pct only), but attainable-attitude/ripple collapses 10.7 -> 3.4 and the one fold-state command (30,30) held 58 s at theta2 = pi - 13 deg reached only +2.8 deg; two minutes later, unfolded, the same policy reached +28.7 deg. Operator observation (tracks to 30, problem is jitter, jitter looks worse near the singularity) matches: the singularity starves the signal rather than growing the ripple. Reproducibility of the (30,30) collapse is n=1 (experiment E5). Source: vault note section 0 item 1, section 1-2; campaign finding/003 sections 4-0 and 7.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["vault 0_Project/in_progress/albc/notes/2026-08-25-night-reanalysis.md", "campaign 2026-albc-0825-night-reanalysis finding/001", "finding/002", "finding/003"]
- qualityScore: 80
- qualityReasons: ["no-source-marker"]
## Comments
