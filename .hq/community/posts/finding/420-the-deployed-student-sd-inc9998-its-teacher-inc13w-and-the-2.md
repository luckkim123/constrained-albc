# The deployed student `sd_inc9998`, its teacher `inc13w` and the 2026-09-06 candi

- id: finding/420 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-deployed-student-sd_inc9998-its-teacher-inc13w-and-the-2026-09-06-candi · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The deployed student `sd_inc9998`, its teacher `inc13w` and the 2026-09-06 candidate `sd_r3a` (with its `--env-dr-anchor

The deployed student `sd_inc9998`, its teacher `inc13w` and the 2026-09-06 candidate `sd_r3a` (with its `--env-dr-anchor` re-score `sd_r3a_envdr`) were only ever examined on the p3b plant: `control_delay_steps` (0, 3), no always-dead thrusters, no disturbance, and a p3b sidecar. On that plant `healthy` medium is 0.76–1.22 deg — five to seven times smaller than the p5 policies on the p5 plant. These rows are **not comparable** to anything above; the plant width, not the policy, sets the level. A regrade of `sd_r3a` and `sd_inc9998` on the p5 final sidecar with the p5 delta is the one experiment that would rank the pack against what is on the robot today.

[EVIDENCE: `exam_table.csv` rows base=`p4`, tag ∈ {`inc13w`, `sd_inc9998`, `sd_r3a`, `sd_r3a_envdr`} from `.hq/work/p4/<tag>/<cell>/summary.json` (their own eval files, read fresh for this report); p3b plant definition in `constrained_albc/envs/main/config_simtoreal.py` (`control_delay_steps=(0, 3)`)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
