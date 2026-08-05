# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Frozen lifted-dynamics module for the Koopman step-3 arms (programs/koopman-lifting PLAN 12.2).

Loads a checkpoint produced by `.omx/programs/koopman-lifting/step3_fit_modules.py` and turns
(previous noised policy observation, last applied action) into a HORIZON-step-ahead prediction
of [roll, pitch, p, q, r], in raw observation units, which `ALBCEnv._get_observations` appends
to the policy observation.

Everything here is FROZEN: no parameter is trained during RL, no RNG is drawn, and the forward
runs under no_grad. That is what makes the three arms differ in exactly one thing -- the
representation they are handed -- rather than in how they learn.

Why the architecture is re-declared here instead of imported: the fit script lives under `.omx`
and must not become a runtime dependency of the environment. `load_state_dict(strict=True)` is
what keeps the two definitions in sync -- if they ever diverge, loading fails loudly.
"""

from __future__ import annotations

import torch
import torch.nn as nn

# Width of what this module contributes to the policy observation.
KOOPMAN_PRED_DIM = 5


def _build_psi(d_obs: int, psi_dim: int, hidden: int = 256) -> nn.Sequential:
    """Must mirror step2_fit_lift.Lift.psi exactly; strict state_dict loading enforces it."""
    return nn.Sequential(
        nn.Linear(d_obs, hidden), nn.ELU(),
        nn.Linear(hidden, hidden), nn.ELU(),
        nn.Linear(hidden, psi_dim), nn.LayerNorm(psi_dim),
    )


class FrozenKoopmanLift(nn.Module):
    """phi(o) = [o ; psi(o)], rolled forward HORIZON steps with the action held constant.

    The zero-order hold is not a modelling shortcut chosen for convenience: the prediction is
    itself a policy input, so the actions for t..t+h do not exist when it is computed. The fit
    uses the same assumption, so there is no train/inference mismatch.

    Every arm ITERATES the operator h times, including the linear ones. A linear ZOH map does
    fold into two constant matrices (z_h = A^h z_0 + (sum_{i<h} A^i) B u), and that is exact in
    exact arithmetic -- but Isaac Lab enables TF32, under which the folded and iterated forms
    were measured to differ by 1.5e-2 sigma (5.96e-6 with TF32 off). On the attitude channel
    that is 0.19 deg, above the 0.1 deg floor these arms are judged on. Iterating makes
    inference match how the module was FITTED, and makes the linear and MLP arms structurally
    symmetric rather than one being a single matmul. The fold stays available as a deployment
    optimization; it is not used here.
    """

    def __init__(self, ckpt_path: str, device: str | torch.device):
        super().__init__()
        ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        self.d_obs: int = int(ck["d_obs"])
        self.d_act: int = int(ck["d_act"])
        self.horizon: int = int(ck["horizon"])
        self.out_idx = tuple(int(i) for i in ck["out_idx"])
        self.arm_operator: str = str(ck["operator"])
        if len(self.out_idx) != KOOPMAN_PRED_DIM:
            raise ValueError(f"checkpoint predicts {len(self.out_idx)} channels, "
                             f"KOOPMAN_PRED_DIM is {KOOPMAN_PRED_DIM}: {ckpt_path}")

        self.psi = _build_psi(self.d_obs, int(ck["psi_dim"]))
        self.psi.load_state_dict({k[4:]: v for k, v in ck["lift"].items() if k.startswith("psi.")},
                                 strict=True)
        d_z = self.d_obs + int(ck["psi_dim"])

        self._mlp_op = None
        op_sd = ck["op"]
        if self.arm_operator == "LinearOperator":
            self.register_buffer("_A", op_sd["A"].clone())
            self.register_buffer("_B", op_sd["B"].clone())
        else:
            hidden = op_sd["net.0.weight"].shape[0]
            self._mlp_op = nn.Sequential(
                nn.Linear(d_z + self.d_act, hidden), nn.ELU(),
                nn.Linear(hidden, hidden), nn.ELU(),
                nn.Linear(hidden, d_z),
            )
            self._mlp_op.load_state_dict({k[4:]: v for k, v in op_sd.items() if k.startswith("net.")},
                                         strict=True)

        mu = torch.as_tensor(ck["obs_mu"], dtype=torch.float32)
        sd = torch.as_tensor(ck["obs_sd"], dtype=torch.float32)
        self.register_buffer("_mu", mu)
        self.register_buffer("_sd", sd)
        self.register_buffer("_probe_obs", torch.as_tensor(ck["probe_obs"], dtype=torch.float32))
        self.register_buffer("_probe_act", torch.as_tensor(ck["probe_act"], dtype=torch.float32))
        self.register_buffer("_probe_out", torch.as_tensor(ck["probe_out"], dtype=torch.float32))
        idx = torch.tensor(self.out_idx, dtype=torch.long)
        self.register_buffer("_out_mu", mu[idx])
        self.register_buffer("_out_sd", sd[idx])
        self.register_buffer("_out_idx", idx)

        self.to(device)
        self.eval()
        for p in self.parameters():
            p.requires_grad_(False)

    def _step_lift(self, o_std: torch.Tensor) -> torch.Tensor:
        return torch.cat([o_std, self.psi(o_std)], dim=-1)

    @torch.no_grad()
    def forward(self, prev_obs_raw: torch.Tensor, last_action: torch.Tensor) -> torch.Tensor:
        """(N, d_obs), (N, d_act) -> (N, KOOPMAN_PRED_DIM) in RAW observation units.

        Raw units, not standardized, so the appended channels sit on the same scale as the
        observation dims they predict and the policy sees one homogeneous vector.
        """
        z = self._step_lift((prev_obs_raw - self._mu) / self._sd)
        for _ in range(self.horizon):
            if self._mlp_op is None:
                z = z @ self._A.T + last_action @ self._B.T
            else:
                z = z + self._mlp_op(torch.cat([z, last_action], dim=-1))
        return z[:, self._out_idx] * self._out_sd + self._out_mu

    @torch.no_grad()
    def reproduction_error(self) -> float:
        """Max deviation, in sigma, from the outputs this module produced when it was FITTED.

        The probe and its fitted outputs travel inside the checkpoint, so this checks the whole
        deployed path -- scaler, lift, operator, un-scaler -- reproduces the fitted behaviour,
        not merely that the weights loaded. It is the one load-time gate that can actually fail:
        a corrupted tensor, a normalization mismatch, or an architecture that strict loading
        happened to accept would all show up here.
        """
        got = self(self._probe_obs, self._probe_act)
        return float(((got - self._probe_out) / self._out_sd).abs().max())


def load_koopman_module(ckpt_path: str, device, tol: float = 0.05) -> FrozenKoopmanLift:
    """Build the frozen module and prove it reproduces its fitted outputs before RL uses it.

    The probe is REAL observations carried in the checkpoint, together with the outputs the
    module produced on them at fit time. Testing on synthetic inputs the module will never see
    measures the wrong thing: an all-dims-at-2-sigma sweep sits far off the data manifold where
    float32 conditioning dominates.

    `tol` is in units of each predicted channel's own standard deviation. It is 0.05 rather
    than something tighter because the fit runs in plain fp32 while Isaac Lab enables TF32,
    which alone moves 25 iterated 136x136 matmuls by ~1e-2 sigma. That is noise on a forecast
    whose own error is ~3 deg, not on a measurement -- but it is a real floor on how tight this
    gate can be, so it is stated rather than hidden.
    """
    m = FrozenKoopmanLift(ckpt_path, device)
    err = m.reproduction_error()
    if err > tol:
        raise RuntimeError(f"module does not reproduce its fitted outputs: {err:.3e} sigma "
                           f"(tol {tol}) for {ckpt_path}; refusing to train on it.")
    return m
