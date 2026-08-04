# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Paired-condition comparison (G4, 2026-07-27).

Robustness questions are inherently paired: (policy, baseline-condition) vs
(policy, treatment-condition) across N policies x DR levels -- e.g. the FTC
question (healthy vs m4-dead). `compare.py dr` compares runs; this mode compares
CONDITIONS within each policy, emits the per-axis x per-DR-level delta table
with the pre-registered decision floors applied (REAL / BELOW-FLOOR per cell),
and runs the injection bite-check FIRST: an injector that "ran" but was a silent
no-op has already burned this workspace once (feedback-verify-injection-bites).

Reusable for any condition sweep (fault, latency, thruster-curve), not just faults.
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np
from common import DR_LEVELS  # type: ignore[import-not-found]

from .recompute_metrics import floor_verdict, unit_for

DEFAULT_AXES = ("att_norm", "roll", "pitch", "yaw")
DEFAULT_FIELDS = ("ss_error", "ss_error_std", "os_env_mean", "n_gt20", "survival_pct")


def _load_summary(eval_dir: str) -> dict:
    with open(os.path.join(eval_dir, "summary.json")) as f:
        return json.load(f)


def bite_check(pairs: list[tuple[str, str, str]], key: str, levels: list[str]) -> tuple[list[str], int]:
    """Assert the treatment condition actually differs in the recorded npz.

    For each pair x level: the treatment npz must contain `key`, and its values
    must differ from the baseline's. The baseline may legitimately lack the key
    (absent-by-design for healthy evals, see G5). Byte-identical arrays mean a
    silent no-op injector -- the exact failure mode the E2 delay sweep hit.
    Returns (failure strings, number of levels actually checked). Zero checked
    levels is itself a failure: certifying a bite on no evidence is the same
    trap this function exists to close.
    """
    failures = []
    n_checked = 0
    for label, base_dir, treat_dir in pairs:
        for lvl in levels:
            tp = os.path.join(treat_dir, f"data_{lvl}.npz")
            if not os.path.exists(tp):
                continue
            n_checked += 1
            with np.load(tp) as tz:
                if key not in tz.files:
                    failures.append(f"{label}/{lvl}: treatment npz lacks '{key}'")
                    continue
                tv = np.asarray(tz[key])
            print(f"[BITE] {label}/{lvl}: {key} mean={tv.mean():.4f} min={tv.min():.4f} "
                  f"zeros={int((tv == 0).sum())}/{tv.size}")
            bp = os.path.join(base_dir, f"data_{lvl}.npz")
            if os.path.exists(bp):
                with np.load(bp) as bz:
                    if key in bz.files and np.array_equal(np.asarray(bz[key]), tv):
                        failures.append(
                            f"{label}/{lvl}: '{key}' byte-identical between conditions "
                            "(silent no-op injector)"
                        )
    if n_checked == 0:
        failures.append(
            "bite-check ran on 0 levels: no data_<level>.npz under any treatment dir"
        )
    return failures, n_checked


def _val(summary: dict, lvl: str, ax: str, field: str):
    if field == "survival_pct":
        return summary.get(lvl, {}).get("survival_pct")
    return summary.get(lvl, {}).get(ax, {}).get(field)


def cmd_paired(args: argparse.Namespace) -> None:
    pairs = []
    for spec in args.pair:
        parts = spec.split(":")
        if len(parts) != 3:
            raise SystemExit(f"--pair must be LABEL:BASELINE_DIR:TREATMENT_DIR, got {spec!r}")
        pairs.append((parts[0], parts[1], parts[2]))
    labels = [p[0] for p in pairs]
    if len(set(labels)) != len(labels):
        raise SystemExit(f"duplicate --pair labels: {labels}")

    summaries = {lbl: (_load_summary(b), _load_summary(t)) for lbl, b, t in pairs}
    levels = [lvl for lvl in DR_LEVELS
              if all(lvl in s for pair in summaries.values() for s in pair)]
    if not levels:
        raise SystemExit("no common DR level across all summaries")

    if args.bite:
        failures, n_checked = bite_check(pairs, args.bite, levels)
        if failures:
            print("[BITE-CHECK FAILED]")
            for f in failures:
                print(f"  {f}")
            raise SystemExit(2)
        print(f"[BITE-CHECK OK] '{args.bite}' differs between conditions on {n_checked} pair-level(s)")

    print("\nPaired delta = treatment - baseline, per DR level. Floors: "
          "REAL / BELOW-FLOOR from _analyze.recompute_metrics.DECISION_FLOORS "
          "(NO-FLOOR = no registered floor for that field/axis).")
    for field in args.fields:
        axes = ["-"] if field == "survival_pct" else list(args.axes)
        for ax in axes:
            # a delta of a percent value is percentage points, hence "pp" while
            # FIELD_UNITS carries "%" for the level value itself
            unit = "pp" if field == "survival_pct" else unit_for(ax, field)
            print(f"\n-- delta {field}" + (f" [{ax}]" if ax != "-" else "")
                  + f" ({unit or 'unitless'})")
            print(f"{'level':<8}" + "".join(f"{lbl:>26}" for lbl in labels))
            for lvl in levels:
                cells = []
                for lbl in labels:
                    base, treat = summaries[lbl]
                    b, t = _val(base, lvl, ax, field), _val(treat, lvl, ax, field)
                    if b is None or t is None:
                        cells.append(f"{'n/a':>26}")
                        continue
                    d = float(t) - float(b)
                    verdict = floor_verdict(field, d, None if ax == "-" else ax)
                    cells.append(f"{d:>+13.3f} {verdict:>12}")
                print(f"{lvl:<8}" + "".join(cells))
