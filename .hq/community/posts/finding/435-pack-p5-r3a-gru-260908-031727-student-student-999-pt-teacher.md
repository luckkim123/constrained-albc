# `pack_p5_r3a_gru_260908_031727` (student `student_999.pt`, teacher `model_9999.p

- id: finding/435 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: pack_p5_r3a_gru_260908_031727-student-student_999-pt-teacher-model_9999-p · supersedes: none
- topic: session-log
- confidence: low · status: none
- verified: none · keywords: auto-captured, trpo_p5_s30_r4450_260907_175721
- summary: `pack_p5_r3a_gru_260908_031727` (student `student_999.pt`, teacher `model_9999.pt`, obs 72 / latent 9 / action 8 / GRU h

`pack_p5_r3a_gru_260908_031727` (student `student_999.pt`, teacher `model_9999.pt`, obs 72 / latent 9 / action 8 / GRU hidden 128) passed every gate that can be run without the robot: container self-close (teacher normalize 0, teacher act 1.19e-7, GRU latent 1.71e-7, GRU hidden 1.34e-7, atol 1e-5), Mac numpy 2.4.6 self-close with the pack's own `npforward.py` (sha 8ab626b0…, identical to the deployed board code; act 8.9e-8, latent 1.7e-7, hidden 1.3e-7), sha256 5/5 identical container = Mac, and the board package tests run on the Mac copy of the `agent-jetson` clone: `test_npforward.py` all parity checks passed, `test_np_policy_api.py` 12 passed / 2 xpassed — the two `xfail`-marked tests (tick-1 saturated action with all error terms ≈ 0; monotone joint-target runaway with the arm fixed and the body level) **pass** with this student where they failed with `inc9998` and `r3a`. That is test evidence on the field condition of `finding/163`, not field evidence. Open: the TX2 gate itself (py2.7, numpy 1.11; jump host offline) and the field run.

[EVIDENCE: `deploy/retrain_simtoreal_p5/pack_p5_r3a_gru_260908_031727/MANIFEST.json` `parity` and `dims`; `status.log` 2026-09-08 MAC GATE entry; `MACBOOK_DEPLOY_PROMPT.md` beside the pack on the Mac]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p5/trpo_p5_s30_r4450_260907_175721/analysis/diagnose-20260908-142536/report.md
## Comments
