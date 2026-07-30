---
title: "E-ftc1 ends ahead on every reward term, so its worse fault rejection is not a tr"
tags: ["auto-captured", "trpo_ftc1sevinit_s30_260729_105510"]
created: 2026-07-29T08:24:32.720137
updated: 2026-07-29T12:20:47.836515
sources: ["experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# E-ftc1 ends ahead on every reward term, so its worse fault rejection is not a tr

E-ftc1 ends ahead on every reward term, so its worse fault rejection is not a training-reward regression — the two policies optimized the same objective and E-ftc1 optimized it better.

[EVIDENCE: `tb_final.py --window 200` (profile-owned reducer; `omx reduce tb-final` is unusable here, system python3 has no tensorboard)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

E-ftc1 ends ahead on every reward term, so its worse fault rejection is not a training-reward regression — the two policies optimized the same objective and E-ftc1 optimized it better.

[EVIDENCE: `tb_final.py --window 200` (profile-owned reducer; `omx reduce tb-final` is unusable here, system python3 has no tensorboard)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
