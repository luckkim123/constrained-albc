# The p5 plant is the `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` task plus a three-

- id: finding/434 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: the-p5-plant-is-the-isaac-constrainedalbc-trpo-simtoreal-v0-task-plus-a-three · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: The p5 plant is the `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` task plus a three-field launch delta, and the `performance

The p5 plant is the `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` task plus a three-field launch delta, and the `performance_lb` that made the curriculum work exists only as a resume-time CLI value. A launch of the task id with no override reproduces the p3b plant (`control_delay_steps` (0, 3), `performance_lb` 200) — i.e. exactly the dead-curriculum segment 1 with a narrower delay range. None of the four values is a code default.

[EVIDENCE: `/workspace/g0c_runner/p5_common.sh` `P5_DELTA`; `p5_teacher_resume.sh` (`env.doraemon.performance_lb=$LB` with LB −20); task defaults in `constrained_albc/envs/main/config_simtoreal.py` (`control_delay_steps=(0, 3)`, `performance_lb=200.0`)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
