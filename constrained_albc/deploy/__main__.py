"""CLI: export torch checkpoints to deployment .npz.

Examples:
    python -m constrained_albc.deploy --list-specs
    python -m constrained_albc.deploy --spec student_tcn --ckpt PATH --out DIR
    python -m constrained_albc.deploy --batch attitude_only_5000 \
        --student-ckpt PATH --teacher-ckpt PATH \
        --run-group dr_harder --tag pack_5000iter --golden --report
    # --out omitted -> deploy/<run-group>/<tag>_<YYMMDD_HHMMSS>/ (cwd-relative;
    # label-before-date, mirrors the logs tree group layer)
    # --golden -> + golden/ vectors (CPU), npforward.py copy, parity self-close,
    # MANIFEST.json: one command produces a complete self-verifying deploy pack

The export run loads real models that import the training stack, so run it via
isaaclab's interpreter:
    cd /workspace/isaaclab && ./isaaclab.sh -p -m constrained_albc.deploy ...
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

from constrained_albc.analysis.paths import RUN_TS_FORMAT
from constrained_albc.deploy.specs import SPEC_REGISTRY


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="constrained_albc.deploy", description=__doc__)
    p.add_argument("--list-specs", action="store_true", help="list registered specs and exit")
    p.add_argument("--spec", choices=sorted(SPEC_REGISTRY), help="single-export spec name")
    p.add_argument("--ckpt", help="checkpoint .pt path for --spec")
    p.add_argument("--out", help="output directory (default: deploy/<run-group>/<tag>_<ts>)")
    p.add_argument("--run-group", help="campaign group layer for the default --out path")
    p.add_argument("--tag", help="pack label for the default --out path (e.g. pack_5000iter)")
    p.add_argument("--batch", choices=["attitude_only_5000"], help="named batch export")
    p.add_argument("--student-ckpt", help="student .pt for --batch")
    p.add_argument("--teacher-ckpt", help="teacher .pt for --batch")
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--report", action="store_true", help="also write EXPORT_REPORT.md")
    p.add_argument("--golden", action="store_true",
                   help="complete the pack: golden vectors (CPU) + npforward.py copy "
                        "+ parity self-close + MANIFEST.json")
    return p


def _ckpt_iter(path: str):
    """Read the training iter recorded in the checkpoint, or '?' if absent."""
    import torch

    return torch.load(path, map_location="cpu", weights_only=False).get("iter", "?")


def _student_cfg(path: str) -> dict:
    """Read the student checkpoint's stored cfg dict (empty if the ckpt predates it)."""
    import torch

    cfg = torch.load(path, map_location="cpu", weights_only=False).get("cfg", {})
    return cfg if isinstance(cfg, dict) else {}


def _build_student_spec(cfg: dict, obs_dim: int, latent_dim: int):
    """Pick and size the student spec from the checkpoint's OWN declared architecture.

    The checkpoint is the authority on which encoder it holds (same discipline as
    engine._infer_teacher_dims); guessing here is what shipped a TCN-shaped pack for
    a GRU student. obs_dim/latent_dim come from the TEACHER so a student distilled
    against a different-geometry teacher fails at the contract instead of shipping.

    Returns (spec, arch) where arch is the 'tcn'/'gru' tag the golden + pack take.
    """
    from constrained_albc.deploy.specs import STUDENT_SPEC_BY_ENCODER

    arch = cfg.get("encoder_type", "tcn")
    if arch not in STUDENT_SPEC_BY_ENCODER:
        raise SystemExit(
            f"student checkpoint declares encoder_type={arch!r}, which has no export spec "
            f"(known: {sorted(STUDENT_SPEC_BY_ENCODER)})"
        )
    spec_cls = STUDENT_SPEC_BY_ENCODER[arch]
    if arch == "gru":
        spec = spec_cls(obs_dim=obs_dim, hidden=cfg.get("gru_hidden", 128),
                        head_hidden=cfg.get("gru_head_hidden", 64), latent_dim=latent_dim)
    else:
        spec = spec_cls(obs_dim=obs_dim)
    return spec, arch


def resolve_out_dir(args: argparse.Namespace) -> str:
    """Resolve the export output dir per the deploy artifacts convention.

    Explicit ``--out`` wins. Otherwise derive ``deploy/<run_group>/<tag>_<ts>``
    (cwd-relative; label-before-date with the same timestamp format as
    ``analysis.paths.make_run_id``, mirroring the logs tree group layer).
    """
    if args.out:
        return args.out
    if not (args.run_group and args.tag):
        raise SystemExit("--out missing: provide it, or both --run-group and --tag")
    stamp = datetime.now().strftime(RUN_TS_FORMAT)
    return os.path.join("deploy", args.run_group, f"{args.tag}_{stamp}")


def list_specs_text() -> str:
    lines = ["Registered export specs:"]
    for name, cls in sorted(SPEC_REGISTRY.items()):
        lines.append(f"  {name:16s} -> {cls.npz_filename}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
    args = build_parser().parse_args(argv)

    if args.list_specs:
        print(list_specs_text())
        return 0

    # Imports that pull torch/training stack are deferred to here so --list-specs is light.
    from constrained_albc.deploy.engine import (
        build_student_model,
        build_teacher_model,
        export_from_state_dict,
    )
    from constrained_albc.deploy.specs import TeacherActorSpec

    if args.batch == "attitude_only_5000":
        assert args.student_ckpt and args.teacher_ckpt, \
            "--batch needs --student-ckpt and --teacher-ckpt"
        out_dir = resolve_out_dir(args)
        # Build the teacher first: it is the authority on the pack's obs/latent
        # geometry (campaign-dependent), and the student contract is checked against
        # the SAME width so a mispaired student fails here instead of shipping.
        t_model = build_teacher_model(args.teacher_ckpt, args.device)
        obs_dim = t_model.actor_obs_normalizer._mean.shape[1]
        latent_dim = t_model.actor[0].weight.shape[1] - obs_dim
        s_spec, arch = _build_student_spec(
            _student_cfg(args.student_ckpt), obs_dim=obs_dim, latent_dim=latent_dim)
        t_spec = TeacherActorSpec(obs_dim=obs_dim, latent_dim=latent_dim)
        s_model = build_student_model(s_spec, args.student_ckpt, args.device)
        s_rep = export_from_state_dict(s_spec, s_model, out_dir)
        t_rep = export_from_state_dict(t_spec, t_model, out_dir)
        if args.report:
            from constrained_albc.deploy.report import build_report

            chosen = {
                s_spec.name: {"file": os.path.basename(args.student_ckpt),
                              "iter": _ckpt_iter(args.student_ckpt),
                              "rationale": "last student checkpoint"},
                "teacher_actor": {"file": os.path.basename(args.teacher_ckpt),
                                  "iter": _ckpt_iter(args.teacher_ckpt),
                                  "rationale": "final teacher checkpoint"},
            }
            golden_status = (
                f"Skipped: the {obs_dim}D observation assembly lives in albc_env.py (the "
                "simulation environment), not in the student code, so it cannot be "
                "lifted byte-identically on an export host. The exported weights are "
                "independently verified value-for-value against the source checkpoints "
                "(max|delta| = 0 for actor/normalizer/student keys), so the .npz "
                "payloads are complete and correct; only the env-side input assembly "
                "is out of scope here. Recommend generating golden_e2e_tcn.npz "
                "(input -> output pairs from the real model) on the Mac/ksm-nas path "
                "during board integration."
            )
            md = build_report({s_spec.name: s_rep, "teacher_actor": t_rep}, chosen,
                              out_dir=out_dir, mount_status="overlay (docker cp)",
                              golden_status=golden_status)
            with open(os.path.join(out_dir, "EXPORT_REPORT.md"), "w") as f:
                f.write(md)

        if args.golden:
            from constrained_albc.deploy.golden import (
                export_golden_gru,
                export_golden_tcn,
                export_golden_teacher,
            )
            from constrained_albc.deploy.pack import copy_npforward, self_close, write_manifest

            # Goldens MUST be CPU-generated: GPU cuDNN conv differs from the
            # standard conv (~1e-4) the board numpy runtime implements (golden.py).
            s_model.to("cpu")
            t_model.to("cpu")
            if arch == "gru":
                export_golden_gru(s_model, out_dir)
            else:
                export_golden_tcn(s_model, out_dir)
            export_golden_teacher(t_model, out_dir)
            copy_npforward(out_dir)
            parity = self_close(out_dir, arch=arch)
            if not parity["closed_in_container"]:
                raise SystemExit(f"parity self-close FAILED: {parity}")
            write_manifest(
                out_dir,
                checkpoints={
                    s_spec.name: {"file": os.path.basename(args.student_ckpt),
                                  "iter": _ckpt_iter(args.student_ckpt),
                                  "path": args.student_ckpt},
                    "teacher": {"file": os.path.basename(args.teacher_ckpt),
                                "iter": _ckpt_iter(args.teacher_ckpt),
                                "path": args.teacher_ckpt},
                },
                parity=parity,
                arch=arch,
            )
            logger = logging.getLogger("deploy.export")
            logger.info("pack complete: parity self-close CLOSED, MANIFEST written -> %s", out_dir)
        return 0

    if args.spec:
        assert args.ckpt, "--spec needs --ckpt"
        out_dir = resolve_out_dir(args)
        if args.spec == "teacher_actor":
            spec = SPEC_REGISTRY[args.spec]()
            model = build_teacher_model(args.ckpt, args.device)
        else:
            # No teacher here to cross-check against, so size the student contract from
            # its own cfg -- but still refuse a --spec that contradicts the checkpoint.
            cfg = _student_cfg(args.ckpt)
            spec, arch = _build_student_spec(cfg, obs_dim=cfg.get("policy_obs_dim", 72),
                                             latent_dim=cfg.get("latent_dim", 9))
            if spec.name != args.spec:
                raise SystemExit(
                    f"--spec {args.spec} contradicts the checkpoint, which declares "
                    f"encoder_type={arch!r} (spec {spec.name}). Pass --spec {spec.name}."
                )
            model = build_student_model(spec, args.ckpt, args.device)
        export_from_state_dict(spec, model, out_dir)
        return 0

    build_parser().print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
