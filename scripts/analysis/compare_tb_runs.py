# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Compare TensorBoard metrics across multiple Hero Agent training runs.

Prints side-by-side metric tables at configurable iteration checkpoints.

Usage:
    # Compare two most recent runs
    python scripts/analysis/compare_tb_runs.py --runs 0 1

    # Compare by path
    python scripts/analysis/compare_tb_runs.py \
        --runs logs/rsl_rl/hero_agent_.../run_a logs/rsl_rl/hero_agent_.../run_b \
        --labels "Run A" "Run B"

    # Custom metrics and iterations
    python scripts/analysis/compare_tb_runs.py --runs 0 1 \
        --metrics "Attitude_Error/roll_deg" "Train/mean_reward" \
        --iters 100 200 500 1000
"""

import argparse

from common import load_tb_scalars, resolve_run_path

DEFAULT_METRICS = [
    "Attitude_Error/roll_deg",
    "Attitude_Error/pitch_deg",
    "Train/mean_reward",
    "Loss/value_function",
    "Loss/surrogate",
    "Loss/entropy",
]

DEFAULT_ITERS = [50, 100, 200, 300, 500, 600, 800, 1000, 1500]


def find_closest_value(data: list[tuple[int, float]], target: int, tolerance: int = 10):
    """Find value at the closest step to target within tolerance."""
    if not data:
        return None
    best = None
    best_dist = float("inf")
    for step, value in data:
        dist = abs(step - target)
        if dist < best_dist:
            best_dist = dist
            best = (step, value)
    if best and best_dist <= tolerance:
        return best
    return None


def main():
    parser = argparse.ArgumentParser(description="Compare TB metrics across runs")
    parser.add_argument("--runs", nargs="+", required=True, help="Run paths or indices (0=latest)")
    parser.add_argument("--labels", nargs="+", default=None, help="Labels for each run (default: dir name)")
    parser.add_argument("--metrics", nargs="+", default=DEFAULT_METRICS, help="Metrics to compare")
    parser.add_argument("--iters", nargs="+", type=int, default=DEFAULT_ITERS, help="Iterations to report")
    args = parser.parse_args()

    # Resolve run paths
    run_paths = [resolve_run_path(r) for r in args.runs]
    labels = args.labels or [f"{p.parent.name}/{p.name}" for p in run_paths]
    assert len(run_paths) == len(labels), "Number of labels must match number of runs"

    # Short labels for table headers (max 20 chars)
    short_labels = [l[:20] for l in labels]

    # Load data
    all_data = {}
    for label, path in zip(labels, run_paths):
        print(f"Loading: {label} -> {path}")
        all_data[label] = load_tb_scalars(str(path))

    # ---- Available tags ----
    print(f"\n{'=' * 100}")
    print("AVAILABLE TAGS PER RUN:")
    print(f"{'=' * 100}")
    for label in labels:
        tags = sorted(all_data[label].keys())
        print(f"\n  {label} ({len(tags)} tags):")
        for t in tags[:30]:
            entries = all_data[label][t]
            steps = [s for s, _ in entries]
            print(f"    {t:55s}  steps: {min(steps):5d} - {max(steps):5d}  ({len(entries)} pts)")
        if len(tags) > 30:
            print(f"    ... and {len(tags) - 30} more")

    # ---- Comparison tables ----
    print(f"\n{'=' * 100}")
    print("COMPARISON TABLES")
    print(f"{'=' * 100}")

    for metric in args.metrics:
        has_data = any(metric in all_data[l] for l in labels)
        if not has_data:
            continue

        print(f"\n  {metric}")
        header = f"  {'Iter':>6s}"
        for sl in short_labels:
            header += f"  {sl:>20s}"
        print(header)
        print(f"  {'----':>6s}" + "  " + ("  ".join(["-" * 20] * len(labels))))

        for target in args.iters:
            row = f"  {target:6d}"
            any_value = False
            for label in labels:
                entries = all_data[label].get(metric, [])
                result = find_closest_value(entries, target)
                if result:
                    _, val = result
                    row += f"  {val:20.6f}"
                    any_value = True
                else:
                    row += f"  {'--':>20s}"
            if any_value:
                print(row)

        # Last value
        row_last = f"  {'LAST':>6s}"
        for label in labels:
            entries = all_data[label].get(metric, [])
            if entries:
                last_step, last_val = entries[-1]
                row_last += f"  {last_val:14.4f}@{last_step:<5d}"
            else:
                row_last += f"  {'--':>20s}"
        print(row_last)

    # ---- Final summary ----
    print(f"\n{'=' * 100}")
    print("FINAL SUMMARY (last value per metric)")
    print(f"{'=' * 100}")

    header = f"  {'Metric':45s}"
    for sl in short_labels:
        header += f"  {sl:>20s}"
    print(header)
    print(f"  {'-' * 45}" + "  " + ("  ".join(["-" * 20] * len(labels))))

    for metric in args.metrics:
        row = f"  {metric:45s}"
        for label in labels:
            entries = all_data[label].get(metric, [])
            if entries:
                _, last_val = entries[-1]
                row += f"  {last_val:20.6f}"
            else:
                row += f"  {'N/A':>20s}"
        print(row)

    # ---- Encoder-related metrics (auto-discover) ----
    encoder_tags = set()
    for label in labels:
        for t in all_data[label]:
            if any(k in t.lower() for k in ["encoder", "z_", "latent", "adapt"]):
                encoder_tags.add(t)

    if encoder_tags:
        print(f"\n{'=' * 100}")
        print("ENCODER METRICS (auto-discovered)")
        print(f"{'=' * 100}")

        for metric in sorted(encoder_tags):
            if metric in args.metrics:
                continue
            has_data = any(metric in all_data[l] for l in labels)
            if not has_data:
                continue

            row_last = f"  {metric:45s}"
            for label in labels:
                entries = all_data[label].get(metric, [])
                if entries:
                    last_step, last_val = entries[-1]
                    row_last += f"  {last_val:14.4f}@{last_step:<5d}"
                else:
                    row_last += f"  {'--':>20s}"
            print(row_last)

    print(f"\n{'=' * 100}")
    print("Analysis complete.")


if __name__ == "__main__":
    main()
