"""CLI: export torch checkpoints to deployment .npz.

Examples:
    python -m constrained_albc.deploy --list-specs
    python -m constrained_albc.deploy --spec student_tcn --ckpt PATH --out DIR
    python -m constrained_albc.deploy --batch attitude_only_5000 \
        --student-ckpt PATH --teacher-ckpt PATH --out DIR --report

The export run loads real models that import the training stack, so run it via
isaaclab's interpreter:
    cd /workspace/isaaclab && ./isaaclab.sh -p -m constrained_albc.deploy ...
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

from constrained_albc.deploy.specs import SPEC_REGISTRY


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="constrained_albc.deploy", description=__doc__)
    p.add_argument("--list-specs", action="store_true", help="list registered specs and exit")
    p.add_argument("--spec", choices=sorted(SPEC_REGISTRY), help="single-export spec name")
    p.add_argument("--ckpt", help="checkpoint .pt path for --spec")
    p.add_argument("--out", help="output directory")
    p.add_argument("--batch", choices=["attitude_only_5000"], help="named batch export")
    p.add_argument("--student-ckpt", help="student .pt for --batch")
    p.add_argument("--teacher-ckpt", help="teacher .pt for --batch")
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--report", action="store_true", help="also write EXPORT_REPORT.md")
    return p


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
    from constrained_albc.deploy.specs import StudentTCNSpec, TeacherActorSpec

    if args.batch == "attitude_only_5000":
        assert args.student_ckpt and args.teacher_ckpt and args.out, \
            "--batch needs --student-ckpt, --teacher-ckpt, --out"
        s_spec, t_spec = StudentTCNSpec(), TeacherActorSpec()
        s_model = build_student_model(s_spec, args.student_ckpt, args.device)
        s_rep = export_from_state_dict(s_spec, s_model, args.out)
        t_model = build_teacher_model(args.teacher_ckpt, args.device)
        t_rep = export_from_state_dict(t_spec, t_model, args.out)
        if args.report:
            from constrained_albc.deploy.report import build_report
            chosen = {
                "student_tcn": {"file": os.path.basename(args.student_ckpt),
                                "iter": 999, "rationale": "last of 1000 (0-indexed)"},
                "teacher_actor": {"file": os.path.basename(args.teacher_ckpt),
                                  "iter": 4999, "rationale": "max iter; 5000 absent"},
            }
            md = build_report({"student_tcn": s_rep, "teacher_actor": t_rep}, chosen,
                              out_dir=args.out, mount_status="overlay (docker cp)",
                              golden_status="see Task 8 decision")
            with open(os.path.join(args.out, "EXPORT_REPORT.md"), "w") as f:
                f.write(md)
        return 0

    if args.spec:
        assert args.ckpt and args.out, "--spec needs --ckpt and --out"
        spec_cls = SPEC_REGISTRY[args.spec]
        spec = spec_cls()
        if args.spec == "teacher_actor":
            model = build_teacher_model(args.ckpt, args.device)
        else:
            model = build_student_model(spec, args.ckpt, args.device)
        export_from_state_dict(spec, model, args.out)
        return 0

    build_parser().print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
