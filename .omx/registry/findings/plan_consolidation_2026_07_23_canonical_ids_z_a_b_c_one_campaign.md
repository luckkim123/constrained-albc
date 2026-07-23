---
title: "Plan consolidation 2026-07-23: canonical ids Z/A/B/C + one-campaign-per-group; master doc docs/reference/teacher-campaign-plan.md"
tags: ["consolidation", "campaign", "naming", "plan", "ssot"]
created: 2026-07-23T06:38:05.683798
updated: 2026-07-23T06:38:05.683798
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Plan consolidation 2026-07-23: canonical ids Z/A/B/C + one-campaign-per-group; master doc docs/reference/teacher-campaign-plan.md

The scattered plan corpus (60 .sp/plans docs, 2 handoff dirs, abandoned campaign ledgers, 16-lead backlog) was consolidated 2026-07-23 into ONE authoritative document: constrained-albc/docs/reference/teacher-campaign-plan.md (git-versioned; .sp and experiments/ are both gitignored so neither can hold a durable plan). Canonical id scheme = the 2026-07-20 campaign grammar (Z1-Z10 / A1-A7 / B0a-B3 / D-gates) + C0/C3/C4 from the 2026-07-22 roster; C1/C2 retired as aliases; full legacy mapping table (P-A*/P-B*, e1-e4, Arm N/I, Exp A/B, ITEM 1/2, Phase 0-3, two R-sets) lives in the doc, section 3. Campaign stores: one campaign per run group (campaign-status derives runs from group-keyed ledgers; an umbrella id would show zero runs forever) with program=teacher-final-closeout + predecessor links; teacher_baseline_buoyfix / seed_floor_dgx / e3_dgxscale_buoyfix registered and posttam ledger back-filled (0->32 events) on 2026-07-23. Status: Stage A 5/5 zero adoptions; B0a/B1a/B0a-eval done, anchor SOUND; remaining critical path = W0 -> B0c (~15h) -> C3 comparison set (~60h, workstation serial) -> C4. Five leads closed (april entropy, backlog index, slack tail, e3 budget, penalty exchange); live backlog now 7 needs-experiment + 4 needs-apply-before-retrain. Storage convention going forward: durable plan = that doc only; .sp/plans = disposable scaffolding (trash on landing); ledger events appended at launch/eval/verdict time, never batch-reconstructed again. Superseded .sp documents moved to /workspace/.trash/sp-plans-cleanup-260723/.
