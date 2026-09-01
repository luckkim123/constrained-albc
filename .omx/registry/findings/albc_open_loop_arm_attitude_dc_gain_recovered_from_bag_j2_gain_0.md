---
title: "albc open-loop arm attitude DC gain recovered from bag j2_gain_0825 in body frame: 148 deg per m of EE radius, 32 deg/rad of theta2 (n=6, 3 pct spread), matching the closed-loop static map (+145 deg/m, R^2 0.998); the retracted 1.2 deg / 25x-short-of-sim claim is off by 65x and retraining is not justified by arm authority"
tags: ["albc", "dc-gain", "arm-authority", "retraining", "0825"]
created: 2026-08-24T20:31:08.315092
updated: 2026-08-24T20:31:08.315092
sources: ["vault 0_Project/in_progress/albc/notes/2026-08-25-night-reanalysis.md", "campaign 2026-albc-0825-night-reanalysis finding/001", "finding/002", "finding/003"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# albc open-loop arm attitude DC gain recovered from bag j2_gain_0825 in body frame: 148 deg per m of EE radius, 32 deg/rad of theta2 (n=6, 3 pct spread), matching the closed-loop static map (+145 deg/m, R^2 0.998); the retracted 1.2 deg / 25x-short-of-sim claim is off by 65x and retraining is not justified by arm authority

FIELD-MEASURED 2026-08-25 (bag j2_gain_0825, six open-loop theta2 steps, body-frame attitude via validated offline rotate_imu). The earlier reading of the same bag (appendix H-8) used raw IMU frame with J1 fixed near the fold and linear extrapolation, giving 1.2 deg total authority and 25x short of sim; that reading is retracted, the data was sound. Open-loop DC gain 148 deg/m (EE radius) = 32 deg/rad (theta2), spread 3 pct across n=6; the closed-loop staircase static map gives +145 deg/m with R^2 0.998, an independent match. Phase lag 0.38 s (the 1.0 s figure was an alias of the 1.6 s limit-cycle period). Consequence: the arm has the authority the policy needs, so the observed instability is a loop problem (see the limit-cycle page), and retraining cannot be justified on authority grounds. Retraining remains the last-resort branch (user decision D9) gated on experiments E1-E3 and on the needs-apply-before-retrain item control_delay_steps (0,0). Source: vault note section 0 item 5, section 1-3; campaign finding/003 section 3.
