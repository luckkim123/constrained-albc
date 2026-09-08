# Rank the p5 pack against the deployed policies on ONE plant: regrade sd_r3a and sd_inc9998 on the p5 final sidecar with the p5 delta

- id: finding/438 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: rank-the-p5-pack-against-the-deployed-policies-on-one-plant-regrade-sd_r3a-and-s · supersedes: none
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: deploy, exam, sidecar, p5
- summary: From analysis diagnose-20260908-142536 (generalization). inc13w / sd_inc9998 / sd_r3a were only ever examined on the p3b

From analysis diagnose-20260908-142536 (generalization). inc13w / sd_inc9998 / sd_r3a were only ever examined on the p3b plant (control_delay (0,3), no always-dead thrusters, no disturbance): healthy medium 0.76-1.22 deg, five to seven times below the p5 policies on the p5 plant (sd_p5_r3a 5.34) -- plant width, not policy, sets the level, so no ranking of the pack against the robot policy exists. Experiment: eval.py static on the p5 CORE cells with --env-dr-anchor against g0c_runner/p5_frozen_final/doraemon_state.pt and the P5_DELTA for sd_r3a (pack_r3a_p3b7500) and sd_inc9998; compare to sd_p5_r3a on the same files. Zero training.
## Comments
