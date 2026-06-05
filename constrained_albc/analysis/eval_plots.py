# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free plotting helpers extracted from eval.py.

Every function here is pure matplotlib/plotly/numpy and imports on plain
python3 (no Isaac Sim). This is what makes eval output replottable by omx
exp-analyze without booting sim. Mirrors the _eval_dr/ extraction pattern.
"""

from __future__ import annotations

import os  # noqa: E402

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402,F401
import numpy as np  # noqa: E402,F401
from matplotlib.ticker import MultipleLocator  # noqa: E402,F401

from common import DR_COLORS, DR_LEVELS, DR_SCALE  # type: ignore[import-not-found]  # noqa: E402
from _eval_dr.metrics import _get_block_step_range, _pick_sample_env  # type: ignore[import-not-found]  # noqa: E402

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False


def _bar_subplot(ax, x, values, colors, xlabels, ylabel, title, ylim=None, yerr=None):
    """Render a single bar chart subplot with consistent styling."""
    ax.bar(x, values, color=colors, yerr=yerr, capsize=4, error_kw={"linewidth": 1.2})
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(True, alpha=0.3, axis="y")


def generate_plots(
    all_data: dict[str, dict],
    all_metrics: dict[str, dict],
    output_dir: str,
) -> None:
    """Generate all evaluation figures. PNG for all, HTML (interactive) for core plots."""
    levels = [lvl for lvl in DR_LEVELS if lvl in all_data]

    # Static PNG plots
    _plot_attitude_tracking(all_data, levels, output_dir)
    _plot_lin_vel(all_data, levels, output_dir)
    _plot_yaw_rate(all_data, levels, output_dir)
    _plot_error(all_data, levels, output_dir)
    _plot_summary_attitude(all_metrics, levels, output_dir)
    _plot_summary_lin_vel(all_metrics, levels, output_dir)
    _plot_summary_yaw(all_metrics, levels, output_dir)
    _plot_failure_time(all_data, levels, output_dir)

    # Interactive HTML plots (core tracking plots only) -- skip if plotly missing
    if _HAS_PLOTLY:
        _plot_attitude_interactive(all_data, levels, output_dir)
        _plot_lin_vel_interactive(all_data, levels, output_dir)
        _plot_yaw_rate_interactive(all_data, levels, output_dir)
        _plot_error_interactive(all_data, levels, output_dir)


# ---------------------------------------------------------------------------
# Interactive Plotly plots (HTML, hover tooltips)
# ---------------------------------------------------------------------------


def _plotly_color(lvl: str) -> str:
    """Convert matplotlib color name/hex to CSS color for plotly."""
    from matplotlib.colors import to_hex
    return to_hex(DR_COLORS[lvl])


def _plot_attitude_interactive(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Interactive roll/pitch attitude tracking per DR level (rows = DR, cols = roll/pitch)."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    if att_start >= att_end:
        return

    fig = make_subplots(
        rows=len(levels), cols=2,
        shared_xaxes=True, shared_yaxes=False,
        subplot_titles=[f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%) - {ax}"
                        for lvl in levels for ax in ("Roll", "Pitch")],
        vertical_spacing=0.06, horizontal_spacing=0.08,
    )
    block_time = np.arange(att_end - att_start) * step_dt

    for row_idx, lvl in enumerate(levels, start=1):
        d = all_data[lvl]
        color = _plotly_color(lvl)
        alive = ~d["terminated"][att_start:att_end]

        for col_idx, (actual_key, target_key) in enumerate(
            [("actual_roll_deg", "target_roll_deg"), ("actual_pitch_deg", "target_pitch_deg")],
            start=1,
        ):
            target = d[target_key][att_start:att_end]
            vals = np.where(alive, d[actual_key][att_start:att_end], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)

            # Target line
            fig.add_trace(
                go.Scatter(x=block_time, y=target, mode="lines",
                           line=dict(color="black", width=1.2, dash="dash"),
                           name="target", legendgroup="target",
                           showlegend=(row_idx == 1 and col_idx == 1),
                           hovertemplate="t=%{x:.2f}s<br>target=%{y:.2f} deg<extra></extra>"),
                row=row_idx, col=col_idx,
            )
            # Std band (upper + lower fill)
            fig.add_trace(
                go.Scatter(x=np.concatenate([block_time, block_time[::-1]]),
                           y=np.concatenate([mean + std, (mean - std)[::-1]]),
                           fill="toself", fillcolor=color, opacity=0.15,
                           line=dict(color="rgba(0,0,0,0)"),
                           name=f"{lvl} +/-std", showlegend=False, hoverinfo="skip"),
                row=row_idx, col=col_idx,
            )
            # Mean line
            fig.add_trace(
                go.Scatter(x=block_time, y=mean, mode="lines",
                           line=dict(color=color, width=1.5),
                           name=f"{lvl}", legendgroup=lvl,
                           showlegend=(col_idx == 1),
                           hovertemplate=("t=%{x:.2f}s<br>mean=%{y:.2f} deg"
                                          f"<br>DR={int(DR_SCALE[lvl] * 100)}%<extra></extra>")),
                row=row_idx, col=col_idx,
            )

    fig.update_layout(
        title="Attitude Tracking per DR Level (attitude block) -- interactive",
        height=260 * len(levels), hovermode="x unified",
    )
    for row in range(1, len(levels) + 1):
        fig.update_yaxes(title_text="Roll (deg)", row=row, col=1)
        fig.update_yaxes(title_text="Pitch (deg)", row=row, col=2)
    fig.update_xaxes(title_text="Time (s)", row=len(levels), col=1)
    fig.update_xaxes(title_text="Time (s)", row=len(levels), col=2)
    fig.write_html(os.path.join(output_dir, "traj_attitude.html"), include_plotlyjs="cdn")


def _plot_lin_vel_interactive(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Interactive linear velocity tracking per DR level (rows = DR, cols = vx/vy/vz)."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    lv_start, lv_end = _get_block_step_range(seg_names, seg_steps, "lin_vel")
    if lv_start >= lv_end:
        return

    data_keys = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    target_keys = ["target_vx", "target_vy", "target_vz"]
    axis_labels = ["Vx (m/s)", "Vy (m/s)", "Vz (m/s)"]

    fig = make_subplots(
        rows=len(levels), cols=3,
        shared_xaxes=True,
        subplot_titles=[f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%) - {ax}"
                        for lvl in levels for ax in ("Vx", "Vy", "Vz")],
        vertical_spacing=0.06, horizontal_spacing=0.06,
    )
    block_time = np.arange(lv_end - lv_start) * step_dt

    for row_idx, lvl in enumerate(levels, start=1):
        d = all_data[lvl]
        color = _plotly_color(lvl)
        alive = ~d["terminated"][lv_start:lv_end]

        for col_idx, (dkey, tkey, label) in enumerate(zip(data_keys, target_keys, axis_labels), start=1):
            target = d[tkey][lv_start:lv_end]
            vals = np.where(alive, d[dkey][lv_start:lv_end], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)

            fig.add_trace(
                go.Scatter(x=block_time, y=target, mode="lines",
                           line=dict(color="black", width=1.2, dash="dash"),
                           name="target", legendgroup="target",
                           showlegend=(row_idx == 1 and col_idx == 1),
                           hovertemplate="t=%{x:.2f}s<br>target=%{y:.3f} m/s<extra></extra>"),
                row=row_idx, col=col_idx,
            )
            fig.add_trace(
                go.Scatter(x=np.concatenate([block_time, block_time[::-1]]),
                           y=np.concatenate([mean + std, (mean - std)[::-1]]),
                           fill="toself", fillcolor=color, opacity=0.15,
                           line=dict(color="rgba(0,0,0,0)"),
                           showlegend=False, hoverinfo="skip"),
                row=row_idx, col=col_idx,
            )
            fig.add_trace(
                go.Scatter(x=block_time, y=mean, mode="lines",
                           line=dict(color=color, width=1.5),
                           name=f"{lvl}", legendgroup=lvl,
                           showlegend=(col_idx == 1),
                           hovertemplate=("t=%{x:.2f}s<br>mean=%{y:.3f} m/s"
                                          f"<br>DR={int(DR_SCALE[lvl] * 100)}%<extra></extra>")),
                row=row_idx, col=col_idx,
            )

    fig.update_layout(
        title="Linear Velocity Tracking per DR Level (lin_vel block) -- interactive",
        height=240 * len(levels), hovermode="x unified",
    )
    for row in range(1, len(levels) + 1):
        for col_idx, label in enumerate(axis_labels, start=1):
            fig.update_yaxes(title_text=label, row=row, col=col_idx)
    for col_idx in range(1, 4):
        fig.update_xaxes(title_text="Time (s)", row=len(levels), col=col_idx)
    fig.write_html(os.path.join(output_dir, "traj_linvel.html"), include_plotlyjs="cdn")


def _plot_yaw_rate_interactive(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Interactive yaw rate tracking per DR level (rows = DR)."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    yaw_start, yaw_end = _get_block_step_range(seg_names, seg_steps, "yaw")
    if yaw_start >= yaw_end:
        return

    fig = make_subplots(
        rows=len(levels), cols=1, shared_xaxes=True,
        subplot_titles=[f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels],
        vertical_spacing=0.06,
    )
    block_time = np.arange(yaw_end - yaw_start) * step_dt

    for row_idx, lvl in enumerate(levels, start=1):
        d = all_data[lvl]
        color = _plotly_color(lvl)
        alive = ~d["terminated"][yaw_start:yaw_end]
        target = d["target_yaw_rate"][yaw_start:yaw_end]
        vals = np.where(alive, d["yaw_rate"][yaw_start:yaw_end], np.nan)
        mean = np.nanmean(vals, axis=1)
        std = np.nanstd(vals, axis=1)

        fig.add_trace(
            go.Scatter(x=block_time, y=target, mode="lines",
                       line=dict(color="black", width=1.2, dash="dash"),
                       name="target", legendgroup="target", showlegend=(row_idx == 1),
                       hovertemplate="t=%{x:.2f}s<br>target=%{y:.3f} rad/s<extra></extra>"),
            row=row_idx, col=1,
        )
        fig.add_trace(
            go.Scatter(x=np.concatenate([block_time, block_time[::-1]]),
                       y=np.concatenate([mean + std, (mean - std)[::-1]]),
                       fill="toself", fillcolor=color, opacity=0.15,
                       line=dict(color="rgba(0,0,0,0)"),
                       showlegend=False, hoverinfo="skip"),
            row=row_idx, col=1,
        )
        fig.add_trace(
            go.Scatter(x=block_time, y=mean, mode="lines",
                       line=dict(color=color, width=1.5),
                       name=f"{lvl}", legendgroup=lvl, showlegend=True,
                       hovertemplate=("t=%{x:.2f}s<br>mean=%{y:.3f} rad/s"
                                      f"<br>DR={int(DR_SCALE[lvl] * 100)}%<extra></extra>")),
            row=row_idx, col=1,
        )

    fig.update_layout(
        title="Yaw Rate Tracking per DR Level (yaw block) -- interactive",
        height=220 * len(levels), hovermode="x unified",
    )
    for row in range(1, len(levels) + 1):
        fig.update_yaxes(title_text="Yaw Rate (rad/s)", row=row, col=1)
    fig.update_xaxes(title_text="Time (s)", row=len(levels), col=1)
    fig.write_html(os.path.join(output_dir, "traj_yaw.html"), include_plotlyjs="cdn")


def _plot_error_interactive(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Interactive tracking error (|roll|, |pitch|, action mag), all DR overlaid, attitude block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    if att_start >= att_end:
        return

    has_actions = "action_magnitude" in ref
    n_rows = 3 if has_actions else 2
    titles = ["|Roll Error|", "|Pitch Error|"] + (["Action Magnitude"] if has_actions else [])
    fig = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=True,
        subplot_titles=titles, vertical_spacing=0.08,
    )
    block_time = np.arange(att_end - att_start) * step_dt

    for lvl in levels:
        d = all_data[lvl]
        color = _plotly_color(lvl)
        alive = ~d["terminated"][att_start:att_end]
        label = f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%)"

        for row_idx, key in enumerate([("error_roll", "deg"), ("error_pitch", "deg")], start=1):
            key_name, unit = key
            vals = np.where(alive, np.abs(d[key_name][att_start:att_end]), np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            fig.add_trace(
                go.Scatter(x=np.concatenate([block_time, block_time[::-1]]),
                           y=np.concatenate([mean + std, (mean - std)[::-1]]),
                           fill="toself", fillcolor=color, opacity=0.12,
                           line=dict(color="rgba(0,0,0,0)"),
                           showlegend=False, hoverinfo="skip"),
                row=row_idx, col=1,
            )
            fig.add_trace(
                go.Scatter(x=block_time, y=mean, mode="lines",
                           line=dict(color=color, width=1.3),
                           name=label, legendgroup=lvl,
                           showlegend=(row_idx == 1),
                           hovertemplate=(f"t=%{{x:.2f}}s<br>|err|=%{{y:.2f}} {unit}"
                                          f"<br>{label}<extra></extra>")),
                row=row_idx, col=1,
            )

        if has_actions:
            act_vals = np.where(alive, d["action_magnitude"][att_start:att_end], np.nan)
            act_mean = np.nanmean(act_vals, axis=1)
            act_std = np.nanstd(act_vals, axis=1)
            fig.add_trace(
                go.Scatter(x=np.concatenate([block_time, block_time[::-1]]),
                           y=np.concatenate([act_mean + act_std, (act_mean - act_std)[::-1]]),
                           fill="toself", fillcolor=color, opacity=0.12,
                           line=dict(color="rgba(0,0,0,0)"),
                           showlegend=False, hoverinfo="skip"),
                row=3, col=1,
            )
            fig.add_trace(
                go.Scatter(x=block_time, y=act_mean, mode="lines",
                           line=dict(color=color, width=1.3),
                           name=label, legendgroup=lvl, showlegend=False,
                           hovertemplate=(f"t=%{{x:.2f}}s<br>|a|=%{{y:.2f}}"
                                          f"<br>{label}<extra></extra>")),
                row=3, col=1,
            )

    fig.update_layout(
        title="Tracking Error vs DR Level (attitude block) -- interactive",
        height=300 * n_rows, hovermode="x unified",
    )
    fig.update_yaxes(title_text="|Roll Error| (deg)", row=1, col=1)
    fig.update_yaxes(title_text="|Pitch Error| (deg)", row=2, col=1)
    if has_actions:
        fig.update_yaxes(title_text="Action Magnitude", row=3, col=1)
    fig.update_xaxes(title_text="Time (s)", row=n_rows, col=1)
    fig.write_html(os.path.join(output_dir, "traj_error.html"), include_plotlyjs="cdn")


# ---------------------------------------------------------------------------
# Attitude tracking (cropped to attitude block, per-DR-row)
# ---------------------------------------------------------------------------

def _plot_attitude_tracking(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Roll/pitch attitude tracking per DR level (Nx2 grid), cropped to attitude block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    if att_start >= att_end:
        return

    fig, axes = plt.subplots(len(levels), 2, figsize=(16, 3 * len(levels)), sharex=True)
    fig.suptitle("Attitude Tracking per DR Level (attitude block)", fontsize=14, y=0.98)

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][att_start:att_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        block_time = np.arange(att_end - att_start) * step_dt
        sample_idx = _pick_sample_env(d)

        for col, (actual_key, target_key, axis_label) in enumerate(
            [
                ("actual_roll_deg", "target_roll_deg", "Roll (deg)"),
                ("actual_pitch_deg", "target_pitch_deg", "Pitch (deg)"),
            ]
        ):
            ax = axes[row, col] if len(levels) > 1 else axes[col]
            target = d[target_key][att_start:att_end]
            ax.plot(block_time, target, "k--", linewidth=1.2, alpha=0.6, label="target")
            vals = np.where(alive, d[actual_key][att_start:att_end], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(block_time, mean, color=color, linewidth=1.0, label="actual (mean)")
            ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.15)
            if sample_idx is not None:
                ax.plot(block_time, vals[:, sample_idx], color=color, linewidth=1.2,
                        linestyle="--", alpha=0.9, label=f"sample (env {sample_idx})")
            ax.set_ylabel(axis_label, fontsize=9)
            ax.yaxis.set_major_locator(MultipleLocator(15))
            ax.grid(True, alpha=0.3)
            if col == 0:
                ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10, fontweight="bold", color=color)
            if row == 0 and col == 0:
                ax.legend(loc="upper right", fontsize=8)
            if row == len(levels) - 1:
                ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "traj_attitude.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Linear velocity tracking (per-DR-row, 3 columns = vx/vy/vz)
# ---------------------------------------------------------------------------

def _plot_lin_vel(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Linear velocity tracking per DR level (Nx3 grid), cropped to lin_vel block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    lv_start, lv_end = _get_block_step_range(seg_names, seg_steps, "lin_vel")
    if lv_start >= lv_end:
        return

    data_keys = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    target_keys = ["target_vx", "target_vy", "target_vz"]
    axis_labels = ["Vx (m/s)", "Vy (m/s)", "Vz (m/s)"]

    fig, axes = plt.subplots(len(levels), 3, figsize=(18, 3 * len(levels)), sharex=True)
    fig.suptitle("Linear Velocity Tracking per DR Level (lin_vel block)", fontsize=14, y=0.98)

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][lv_start:lv_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        block_time = np.arange(lv_end - lv_start) * step_dt
        sample_idx = _pick_sample_env(d)

        for col, (dkey, tkey, ylabel) in enumerate(zip(data_keys, target_keys, axis_labels)):
            ax = axes[row, col] if len(levels) > 1 else axes[col]
            target = d[tkey][lv_start:lv_end]
            ax.plot(block_time, target, "k--", linewidth=1.2, alpha=0.6, label="target")
            vals = np.where(alive, d[dkey][lv_start:lv_end], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(block_time, mean, color=color, linewidth=1.0, label="actual (mean)")
            ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.15)
            if sample_idx is not None:
                ax.plot(block_time, vals[:, sample_idx], color=color, linewidth=1.2,
                        linestyle="--", alpha=0.9, label=f"sample (env {sample_idx})")
            ax.set_ylabel(ylabel, fontsize=9)
            ax.grid(True, alpha=0.3)
            if col == 0:
                ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10, fontweight="bold", color=color)
            if row == 0 and col == 1:
                ax.legend(loc="upper right", fontsize=8)
            if row == len(levels) - 1:
                ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "traj_linvel.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Yaw rate tracking (per-DR-row, 1 column)
# ---------------------------------------------------------------------------

def _plot_yaw_rate(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Yaw rate tracking per DR level (Nx1 grid), cropped to yaw block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    yaw_start, yaw_end = _get_block_step_range(seg_names, seg_steps, "yaw")
    if yaw_start >= yaw_end:
        return

    fig, axes = plt.subplots(len(levels), 1, figsize=(14, 3 * len(levels)), sharex=True)
    fig.suptitle("Yaw Rate Tracking per DR Level (yaw block)", fontsize=14, y=0.98)
    if len(levels) == 1:
        axes = [axes]

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][yaw_start:yaw_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        block_time = np.arange(yaw_end - yaw_start) * step_dt
        sample_idx = _pick_sample_env(d)

        ax = axes[row]
        target = d["target_yaw_rate"][yaw_start:yaw_end]
        ax.plot(block_time, target, "k--", linewidth=1.2, alpha=0.6, label="target")
        vals = np.where(alive, d["yaw_rate"][yaw_start:yaw_end], np.nan)
        mean = np.nanmean(vals, axis=1)
        std = np.nanstd(vals, axis=1)
        ax.plot(block_time, mean, color=color, linewidth=1.0, label="actual (mean)")
        ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.15)
        if sample_idx is not None:
            ax.plot(block_time, vals[:, sample_idx], color=color, linewidth=1.2,
                    linestyle="--", alpha=0.9, label=f"sample (env {sample_idx})")
        ax.set_ylabel("Yaw Rate (rad/s)", fontsize=9)
        ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10, fontweight="bold", color=color)
        ax.grid(True, alpha=0.3)
        if row == 0:
            ax.legend(loc="upper right", fontsize=8)
        if row == len(levels) - 1:
            ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "traj_yaw.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Error plot (|roll error|, |pitch error|, action magnitude -- all DR overlaid)
# ---------------------------------------------------------------------------

def _plot_error(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Tracking error and action magnitude, cropped to attitude block, all DR overlaid."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    if att_start >= att_end:
        return

    has_actions = "action_magnitude" in ref
    n_rows = 3 if has_actions else 2
    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 4 * n_rows), sharex=True)
    fig.suptitle("Tracking Error vs DR Level (attitude block)", fontsize=14)
    ax_re, ax_pe = axes[0], axes[1]

    block_time = np.arange(att_end - att_start) * step_dt

    for lvl in levels:
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][att_start:att_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        label = f"{lvl} (DR {dr_pct}%)"

        for ax, key in [(ax_re, "error_roll"), (ax_pe, "error_pitch")]:
            vals = np.where(alive, np.abs(d[key][att_start:att_end]), np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(block_time, mean, color=color, linewidth=1.2, label=label)
            ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.12)

        if has_actions:
            ax_act = axes[2]
            act_vals = np.where(alive, d["action_magnitude"][att_start:att_end], np.nan)
            act_mean = np.nanmean(act_vals, axis=1)
            act_std = np.nanstd(act_vals, axis=1)
            ax_act.plot(block_time, act_mean, color=color, linewidth=1.2, label=label)
            ax_act.fill_between(block_time, act_mean - act_std, act_mean + act_std, color=color, alpha=0.12)

    ax_re.set_ylabel("|Roll Error| (deg)")
    ax_pe.set_ylabel("|Pitch Error| (deg)")
    ax_re.legend(loc="upper right", fontsize=9)
    for _ax in [ax_re, ax_pe]:
        _ax.yaxis.set_major_locator(MultipleLocator(15))
        _ax.grid(True, alpha=0.3)
    if has_actions:
        axes[2].set_ylabel("Action Magnitude")
        axes[2].set_xlabel("Time (s)")
        axes[2].grid(True, alpha=0.3)
    else:
        ax_pe.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "traj_error.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary: attitude (2x2 bar chart)
# ---------------------------------------------------------------------------

def _plot_summary_attitude(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Summary bar chart for attitude: SS error, jitter, settling, rise, overshoot, zero-X."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    fig.suptitle("Attitude Summary", fontsize=14)
    x = np.arange(len(levels))
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0): SS error
    ss_means = [float(np.nanmean(all_metrics[lvl]["att_ss_errors"])) for lvl in levels]
    ss_stds = [float(np.nanstd(all_metrics[lvl]["att_ss_errors"])) for lvl in levels]
    _bar_subplot(axes[0, 0], x, ss_means, bar_colors, xlabels, "Error (deg)", "Attitude SS Error", yerr=ss_stds)

    # (0,1): SS jitter
    jt_means = [float(np.nanmean(all_metrics[lvl]["att_ss_jitters"])) for lvl in levels]
    jt_stds = [float(np.nanstd(all_metrics[lvl]["att_ss_jitters"])) for lvl in levels]
    _bar_subplot(axes[0, 1], x, jt_means, bar_colors, xlabels, "Jitter (deg)", "SS Jitter (std of error in SS)", yerr=jt_stds)

    # (1,0): Settling time
    st_means = [float(np.nanmean(all_metrics[lvl]["att_settling_times"])) for lvl in levels]
    st_stds = [float(np.nanstd(all_metrics[lvl]["att_settling_times"])) for lvl in levels]
    _bar_subplot(axes[1, 0], x, st_means, bar_colors, xlabels, "Time (s)", "Settling Time", yerr=st_stds)

    # (1,1): Overshoot
    os_means = [float(np.nanmean(all_metrics[lvl]["att_overshoot_pcts"])) for lvl in levels]
    os_stds = [float(np.nanstd(all_metrics[lvl]["att_overshoot_pcts"])) for lvl in levels]
    _bar_subplot(axes[1, 1], x, os_means, bar_colors, xlabels, "Overshoot (%)", "Step-Response Overshoot", yerr=os_stds)

    # (2,0): Rise time
    rt_means = [float(np.nanmean(all_metrics[lvl]["att_rise_times"])) for lvl in levels]
    rt_stds = [float(np.nanstd(all_metrics[lvl]["att_rise_times"])) for lvl in levels]
    _bar_subplot(axes[2, 0], x, rt_means, bar_colors, xlabels, "Time (s)", "Rise Time (10%->90%)", yerr=rt_stds)

    # (2,1): Zero crossings
    zx_means = [float(np.nanmean(all_metrics[lvl]["att_zero_crossings"])) for lvl in levels]
    zx_stds = [float(np.nanstd(all_metrics[lvl]["att_zero_crossings"])) for lvl in levels]
    _bar_subplot(axes[2, 1], x, zx_means, bar_colors, xlabels, "Count", "Zero Crossings (oscillation)", yerr=zx_stds)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_attitude.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary: linear velocity (2x2 bar chart, per-axis SS + step-response)
# ---------------------------------------------------------------------------

def _plot_summary_lin_vel(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Summary bar chart for lin vel: per-axis SS error, jitter, rise, overshoot, zero-X, survival."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    fig.suptitle("Linear Velocity Summary", fontsize=14)
    axis_names = ["vx", "vy", "vz"]
    n_ax = len(axis_names)
    n_lvl = len(levels)
    bar_width = 0.8 / n_ax
    x_base = np.arange(n_lvl)
    ax_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # per-axis colors
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    def _grouped_bar(ax, metric_key, ylabel, title):
        for ai, aname in enumerate(axis_names):
            vals = [float(np.nanmean(all_metrics[lvl][metric_key][aname])) for lvl in levels]
            offset = (ai - (n_ax - 1) / 2) * bar_width
            ax.bar(x_base + offset, vals, width=bar_width, color=ax_colors[ai], label=aname)
        ax.set_xticks(x_base)
        ax.set_xticklabels(xlabels, fontsize=9)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

    _grouped_bar(axes[0, 0], "lin_vel_ss_errors", "SS Error (m/s)", "Per-Axis SS Error")
    _grouped_bar(axes[0, 1], "lin_vel_ss_jitters", "Jitter (m/s)", "Per-Axis SS Jitter")
    _grouped_bar(axes[1, 0], "lin_vel_rise_times", "Time (s)", "Rise Time (10%->90%)")
    _grouped_bar(axes[1, 1], "lin_vel_overshoot_pcts", "Overshoot (%)", "Step-Response Overshoot")
    _grouped_bar(axes[2, 0], "lin_vel_zero_crossings", "Count", "Zero Crossings (oscillation)")

    # (2,1): Survival at end of lin_vel block
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    survivals = [all_metrics[lvl]["lin_vel_survival"] for lvl in levels]
    _bar_subplot(
        axes[2, 1], x_base, survivals, bar_colors, xlabels,
        "Survival (%)", "Survival (end of lin_vel)", ylim=(0, 105),
    )

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_linvel.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary: yaw (2x2 bar chart)
# ---------------------------------------------------------------------------

def _plot_summary_yaw(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Summary bar chart for yaw: SS error, jitter, rise, overshoot, zero-X, survival."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    fig.suptitle("Yaw Rate Summary", fontsize=14)
    x = np.arange(len(levels))
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0): SS error
    ss_means = [float(np.nanmean(all_metrics[lvl]["yaw_ss_errors"])) for lvl in levels]
    ss_stds = [float(np.nanstd(all_metrics[lvl]["yaw_ss_errors"])) for lvl in levels]
    _bar_subplot(axes[0, 0], x, ss_means, bar_colors, xlabels, "Error (rad/s)", "Yaw SS Error", yerr=ss_stds)

    # (0,1): SS jitter
    jt_means = [float(np.nanmean(all_metrics[lvl]["yaw_ss_jitters"])) for lvl in levels]
    jt_stds = [float(np.nanstd(all_metrics[lvl]["yaw_ss_jitters"])) for lvl in levels]
    _bar_subplot(axes[0, 1], x, jt_means, bar_colors, xlabels, "Jitter (rad/s)", "SS Jitter (std of error in SS)", yerr=jt_stds)

    # (1,0): Overshoot
    os_means = [float(np.nanmean(all_metrics[lvl]["yaw_overshoot_pcts"])) for lvl in levels]
    os_stds = [float(np.nanstd(all_metrics[lvl]["yaw_overshoot_pcts"])) for lvl in levels]
    _bar_subplot(axes[1, 0], x, os_means, bar_colors, xlabels, "Overshoot (%)", "Step-Response Overshoot", yerr=os_stds)

    # (1,1): Rise time
    rt_means = [float(np.nanmean(all_metrics[lvl]["yaw_rise_times"])) for lvl in levels]
    rt_stds = [float(np.nanstd(all_metrics[lvl]["yaw_rise_times"])) for lvl in levels]
    _bar_subplot(axes[1, 1], x, rt_means, bar_colors, xlabels, "Time (s)", "Rise Time (10%->90%)", yerr=rt_stds)

    # (2,0): Zero crossings
    zx_means = [float(np.nanmean(all_metrics[lvl]["yaw_zero_crossings"])) for lvl in levels]
    zx_stds = [float(np.nanstd(all_metrics[lvl]["yaw_zero_crossings"])) for lvl in levels]
    _bar_subplot(axes[2, 0], x, zx_means, bar_colors, xlabels, "Count", "Zero Crossings (oscillation)", yerr=zx_stds)

    # (2,1): Survival at end of yaw block
    survivals = [all_metrics[lvl]["yaw_survival"] for lvl in levels]
    _bar_subplot(axes[2, 1], x, survivals, bar_colors, xlabels, "Survival (%)", "Survival (end of yaw)", ylim=(0, 105))

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_yaw.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Failure time distribution (unchanged layout)
# ---------------------------------------------------------------------------

def _plot_failure_time(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Failure time distribution histogram per DR level."""
    if "time_to_failure" not in all_data[levels[0]]:
        return

    fig, axes = plt.subplots(1, len(levels), figsize=(4 * len(levels), 4), sharey=True)
    fig.suptitle("Failure Time Distribution", fontsize=14)
    if len(levels) == 1:
        axes = [axes]
    for i, lvl in enumerate(levels):
        ttf = all_data[lvl]["time_to_failure"]
        valid = ttf[~np.isnan(ttf)]
        ax = axes[i]
        dr_pct = int(DR_SCALE[lvl] * 100)
        if len(valid) > 0:
            ax.hist(valid, bins=20, color=DR_COLORS[lvl], alpha=0.7, edgecolor="black")
            ax.axvline(
                np.median(valid), color="black", linestyle="--", linewidth=1.0,
                label=f"median={np.median(valid):.1f}s",
            )
            ax.legend(fontsize=8)
        ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10)
        ax.set_xlabel("Time to Failure (s)")
        if i == 0:
            ax.set_ylabel("Count")
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_failuretime.png"), dpi=150)
    plt.close(fig)
