#!/usr/bin/env python3
"""Final-window TensorBoard scalar reducer (G2, 2026-07-27).

`omx reduce tb-final` is unusable on this machine: the omx CLI entry point
resolves to system python3, which has no tensorboard. This profile-owned
reducer is the supported TB code-exec source here; run it under the Isaac Sim
interpreter:

    /isaac-sim/python.sh .omx/profile/tb_final.py <run_dir>... \
        --tags Train/mean_reward Loss/kl [--window 200]

Prints JSON: {run_dir: {tag: mean-of-last-<window>-points | null}}.
Use --list-tags to discover available scalar tags per run.
"""
import argparse
import glob
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser(description="Final-window TB scalar reducer (JSON out).")
    ap.add_argument("runs", nargs="+", help="Run dirs containing events.out.tfevents.*")
    ap.add_argument("--tags", nargs="+", default=None, help="Scalar tags to reduce.")
    ap.add_argument("--window", type=int, default=200, help="Mean over the last N scalar points.")
    ap.add_argument("--list-tags", action="store_true", help="Print available scalar tags per run and exit.")
    args = ap.parse_args()
    if not args.list_tags and not args.tags:
        ap.error("--tags is required unless --list-tags")

    try:
        import numpy as np
        from tensorboard.backend.event_processing import event_accumulator
    except Exception as exc:
        sys.stderr.write(
            f"[PREFLIGHT] {type(exc).__name__}: {exc}\n"
            "Run under the Isaac Sim interpreter: /isaac-sim/python.sh .omx/profile/tb_final.py ...\n"
        )
        sys.exit(2)

    out = {}
    for run in args.runs:
        if not glob.glob(os.path.join(run, "events.out.tfevents.*")):
            sys.stderr.write(f"[WARN] no event file under {run}\n")
            out[run] = None
            continue
        # EventAccumulator on the dir merges all event files (resume-safe).
        ea = event_accumulator.EventAccumulator(
            run, size_guidance={event_accumulator.SCALARS: 10000}
        )
        ea.Reload()
        avail = set(ea.Tags()["scalars"])
        if args.list_tags:
            out[run] = sorted(avail)
        else:
            out[run] = {
                t: (float(np.mean([s.value for s in ea.Scalars(t)][-args.window:])) if t in avail else None)
                for t in args.tags
            }
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
