# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Create a WandB Report with PPO + Encoder training health dashboard.

Usage:
    # Preview panel layout (no WandB dependency):
    python scripts/analysis/create_wandb_dashboard.py --dry-run

    # Create WandB report:
    python scripts/analysis/create_wandb_dashboard.py \
        --entity <WANDB_ENTITY> --project hero_agent

    # With specific run filter:
    python scripts/analysis/create_wandb_dashboard.py \
        --entity <WANDB_ENTITY> --project hero_agent \
        --run-filter "encoder-base*"
"""

from __future__ import annotations

import argparse
import sys


# =============================================================================
# Panel Definitions (8-panel PPO + Encoder dashboard)
# =============================================================================

PANELS: list[dict[str, str | list[str]]] = [
    {
        "title": "1. Training Progress (Primary)",
        "metrics": [
            "Train/mean_reward",
            "Episode_Reward/total",
            "Train/episode_length",
            "Attitude_Error/roll_deg",
            "Attitude_Error/pitch_deg",
        ],
    },
    {
        "title": "2. Reward Breakdown",
        "metrics": [
            "Episode_Reward/tracking",
            "Episode_Reward/settling",
            "Episode_Reward/linear_error",
            "Episode_Reward/progress",
            "Episode_Reward/action_magnitude",
            "Episode_Reward/action_rate",
            "Episode_Reward/joint_velocity",
            "Episode_Reward/joint_oscillation",
        ],
    },
    {
        "title": "3. PPO Loss",
        "metrics": [
            "Loss/value_function",
            "Loss/surrogate",
            "Loss/entropy",
            "Loss/learning_rate",
        ],
    },
    {
        "title": "4. Encoder Health",
        "metrics": [
            "Encoder/z_mean",
            "Encoder/z_std",
            "Encoder/z_min",
            "Encoder/z_max",
            "Encoder/grad_norm",
            "Loss/encoder",
        ],
    },
    {
        "title": "5. DORAEMON DR Scheduling",
        "metrics": [
            "DORAEMON/success_rate",
            "DORAEMON/entropy",
            "DORAEMON/temperature",
        ],
    },
    {
        "title": "6. Constraint Costs (NORBC)",
        "metrics": [
            "Constraint/joint_velocity",
            "Constraint/joint_oscillation",
            "Constraint/barrier_cost_total",
        ],
    },
    {
        "title": "7. Training Diagnostics",
        "metrics": [
            "Train/fps",
            "Train/terminated",
            "Train/time_out",
        ],
    },
    {
        "title": "8. DR Parameters (Sanity Check)",
        "metrics": [
            "DR/buoyancy_force_mean",
            "DR/inertia_mean",
            "DR/payload_mass_mean",
            "DR/ocean_current_mag_mean",
        ],
    },
]


def dry_run() -> None:
    """Print the panel layout without creating a WandB report."""
    total = 0
    print("=" * 60)
    print("PPO + Encoder Training Dashboard - Panel Layout")
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


def create_report(entity: str, project: str, run_filter: str | None = None) -> str:
    """Create WandB report with PPO + Encoder training dashboard.

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
        wr.H1("PPO + Encoder Training Dashboard"),
        wr.P(
            "Hero Agent training health dashboard. "
            "Panels cover reward, PPO loss, encoder z statistics, "
            "DORAEMON DR scheduling, and constraint costs."
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
        title="PPO + Encoder Training Dashboard",
        description="8-panel monitoring dashboard for Hero Agent PPO + Encoder training",
        blocks=blocks,
    )

    report.save()
    url = report.url
    print(f"Report created: {url}")
    return url


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create WandB Report with PPO + Encoder training dashboard"
    )
    parser.add_argument("--entity", default=None, help="WandB entity (username or team)")
    parser.add_argument("--project", default="hero_agent", help="WandB project name")
    parser.add_argument(
        "--run-filter",
        default=None,
        help="Optional run name glob filter (e.g., 'encoder-base*')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print panel layout without creating WandB report",
    )
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        if args.entity is None:
            parser.error("--entity is required when not using --dry-run")
        create_report(args.entity, args.project, args.run_filter)


if __name__ == "__main__":
    main()
