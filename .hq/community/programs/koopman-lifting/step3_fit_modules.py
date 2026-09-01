#!/usr/bin/env python
"""Fit and export the three FROZEN representation modules for koopman-lifting step 3.

Produces one checkpoint per arm of PLAN 12.2:

  arm_c   learned dictionary psi + learned LINEAR operator      (the full Koopman lift)
  twin    same-architecture learned psi + MLP operator          (isolates linearity itself)
  random  frozen random psi + learned linear operator           (expansion vs structure)

Every arm exports the same interface, so the env-side loader is one code path:
given the previous noised 72D policy observation and the last applied 8D action, roll the
operator forward --horizon steps and return the predicted [roll, pitch, p, q, r] in raw
observation units.

Three design points, each settled by evidence rather than default (PLAN 12.7 / 12.8):

* --horizon and --autonomous are SWEPT, not assumed: PLAN 12.7's default of a one-step
  prediction under a held action is measured against the persistence null before one is
  picked. The original reasoning for a long horizon was that step 2 Step 2
  measured every model sitting at the persistence null at H1 (0.185-0.211 vs 0.1905), i.e.
  the one-step prediction IS the current observation -- feeding it would widen the policy
  input with duplicates, and arm B already showed +7 duplicate-ish channels cost transient
  quality. 25 is also the horizon every number in PLAN 12.8 was measured at.
* Zero-order-hold action. The prediction is itself a policy input, so the action for
  t..t+h is not known when it is computed; the last APPLIED action is held instead. The
  fit uses the same assumption, so there is no train/inference mismatch.
* Fitted on an EXCITED pass. During RL the policy is stochastic and its own exploration
  excites the input, so an excited eval pass matches the training-time distribution far
  better than the deterministic one (on which u is 96.5 % linearly predictable from o and
  B is not identified at all -- PLAN 12.8 reading 6).

Run with the Isaac interpreter (torch):
    CUDA_VISIBLE_DEVICES=1 /isaac-sim/python.sh .omx/programs/koopman-lifting/step3_fit_modules.py \
        --data <excited eval static dir> --out <dir>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step2_fit_lift import Lift  # noqa: E402  -- unchanged; it is the PLAN 12.8 artifact

# Columns of the 72D policy obs that the module predicts and feeds back to the policy.
# Same five signals arm B's dictionary was built from (mdp/observations.MARINE_SRC_IDX):
# euler roll/pitch and body rates p/q/r. Verified against this run's own actual_roll_deg /
# actual_pitch_deg / yaw_rate arrays (r = 0.9999 / 0.9998 / 0.9941).
OUT_IDX = (3, 4, 6, 7, 8)
LEVELS = ("none", "soft", "medium", "hard")


class LinearOperator(nn.Module):
    """z' = A z + B u. A is what PLAN 12.2 calls K."""

    def __init__(self, d_z: int, d_u: int):
        super().__init__()
        self.A = nn.Parameter(torch.eye(d_z) + 0.01 * torch.randn(d_z, d_z) / d_z**0.5)
        self.B = nn.Parameter(0.01 * torch.randn(d_z, d_u) / d_u**0.5)

    def forward(self, z, u):
        return z @ self.A.T + u @ self.B.T


class MLPOperator(nn.Module):
    """z' = MLP([z, u]), initialised at the identity map so it starts where LinearOperator does.

    This is PLAN 12.2 arm 4: the SAME lift, the operator swapped for a same-size MLP. It is
    NOT the nested residual used in the offline study (PLAN 12.8) -- that one was chosen so a
    capacity confound could not exist; here the plan asks for the swap.
    """

    def __init__(self, d_z: int, d_u: int, hidden: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_z + d_u, hidden), nn.ELU(),
            nn.Linear(hidden, hidden), nn.ELU(),
            nn.Linear(hidden, d_z),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, z, u):
        return z + self.net(torch.cat([z, u], dim=-1))


ARMS = {
    # name: (lift mode, operator class)
    "arm_c": ("learned", LinearOperator),
    "twin": ("learned", MLPOperator),
    "random": ("random", LinearOperator),
}


def load_union(data_dir: str):
    """Concatenate all DR levels along the env axis.

    A single frozen module is used across the whole DORAEMON DR range during training, so it
    is fitted across the range too rather than on one level.
    """
    obs, act = [], []
    for lv in LEVELS:
        d = np.load(os.path.join(data_dir, f"data_{lv}.npz"))
        if d["terminated"].any():
            raise SystemExit(f"[FATAL] {lv}: terminations present; pairs would straddle a reset.")
        if "excite_std" not in d.files:
            raise SystemExit(f"[FATAL] {lv}: no excite_std key -- this is an UNEXCITED pass. "
                             "The module must be fitted on excited data (see module docstring).")
        obs.append(d["policy_obs"].astype(np.float32))
        act.append(d["action"].astype(np.float32))
    return np.concatenate(obs, axis=1), np.concatenate(act, axis=1), obs[0].shape[1]


def split_envs(n_per_level: int, n_levels: int, n_test_per_level: int):
    """Hold out the LAST n_test envs of every level, not the last envs overall.

    Concatenation is level-major, so a flat 192/64 cut would put the entire `hard` level in
    the test set -- that is a DR-level extrapolation test, not a held-out-plant test, and it
    silently made the linear arms score worse than the persistence null.
    """
    train, test = [], []
    for lv in range(n_levels):
        base = lv * n_per_level
        train += list(range(base, base + n_per_level - n_test_per_level))
        test += list(range(base + n_per_level - n_test_per_level, base + n_per_level))
    return torch.tensor(train), torch.tensor(test)


def rollout_zoh(lift, op, o0, u0, horizon, autonomous=False):
    """Roll the operator forward holding u0 constant. Returns the full lifted trajectory.

    Callers slice: [..., :d_obs] is the predicted observation, [..., d_obs:] the predicted
    latent. Returning both from ONE rollout keeps the obs loss and the latent-consistency
    loss from paying for the operator twice.
    """
    z = lift(o0)
    u = torch.zeros_like(u0) if autonomous else u0
    outs = []
    for _ in range(horizon):
        z = op(z, u)
        outs.append(z)
    return torch.stack(outs, 0)


def sample(obs, act, envs, batch, gen, device, horizon):
    T = obs.shape[0]
    e = envs[torch.randint(len(envs), (batch,), generator=gen)].to(device)
    t0 = torch.randint(T - horizon - 1, (batch,), generator=gen).to(device)
    k = torch.arange(horizon, device=device)[:, None]
    tgt = obs[t0[None, :] + k + 1, e[None, :].expand(horizon, -1)]
    return obs[t0, e], act[t0, e], tgt


@torch.no_grad()
def eval_dense(lift, op, obs, act, envs, args, d_obs, device, stride: int = 7, chunk: int = 4096):
    """Predict from every `stride`-th start time on every held-out env. Returns (pred, target, o0)."""
    T = obs.shape[0]
    e = envs.to(device)
    t0 = torch.arange(0, T - args.horizon - 1, stride, device=device)
    tt, ee = torch.meshgrid(t0, e, indexing="ij")
    tt, ee = tt.reshape(-1), ee.reshape(-1)
    preds, fins, starts = [], [], []
    for i in range(0, tt.numel(), chunk):
        ti, ei = tt[i:i + chunk], ee[i:i + chunk]
        o0 = obs[ti, ei]
        z = rollout_zoh(lift, op, o0, act[ti, ei], args.horizon, args.autonomous)
        preds.append(z[-1][:, :d_obs])
        fins.append(obs[ti + args.horizon, ei])
        starts.append(o0)
    return torch.cat(preds), torch.cat(fins), torch.cat(starts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="EXCITED eval static_<ts> directory")
    ap.add_argument("--out", default=None)
    ap.add_argument("--psi-dim", type=int, default=64, help="PLAN 12.8 reading 5: plateau is 64")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--horizon", type=int, default=25)
    ap.add_argument("--autonomous", action="store_true", default=False,
                    help="drop the action from the rollout: predict where the CLOSED LOOP is "
                         "heading instead of where a held action would take it")
    ap.add_argument("--arms", nargs="+", default=list(ARMS))
    ap.add_argument("--n-test-per-level", type=int, default=16,
                    help="held-out envs taken from EVERY level (see split_envs)")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    obs_np, act_np, n_per_level = load_union(args.data)
    T, E, d_obs = obs_np.shape
    d_act = act_np.shape[-1]
    train_envs, test_envs = split_envs(n_per_level, len(LEVELS), args.n_test_per_level)

    tr = train_envs.numpy()
    mu = obs_np[:, tr].reshape(-1, d_obs).mean(0)
    sd = obs_np[:, tr].reshape(-1, d_obs).std(0) + 1e-6
    obs = torch.from_numpy((obs_np - mu) / sd).to(device)
    act = torch.from_numpy(act_np).to(device)
    print(f"[data] T={T} E={E} ({n_per_level}/level x {len(LEVELS)}) d_obs={d_obs} d_act={d_act} "
          f"train={len(train_envs)} test={len(test_envs)} (held out per level) dev={device}")

    outdir = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "step3_modules")
    os.makedirs(outdir, exist_ok=True)
    report = {"data": args.data, "horizon": args.horizon, "autonomous": args.autonomous,
              "out_idx": list(OUT_IDX),
              "psi_dim": args.psi_dim, "args": vars(args), "arms": {}}

    for name in args.arms:
        lift_mode, op_cls = ARMS[name]
        t0 = time.time()
        torch.manual_seed(args.seed)
        lift = Lift(d_obs, args.psi_dim, lift_mode).to(device)
        op = op_cls(lift.dim, d_act).to(device)
        params = [q for q in list(lift.parameters()) + list(op.parameters()) if q.requires_grad]
        opt = torch.optim.Adam(params, lr=args.lr)
        gen = torch.Generator().manual_seed(args.seed)
        for _ in range(args.steps):
            o0, u0, tgt = sample(obs, act, train_envs, args.batch, gen, device, args.horizon)
            z = rollout_zoh(lift, op, o0, u0, args.horizon, args.autonomous)
            loss = ((z[..., :d_obs] - tgt) ** 2).mean()
            if args.lam > 0:
                with torch.no_grad():
                    psi_t = lift(tgt.reshape(-1, d_obs))[:, d_obs:]
                loss = loss + args.lam * ((z[..., d_obs:].reshape(-1, args.psi_dim) - psi_t) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()

        with torch.no_grad():
            lift.eval(), op.eval()
            # DENSE and DETERMINISTIC: every 7th start time on every held-out env. A random
            # 2000-window sample made the persistence null NON-MONOTONIC in the horizon --
            # impossible physically, and the tell that the estimate was being dominated by the
            # rare windows that straddle a 250-step command change.
            pred, fin, o0 = eval_dense(lift, op, obs, act, test_envs, args, d_obs, device)
            idx = torch.tensor(OUT_IDX, device=device)
            sdv = torch.from_numpy(sd).to(device)
            err = ((pred[:, idx] - fin[:, idx]) * sdv[idx])
            per = ((o0[:, idx] - fin[:, idx]) * sdv[idx])  # persistence null, raw obs units
            m = {"rmse_std_all72": float((pred - fin).pow(2).mean().sqrt()),
                 "persistence_rmse_std_all72": float((o0 - fin).pow(2).mean().sqrt()),
                 "rmse_roll_deg": float(err[:, 0].pow(2).mean().sqrt() * 57.2958),
                 "persistence_rmse_roll_deg": float(per[:, 0].pow(2).mean().sqrt() * 57.2958),
                 "rmse_pitch_deg": float(err[:, 1].pow(2).mean().sqrt() * 57.2958),
                 # The decision metric: these 5 channels are what the policy is actually
                 # handed, so the module is selected on them, not on all 72 and not on roll.
                 "rmse_fed5_std": float((pred[:, idx] - fin[:, idx]).pow(2).mean().sqrt()),
                 "persistence_rmse_fed5_std": float((o0[:, idx] - fin[:, idx]).pow(2).mean().sqrt()),
                 "wall_s": time.time() - t0}
        report["arms"][name] = m
        # Carry a small REAL probe so the loader's fold check runs on inputs the module will
        # actually see. A synthetic extreme probe (all 72 dims at +-2 sigma at once, every
        # thruster saturated) sits far off the data manifold, where float32 conditioning --
        # not the fold -- dominates the difference: 1e-6 on real rows, 2.6e-3 on that probe.
        pg = torch.Generator().manual_seed(args.seed + 11)
        pi = torch.randint(obs.shape[0], (256,), generator=pg)
        pe = test_envs[torch.randint(len(test_envs), (256,), generator=pg)]
        probe_std = obs[pi.to(device), pe.to(device)]          # standardized: what the fit uses
        probe_o = (probe_std * torch.from_numpy(sd).to(device)
                   + torch.from_numpy(mu).to(device)).cpu()      # raw: what the env feeds
        probe_u = act[pi.to(device), pe.to(device)].cpu()
        # The module's OWN outputs on that probe, so the env-side loader can prove the whole
        # deployed path (scaler -> lift -> operator -> un-scaler) reproduces what was fitted,
        # rather than only that the weights loaded.
        with torch.no_grad():
            # STANDARDIZED input: rollout_zoh lifts directly, while the env-side module
            # standardizes internally. Feeding the raw rows here made the saved outputs
            # disagree with the deployed path by 4.8 sigma -- which is what the loader's
            # reproduction gate exists to catch, and did.
            _z = rollout_zoh(lift, op, probe_std, probe_u.to(device),
                             args.horizon, args.autonomous)[-1]
            _idxt = torch.tensor(OUT_IDX, device=device)
            probe_out = (_z[:, _idxt] * torch.from_numpy(sd[list(OUT_IDX)]).to(device)
                         + torch.from_numpy(mu[list(OUT_IDX)]).to(device)).cpu()
        torch.save({"lift_mode": lift_mode, "operator": op_cls.__name__,
                    "probe_obs": probe_o, "probe_act": probe_u, "probe_out": probe_out,
                    "psi_dim": args.psi_dim, "d_obs": d_obs, "d_act": d_act,
                    "horizon": args.horizon, "autonomous": args.autonomous,
                    "out_idx": list(OUT_IDX), "obs_mu": mu, "obs_sd": sd,
                    "lift": lift.state_dict(), "op": op.state_dict(),
                    "fit": m, "data": args.data},
                   os.path.join(outdir, f"{name}.pt"))
        gain = 100 * (1 - m["rmse_fed5_std"] / m["persistence_rmse_fed5_std"])
        m["fed5_gain_pct"] = gain
        print(f"  {name:7s} H{args.horizon} fed5={m['rmse_fed5_std']:.4f} "
              f"(persist {m['persistence_rmse_fed5_std']:.4f}, gain {gain:5.1f}%)  "
              f"all72={m['rmse_std_all72']:.4f} "
              f"(persist {m['persistence_rmse_std_all72']:.4f})  "
              f"roll={m['rmse_roll_deg']:.3f}deg (persist {m['persistence_rmse_roll_deg']:.3f}) "
              f"[{m['wall_s']:.0f}s]")

    with open(os.path.join(outdir, "fit_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[done] -> {outdir}")


if __name__ == "__main__":
    main()
