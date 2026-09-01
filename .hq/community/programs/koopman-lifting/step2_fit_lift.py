#!/usr/bin/env python
"""Offline lifted-linear-model study for koopman-lifting PLAN section 12.3 step 2.

Answers the step-2 kill gate: does a LEARNED lift give a multi-step-prediction
advantage over a RANDOM expansion of the same width, on this plant?

Design notes that make the comparison honest:

* phi(o) = [o ; psi(o)] -- the raw observation is always inside the lift, so
  predicting o is the SAME linear readout (first d_obs rows) for every model.
  No decoder, and the degenerate "shrink the latent to shrink the loss"
  solution cannot buy anything.
* Multi-step rollout applies the operator repeatedly (z <- A z + B u) WITHOUT
  re-lifting. Re-lifting each step would turn every model into a nonlinear
  predictor and would not test linearity at all.
* Every model is trained with the identical objective/optimizer and differs
  only in what is learnable. The closed-form one-step EDMD ridge solution is
  reported alongside as a convergence sanity check.
* Persistence (o_hat = o_t) is reported as the null model. Per-step obs change
  is ~1e-3 in standardized units, so an absolute RMSE is meaningless without
  it -- this is what lets the gate actually fail.

Run with the Isaac interpreter (torch lives there):
    CUDA_VISIBLE_DEVICES=1 /isaac-sim/python.sh .omx/programs/koopman-lifting/step2_fit_lift.py \
        --data <eval static dir> --level none
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn

# obs dim -> (physical name, scale from obs unit to physical unit).
# Verified by correlation against the eval's own actual_roll_deg / actual_pitch_deg /
# yaw_rate arrays: r = 0.9999 / 0.9998 / 0.9941, i.e. these dims ARE those signals.
PHYS = {3: ("roll_deg", 57.2958), 4: ("pitch_deg", 57.2958), 8: ("yaw_rate_rps", 1.0)}
HORIZONS = (1, 5, 25, 50)


def load_level(data_dir: str, level: str):
    d = np.load(os.path.join(data_dir, f"data_{level}.npz"))
    obs = d["policy_obs"].astype(np.float32)  # (T, E, d_obs)
    act = d["action"].astype(np.float32)  # (T, E, d_act)
    term = d["terminated"]
    if term.any():
        # Episode boundaries would put a teleport inside a transition pair. The
        # static protocol has never produced one; refuse rather than fit through it.
        raise SystemExit(f"[FATAL] {level}: {int(term.sum())} terminations present; "
                         "transition pairs would straddle a reset. Handle before fitting.")
    return obs, act


class Lift(nn.Module):
    """phi(o) = [o ; psi(o)]. psi is LayerNorm'd so it cannot collapse to zero."""

    def __init__(self, d_obs: int, p: int, mode: str, hidden: int = 256):
        super().__init__()
        self.d_obs, self.p, self.mode = d_obs, p, mode
        if p == 0:
            self.psi = None
            return
        self.psi = nn.Sequential(
            nn.Linear(d_obs, hidden), nn.ELU(),
            nn.Linear(hidden, hidden), nn.ELU(),
            nn.Linear(hidden, p), nn.LayerNorm(p),
        )
        if mode == "random":
            for prm in self.psi.parameters():
                prm.requires_grad_(False)

    @property
    def dim(self) -> int:
        return self.d_obs + self.p

    def forward(self, o):
        return o if self.psi is None else torch.cat([o, self.psi(o)], dim=-1)


class Operator(nn.Module):
    """z' = A z + B u, optionally plus a nonlinear residual.

    The nonlinear variant NESTS the linear one (the residual head starts at
    zero), so it has strictly more capacity. If extra capacity buys nothing,
    linearity is free -- a nested comparison cannot be confounded by one
    architecture simply optimizing more easily than the other.
    """

    def __init__(self, d_z: int, d_u: int, nonlinear: bool = False, hidden: int = 256):
        super().__init__()
        self.A = nn.Parameter(torch.eye(d_z) + 0.01 * torch.randn(d_z, d_z) / d_z**0.5)
        self.B = nn.Parameter(0.01 * torch.randn(d_z, d_u) / d_u**0.5)
        self.res = None
        if nonlinear:
            self.res = nn.Sequential(
                nn.Linear(d_z + d_u, hidden), nn.ELU(),
                nn.Linear(hidden, hidden), nn.ELU(),
                nn.Linear(hidden, d_z),
            )
            nn.init.zeros_(self.res[-1].weight)
            nn.init.zeros_(self.res[-1].bias)

    def forward(self, z, u):
        out = z @ self.A.T + u @ self.B.T
        if self.res is not None:
            out = out + self.res(torch.cat([z, u], dim=-1))
        return out


def rollout(lift, op, o0, useq, use_u: bool):
    """Operator-only rollout. Returns the full lifted trajectory, (H, N, d_z).

    The obs block is z[..., :d_obs]; callers slice what they need. Returning the
    whole z lets the obs loss and the latent-consistency loss share one rollout.
    """
    z = lift(o0)
    zs = []
    for k in range(useq.shape[0]):
        u = useq[k] if use_u else torch.zeros_like(useq[k])
        z = op(z, u)
        zs.append(z)
    return torch.stack(zs, 0)


def sample_batch(obs, act, envs, horizon, batch, gen, device):
    """One gather per tensor -- obs/act already live on `device`."""
    T = obs.shape[0]
    e = envs[torch.randint(len(envs), (batch,), generator=gen)].to(device)
    t0 = torch.randint(T - horizon - 1, (batch,), generator=gen).to(device)
    k = torch.arange(horizon, device=device)[:, None]
    ee = e[None, :].expand(horizon, -1)
    return obs[t0, e], act[t0[None, :] + k, ee], obs[t0[None, :] + k + 1, ee]


def train_model(obs, act, envs, lift, op, args, device, seed, use_u=True):
    params = [q for q in list(lift.parameters()) + list(op.parameters()) if q.requires_grad]
    opt = torch.optim.Adam(params, lr=args.lr)
    gen = torch.Generator().manual_seed(seed)
    lift.train(), op.train()
    for _ in range(args.steps):
        o0, useq, tgt = sample_batch(obs, act, envs, args.horizon, args.batch, gen, device)
        z = rollout(lift, op, o0, useq, use_u)
        loss = ((z[..., : lift.d_obs] - tgt) ** 2).mean()
        if lift.p > 0 and args.lam > 0:
            # standard deep-Koopman latent-consistency term, on top of the obs loss
            with torch.no_grad():
                psi_tgt = lift(tgt.reshape(-1, lift.d_obs))[:, lift.d_obs:]
            loss = loss + args.lam * ((z[..., lift.d_obs:].reshape(-1, lift.p) - psi_tgt) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
    return float(loss.item())


@torch.no_grad()
def evaluate(obs, act, envs, lift, op, device, use_u=True, n_starts=400, seed=0):
    """Multi-step obs-space error on held-out envs, plus the persistence null."""
    lift.eval(), op.eval()
    gen = torch.Generator().manual_seed(seed)
    T, Hmax = obs.shape[0], max(HORIZONS)
    e = envs[torch.randint(len(envs), (n_starts,), generator=gen)].to(device)
    t0 = torch.randint(T - Hmax - 1, (n_starts,), generator=gen).to(device)
    k = torch.arange(Hmax, device=device)[:, None]
    ee = e[None, :].expand(Hmax, -1)
    o0, useq, tgt = obs[t0, e], act[t0[None, :] + k, ee], obs[t0[None, :] + k + 1, ee]
    pred = rollout(lift, op, o0, useq, use_u)[..., : lift.d_obs]

    out = {}
    for H in HORIZONS:
        err = pred[H - 1] - tgt[H - 1]
        per = (o0 - tgt[H - 1])  # persistence null
        rec = {
            "rmse_std": float(err.pow(2).mean().sqrt()),
            "persistence_rmse_std": float(per.pow(2).mean().sqrt()),
        }
        for dim, (name, scale) in PHYS.items():
            rec[f"rmse_{name}"] = float(err[:, dim].pow(2).mean().sqrt() * scale)
            rec[f"persistence_rmse_{name}"] = float(per[:, dim].pow(2).mean().sqrt() * scale)
        out[f"H{H}"] = rec

    if lift.p > 0:
        psi = lift(obs[::37][:, envs.to(device)].reshape(-1, lift.d_obs))[:, lift.d_obs:]
        s = torch.linalg.svdvals(psi - psi.mean(0))
        out["psi_std_mean"] = float(psi.std(0).mean())
        out["psi_eff_rank"] = float((s.sum() ** 2) / (s.pow(2).sum()))  # participation ratio
    return out


@torch.no_grad()
def u_identifiability(obs, act, envs, lift, device, ridge=1e-4, n=200000, seed=0):
    """How linearly predictable is u from the lifted state?

    The logging policy is deterministic (eval.py calls the inference policy, so
    u_t = pi(o_t) exactly). If u is also LINEAR in z, then B u = B C z can be
    absorbed into A and B is not identified -- the fitted operator would only be
    valid along this policy's own closed loop. R^2 near 1 is the signal that the
    scripted-excitation collection pass is mandatory before trusting any B.
    """
    gen = torch.Generator().manual_seed(seed)
    T = obs.shape[0]
    e = envs[torch.randint(len(envs), (n,), generator=gen)].to(device)
    t = torch.randint(T - 1, (n,), generator=gen).to(device)
    z = lift(obs[t, e])
    u = act[t, e]
    x = torch.cat([z, torch.ones_like(z[:, :1])], dim=-1)
    g = x.T @ x + ridge * torch.eye(x.shape[1], device=device)
    resid = x @ torch.linalg.solve(g, x.T @ u) - u
    ss_res = resid.pow(2).sum(0)
    ss_tot = (u - u.mean(0)).pow(2).sum(0)
    r2 = 1.0 - ss_res / ss_tot
    return {"u_r2_mean": float(r2.mean()), "u_r2_per_dim": [round(float(v), 4) for v in r2]}


@torch.no_grad()
def edmd_ridge(obs, act, envs, lift, device, ridge=1e-4, n=200000, seed=0):
    """Closed-form one-step EDMD-with-control solution. Convergence sanity check."""
    gen = torch.Generator().manual_seed(seed)
    T = obs.shape[0]
    e = envs[torch.randint(len(envs), (n,), generator=gen)].to(device)
    t = torch.randint(T - 1, (n,), generator=gen).to(device)
    z = lift(obs[t, e])
    zp = lift(obs[t + 1, e])
    x = torch.cat([z, act[t, e]], dim=-1)
    g = x.T @ x + ridge * torch.eye(x.shape[1], device=device)
    w = torch.linalg.solve(g, x.T @ zp)  # (d_z + d_u, d_z)
    resid = (x @ w - zp)[:, : lift.d_obs]
    return {"onestep_rmse_std": float(resid.pow(2).mean().sqrt())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="eval static_<ts> directory")
    ap.add_argument("--level", default="none")
    ap.add_argument("--widths", type=int, nargs="+", default=[0, 16, 32, 64, 128])
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--horizon", type=int, default=25)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=3,
                    help="repeats per configuration; the learned-vs-random gap is only "
                         "readable against this spread")
    ap.add_argument("--n-train-envs", type=int, default=48)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    obs_np, act_np = load_level(args.data, args.level)
    T, E, d_obs = obs_np.shape
    d_act = act_np.shape[-1]

    train_envs = torch.arange(args.n_train_envs)
    test_envs = torch.arange(args.n_train_envs, E)
    # Standardize with TRAIN envs only -- held-out plants must not leak into the scaler.
    mu = obs_np[:, : args.n_train_envs].reshape(-1, d_obs).mean(0)
    sd = obs_np[:, : args.n_train_envs].reshape(-1, d_obs).std(0) + 1e-6
    # ~160 MB for both tensors -- resident on the GPU so batch gathers never cross PCIe.
    obs = torch.from_numpy((obs_np - mu) / sd).to(device)
    act = torch.from_numpy(act_np).to(device)
    # PHYS scales are quoted in obs units; standardizing rescales them.
    phys = {d: (n, s * float(sd[d])) for d, (n, s) in PHYS.items()}
    PHYS.clear(), PHYS.update(phys)

    print(f"[data] {args.level}: T={T} E={E} d_obs={d_obs} d_act={d_act} "
          f"train_envs={len(train_envs)} test_envs={len(test_envs)} device={device}")

    results, t_start = [], time.time()
    for p in args.widths:
        modes = [("raw", "linear", False)] if p == 0 else [
            ("random", "linear", False), ("learned", "linear", False), ("learned", "nested_nl", True)]
        for lift_mode, op_name, nonlin in modes:
            per_seed = []
            for s in range(args.seeds):
                seed = args.seed + 100 * s
                torch.manual_seed(seed)
                lift = Lift(d_obs, p, lift_mode).to(device)
                op = Operator(lift.dim, d_act, nonlinear=nonlin).to(device)
                final = train_model(obs, act, train_envs, lift, op, args, device, seed)
                one = {"seed": seed, "final_train_loss": final,
                       "test": evaluate(obs, act, test_envs, lift, op, device, seed=1),
                       "train": evaluate(obs, act, train_envs, lift, op, device, seed=2),
                       "edmd_ridge": edmd_ridge(obs, act, train_envs, lift, device),
                       "u_ident": u_identifiability(obs, act, train_envs, lift, device),
                       # Evaluating a u-trained model at u=0: measures how much the
                       # fitted B is being used, NOT identifiability (see u_ident).
                       "test_u_zeroed": evaluate(obs, act, test_envs, lift, op, device,
                                                 use_u=False, seed=1)}
                per_seed.append(one)
            rec = {"width": p, "lift": lift_mode, "operator": op_name, "per_seed": per_seed}
            for H in HORIZONS:
                v = [x["test"][f"H{H}"]["rmse_std"] for x in per_seed]
                r = [x["test"][f"H{H}"]["rmse_roll_deg"] for x in per_seed]
                rec[f"H{H}"] = {"rmse_std_mean": float(np.mean(v)), "rmse_std_std": float(np.std(v)),
                                "rmse_roll_deg_mean": float(np.mean(r)),
                                "rmse_roll_deg_std": float(np.std(r)),
                                "persistence_rmse_std": per_seed[0]["test"][f"H{H}"]["persistence_rmse_std"]}
            results.append(rec)
            h = rec["H25"]
            print(f"  p={p:4d} {lift_mode:8s}/{op_name:10s} H25 rmse={h['rmse_std_mean']:.4f}"
                  f"+-{h['rmse_std_std']:.4f} (persist {h['persistence_rmse_std']:.4f})  "
                  f"roll={h['rmse_roll_deg_mean']:.3f}+-{h['rmse_roll_deg_std']:.3f}deg  "
                  f"u_r2={per_seed[0]['u_ident']['u_r2_mean']:.4f}")

    out = {"data": args.data, "level": args.level, "args": vars(args),
           "phys_scales": {str(k): v for k, v in PHYS.items()},
           "wall_s": time.time() - t_start, "results": results}
    path = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "step2_fit", f"fit_{args.level}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[done] {time.time() - t_start:.0f}s -> {path}")


if __name__ == "__main__":
    main()
