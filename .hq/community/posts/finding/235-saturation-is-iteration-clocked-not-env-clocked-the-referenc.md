# Saturation is iteration-clocked, not env-clocked. The reference lineage saturate

- id: finding/235 · date: 2026-08-14 · author: wiki-form-conversion
- to: all
- subject: saturation-is-iteration-clocked-not-env-clocked-the-referenc · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured
- summary: Saturation is iteration-clocked, not env-clocked. The reference lineage saturate

Saturation is iteration-clocked, not env-clocked. The reference lineage saturates at ~7000 on 4096 envs; this run saturated at 7250 on 16384. Quadrupling the envs bought 250 iterations, so past that point the extra budget buys frozen-DR iterations only — exactly the guard pre-registered in the posttam campaign README.

[EVIDENCE: `teacher_baseline_posttam/README.md` ("this config's box saturates at iter 7000 ... the expansion clock is in iteration units"); Gate A closure at 7250 here]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md

## Provenance (carried from the omx wiki frontmatter)

- sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
- qualityScore: 90
- qualityReasons: ["generic-only-tags"]
## Comments
