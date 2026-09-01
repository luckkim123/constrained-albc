# albc control_hz re-verdict from three undocumented 2026-08-25 runs recovered from bags: 10 Hz was the quietest of the night (yaw span 4.0 deg, roll std 2.9, pitch std 0.36 over 40 s, joint rate unsaturated), 100 Hz diverged in 4 s (policy pushed the arm first, then body), and observation rate and control_hz are not separable in this data

- id: finding/017 · date: 2026-08-24 · author: wiki-form-conversion
- to: all
- subject: albc-control-hz-re-verdict-from-three-undocumented-2026-08-2 · supersedes: none
- topic: reference
- confidence: medium · status: none
- verified: 2026-08-25 · keywords: albc, control_hz, observation-rate, 0825
- summary: albc control_hz re-verdict from three undocumented 2026-08-25 runs recovered from bags: 10 Hz was the quietest of the night (yaw span 4.0 deg, roll std 2.9, pitch std 0.36 over 40 s, joint rate unsaturated), 100 Hz diverged in 4 s (policy pushed the arm first, then body), and observation rate and control_hz are not separable in this data

FIELD-MEASURED 2026-08-25, recovered by keeping rosbag recorders running across the whole session (the runs were not in any note). Segments: 50 Hz 35 s (appendix H run), 10 Hz 40 s, 100 Hz 4 s, 20 Hz 23 s, 20 Hz 192 s (staircase), plus 4 START REFUSED launches at 20/30 Hz after the 100 Hz run wound J1 to 8.6 rad. 100 Hz causal order: j1 moves at 0.23 s, j2 at 0.27 s, roll at 0.36 s - the policy drove the arm, the body followed. Observation rate seen by the node falls with policy rate: idle 104 / 10 Hz 99.9 / 20 Hz 97.2 / 50 Hz 88.7 / 100 Hz 78.2 Hz. Ordered by obs/policy ratio the quality is monotone, but obs rate and control_hz moved together in every run, so observation freshness remains a necessary-condition claim only. control_hz is not a knob: CONTROL_DT=0.02 is hard-coded in np_policy.py and DELTA_SCALE, INTEGRAL_LEAK and golden_steps are per-tick constants, so changing control_hz rescales joint-rate ceiling, integrator time constant and GRU history span together. Experiment E3 (firmware 100 Hz kept, control_hz fixed at 20, node-side observation decimation 100/40/20/10) is the only clean test; also re-measure /albc/joint_states publish rate (10 Hz on 2026-08-12, not re-measured after the IMU fix). Source: vault note section 0 item 4, section 1; campaign finding/001, finding/002 A13.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["vault 0_Project/in_progress/albc/notes/2026-08-25-night-reanalysis.md", "campaign 2026-albc-0825-night-reanalysis finding/001", "finding/002", "finding/003"]
- qualityScore: 80
- qualityReasons: ["no-source-marker"]
## Comments
