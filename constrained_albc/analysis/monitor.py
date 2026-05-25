# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Training-time monitoring for constrained_full_albc (pure Python, no Isaac Sim).

Subcommands:
    plot     <run> --output        single-run 6-panel TB dashboard
    compare  --runs --metrics       multi-run TB metric table
    wandb    --entity --project     create WandB training report

Usage:
    python3 scripts/analysis/monitor.py plot 0
    python3 scripts/analysis/monitor.py compare --runs 0 1 --metrics "Train/mean_reward"
    python3 scripts/analysis/monitor.py wandb --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# compare subcommand constants
# ---------------------------------------------------------------------------

DEFAULT_METRICS = [
    "Track/att/roll_err_deg",
    "Track/att/pitch_err_deg",
    "Train/mean_reward",
    "Loss/value_function",
    "Loss/surrogate",
    "Loss/entropy",
]

DEFAULT_ITERS = [50, 100, 200, 300, 500, 600, 800, 1000, 1500]

# ---------------------------------------------------------------------------
# wandb subcommand constants
# ---------------------------------------------------------------------------

PANELS: list[dict[str, str | list[str]]] = [
    {
        "title": "1. Training Progress",
        "metrics": [
            "Train/mean_reward",
            "Reward/total",
            "Train/mean_episode_length",
        ],
    },
    {
        "title": "2. Reward Breakdown",
        "metrics": [
            "Reward/att_rp",
            "Reward/lin_vel",
            "Reward/yaw_vel",
            "Reward/torque",
            "Reward/thruster",
            "Reward/smoothness",
        ],
    },
    {
        "title": "3. Tracking Error",
        "metrics": [
            "Track/att/roll_err_deg",
            "Track/att/pitch_err_deg",
            "Track/lin/err_x",
            "Track/lin/err_y",
            "Track/lin/err_z",
            "Track/yaw/rate_err",
        ],
    },
    {
        "title": "4. Encoder Health",
        "metrics": [
            "Encoder/z_mean",
            "Encoder/z_std",
            "Encoder/z_min",
            "Encoder/z_max",
            "Policy/encoder_grad_norm",
        ],
    },
    {
        "title": "5. DORAEMON DR Scheduling",
        "metrics": [
            "DORAEMON/success_rate",
            "DORAEMON/entropy_before",
            "DORAEMON/entropy_after",
            "DORAEMON/kl_step",
        ],
    },
    {
        "title": "6. Constraint (IPO)",
        "metrics": [
            "Constraint/barrier_penalty",
            "Policy/line_search_success",
            "Policy/entropy",
        ],
    },
    {
        "title": "7. Policy & Gradient",
        "metrics": [
            "Policy/surrogate_loss",
            "Loss/value_function",
            "Loss/cost_value",
            "Grad/enc_step",
            "Grad/actor_step",
            "Noise/std_mean",
            "Noise/std_min",
        ],
    },
    {
        "title": "8. DR Parameters",
        "metrics": [
            "DR/buoyancy_force_mean",
            "DR/inertia_roll_mean",
            "DR/inertia_pitch_mean",
            "DR/payload_mass_mean",
            "DR/ocean_current_mag_mean",
        ],
    },
]


# ---------------------------------------------------------------------------
# compare helper
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# plot subcommand
# ---------------------------------------------------------------------------


def cmd_plot(args: argparse.Namespace) -> None:
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    from common import load_tb_scalars, resolve_run_path, smooth

    matplotlib.use("Agg")

    run_path = resolve_run_path(args.run)
    print(f"[INFO] Run: {run_path}")
    log_dir = str(run_path)
    output = args.output

    data = load_tb_scalars(log_dir)

    def _steps_vals(tag: str) -> tuple[np.ndarray, np.ndarray] | None:
        if tag not in data:
            return None
        entries = data[tag]
        return np.array([s for s, _ in entries]), np.array([v for _, v in entries])

    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle(f"Encoder Training: {Path(log_dir).name}", fontsize=14, fontweight="bold")

    # -- Panel 1: Encoder z statistics --
    ax = axes[0, 0]
    for tag, label, color in [
        ("Encoder/z_mean", "z_mean", "#2196F3"),
        ("Encoder/z_std", "z_std", "#FF9800"),
        ("Encoder/z_min", "z_min", "#F44336"),
        ("Encoder/z_max", "z_max", "#4CAF50"),
    ]:
        sv = _steps_vals(tag)
        if sv is not None:
            steps, vals = sv
            ax.plot(steps, vals, alpha=0.25, color=color, linewidth=0.5)
            ax.plot(steps, smooth(vals), color=color, label=label, linewidth=1.5)
    ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.3, label="tanh bounds")
    ax.axhline(y=-1.0, color="gray", linestyle="--", alpha=0.3)
    ax.axhline(y=0.99, color="red", linestyle=":", alpha=0.3, label="saturation zone")
    ax.axhline(y=-0.99, color="red", linestyle=":", alpha=0.3)
    ax.set_ylabel("z value")
    ax.set_title("Encoder z Statistics")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 2: Encoder grad norm --
    ax = axes[0, 1]
    sv = _steps_vals("Policy/encoder_grad_norm")
    if sv is not None:
        steps, vals = sv
        ax.plot(steps, vals, alpha=0.25, color="#9C27B0", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#9C27B0", label="grad_norm", linewidth=1.5)
    ax.set_ylabel("Gradient Norm")
    ax.set_title("Encoder Gradient Norm")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 3: Attitude Error --
    ax = axes[1, 0]
    for tag, label, color in [
        ("Track/att/roll_err_deg", "Roll Error", "#E91E63"),
        ("Track/att/pitch_err_deg", "Pitch Error", "#3F51B5"),
    ]:
        sv = _steps_vals(tag)
        if sv is not None:
            steps, vals = sv
            ax.plot(steps, vals, alpha=0.2, color=color, linewidth=0.5)
            ax.plot(steps, smooth(vals), color=color, label=label, linewidth=1.5)
    ax.axhline(y=5.0, color="green", linestyle="--", alpha=0.4, label="5 deg target")
    ax.axhline(y=2.0, color="green", linestyle=":", alpha=0.4, label="2 deg target")
    ax.set_ylabel("Error (degrees)")
    ax.set_title("Attitude Error")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 4: Mean Reward --
    ax = axes[1, 1]
    for tag, label, color in [
        ("Train/mean_reward", "mean_reward", "#009688"),
        ("Reward/total", "episode_total", "#FF5722"),
    ]:
        sv = _steps_vals(tag)
        if sv is not None:
            steps, vals = sv
            ax.plot(steps, vals, alpha=0.2, color=color, linewidth=0.5)
            ax.plot(steps, smooth(vals), color=color, label=label, linewidth=1.5)
    ax.set_ylabel("Reward")
    ax.set_title("Training Reward")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 5: DORAEMON DR progress --
    ax = axes[2, 0]
    sv = _steps_vals("DORAEMON/success_rate")
    if sv is not None:
        steps, vals = sv
        ax.plot(steps, vals, alpha=0.2, color="#795548", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#795548", label="success_rate", linewidth=1.5)
    sv_e = _steps_vals("DORAEMON/entropy")
    if sv_e is not None:
        steps_e, vals_e = sv_e
        ax2 = ax.twinx()
        ax2.plot(steps_e, vals_e, alpha=0.2, color="#607D8B", linewidth=0.5)
        ax2.plot(steps_e, smooth(vals_e), color="#607D8B", label="entropy", linewidth=1.5)
        ax2.set_ylabel("Entropy", color="#607D8B")
        ax2.legend(loc="lower right", fontsize=8)
    ax.set_ylabel("Success Rate", color="#795548")
    ax.set_xlabel("Iteration")
    ax.set_title("DORAEMON DR Scheduling")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 6: Reward Breakdown --
    ax = axes[2, 1]
    reward_tags = [
        ("Reward/lin_vel", "lin_vel", "#4CAF50"),
        ("Reward/att_rp", "att_rp", "#2196F3"),
        ("Reward/yaw_vel", "yaw_vel", "#F44336"),
        ("Reward/torque", "torque", "#FF9800"),
        ("Reward/thruster", "thruster", "#9C27B0"),
        ("Reward/smoothness", "smoothness", "#795548"),
        ("Reward/bias", "bias", "#00BCD4"),
    ]
    for tag, label, color in reward_tags:
        sv = _steps_vals(tag)
        if sv is not None:
            steps, vals = sv
            ax.plot(steps, smooth(vals, window=25), color=color, label=label, linewidth=1.2)
    ax.set_ylabel("Episode Reward Component")
    ax.set_xlabel("Iteration")
    ax.set_title("Reward Breakdown")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output is None:
        output = str(Path(log_dir) / "encoder_dashboard.png")
    plt.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Saved: {output}")
    plt.close()


# ---------------------------------------------------------------------------
# compare subcommand
# ---------------------------------------------------------------------------


def cmd_compare(args: argparse.Namespace) -> None:
    from common import load_tb_scalars, resolve_run_path

    # Resolve run paths
    run_paths = [resolve_run_path(r) for r in args.runs]
    labels: list[str] = args.labels or [f"{p.parent.name}/{p.name}" for p in run_paths]
    assert len(run_paths) == len(labels), "Number of labels must match number of runs"

    # Short labels for table headers (max 20 chars)
    short_labels = [label[:20] for label in labels]

    # Load data
    all_data: dict[str, dict] = {}
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
        has_data = any(metric in all_data[label] for label in labels)
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
    encoder_tags: set[str] = set()
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
            has_data = any(metric in all_data[label] for label in labels)
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


# ---------------------------------------------------------------------------
# wandb subcommand
# ---------------------------------------------------------------------------


def _wandb_dry_run() -> None:
    """Print the panel layout without creating a WandB report."""
    total = 0
    print("=" * 60)
    print("TRPO + IPO + Encoder Training Dashboard - Panel Layout")
    print("=" * 60)
    for panel in PANELS:
        metrics = panel["metrics"]
        print(f"\n## {panel['title']} ({len(metrics)} metrics)")
        for m in metrics:
            print(f"  - {m}")
        total += len(metrics)
    print(f"\n{'=' * 60}")
    print(f"Total: {total} metrics across {len(PANELS)} panels")
    print("=" * 60)


def _wandb_create_report(entity: str, project: str, run_filter: str | None = None) -> str:
    """Create WandB report with TRPO + IPO + Encoder training dashboard.

    Args:
        entity: WandB entity (username or team).
        project: WandB project name.
        run_filter: Optional run name glob filter.

    Returns:
        URL of the created report.
    """
    try:
        import wandb_workspaces.reports.v2 as wr
    except ImportError:
        print(
            "ERROR: wandb_workspaces not installed.\n"
            "Install with: pip install wandb[workspaces]\n"
            "Or use --dry-run to preview panel layout without creating a report.",
            file=sys.stderr,
        )
        sys.exit(1)

    blocks: list = [
        wr.H1("TRPO + IPO + Encoder Training Dashboard"),
        wr.P(
            "Full-DOF ALBC training health dashboard. "
            "Panels cover reward, tracking error, encoder z statistics, "
            "DORAEMON DR scheduling, constraint (IPO), and gradient diagnostics."
        ),
    ]

    runset_kwargs: dict = {"entity": entity, "project": project}
    if run_filter:
        runset_kwargs["filters"] = {"display_name": {"$regex": run_filter}}

    runset = wr.Runset(**runset_kwargs)

    for panel_def in PANELS:
        metrics = panel_def["metrics"]
        blocks.append(wr.H2(str(panel_def["title"])))
        blocks.append(
            wr.PanelGrid(
                panels=[
                    wr.LinePlot(
                        title=str(panel_def["title"]),
                        y=[m for m in metrics],
                        smoothing_factor=0.6,
                    )
                ],
                runsets=[runset],
            )
        )

    report = wr.Report(
        entity=entity,
        project=project,
        title="TRPO + IPO + Encoder Training Dashboard",
        description="8-panel monitoring dashboard for constrained_full_albc TRPO + Encoder training",
        blocks=blocks,
    )

    report.save()
    url = report.url
    print(f"Report created: {url}")
    return url


def cmd_wandb(args: argparse.Namespace) -> None:
    if args.dry_run:
        _wandb_dry_run()
    else:
        if args.entity is None:
            args._parser.error("--entity is required when not using --dry-run")
        _wandb_create_report(args.entity, args.project, args.run_filter)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Training-time monitoring for constrained_full_albc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # -- plot --
    p_plot = sub.add_parser("plot", help="Single-run 6-panel TB dashboard")
    p_plot.add_argument("run", help="Path to log directory, run index (0=latest), or substring match")
    p_plot.add_argument("--output", "-o", help="Output image path (default: <log_dir>/encoder_dashboard.png)")
    p_plot.set_defaults(func=cmd_plot)

    # -- compare --
    p_cmp = sub.add_parser("compare", help="Multi-run TB metric table")
    p_cmp.add_argument("--runs", nargs="+", required=True, help="Run paths or indices (0=latest)")
    p_cmp.add_argument("--labels", nargs="+", default=None, help="Labels for each run (default: dir name)")
    p_cmp.add_argument("--metrics", nargs="+", default=DEFAULT_METRICS, help="Metrics to compare")
    p_cmp.add_argument("--iters", nargs="+", type=int, default=DEFAULT_ITERS, help="Iterations to report")
    p_cmp.set_defaults(func=cmd_compare)

    # -- wandb --
    p_wb = sub.add_parser("wandb", help="Create WandB training report")
    p_wb.add_argument("--entity", default=None, help="WandB entity (username or team)")
    p_wb.add_argument("--project", default="full_dof_trpo", help="WandB project name")
    p_wb.add_argument(
        "--run-filter",
        default=None,
        help="Optional run name glob filter (e.g., 'full_dof*')",
    )
    p_wb.add_argument(
        "--dry-run",
        action="store_true",
        help="Print panel layout without creating WandB report",
    )
    p_wb.set_defaults(func=cmd_wandb, _parser=p_wb)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
