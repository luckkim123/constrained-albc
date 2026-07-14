---
title: "train.py --max_iterations under --resume is iters-FROM-resume, not an absolute target (e3 got +10000 not +5000)"
tags: ["train.py", "resume", "max_iterations", "launch", "gotcha", "budget", "rsl_rl"]
created: 2026-07-13T23:59:24.291196
updated: 2026-07-13T23:59:24.291196
sources: ["diagnose-20260714-084409"]
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# train.py --max_iterations under --resume is iters-FROM-resume, not an absolute target (e3 got +10000 not +5000)

GOTCHA: when resuming a run, scripts/train.py --max_iterations N --resume runs N MORE iterations from the resume point, NOT to an absolute iter-N target. e3 (proposal designed +5000 / 10k-total) was launched with --max_iterations 10000 --resume from baseline model_4999.pt and actually trained iter 4999 -> 14998 (~15000 total = +10000, DOUBLE the design). Confirmed from checkpoint files (model_14998.pt) + TB event range + train/params/agent.yaml max_iterations:10000. CONSEQUENCE for planning: to extend a 5000-iter run BY 5000 (to 10k total) under --resume, pass --max_iterations 5000, not 10000. To hit an absolute target T from a resume at iter R, pass --max_iterations (T-R). e4 is a FRESH train (no --resume, --max_iterations 5000 = 5000 iters from scratch) so it is UNAFFECTED, but any future resume-based launch must account for this. In e3's case the extra budget only strengthened the H2/regression verdict, so no re-run needed. See analysis diagnose-20260714-084409.
