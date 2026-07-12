# Container Deploy Pack — Redeployment SSOT

> Container-side workflow for producing a self-verifying deploy pack
> (BlueROV attitude-only teacher + TCN student) for the Mac -> agent-jetson handoff.
> Recreated 2026-06-12 (the earlier copy of this file was lost from disk; workflow
> now codified in the CLI itself, commit `feat/deploy-export`).

## One command produces the whole pack

```bash
cd /workspace/constrained-albc && python scripts/export_deploy.py \
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
- Use `scripts/export_deploy.py` (import-isolation launcher), NOT
  `python -m constrained_albc.deploy` — the `-m` form fires the package `__init__`
  -> sim stack -> `pxr` and dies on export hosts.

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

## Current pack (2026-06-12)

- Path: `/workspace/constrained-albc/deploy/dr_harder/pack_5000iter_260612_135619/`
- Checkpoints: teacher `model_4999.pt` (iter 4999), student `student_999.pt` (iter 999)
- Parity (container self-close, atol 1e-5): teacher normalize 0.0 / act 1.9e-6,
  TCN latent 1.6e-7 — CLOSED
- `npforward_sha256`: `8eff0046cf1665ee15955fd8fa52a5a2d96d9a7003f8beff2b9382c57a008741`
  (py2.7 fix; supersedes `4b708314...b10e2`, which dies with SyntaxError under py2.7)
- weights + goldens are byte-identical to the 260611 pack; only npforward.py changed.
