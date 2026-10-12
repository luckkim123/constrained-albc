# Container Deploy Pack — Redeployment SSOT

> Container-side workflow for producing a self-verifying deploy pack
> (attitude-only teacher + GRU student) for the Mac -> agent-jetson handoff.
> Recreated 2026-06-12 (the earlier copy of this file was lost from disk; workflow
> now codified in the CLI itself, commit `feat/deploy-export`).

## One command produces the whole pack

```bash
cd /workspace/constrained-albc && /isaac-sim/python.sh scripts/export_deploy_pack.py \
    --batch attitude_only_5000 \
    --student-ckpt <student .pt> --teacher-ckpt <teacher .pt> \
    --run-group <campaign> --tag pack_<label> \
    --device cpu --golden --report
```

- Output: `deploy/<run-group>/<tag>_<YYMMDD_HHMMSS>/` (cwd-relative, label-before-date,
  mirrors the logs tree group layer). Never pass ad-hoc `--out` paths.
- `--golden` appends: golden vectors (CPU), `npforward.py` copy, parity self-close
  (loud-fail if not closed), `MANIFEST.json` (payload-derived dims + per-file sha256).
- `--report` additionally writes `EXPORT_REPORT.md` alongside the pack.
- Use `scripts/export_deploy_pack.py`, NOT `python -m constrained_albc.deploy` — the
  `-m` form fires the package `__init__` -> sim stack -> `pxr` and dies on export hosts.

## Non-negotiable contracts

1. **Teacher normalization is eps=0.01**: `(obs - mean) / (std + 0.01)`;
   the stored `_std` is `sqrt(var)` with eps NOT folded in.
2. **Goldens are CPU-generated, always**: GPU cuDNN conv differs from the standard
   conv (~1e-4) that the board numpy runtime implements. `--golden` enforces this
   by moving models to CPU before capture.
3. **npforward.py must stay Python 2.7-loadable: `np.dot` only, `@` is FORBIDDEN
   (PEP 465 is py3.5+; the board's ROS lunar rospy runs the inference node on
   py2.7).** Also no f-strings, no annotations, no keyword-only args. Enforced by
   `tests/deploy/test_npforward_compat.py` (AST gate, runs sim-free).
4. Goldens MUST come from the same in-memory model instances the weights were
   dumped from (`--golden` guarantees this; `golden.py` documents the contract).

## Mac handoff

Mac pulls the pack directory, then:
1. Verify every file's sha256 against `MANIFEST.json` (`files` section).
2. Run `test_npforward.py` against the pack (parity atol 1e-5).
3. Deploy to agent-jetson. The board node imports `npforward.py` under py2.7 /
   numpy 1.11 — contract 3 above is what makes that import survive.

## Paper pack

- Tag: `pack_rr_ft_ftp7200_s30_gru_260927_193819` (`student_arch: gru`)
- Checkpoints: teacher `model_7200.pt` (run `trpo_rr_FTP_s30_260927_182609`), student
  `student_999.pt` (run `trpo_sd_rr_ft_ftp7200_s30_260927_192341`)
- Dims: obs 72, action 8, latent 9, teacher input 81, GRU hidden 128
- Parity (container self-close, atol 1e-5): teacher normalize 0.0 / act 1.1e-6,
  GRU latent 2.8e-7 / hidden 1.8e-7 — CLOSED
