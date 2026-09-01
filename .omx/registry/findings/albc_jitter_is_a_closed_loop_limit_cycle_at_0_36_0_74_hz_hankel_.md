---
title: "albc jitter is a closed-loop limit cycle at 0.36-0.74 Hz (Hankel-DMD |lambda| 0.997-1.001 complex pairs in every closed-loop window, none in open-loop), open-loop arm-step ripple is 0.04-0.20 deg; delay-dominated vs rate-saturation-dominated is undecided"
tags: ["albc", "jitter", "limit-cycle", "koopman", "dmd", "0825"]
created: 2026-08-24T20:31:08.026949
updated: 2026-08-24T20:31:08.026949
sources: ["vault 0_Project/in_progress/albc/notes/2026-08-25-night-reanalysis.md", "campaign 2026-albc-0825-night-reanalysis finding/001", "finding/002", "finding/003"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# albc jitter is a closed-loop limit cycle at 0.36-0.74 Hz (Hankel-DMD |lambda| 0.997-1.001 complex pairs in every closed-loop window, none in open-loop), open-loop arm-step ripple is 0.04-0.20 deg; delay-dominated vs rate-saturation-dominated is undecided

FIELD-MEASURED 2026-08-25. Closed-loop ripple (RL policy, arm only): roll std 4.4-8.8 deg, pk-pk 13.6-35.8 deg, PSD peak 0.36-0.74 Hz across the 20 Hz staircase run. Same arm, same attitude band, open-loop steps (bag j2_gain_0825): ripple 0.04-0.20 deg. Hankel-DMD on the body-frame 100 Hz series: all 5 closed-loop windows carry |lambda| 0.997-1.001 complex pairs at 0.40-0.85 Hz matching the PSD peaks; the open-loop record has zero limit modes in 0.2-3 Hz. So the plant does not oscillate, the loop does. NOT decided: whether the limit cycle is delay-dominated (effective phase lag 0.38 s measured; 1.0 s reported earlier was an alias of the 1.6 s period) or rate-saturation-dominated (at 20 and 50 Hz the joint rate sat at the DELTA_SCALE x control_hz ceiling continuously; only the 10 Hz run was unsaturated). Discriminating experiment E2: joint_delta_scale 0.10/0.05/0.025 at 20 Hz - amplitude scaling alone means saturation, frequency dropping too means delay. Do NOT add a low-pass filter before that is decided: it adds phase lag and worsens a delay-type cycle. Source: vault note section 0 item 2; campaign finding/003 sections 5 and 6; review/004.
