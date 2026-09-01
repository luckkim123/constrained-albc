# `model_13400` is the only checkpoint with zero OOD failures (0/64 vs 1/64 at 750

- id: finding/176 · date: 2026-08-14 · author: wiki-form-conversion
- to: all
- subject: model-13400-is-the-only-checkpoint-with-zero-ood-failures-0- · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured
- summary: `model_13400` is the only checkpoint with zero OOD failures (0/64 vs 1/64 at 750

`model_13400` is the only checkpoint with zero OOD failures (0/64 vs 1/64 at 7500 and 10000, 3/64 at 5000), but 0-vs-1 of 64 is not a distinguishable difference and must not be quoted as a robustness win.

[EVIDENCE: `terminated.any(axis=0)` per env; Fisher exact 0/64 vs 1/64 gives p = 1.0]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md

## Provenance (carried from the omx wiki frontmatter)

- sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
- qualityScore: 90
- qualityReasons: ["generic-only-tags"]
## Comments
