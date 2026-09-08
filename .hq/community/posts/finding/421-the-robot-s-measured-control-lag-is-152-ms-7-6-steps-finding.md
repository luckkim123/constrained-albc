# The robot's measured control lag is 152 ms = 7.6 steps (`finding/264`). Every pr

- id: finding/421 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-robot-s-measured-control-lag-is-152-ms-7-6-steps-finding-264-every-pr · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The robot's measured control lag is 152 ms = 7.6 steps (`finding/264`). Every previous pack was trained at (0, 0) or (0,

The robot's measured control lag is 152 ms = 7.6 steps (`finding/264`). Every previous pack was trained at (0, 0) or (0, 3) steps; the p5 teacher's plant allows (0, 13) and the student's rollouts sampled it uniformly, so the field regime is inside the student's training distribution even though the teacher's paced dim only reached 0.06. The exam's `d8` cells (8 steps) are the closest proxy and read 15.6–17.0 deg medium for the student — the number to expect in the tank if the simulation lag model is right, not the 5 deg of the no-lag cells.

[EVIDENCE: `exam_table.csv` `sd_p5_r3a` `healthy_d8`/`pair34_d8` medium; `P5_DELTA` in `/workspace/g0c_runner/p5_common.sh`; student plant line above]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
