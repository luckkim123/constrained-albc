---
title: "engine-gap: barrier_alpha is 0.02 not 0.05 (dr-harder docs drift)"
tags: ["engine-gap", "constraint_trpo", "barrier_alpha", "doc-drift"]
created: 2026-06-07T02:54:26.487897
updated: 2026-06-07T02:54:26.487897
sources: ["diagnose-20260607-113942"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: barrier_alpha is 0.02 not 0.05 (dr-harder docs drift)

[ENGINE-GAP] dr-harder campaign docs (README, docs/results/260607_041243_trpo.md front-matter, several Batch-2 briefings) state adaptive_d_k = max(d_k, J_C + 0.05*d_k), i.e. barrier_alpha=0.05. The actual code value is 0.02. [WHERE] constrained_albc/envs/main/algorithms/constraint_trpo.py:65 (default line_search ctor) and :120 (self._barrier_alpha = barrier_alpha), used at :308 (_compute_adaptive_thresholds: torch.max(self.d_k, mean_cost_returns + self._barrier_alpha*self.d_k)). [SPEC] when citing the adaptive-threshold formula in any report/wiki, use 0.02; the per-constraint adaptive FLOOR is alpha*d_k = 0.02*d_k (thruster_util floor = 0.4, not 1.0). This does NOT change the J_C/d_k binding conclusions because those are computed in the slack regime (margin > alpha*d_k) as J_C = d_k - margin, alpha-independent. [EVIDENCE] code lines read this session; docs/results/260607_041243_trpo.md line 50 said barrier_alpha=0.05. [STATUS] proposed (fix doc citations; code is correct).
