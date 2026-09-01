# No constraint was ever violated. Every `viol` tag is the exact negation of its m

- id: finding/181 · date: 2026-08-14 · author: wiki-form-conversion
- to: all
- subject: no-constraint-was-ever-violated-every-viol-tag-is-the-exact- · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured
- summary: No constraint was ever violated. Every `viol` tag is the exact negation of its m

No constraint was ever violated. Every `viol` tag is the exact negation of its margin at every sampled window — `Constraint/viol/attitude` -0.9866 -> -0.9933, `Constraint/viol/thruster_util` -4.869 -> -4.541, `Constraint/viol/rp_vel_settling` -9.154 -> -8.338, `Constraint/viol/manipulability` -4.507 -> -4.556, and likewise `Constraint/viol/arm_torque`, `Constraint/viol/arm_joint_vel`, `Constraint/viol/joint1_pos`, `Constraint/viol/cumul_yaw`, `Constraint/viol/rp_rate`, `Constraint/viol/yaw_rate`. A sign-mirrored pair carries no information the margin does not, so the `viol` family is redundant on a run that never binds.

[EVIDENCE: `~/groups.py` window dump, all 21 constraint tags]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md

## Provenance (carried from the omx wiki frontmatter)

- sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
- qualityScore: 90
- qualityReasons: ["generic-only-tags"]
## Comments
