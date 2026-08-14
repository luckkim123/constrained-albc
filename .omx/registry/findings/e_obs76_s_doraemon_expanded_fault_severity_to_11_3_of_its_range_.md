---
title: "E-obs76's DORAEMON expanded `fault_severity` to 11.3% of its range while fault i"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# E-obs76's DORAEMON expanded `fault_severity` to 11.3% of its range while fault i

E-obs76's DORAEMON expanded `fault_severity` to 11.3% of its range while fault injection was disabled in code, so the curriculum spent the whole run widening a dimension that could not reach the plant — direct internal evidence of the confound.

[EVIDENCE: `albc_env.py:1652` gates the entire fault-sampling block on `if self.cfg.fault.enable and self._thruster is not None:` and the run's recorded config has `fault: enable: false`; `DORAEMON/mean/fault_severity` final-50 mean 0.11291 with engine verdict EXPANDING]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
