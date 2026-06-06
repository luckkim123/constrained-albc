---
title: "Autonomous campaign tail-run died from MISSING launch automation, not wall-clock"
tags: ["campaign", "autonomous", "scheduling", "worktree", "automation-gap"]
created: 2026-06-06T06:34:31.697188
updated: 2026-06-06T06:45:00.000000
sources: ["trpo_e1_kl_ub_012_260605_193501", "trpo_e2_ocean_shift_260606_055938", "trpo_e4_baseline_repro_260606_004205"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# Autonomous campaign tail-run died from MISSING launch automation, not wall-clock

The 2026-06-05 DR-harder campaign was planned as 4 runs (E1 kl_ub, E4 baseline-repro, E2 ocean-shift, E3 both) sequential on a single RTX 4070 (4060 OOMs at the user-locked num_envs 4096). Outcome: E1, E4, E2 all completed 5000 iter; E3 NEVER STARTED.

CORRECTED ROOT CAUSE (an earlier version of this finding wrongly blamed wall-clock; the user disproved it). Timeline from logs_queue mtimes: E1 done ~00:40, E4 done ~05:46, E2 train done 11:03, E2 eval done 11:12. The user returned at 15:00 and E3 STILL had not started. That is a ~3h48m idle window after E2 finished. So wall-clock was NOT the limiter.

The real cause: there was NO launch mechanism for E3 at all. grep across the workspace finds zero scripts, cron jobs, or nohup chains that launch E3 (ocean 0.3 + kl_ub 0.12). The only monitor script (isaaclab/monitor_and_launch_baseline.sh) is a stale Round-2 artifact for Isaac-FullDOF-TRPO-v0/perdiment_kl06, unrelated to this campaign. E1/E4/E2 were each launched individually (by the prior session, one at a time); nothing watched for E2's completion to fire E3. When E2 ended, the queue simply went empty and stayed empty. The plan DOCUMENTED "E2/E3 run as time permits" but no code ever implemented the "then run E3" step.

WHY E4 WAS RUN AT ALL (redundant-looking control): the plan deliberately included E4 as the control cell of a 2x2 factorial (E4 = exact baseline re-run, kl_ub 0.06, ocean 0.0). Intent was to prove determinism so E1/E2/E3 deltas are attributable to the knob, not seed noise. E4 did reproduce teacher bit-for-bit (reward/ocean/success/z_std all identical). But determinism with a fixed seed was already known, so spending ~5 GPU-hours to re-confirm it was low-value -- the control could have been a 30-iter smoke, not a full 5000-iter run.

LESSON for next autonomous campaign:
- A multi-run queue MUST have an actual chaining mechanism (a loop/monitor that launches run N+1 when run N's checkpoint lands), not just an ordered list in the plan. "Run as time permits" with no launcher = the tail silently never runs.
- Leave a MORNING HAND-OFF artifact (a results-md line or notepad) stating which runs completed / partial / never-started, with the literal command to launch the un-started ones. The user found E3 un-started by inspection; the campaign should have told them.
- For a determinism control, a short smoke (tens of iters) is enough to confirm seed-stability. Do not burn a full training budget re-confirming something already known.
- The idle 4060 was never used as a fallback lane for a smaller-num_envs run; consider it when the user lock pins the primary GPU.
