# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""`export` subcommand: eval artifacts -> MATLAB .mat / long-format CSV.

Two tracks, matched to each artifact's natural interchange format:
  - trajectory npz (data_*.npz) -> .mat (scipy.io.savemat).
    MATLAB then `load('data_hard.mat')` gives error_roll, target_vx, ... as matrices.
  - summary.json (nested metrics[level][axis][metric]) -> long-format CSV
    with columns [run, dr_level, axis, metric, value]. This is the form MATLAB
    readtable / pandas / Excel pivot all consume directly, and makes the rules/03
    CV computation (ss_error_std / ss_error across DR x axis) a one-liner groupby.

Pure Python (no Isaac Sim). Operates on existing artifacts only.
"""

from __future__ import annotations

import argparse
import csv
import json
import os

import numpy as np
from scipy.io import savemat

from ._shared import _load_npz


def _sanitize_mat_key(key: str) -> str:
    """MATLAB struct field names must be valid identifiers (alnum + underscore,
    not starting with a digit). Map any other npz key to a safe field name."""
    safe = "".join(c if (c.isalnum() or c == "_") else "_" for c in key)
    if safe and safe[0].isdigit():
        safe = "f_" + safe
    return safe or "field"


def _npz_to_mat(npz_path: str, out_path: str) -> None:
    """Convert one trajectory npz to a .mat. String arrays become MATLAB cell
    arrays (dtype=object) so savemat does not choke on them."""
    data = _load_npz(npz_path)
    mat: dict[str, object] = {}
    for k, v in data.items():
        key = _sanitize_mat_key(k)
        # numeric arrays pass through; string/unicode arrays -> object (cell)
        if v.dtype.kind in ("U", "S"):
            mat[key] = np.array([str(x) for x in v.ravel()], dtype=object).reshape(v.shape)
        else:
            mat[key] = v
    savemat(out_path, mat, do_compression=True)
    print(f"  Saved {out_path}  ({len(mat)} arrays)")


def _summary_to_csv(json_path: str, out_path: str, run_label: str) -> int:
    """Flatten summary.json (metrics[level][axis][metric]) to long format.

    Returns the number of data rows written. Skips entries that are not numeric
    scalars (the per-axis dict may carry nested lists for some fields)."""
    with open(json_path) as f:
        summary = json.load(f)

    rows: list[tuple[str, str, str, str, float]] = []
    for level, axes in summary.items():
        if not isinstance(axes, dict):
            continue
        for axis, metrics in axes.items():
            if not isinstance(metrics, dict):
                continue
            for metric, value in metrics.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue  # only numeric scalars; null/list fields skipped
                rows.append((run_label, level, axis, metric, float(value)))

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "dr_level", "axis", "metric", "value"])
        w.writerows(rows)
    print(f"  Saved {out_path}  ({len(rows)} rows)")
    return len(rows)


def cmd_export(ns: argparse.Namespace) -> int:
    """Export eval artifacts to .mat and/or long-format CSV.

    The positional `path` may be:
      - a .npz file               -> .mat (format must allow 'mat')
      - a summary.json            -> CSV  (format must allow 'csv')
      - a run dir / eval_dr dir   -> auto: every data_*.npz -> .mat (if 'mat'),
                                     summary.json -> CSV (if 'csv')
    """
    path = ns.path.rstrip("/")
    want_mat = ns.format in ("mat", "both")
    want_csv = ns.format in ("csv", "both")
    out_dir = ns.output_dir or (path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path)))
    os.makedirs(out_dir, exist_ok=True)

    n_mat = n_csv = 0

    if os.path.isfile(path) and path.endswith(".npz"):
        if not want_mat:
            print(f"[WARN] {path} is a trajectory npz but --format={ns.format} excludes 'mat'; nothing to do.")
            return 1
        out = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ".mat")
        _npz_to_mat(path, out)
        n_mat += 1
    elif os.path.isfile(path) and path.endswith(".json"):
        if not want_csv:
            print(f"[WARN] {path} is a summary json but --format={ns.format} excludes 'csv'; nothing to do.")
            return 1
        run_label = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(path)))) or "run"
        out = os.path.join(out_dir, "summary.csv")
        _summary_to_csv(path, out, run_label)
        n_csv += 1
    elif os.path.isdir(path):
        # auto: scan the dir (and an eval_dr/ subdir) for both artifact kinds
        search_dirs = [path]
        eval_sub = os.path.join(path, "eval_dr")
        if os.path.isdir(eval_sub):
            search_dirs.append(eval_sub)
        run_label = os.path.basename(path) or "run"
        for d in search_dirs:
            if want_mat:
                for fn in sorted(f for f in os.listdir(d) if f.endswith(".npz")):
                    _npz_to_mat(os.path.join(d, fn), os.path.join(out_dir, os.path.splitext(fn)[0] + ".mat"))
                    n_mat += 1
            if want_csv:
                js = os.path.join(d, "summary.json")
                if os.path.isfile(js):
                    _summary_to_csv(js, os.path.join(out_dir, "summary.csv"), run_label)
                    n_csv += 1
    else:
        print(f"[ERROR] path not found or unsupported: {path}")
        return 1

    if n_mat == 0 and n_csv == 0:
        print(f"[WARN] nothing exported from {path} (no matching artifacts for --format={ns.format}).")
        return 1
    print(f"Export done: {n_mat} .mat, {n_csv} .csv -> {out_dir}")
    return 0
