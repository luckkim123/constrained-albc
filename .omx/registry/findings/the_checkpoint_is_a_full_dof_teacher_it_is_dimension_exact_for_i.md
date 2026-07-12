---
title: "The checkpoint is a full-DOF teacher; it is dimension-exact for `Isaac-Constrain"
tags: ["auto-captured", "trpo_main_teacher_260525_232805"]
created: 2026-07-12T18:26:43.465984
updated: 2026-07-12T18:26:43.465984
sources: ["experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The checkpoint is a full-DOF teacher; it is dimension-exact for `Isaac-Constrain

The checkpoint is a full-DOF teacher; it is dimension-exact for `Isaac-ConstrainedALBC-Full-TRPO-v0` and incompatible with the attitude-only main env, so the Full task on current code is the faithful continuation of the proposal's "old teacher".

[EVIDENCE: torch.load(model_4999.pt) state_dict dims (engine.py method) vs envs/full_dof/config.py:306-311 and envs/main/config.py:9,382]
[CONFIDENCE: HIGH]

source report: experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md
