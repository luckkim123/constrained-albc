---
title: "Deploy export was TCN-only so it shipped the non-adopted student arm; StudentGRUSpec closes GRU parity (latent 1.2e-07, hidden 1.6e-07 over 9 steps) and rejects shallow-head / multi-layer geometries"
tags: ["deploy", "student", "gru", "export", "parity", "stonefish", "npforward"]
created: 2026-07-30T04:43:30.898808
updated: 2026-07-30T04:43:30.898808
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# Deploy export was TCN-only so it shipped the non-adopted student arm; StudentGRUSpec closes GRU parity (latent 1.2e-07, hidden 1.6e-07 over 9 steps) and rejects shallow-head / multi-layer geometries

[FINDING] The deploy export pipeline was TCN-only, which is why the 2026-07-30 pack shipped the NON-adopted student arm; StudentGRUSpec now exports the adopted A0g GRU with parity closed, and the numpy runtime accepts only the deep-head single-layer geometry.

[EVIDENCE] Before the fix, SPEC_REGISTRY held student_tcn + teacher_actor only, golden.py had export_golden_tcn only, and pack.py hardcoded weights_tcn.npz / golden_tcn.npz / channel_transform.0.weight -- so pack_eint_a0tcn_260730_130032 packaged the TCN arm (trpo_sdeint_a0_tcn_s30_260729_130559) even though the campaign adopted A0g/GRU. The board runtime npforward.StudentGRU already pinned the contract, so the fix filled in the ExportSpec the registry was designed for. Real export of the adopted student (trpo_sdeint_a0g_gru_s30_260729_151017/student_999.pt) against the E-int teacher (teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/model_4999.pt) closed parity at atol 1e-5 with gru_latent_max_err 1.1920929e-07 and gru_hidden_max_err 1.6391277e-07, dims obs 72 / latent 9 / gru_hidden 128, carry verified over 9 steps -> deploy/student_distill_eint/pack_eint_a0g_gru_260730_134104. Commit 2f057b9 on exp/ftc1-severity-init.

[CONFIDENCE] HIGH

Two geometries are NOT deployable and are now rejected at export instead of at the board:
- gru_head_hidden == 0 builds head = Linear only, but npforward.StudentGRU reads head.2 (LayerNorm) and head.3 (second Linear). Only the deep-head variant runs on the board. StudentCfg default is 64, so the adopted arm is fine -- but a shallow-head ablation would be unexportable.
- gru_layers != 1: npforward.gru_cell implements a single layer and reads only the *_l0 weights.

The GRU golden is a MULTI-STEP sequence and export_golden_gru refuses steps < 2. This is the load-bearing design point: torch runs the whole (1,T,D) sequence in one nn.GRU call while the board steps T times carrying its own hidden, so a single-step golden (h == 0 on both sides) would leave the hidden carry AND the torch [r, z, n] gate order unchecked. Both are wrong-answer bugs, not crashes. The final hidden state is therefore saved and compared directly, not only through the latents it feeds. The regression test perturbs gru.weight_hh_l0 specifically, because that weight acts ONLY through the carry -- it is the check a single-step golden passes blind.

Two collateral facts established:
- The exporter now reads the student checkpoint's own cfg encoder_type to choose the spec (same discipline as engine._infer_teacher_dims: the checkpoint is the authority, never a hardcoded arch), and a --spec that contradicts the checkpoint is refused.
- python -m constrained_albc.deploy could never have worked: -m runs the top-level constrained_albc/__init__.py, which registers the gym tasks and cascades into isaaclab.sim -> pxr, before _isolation's stub can be injected. /isaac-sim/python.sh alone does not provide pxr. The launcher that _isolation.py's docstring already named now exists at scripts/export_deploy_pack.py; use it, not -m, and run it from the repo root so packs land in constrained-albc/deploy/ and never in the pristine isaaclab fork.

TCN regression is closed: re-exporting the TCN pack after the change reproduces pack_eint_a0tcn_260730_130032 with all four payload sha256 IDENTICAL and the same parity values.

Still open: there is no ONNX/JIT export and no ROS2 bridge. The numpy pack remains the validated reference runtime any future bridge must be diffed against.

