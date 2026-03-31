# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""DORAEMON: Domain Randomization with Entropy Maximization (ICLR 2024).

Adaptive Beta distribution scheduling for DR, replacing linear curriculum.
Reference: Tiboni et al., "Domain Randomization via Entropy Maximization", ICLR 2024.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np
import torch
from scipy.optimize import NonlinearConstraint, minimize

from isaaclab.utils import configclass

logger = logging.getLogger(__name__)


# Configuration
# ---------------------------------------------------------------------------


@configclass
class DoraemonCfg:
    """DORAEMON scheduler configuration."""

    enable: bool = True
    alpha: float = 0.5  # Success rate threshold for distribution expansion
    kl_ub: float = 0.0015  # Trust region KL upper bound per step
    init_concentration: float = 30.0  # Initial Beta(a,b) concentration (a+b)
    success_threshold: float = 0.25  # Velocity error threshold (m/s)
    success_threshold_final: float = 0.25  # Final threshold (no annealing if same)
    success_threshold_anneal_steps: int = 0  # 0 = immediate final threshold
    buffer_size: int = 2000  # Maximum episode buffer capacity
    min_episodes: int = 200  # Minimum episodes before first update
    traversability_tau: float = 0.035  # Sigmoid temperature (m/s)
    min_ess_ratio: float = 0.05  # Minimum ESS/buffer_size to accept update
    param_overrides: dict[str, tuple[float, float]] = {}  # Per-param bound overrides {name: (lo, hi)}


# Parameter Specification
# ---------------------------------------------------------------------------


class ParamSpec(NamedTuple):
    """Single DR parameter specification."""

    name: str
    min_bound: float
    max_bound: float
    nominal: float


# 15 DORAEMON-managed DR parameters for constrained ALBC.
# Order matches BetaDistribution dimension indices.
# SYNC: Bounds must match DomainRandomizationCfg in config.py.
#       Use DoraemonCfg.param_overrides to widen bounds for Hard DR.
PARAM_SPECS: list[ParamSpec] = [
    # name                    min     max     nominal
    ParamSpec("payload_mass", 0.0, 1.0, 0.5),
    ParamSpec("added_mass_scale", 0.85, 1.15, 1.0),
    ParamSpec("linear_damping_scale", 0.5, 1.5, 1.0),
    ParamSpec("quadratic_damping_scale", 0.5, 1.5, 1.0),
    ParamSpec("water_density", 995.0, 1025.0, 1010.0),
    ParamSpec("cog_offset_z", -0.02, 0.02, 0.0),
    ParamSpec("cob_offset_z", -0.02, 0.02, 0.0),
    ParamSpec("volume_scale", 0.9, 1.1, 1.0),
    ParamSpec("cob_offset_x", -0.01, 0.01, 0.0),
    ParamSpec("cob_offset_y", -0.01, 0.01, 0.0),
    ParamSpec("cog_offset_x", -0.01, 0.01, 0.0),
    ParamSpec("cog_offset_y", -0.01, 0.01, 0.0),
    ParamSpec("inertia_scale", 0.75, 1.3, 1.0),
    ParamSpec("body_mass_scale", 0.9, 1.1, 1.0),
    ParamSpec("payload_cog_offset_z", -0.03, 0.0, -0.015),
]

NDIMS = len(PARAM_SPECS)

_MIN_BETA_PARAM = 1.0
_MAX_BETA_PARAM = 500.0


def _compute_kl(flat_new: np.ndarray, flat_prev: np.ndarray) -> float:
    """Compute KL(new || prev) for independent Beta distributions."""
    a_b_new = torch.from_numpy(flat_new.copy()).reshape(-1, 2).double()
    a_b_prev = torch.from_numpy(flat_prev.copy()).reshape(-1, 2).double()
    new = torch.distributions.Beta(
        a_b_new[:, 0].clamp(min=_MIN_BETA_PARAM),
        a_b_new[:, 1].clamp(min=_MIN_BETA_PARAM),
    )
    prev = torch.distributions.Beta(
        a_b_prev[:, 0].clamp(min=_MIN_BETA_PARAM),
        a_b_prev[:, 1].clamp(min=_MIN_BETA_PARAM),
    )
    return torch.distributions.kl_divergence(new, prev).sum().item()


# Beta Distribution
# ---------------------------------------------------------------------------


class BetaDistribution:
    """Independent Beta distributions over DR parameter space, mapped to physical bounds."""

    def __init__(self, params: list[ParamSpec], device: torch.device, concentration: float = 200.0) -> None:
        self.params = params
        self.ndims = len(params)
        self.device = device

        self._mins = torch.tensor([p.min_bound for p in params], dtype=torch.float64)
        self._maxs = torch.tensor([p.max_bound for p in params], dtype=torch.float64)
        self._ranges = self._maxs - self._mins

        self._a = torch.zeros(self.ndims, dtype=torch.float64)
        self._b = torch.zeros(self.ndims, dtype=torch.float64)

        for i, p in enumerate(params):
            mu = (p.nominal - p.min_bound) / (p.max_bound - p.min_bound)
            mu = max(0.01, min(0.99, mu))
            a_raw = mu * concentration
            b_raw = (1.0 - mu) * concentration
            if a_raw < _MIN_BETA_PARAM or b_raw < _MIN_BETA_PARAM:
                # Preserve mean: derive the other param from the clamped one
                if mu <= 0.5:
                    self._a[i] = _MIN_BETA_PARAM
                    self._b[i] = _MIN_BETA_PARAM * (1.0 - mu) / mu
                else:
                    self._b[i] = _MIN_BETA_PARAM
                    self._a[i] = _MIN_BETA_PARAM * mu / (1.0 - mu)
            else:
                self._a[i] = a_raw
                self._b[i] = b_raw

    def sample(self, n: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Sample n parameter vectors and their log probabilities."""
        a_gpu = self._a.float().to(self.device)
        b_gpu = self._b.float().to(self.device)
        dist = torch.distributions.Beta(a_gpu, b_gpu)

        xi_unit = dist.sample((n,))
        log_probs = dist.log_prob(xi_unit).sum(dim=-1)

        mins_gpu = self._mins.float().to(self.device)
        ranges_gpu = self._ranges.float().to(self.device)
        xi_physical = mins_gpu + xi_unit * ranges_gpu
        return xi_physical, log_probs

    def log_prob(self, xi_physical: torch.Tensor) -> torch.Tensor:
        """Compute log probability of physical-scale samples."""
        mins_gpu = self._mins.float().to(self.device)
        ranges_gpu = self._ranges.float().to(self.device)
        xi_unit = (xi_physical - mins_gpu) / ranges_gpu
        xi_unit = xi_unit.clamp(1e-6, 1.0 - 1e-6)

        a_gpu = self._a.float().to(self.device)
        b_gpu = self._b.float().to(self.device)
        dist = torch.distributions.Beta(a_gpu, b_gpu)
        return dist.log_prob(xi_unit).sum(dim=-1)

    def entropy(self) -> float:
        """Total entropy: sum of per-dim Beta entropies + log(range) scaling."""
        dist = torch.distributions.Beta(self._a, self._b)
        return (dist.entropy() + self._ranges.log()).sum().item()

    def kl_divergence(self, other: BetaDistribution) -> float:
        """KL(self || other): sum of per-dim KL divergences."""
        p = torch.distributions.Beta(self._a, self._b)
        q = torch.distributions.Beta(other._a, other._b)
        return torch.distributions.kl_divergence(p, q).sum().item()

    def get_flat_params(self) -> np.ndarray:
        """Return [a0, b0, a1, b1, ...] as float64 numpy for scipy."""
        flat = torch.stack([self._a, self._b], dim=-1).flatten()
        return flat.numpy()

    def set_flat_params(self, flat: np.ndarray) -> None:
        """Update from scipy result: [a0, b0, a1, b1, ...]."""
        t = torch.from_numpy(flat.copy()).reshape(self.ndims, 2).double()
        self._a = t[:, 0].clamp(min=_MIN_BETA_PARAM, max=_MAX_BETA_PARAM)
        self._b = t[:, 1].clamp(min=_MIN_BETA_PARAM, max=_MAX_BETA_PARAM)

    def clone(self) -> BetaDistribution:
        """Deep copy."""
        new = BetaDistribution.__new__(BetaDistribution)
        new.params = self.params
        new.ndims = self.ndims
        new.device = self.device
        new._mins = self._mins.clone()
        new._maxs = self._maxs.clone()
        new._ranges = self._ranges.clone()
        new._a = self._a.clone()
        new._b = self._b.clone()
        return new

    def get_stats(self) -> dict[str, float]:
        """Per-dimension mean and std in physical space for logging."""
        stats = {}
        for i, p in enumerate(self.params):
            a, b = self._a[i].item(), self._b[i].item()
            mean_unit = a / (a + b)
            var_unit = (a * b) / ((a + b) ** 2 * (a + b + 1))
            std_unit = var_unit**0.5
            mean_phys = p.min_bound + mean_unit * (p.max_bound - p.min_bound)
            std_phys = std_unit * (p.max_bound - p.min_bound)
            stats[f"mean/{p.name}"] = mean_phys
            stats[f"std/{p.name}"] = std_phys
        return stats


# Episode Buffer
# ---------------------------------------------------------------------------


@dataclass
class EpisodeBuffer:
    """Ring buffer for completed episode statistics."""

    capacity: int
    ndims: int
    device: torch.device

    xi: torch.Tensor = field(init=False)
    returns: torch.Tensor = field(init=False)
    success: torch.Tensor = field(init=False)
    log_probs: torch.Tensor = field(init=False)
    _count: int = field(init=False, default=0)
    _write_idx: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.xi = torch.zeros(self.capacity, self.ndims, device=self.device)
        self.returns = torch.zeros(self.capacity, device=self.device)
        self.success = torch.zeros(self.capacity, device=self.device)
        self.log_probs = torch.zeros(self.capacity, device=self.device)

    def add(
        self,
        xi: torch.Tensor,
        returns: torch.Tensor,
        success: torch.Tensor,
        log_probs: torch.Tensor,
    ) -> None:
        """Batch insert episodes. Wraps around if capacity exceeded."""
        n = xi.shape[0]
        if n == 0:
            return
        if n > self.capacity:
            tail = n - self.capacity
            xi = xi[tail:]
            returns = returns[tail:]
            success = success[tail:]
            log_probs = log_probs[tail:]
            n = self.capacity
        start = self._write_idx % self.capacity
        if start + n <= self.capacity:
            self.xi[start : start + n] = xi
            self.returns[start : start + n] = returns
            self.success[start : start + n] = success
            self.log_probs[start : start + n] = log_probs
        else:
            first = self.capacity - start
            self.xi[start:] = xi[:first]
            self.returns[start:] = returns[:first]
            self.success[start:] = success[:first]
            self.log_probs[start:] = log_probs[:first]
            self.xi[: n - first] = xi[first:]
            self.returns[: n - first] = returns[first:]
            self.success[: n - first] = success[first:]
            self.log_probs[: n - first] = log_probs[first:]
        self._write_idx += n
        self._count = min(self._count + n, self.capacity)

    def get_all(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return valid entries."""
        n = self._count
        return self.xi[:n], self.returns[:n], self.success[:n], self.log_probs[:n]

    def clear(self) -> None:
        """Reset buffer."""
        self._count = 0
        self._write_idx = 0


# DORAEMON Scheduler
# ---------------------------------------------------------------------------


class DoraemonScheduler:
    """DORAEMON DR distribution scheduler."""

    def __init__(self, cfg: DoraemonCfg, device: torch.device) -> None:
        self.cfg = cfg
        self.device = device

        # Apply per-parameter bound overrides
        specs = list(PARAM_SPECS)
        if cfg.param_overrides:
            name_to_idx = {s.name: i for i, s in enumerate(specs)}
            for name, (lo, hi) in cfg.param_overrides.items():
                if name not in name_to_idx:
                    logger.warning("[DORAEMON] param_overrides: unknown parameter '%s', skipping.", name)
                    continue
                idx = name_to_idx[name]
                old = specs[idx]
                specs[idx] = ParamSpec(old.name, lo, hi, (lo + hi) / 2.0)
                logger.info(
                    "[DORAEMON] Override %s bounds: (%.2f, %.2f) -> (%.2f, %.2f)",
                    name,
                    old.min_bound,
                    old.max_bound,
                    lo,
                    hi,
                )

        self.dist = BetaDistribution(specs, device, cfg.init_concentration)
        self.buffer = EpisodeBuffer(cfg.buffer_size, NDIMS, device)

        self._step_count = 0
        self._backup_count = 0
        self._total_episodes = 0
        self._current_threshold = cfg.success_threshold
        self._threshold_anneal_count = 0

        logger.info(
            "[DORAEMON] Initialized: alpha=%.2f, kl_ub=%.4f, %d parameters, "
            "concentration=%.0f, threshold=%.3f->%.3f m/s over %d steps",
            cfg.alpha,
            cfg.kl_ub,
            NDIMS,
            cfg.init_concentration,
            cfg.success_threshold,
            cfg.success_threshold_final,
            cfg.success_threshold_anneal_steps,
        )

    def sample(self, n: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Sample DR parameters from current Beta distribution."""
        return self.dist.sample(n)

    def record_episodes(
        self,
        xi: torch.Tensor,
        returns: torch.Tensor,
        success: torch.Tensor,
        log_probs: torch.Tensor,
    ) -> None:
        """Record completed episodes into the buffer."""
        self.buffer.add(xi, returns, success, log_probs)
        self._total_episodes += xi.shape[0]

    def step(self) -> dict[str, float]:
        """Run one DORAEMON optimization step. Returns metrics dict."""
        xi, _returns, success, _log_probs = self.buffer.get_all()
        n = xi.shape[0]

        metrics: dict[str, float] = {}
        metrics["buffer_size"] = float(n)
        metrics["total_episodes"] = float(self._total_episodes)

        if n < self.cfg.min_episodes:
            metrics["skipped"] = 1.0
            metrics["entropy"] = self.dist.entropy()
            metrics["success_rate"] = success.mean().item() if n > 0 else 0.0
            return metrics

        success_rate = success.mean().item()
        metrics["success_rate"] = success_rate

        if success_rate >= self.cfg.alpha:
            self._anneal_threshold()
        metrics["success_threshold"] = self._current_threshold

        metrics["entropy_before"] = self.dist.entropy()

        prev_dist = self.dist.clone()

        if success_rate < self.cfg.alpha:
            self._backup(prev_dist, xi, success)
            backup_success = self._estimate_success_rate(xi, success, prev_dist)
            if backup_success >= self.cfg.alpha:
                self._maximize_entropy(self.dist.clone(), xi, success)
                metrics["mode"] = 0.5  # backup-then-expand
            else:
                metrics["mode"] = 0.0  # backup only
            self._backup_count += 1
        else:
            self._maximize_entropy(prev_dist, xi, success)
            metrics["mode"] = 1.0  # expand

        metrics["entropy_after"] = self.dist.entropy()
        metrics["kl_step"] = self.dist.kl_divergence(prev_dist)
        metrics["backup_count"] = float(self._backup_count)

        # ESS validation: revert if IS estimator quality is too low
        ess, ess_ratio = self._compute_ess(xi, prev_dist, n)
        metrics["ess"] = ess
        metrics["ess_ratio"] = ess_ratio
        if ess < self.cfg.min_ess_ratio * n:
            self.dist = prev_dist
            metrics["reverted"] = 1.0
            metrics["entropy_after"] = self.dist.entropy()
            metrics["kl_step"] = 0.0
            logger.warning("[DORAEMON] Reverted: ESS=%.0f (%.1f%% of %d)", ess, 100 * ess_ratio, n)

        # Per-parameter distribution stats
        for k, v in self.dist.get_stats().items():
            metrics[k] = v

        self.buffer.clear()
        self._step_count += 1
        return metrics

    def _anneal_threshold(self) -> None:
        """Anneal success threshold by one step."""
        cfg = self.cfg
        self._threshold_anneal_count += 1
        if cfg.success_threshold_anneal_steps <= 0:
            self._current_threshold = cfg.success_threshold_final
            return
        t = min(1.0, self._threshold_anneal_count / cfg.success_threshold_anneal_steps)
        self._current_threshold = cfg.success_threshold + t * (cfg.success_threshold_final - cfg.success_threshold)

    def _compute_ess(
        self,
        xi: torch.Tensor,
        prev_dist: BetaDistribution,
        n: int,
    ) -> tuple[float, float]:
        """Compute Effective Sample Size between current and previous distribution."""
        new_lp = self.dist.log_prob(xi)
        old_lp = prev_dist.log_prob(xi)
        log_ratio = new_lp - old_lp
        weights = torch.exp(log_ratio - log_ratio.max())
        weights = weights / weights.sum()
        ess = (1.0 / (weights**2).sum()).item()
        return ess, ess / max(n, 1)

    def _estimate_success_rate(
        self,
        xi: torch.Tensor,
        success: torch.Tensor,
        ref_dist: BetaDistribution,
    ) -> float:
        """Estimate success rate under current dist via IS from ref_dist."""
        new_lp = self.dist.log_prob(xi)
        old_lp = ref_dist.log_prob(xi)
        log_ratio = new_lp - old_lp
        weights = torch.exp(log_ratio - log_ratio.max())
        weights = weights / weights.sum()
        return (weights * success).sum().item()

    def _maximize_entropy(
        self,
        prev_dist: BetaDistribution,
        xi: torch.Tensor,
        success: torch.Tensor,
    ) -> None:
        """Maximize entropy subject to success >= alpha and KL trust region."""
        prev_flat = prev_dist.get_flat_params()
        ranges = self.dist._ranges
        mins = self.dist._mins

        xi_cpu = xi.detach().cpu().numpy().astype(np.float64)
        success_cpu = success.detach().cpu().numpy().astype(np.float64)

        def objective_and_grad(flat: np.ndarray) -> tuple[float, np.ndarray]:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            dist = torch.distributions.Beta(a, b)
            neg_entropy = -(dist.entropy() + ranges.log()).sum()
            neg_entropy.backward()
            assert a_b.grad is not None
            return neg_entropy.item(), a_b.grad.flatten().numpy().copy()

        def success_constraint_fun(flat: np.ndarray) -> float:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double()
            a_new = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b_new = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)

            xi_t = torch.from_numpy(xi_cpu).double()
            xi_unit = ((xi_t - mins) / ranges).clamp(1e-6, 1 - 1e-6)
            new_dist = torch.distributions.Beta(a_new, b_new)
            new_lp = new_dist.log_prob(xi_unit).sum(dim=-1)

            old_a_b = torch.from_numpy(prev_flat.copy()).reshape(NDIMS, 2).double()
            old_dist = torch.distributions.Beta(old_a_b[:, 0].clamp(min=1.0), old_a_b[:, 1].clamp(min=1.0))
            old_lp = old_dist.log_prob(xi_unit).sum(dim=-1)

            log_ratio = new_lp - old_lp
            weights = torch.exp(log_ratio - log_ratio.max())
            weights = weights / weights.sum()
            success_t = torch.from_numpy(success_cpu).double()
            return (weights * success_t).sum().item()

        def kl_constraint_fun(flat: np.ndarray) -> float:
            return _compute_kl(flat, prev_flat)

        success_con = NonlinearConstraint(success_constraint_fun, lb=self.cfg.alpha, ub=np.inf)
        kl_con = NonlinearConstraint(kl_constraint_fun, lb=0.0, ub=self.cfg.kl_ub, keep_feasible=True)

        self._run_scipy_step(objective_and_grad, [success_con, kl_con], "Entropy maximization")

    def _run_scipy_step(
        self,
        objective_fn: Callable[[np.ndarray], tuple[float, np.ndarray]],
        constraints: list,
        label: str,
    ) -> None:
        """Run a single trust-constr optimization step on the Beta distribution."""
        bounds = [(float(_MIN_BETA_PARAM), float(_MAX_BETA_PARAM))] * (2 * NDIMS)
        x0 = self.dist.get_flat_params()
        try:
            result = minimize(
                objective_fn,
                x0,
                method="trust-constr",
                jac=True,
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 50, "gtol": 1e-8},
            )
            if result.success or result.fun < objective_fn(x0)[0]:
                self.dist.set_flat_params(result.x)
        except Exception as e:
            logger.warning("[DORAEMON] %s failed: %s", label, e)

    def _backup(
        self,
        prev_dist: BetaDistribution,
        xi: torch.Tensor,
        success: torch.Tensor,
    ) -> None:
        """Maximize IS-weighted success rate within KL trust region."""
        # Skip if no successful episodes (optimizer would drift within trust region)
        if success.sum().item() < 1.0:
            logger.debug("[DORAEMON] Backup skipped: no successful episodes in buffer.")
            return

        prev_flat = prev_dist.get_flat_params()
        mins = self.dist._mins
        ranges = self.dist._ranges

        xi_cpu = xi.detach().cpu().numpy().astype(np.float64)
        success_cpu = success.detach().cpu().numpy().astype(np.float64)

        def neg_success_and_grad(flat: np.ndarray) -> tuple[float, np.ndarray]:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)

            xi_t = torch.from_numpy(xi_cpu).double()
            xi_unit = ((xi_t - mins) / ranges).clamp(1e-6, 1 - 1e-6)

            new_dist = torch.distributions.Beta(a, b)
            new_lp = new_dist.log_prob(xi_unit).sum(dim=-1)

            old_a_b = torch.from_numpy(prev_flat.copy()).reshape(NDIMS, 2).double()
            old_dist = torch.distributions.Beta(old_a_b[:, 0].clamp(min=1.0), old_a_b[:, 1].clamp(min=1.0))
            old_lp = old_dist.log_prob(xi_unit).sum(dim=-1)

            log_ratio = new_lp - old_lp
            weights = torch.exp(log_ratio - log_ratio.max().detach())
            weights = weights / weights.sum().detach()

            success_t = torch.from_numpy(success_cpu).double()
            neg_success = -(weights * success_t).sum()

            neg_success.backward()
            assert a_b.grad is not None
            return neg_success.item(), a_b.grad.flatten().numpy().copy()

        def kl_constraint_fun(flat: np.ndarray) -> float:
            return _compute_kl(flat, prev_flat)

        kl_con = NonlinearConstraint(kl_constraint_fun, lb=0.0, ub=self.cfg.kl_ub, keep_feasible=True)
        self._run_scipy_step(neg_success_and_grad, [kl_con], "Backup step")

    def state_dict(self) -> dict:
        """Serialize scheduler state for checkpoint persistence."""
        return {
            "dist_a": self.dist._a.clone(),
            "dist_b": self.dist._b.clone(),
            "step_count": self._step_count,
            "backup_count": self._backup_count,
            "total_episodes": self._total_episodes,
            "current_threshold": self._current_threshold,
            "threshold_anneal_count": self._threshold_anneal_count,
            "buffer_xi": self.buffer.xi[: self.buffer._count].clone(),
            "buffer_returns": self.buffer.returns[: self.buffer._count].clone(),
            "buffer_success": self.buffer.success[: self.buffer._count].clone(),
            "buffer_log_probs": self.buffer.log_probs[: self.buffer._count].clone(),
            "buffer_write_idx": self.buffer._write_idx,
        }

    def load_state_dict(self, state: dict) -> None:
        """Restore scheduler state from a checkpoint."""
        ndims = self.dist.ndims
        if state["dist_a"].shape[0] != ndims:
            raise ValueError(
                f"DORAEMON checkpoint has {state['dist_a'].shape[0]} dims but current config expects {ndims}."
            )
        self.dist._a = state["dist_a"].double()
        self.dist._b = state["dist_b"].double()

        self._step_count = state["step_count"]
        self._backup_count = state["backup_count"]
        self._total_episodes = state["total_episodes"]
        self._threshold_anneal_count = state["threshold_anneal_count"]
        self._current_threshold = state["current_threshold"]

        # Restore buffer
        n = state["buffer_xi"].shape[0]
        self.buffer.xi[:n] = state["buffer_xi"].to(self.device)
        self.buffer.returns[:n] = state["buffer_returns"].to(self.device)
        self.buffer.success[:n] = state["buffer_success"].to(self.device)
        self.buffer.log_probs[:n] = state["buffer_log_probs"].to(self.device)
        self.buffer._count = n
        self.buffer._write_idx = state["buffer_write_idx"]
