---
title: "eval analysis: core does stats, adapter does heavy-tail"
tags: ["eval", "heavy-tail", "adapter", "engine-gap", "omx"]
created: 2026-06-05T08:55:20.495177
updated: 2026-06-05T08:55:20.495177
sources: ["exp/omx-eval-adapter", "2026-06-05"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# eval analysis: core does stats, adapter does heavy-tail

omx exp-analyze 가 eval 결과를 분석할 때: 기본 통계(per-axis mean/std/CV, 4 DR레벨)는 omx CORE 가 이미 함 -- `omx reduce summarize --path <summary.json> --format eval_summary --cv-field <metric>` (verified EXIT 0, 28 rows). 따라서 기본통계 adapter 를 만들면 DRY 위반. CORE 가 못 하는 것 = heavy-tail / sample-mean divergence 분리 (`--cv-field n_gt20` -> []; core 는 _std sibling 있는 필드만 CV). 그건 sim-free `constrained_albc/analysis/_analyze/eval_dr.py::_ed_analyze_run(eval_dir, levels, t_att=20, t_lv=0.5, t_yaw=0.5)` 가 함 -> `.omx/profile/eval_adapter.py` 가 순수 위임(계산 0, 드리프트 불가; test_adapter_matches_engine_directly 가 out==ref 로 가드). CLI: `python3 .omx/profile/eval_adapter.py heavy-tail <eval_dir>` -> JSON. 함정: sim-free 테스트를 `isaaclab not in sys.modules` 로 검증하면 이 repo(Isaac Sim 컨테이너, interpreter wrapper 가 isaaclab 선로드)에서 FAIL -- 소스 레벨 검사(adapter 가 isaac import/SimulationApp 안 함)로 해야 환경 비의존. branch exp/omx-eval-adapter merged main dedb235.
