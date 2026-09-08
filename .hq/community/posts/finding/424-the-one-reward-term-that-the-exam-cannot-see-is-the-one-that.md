# The one reward term that the exam cannot see is the one that is worst in trainin

- id: finding/424 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-one-reward-term-that-the-exam-cannot-see-is-the-one-that-is-worst-in-trainin · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The one reward term that the exam cannot see is the one that is worst in training. Yaw position error stayed at 22–24 de

The one reward term that the exam cannot see is the one that is worst in training. Yaw position error stayed at 22–24 deg from iteration ~1000 to the end on the training plant (which samples ocean current and disturbance), and `Reward/yaw` never recovered above −1.9. The static attitude-step exam commands roll/pitch only and scores yaw as a *rate* (0.44–0.46 rad/s on the no-lag cells, 1.2–1.5 rad/s under 8-step lag), so a 20-deg yaw-position drift would not show in any table above. Whether the field controller cares depends on the mission; the number is recorded here so it is not discovered in the tank.

[EVIDENCE: `tbread.py` `Track/yaw/err_deg` seg 2 first/last-10 % 21.46 / 23.66 (min 13.6, max 67.1 at the resume step); `exam_table.csv` `yaw.ss_error` column (rad/s)]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
