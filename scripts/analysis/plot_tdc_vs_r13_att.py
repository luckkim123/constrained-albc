"""Overlay roll/pitch: TDC (classical) vs r13_A (RL+Encoder) vs v5_pureppo (RL no-encoder/no-IPO) at OOD.

Reuses existing eval_extreme_ood npz files. Picks env with largest TDC-vs-r13 roll gap
for dramatic contrast (same env index applied to all runs so DR is matched).
"""
from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

TDC_DIR = "/workspace/isaaclab/logs/rsl_rl/full_dof_tdc/classical_baseline"
R13_DIR = "/workspace/isaaclab/logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A"
V5_DIR = "/workspace/isaaclab/logs/rsl_rl/full_dof_ablation/2026-04-22_01-41-00_ablation_v5_pureppo"

DEFAULTS = {
    "v1": {
        "tdc": f"{TDC_DIR}/eval_extreme_ood_v1/eval_ood_1.0x.npz",
        "r13": f"{R13_DIR}/eval_extreme_ood_v1/eval_ood_1.0x.npz",
        "v5":  f"{V5_DIR}/eval_extreme_ood_v1/eval_ood_1.0x.npz",
        "output": f"{TDC_DIR}/tdc_vs_r13a_att_ood_v1.png",
    },
    "v2": {
        "tdc": f"{TDC_DIR}/eval_extreme_ood_v2/eval_ood_1.0x.npz",
        "r13": f"{R13_DIR}/eval_extreme_ood_v2/eval_ood_1.0x.npz",
        "v5":  f"{V5_DIR}/eval_extreme_ood_v2/eval_ood_1.0x.npz",
        "output": f"{TDC_DIR}/tdc_vs_r13a_att_ood_v2.png",
    },
    "v3": {
        "tdc": f"{TDC_DIR}/eval_extreme_ood_v3/eval_ood_1.0x.npz",
        "r13": f"{R13_DIR}/eval_extreme_ood_v3/eval_ood_1.0x.npz",
        "v5":  f"{V5_DIR}/eval_extreme_ood_v3/eval_ood_1.0x.npz",
        "output": f"{TDC_DIR}/tdc_vs_r13a_att_ood_v3.png",
    },
}


def ss_err(actual: np.ndarray, target: np.ndarray, tail_frac: float = 0.25) -> np.ndarray:
    """Per-env |actual - target| averaged over the last `tail_frac` of the trajectory."""
    N = actual.shape[0]
    tail = slice(int(N * (1.0 - tail_frac)), N)
    err = np.abs(actual[tail] - target[tail, None])
    return err.mean(axis=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=["v1", "v2", "v3"], default="v2")
    parser.add_argument("--env", type=int, default=None, help="Env index (default: picks max roll-gap env)")
    parser.add_argument("--t-max", type=float, default=60.0, help="Truncate plot to this many seconds (default: 60)")
    parser.add_argument("--t-start", type=float, default=0.0, help="Drop data before this time (spawn transient); axis re-zeroed (default: 0)")
    args = parser.parse_args()

    d = DEFAULTS[args.preset]
    tdc = np.load(d["tdc"])
    r13 = np.load(d["r13"])
    v5_available = os.path.exists(d["v5"])
    v5 = np.load(d["v5"]) if v5_available else None

    if args.env is None:
        gap = ss_err(tdc["actual_roll_deg"], tdc["target_roll_deg"]) - ss_err(r13["actual_roll_deg"], r13["target_roll_deg"])
        env_idx = int(np.argmax(gap))
    else:
        env_idx = args.env

    t_full = tdc["time"]
    keep = (t_full >= args.t_start) & (t_full <= args.t_max)
    t = t_full[keep] - args.t_start  # re-zero the visible axis

    tgt_roll = tdc["target_roll_deg"][keep]
    tgt_pitch = tdc["target_pitch_deg"][keep]

    def series(dat, key):
        return dat[key][keep, env_idx]

    tdc_r = series(tdc, "actual_roll_deg"); tdc_p = series(tdc, "actual_pitch_deg")
    r13_r = series(r13, "actual_roll_deg"); r13_p = series(r13, "actual_pitch_deg")
    if v5_available:
        v5_r = series(v5, "actual_roll_deg"); v5_p = series(v5, "actual_pitch_deg")

    def ss(dat, key, tgt_key):
        return ss_err(dat[key], dat[tgt_key])[env_idx]
    tdc_rss = ss(tdc, "actual_roll_deg", "target_roll_deg")
    tdc_pss = ss(tdc, "actual_pitch_deg", "target_pitch_deg")
    r13_rss = ss(r13, "actual_roll_deg", "target_roll_deg")
    r13_pss = ss(r13, "actual_pitch_deg", "target_pitch_deg")
    if v5_available:
        v5_rss = ss(v5, "actual_roll_deg", "target_roll_deg")
        v5_pss = ss(v5, "actual_pitch_deg", "target_pitch_deg")

    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)

    rl_ppo_label = f"RL-PPO   (Roll SS: {v5_rss:.2f}\u00b0 / Pitch SS: {v5_pss:.2f}\u00b0)" if v5_available else None
    tdc_label = f"TDC-PD   (Roll SS: {tdc_rss:.2f}\u00b0 / Pitch SS: {tdc_pss:.2f}\u00b0)"
    ours_label = f"Ours        (Roll SS: {r13_rss:.2f}\u00b0 / Pitch SS: {r13_pss:.2f}\u00b0)"

    # --- Roll ---
    ax = axes[0]
    ax.plot(t, tgt_roll, color="black", lw=2.2, ls="--", alpha=0.9, label="Target")
    ax.plot(t, tdc_r, color="tab:green", lw=1.4, alpha=0.9, label=tdc_label)
    if v5_available:
        ax.plot(t, v5_r, color="tab:blue", lw=1.4, alpha=0.9, label=rl_ppo_label)
    ax.plot(t, r13_r, color="tab:red", lw=1.4, alpha=0.9, label=ours_label)
    ax.axhline(0.0, color="gray", lw=0.5, alpha=0.4)
    ax.set_ylabel("Roll (deg)", fontsize=11)
    ax.set_ylim(-25, 25)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.85)
    ax.set_title(f"Attitude tracking under OOD {args.preset} physics (single env #{env_idx})", fontsize=12)

    # --- Pitch ---
    ax = axes[1]
    ax.plot(t, tgt_pitch, color="black", lw=2.2, ls="--", alpha=0.9)
    ax.plot(t, tdc_p, color="tab:green", lw=1.4, alpha=0.9)
    if v5_available:
        ax.plot(t, v5_p, color="tab:blue", lw=1.4, alpha=0.9)
    ax.plot(t, r13_p, color="tab:red", lw=1.4, alpha=0.9)
    ax.axhline(0.0, color="gray", lw=0.5, alpha=0.4)
    ax.set_ylabel("Pitch (deg)", fontsize=11)
    ax.set_xlabel("Time (s)", fontsize=11)
    ax.set_ylim(-25, 25)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    os.makedirs(os.path.dirname(d["output"]), exist_ok=True)
    fig.savefig(d["output"], dpi=150, bbox_inches="tight")
    print(f"Saved: {d['output']}")
    v5_str = f"  PurePPO roll={v5_rss:.2f}\u00b0/pitch={v5_pss:.2f}\u00b0" if v5_available else "  (PurePPO: pending)"
    print(f"Preset {args.preset}, Env {env_idx}:  TDC roll={tdc_rss:.2f}\u00b0/pitch={tdc_pss:.2f}\u00b0  r13_A roll={r13_rss:.2f}\u00b0/pitch={r13_pss:.2f}\u00b0{v5_str}")


if __name__ == "__main__":
    main()
