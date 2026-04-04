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
from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np
import torch
from scipy.optimize import Bounds, NonlinearConstraint, minimize

from isaaclab.utils import configclass

logger = logging.getLogger(__name__)


# Configuration
# ---------------------------------------------------------------------------


@configclass
class DoraemonCfg:
    """DORAEMON scheduler configuration.

    Reference: Tiboni et al., "Domain Randomization via Entropy Maximization", ICLR 2024.
    """

    enable: bool = True
    performance_lb: float = 80.0  # J_LB: episode return threshold for binary success
    alpha: float = 0.5  # Desired IS-estimated success rate for constraint (Ĝ >= alpha)
    kl_ub: float = 0.5  # Trust region KL upper bound per step (ref default=1.0)
    init_concentration: float = 30.0  # Initial Beta(a,b) concentration (a+b)
    step_interval: int = 250  # RL iterations between DORAEMON updates (ref: train_until_converged)
    buffer_size: int = 2000  # Maximum episode buffer capacity
    min_episodes: int = 200  # Minimum episodes before first update
    min_ess_ratio: float = 0.05  # Minimum ESS/buffer_size to accept update
    hard_performance_constraint: bool = True  # Use inverted problem when infeasible
    param_overrides: dict[str, tuple[float, float]] = {}  # Per-param bound overrides {name: (lo, hi)}


# Parameter Specification
# ---------------------------------------------------------------------------


class ParamSpec(NamedTuple):
    """Single DR parameter specification."""

    name: str
    min_bound: float
    max_bound: float
    nominal: float


# 18 DORAEMON-managed parameters for constrained ALBC.
# Order matches BetaDistribution dimension indices.
# Physics bounds are auto-synced from DomainRandomizationCfg at init time.

# Mapping: DORAEMON param name -> DomainRandomizationCfg field name.
# Fields with different names (e.g. payload_mass -> payload_mass_range) are explicit.
_PHYSICS_PARAM_DR_FIELDS: list[tuple[str, str]] = [
    ("payload_mass", "payload_mass_range"),
    ("added_mass_scale", "added_mass_scale"),
    ("linear_damping_scale", "linear_damping_scale"),
    ("quadratic_damping_scale", "quadratic_damping_scale"),
    ("water_density", "water_density_range"),
    ("cog_offset_z", "cog_offset_z"),
    ("cob_offset_z", "cob_offset_z"),
    ("volume_scale", "volume_scale"),
    ("cob_offset_x", "cob_offset_x"),
    ("cob_offset_y", "cob_offset_y"),
    ("cog_offset_x", "cog_offset_x"),
    ("cog_offset_y", "cog_offset_y"),
    ("inertia_scale", "inertia_scale"),
    ("body_mass_scale", "body_mass_scale"),
    ("payload_cog_offset_z", "payload_cog_offset_z"),
]

# Command scales: not in DomainRandomizationCfg, fixed bounds.
_CMD_SCALE_SPECS: list[ParamSpec] = [
    ParamSpec("cmd_lin_scale", 0.1, 1.2, 0.3),
    ParamSpec("cmd_att_scale", 0.1, 1.2, 0.3),
    ParamSpec("cmd_yaw_scale", 0.1, 1.2, 0.3),
]


def build_param_specs(dr_cfg) -> list[ParamSpec]:
    """Build PARAM_SPECS from DomainRandomizationCfg, auto-syncing physics bounds.

    Physics param bounds are read directly from the DR config tuple fields.
    Command scale bounds are fixed (not in DR config).
    """
    specs: list[ParamSpec] = []
    for param_name, field_name in _PHYSICS_PARAM_DR_FIELDS:
        lo, hi = getattr(dr_cfg, field_name)
        nominal = (lo + hi) / 2.0
        specs.append(ParamSpec(param_name, lo, hi, nominal))
    specs.extend(_CMD_SCALE_SPECS)
    return specs


# Default specs for backward compatibility and eval scripts.
# Uses hardcoded defaults matching base DomainRandomizationCfg.
# At runtime, DoraemonScheduler uses build_param_specs(dr_cfg) for actual bounds.
PARAM_SPECS: list[ParamSpec] = [
    ParamSpec(n, lo, hi, (lo + hi) / 2.0)
    for n, _, lo, hi in [
        ("payload_mass", "payload_mass_range", 0.0, 1.0),
        ("added_mass_scale", "added_mass_scale", 0.85, 1.15),
        ("linear_damping_scale", "linear_damping_scale", 0.5, 1.5),
        ("quadratic_damping_scale", "quadratic_damping_scale", 0.5, 1.5),
        ("water_density", "water_density_range", 995.0, 1025.0),
        ("cog_offset_z", "cog_offset_z", -0.02, 0.02),
        ("cob_offset_z", "cob_offset_z", -0.02, 0.02),
        ("volume_scale", "volume_scale", 0.9, 1.1),
        ("cob_offset_x", "cob_offset_x", -0.01, 0.01),
        ("cob_offset_y", "cob_offset_y", -0.01, 0.01),
        ("cog_offset_x", "cog_offset_x", -0.01, 0.01),
        ("cog_offset_y", "cog_offset_y", -0.01, 0.01),
        ("inertia_scale", "inertia_scale", 0.75, 1.3),
        ("body_mass_scale", "body_mass_scale", 0.9, 1.1),
        ("payload_cog_offset_z", "payload_cog_offset_z", -0.03, 0.0),
    ]
] + list(_CMD_SCALE_SPECS)
NDIMS = len(PARAM_SPECS)

_MIN_BETA_PARAM = 1.0
_MAX_BETA_PARAM = 500.0


def _compute_kl(flat_new: np.ndarray, flat_prev: np.ndarray) -> float:
    """Compute KL(new || prev) for independent Beta distributions.

    Uses reverse KL matching Algorithm 1: KL(phi || phi_i) < epsilon.
    Reverse KL penalizes expansion more heavily, providing conservative
    trust region suitable for slow-adapting TRPO policy.
    """
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
    """DORAEMON DR distribution scheduler.

    Aligned with Tiboni et al., ICLR 2024 reference implementation.
    Single constrained optimization: max H(phi) s.t. Ghat >= alpha, KL <= eps.
    When infeasible (hard_performance_constraint): inverted problem first.
    Binary success: episode_return >= performance_lb.
    Unnormalized IS with stored per-episode log probs.
    """

    def __init__(self, cfg: DoraemonCfg, device: torch.device, dr_cfg=None) -> None:
        self.cfg = cfg
        self.device = device

        # Build specs from DR config (auto-sync bounds) or use defaults
        specs = build_param_specs(dr_cfg) if dr_cfg is not None else list(PARAM_SPECS)
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
        self._total_episodes = 0

        logger.info(
            "[DORAEMON] Initialized: alpha=%.2f, kl_ub=%.4f, performance_lb=%.1f, "
            "%d parameters, concentration=%.0f, hard_constraint=%s",
            cfg.alpha,
            cfg.kl_ub,
            cfg.performance_lb,
            NDIMS,
            cfg.init_concentration,
            cfg.hard_performance_constraint,
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

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> dict[str, float]:
        """Run one DORAEMON distribution optimization step.

        Reference structure (Tiboni et al., ICLR 2024):
        1. Estimate success rate under current distribution via unnormalized IS
        2. If feasible (Ghat >= alpha): main optimization
        3. If infeasible + hard_constraint: inverted problem -> main optimization
        """
        xi, _returns, success, log_probs = self.buffer.get_all()
        n = xi.shape[0]

        metrics: dict[str, float] = {}
        metrics["buffer_size"] = float(n)
        metrics["total_episodes"] = float(self._total_episodes)

        if n < self.cfg.min_episodes:
            metrics["skipped"] = 1.0
            metrics["entropy"] = self.dist.entropy()
            metrics["success_rate"] = success.mean().item() if n > 0 else 0.0
            self._step_count += 1
            return metrics

        # Always report metrics; only optimize every step_interval iterations.
        # Between updates the policy trains on the current DR distribution,
        # matching the reference's "train for N steps then update" structure.
        metrics["success_rate"] = success.mean().item()
        metrics["entropy_before"] = self.dist.entropy()

        # Per-parameter distribution stats (always logged)
        for k, v in self.dist.get_stats().items():
            metrics[k] = v

        if self._step_count % self.cfg.step_interval != 0:
            metrics["entropy_after"] = self.dist.entropy()
            metrics["kl_step"] = 0.0
            self._step_count += 1
            return metrics

        prev_dist = self.dist.clone()

        # Estimate success rate under current distribution (unnormalized IS)
        # Use prev_dist as IS denominator: ring buffer data is mostly from recent
        # distributions close to prev_dist, matching reference's fresh-data approach.
        current_success_rate = self._estimate_success_rate(xi, success, prev_dist)
        metrics["success_rate"] = current_success_rate

        if self.cfg.hard_performance_constraint and current_success_rate < self.cfg.alpha:
            # Infeasible: inverted problem to find feasible starting point
            feasible_flat, inv_kl, inv_ok = self._find_feasible_start(
                prev_dist, xi, success
            )

            if inv_ok:
                self.dist.set_flat_params(feasible_flat)
                new_sr = self._estimate_success_rate(xi, success, prev_dist)

                if new_sr >= self.cfg.alpha:
                    # Feasible point found -> run main optimization from here
                    # Use original prev_dist as IS/KL reference (matches reference impl)
                    self._optimize_entropy(prev_dist, xi, success)
                    metrics["mode"] = 1.0  # inverted + optimize
                else:
                    # Max-success point still infeasible -> keep it, skip main opt
                    metrics["mode"] = -2.0  # kept max-success dist
            else:
                # Inverted problem failed -> revert
                self.dist = prev_dist
                metrics["mode"] = -3.0  # optimization error
        else:
            # Feasible (or soft constraint): main optimization directly
            self._optimize_entropy(prev_dist, xi, success)
            metrics["mode"] = 0.0  # normal

        metrics["entropy_after"] = self.dist.entropy()
        metrics["kl_step"] = self.dist.kl_divergence(prev_dist)

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

        self._step_count += 1
        return metrics

    # ------------------------------------------------------------------
    # IS estimation (unnormalized, using stored per-episode log probs)
    # ------------------------------------------------------------------

    def _estimate_success_rate(
        self,
        xi: torch.Tensor,
        success: torch.Tensor,
        ref_dist: BetaDistribution,
    ) -> float:
        """Unnormalized IS estimate: (1/K) sum [p_current(xi_k) / p_ref(xi_k)] * sigma_k.

        Uses ref_dist (typically prev_dist / current dist) as IS denominator instead
        of stored per-episode log_probs.  Ring buffer data is mostly from recent
        distributions close to ref_dist, so this is a good approximation and keeps
        IS weights near 1.0 -- matching the reference implementation which always
        uses current_distr as denominator with fresh data.
        """
        current_lp = self.dist.log_prob(xi)
        ref_lp = ref_dist.log_prob(xi)
        log_ratio = (current_lp - ref_lp).clamp(-20.0, 20.0)
        IS_weights = torch.exp(log_ratio)
        return torch.mean(IS_weights * success).item()

    def _compute_ess(
        self,
        xi: torch.Tensor,
        prev_dist: BetaDistribution,
        n: int,
    ) -> tuple[float, float]:
        """Effective Sample Size between current and previous distribution."""
        current_lp = self.dist.log_prob(xi)
        ref_lp = prev_dist.log_prob(xi)
        log_ratio = current_lp - ref_lp
        weights = torch.exp(log_ratio - log_ratio.max())
        weights = weights / weights.sum()
        ess = (1.0 / (weights**2).sum()).item()
        return ess, ess / max(n, 1)

    # ------------------------------------------------------------------
    # Main optimization: max H(phi) s.t. Ghat >= alpha, KL <= eps
    # ------------------------------------------------------------------

    def _optimize_entropy(
        self,
        prev_dist: BetaDistribution,
        xi: torch.Tensor,
        success: torch.Tensor,
    ) -> None:
        """Maximize entropy subject to success >= alpha and KL trust region.

        Uses trust-constr with analytical gradients (reference implementation).
        keep_feasible=False on all constraints for main problem.
        IS denominator: prev_dist (not stored log_probs) for ring buffer stability.
        """
        prev_flat = prev_dist.get_flat_params()
        ranges = self.dist._ranges
        mins = self.dist._mins

        # Precompute on CPU for scipy
        xi_unit = ((xi.detach().cpu().float() - mins.float()) / ranges.float()).clamp(1e-6, 1 - 1e-6).double()
        success_t = success.detach().cpu().double()
        # IS denominator: prev_dist log_prob (stable for ring buffer)
        prev_a_b_ref = torch.from_numpy(prev_flat.copy()).reshape(NDIMS, 2).double()
        prev_dist_ref = torch.distributions.Beta(
            prev_a_b_ref[:, 0].clamp(min=_MIN_BETA_PARAM), prev_a_b_ref[:, 1].clamp(min=_MIN_BETA_PARAM)
        )
        ref_lp = prev_dist_ref.log_prob(xi_unit).sum(dim=-1).detach()

        # -- Objective: minimize negative entropy --
        def objective_fn(flat: np.ndarray) -> tuple[float, np.ndarray]:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            dist = torch.distributions.Beta(a, b)
            neg_entropy = -(dist.entropy() + ranges.double().log()).sum()
            neg_entropy.backward()
            assert a_b.grad is not None
            return neg_entropy.item(), a_b.grad.flatten().numpy().copy()

        # -- Performance constraint: IS success rate >= alpha --
        def perf_fn(flat: np.ndarray) -> float:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double()
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            new_dist = torch.distributions.Beta(a, b)
            new_lp = new_dist.log_prob(xi_unit).sum(dim=-1)
            IS_w = torch.exp((new_lp - ref_lp).clamp(-20.0, 20.0))
            return torch.mean(IS_w * success_t).item()

        def perf_jac(flat: np.ndarray) -> np.ndarray:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            new_dist = torch.distributions.Beta(a, b)
            new_lp = new_dist.log_prob(xi_unit).sum(dim=-1)
            IS_w = torch.exp((new_lp - ref_lp).clamp(-20.0, 20.0))
            perf = torch.mean(IS_w * success_t)
            perf.backward()
            assert a_b.grad is not None
            return a_b.grad.flatten().numpy().copy()

        # -- KL constraint: KL(new || prev) <= kl_ub  (reverse KL, matching paper Alg. 1) --
        def kl_fn(flat: np.ndarray) -> float:
            return _compute_kl(flat, prev_flat)

        def kl_jac(flat: np.ndarray) -> np.ndarray:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            new_d = torch.distributions.Beta(a, b)
            prev_a_b = torch.from_numpy(prev_flat.copy()).reshape(NDIMS, 2).double()
            prev_d = torch.distributions.Beta(
                prev_a_b[:, 0].clamp(min=_MIN_BETA_PARAM), prev_a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            )
            kl = torch.distributions.kl_divergence(new_d, prev_d).sum()
            kl.backward()
            assert a_b.grad is not None
            return a_b.grad.flatten().numpy().copy()

        constraints = [
            NonlinearConstraint(perf_fn, lb=self.cfg.alpha - 1e-4, ub=np.inf, jac=perf_jac, keep_feasible=False),
            NonlinearConstraint(kl_fn, lb=-np.inf, ub=self.cfg.kl_ub, jac=kl_jac, keep_feasible=True),
        ]
        bounds = Bounds(lb=_MIN_BETA_PARAM, ub=_MAX_BETA_PARAM)
        x0 = self.dist.get_flat_params()

        try:
            result = minimize(
                objective_fn, x0, method="trust-constr", jac=True,
                constraints=constraints, bounds=bounds,
                options={"gtol": 1e-4, "xtol": 1e-6},
            )
            if result.success or result.fun < objective_fn(x0)[0]:
                self.dist.set_flat_params(result.x)
        except Exception as e:
            logger.warning("[DORAEMON] Entropy optimization failed: %s", e)

    # ------------------------------------------------------------------
    # Inverted problem: max Ghat(phi) s.t. KL <= eps
    # ------------------------------------------------------------------

    def _find_feasible_start(
        self,
        prev_dist: BetaDistribution,
        xi: torch.Tensor,
        success: torch.Tensor,
    ) -> tuple[np.ndarray | None, float, bool]:
        """Find a feasible starting distribution by maximizing success rate within trust region.

        Returns (flat_params, kl_step, success_flag).
        Reference: inverted problem from Tiboni et al. implementation.
        IS denominator: prev_dist (not stored log_probs) for ring buffer stability.
        """
        if success.sum().item() < 1.0:
            logger.debug("[DORAEMON] Inverted problem skipped: no successful episodes.")
            return None, 0.0, False

        prev_flat = prev_dist.get_flat_params()
        mins = self.dist._mins
        ranges = self.dist._ranges

        xi_unit = ((xi.detach().cpu().float() - mins.float()) / ranges.float()).clamp(1e-6, 1 - 1e-6).double()
        success_t = success.detach().cpu().double()
        # IS denominator: prev_dist log_prob (stable for ring buffer)
        prev_a_b_ref = torch.from_numpy(prev_flat.copy()).reshape(NDIMS, 2).double()
        prev_dist_ref = torch.distributions.Beta(
            prev_a_b_ref[:, 0].clamp(min=_MIN_BETA_PARAM), prev_a_b_ref[:, 1].clamp(min=_MIN_BETA_PARAM)
        )
        ref_lp = prev_dist_ref.log_prob(xi_unit).sum(dim=-1).detach()

        # Objective: maximize IS success rate = minimize negative
        def neg_success_fn(flat: np.ndarray) -> tuple[float, np.ndarray]:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            new_dist = torch.distributions.Beta(a, b)
            new_lp = new_dist.log_prob(xi_unit).sum(dim=-1)
            IS_w = torch.exp((new_lp - ref_lp).clamp(-20.0, 20.0))
            neg_sr = -torch.mean(IS_w * success_t)
            neg_sr.backward()
            assert a_b.grad is not None
            return neg_sr.item(), a_b.grad.flatten().numpy().copy()

        # KL constraint: KL(new || prev) <= kl_ub - 1e-5  (reverse KL, tighter bound)
        def kl_fn(flat: np.ndarray) -> float:
            return _compute_kl(flat, prev_flat)

        def kl_jac(flat: np.ndarray) -> np.ndarray:
            a_b = torch.from_numpy(flat.copy()).reshape(NDIMS, 2).double().requires_grad_(True)
            a = a_b[:, 0].clamp(min=_MIN_BETA_PARAM)
            b = a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            new_d = torch.distributions.Beta(a, b)
            prev_a_b = torch.from_numpy(prev_flat.copy()).reshape(NDIMS, 2).double()
            prev_d = torch.distributions.Beta(
                prev_a_b[:, 0].clamp(min=_MIN_BETA_PARAM), prev_a_b[:, 1].clamp(min=_MIN_BETA_PARAM)
            )
            kl = torch.distributions.kl_divergence(new_d, prev_d).sum()
            kl.backward()
            assert a_b.grad is not None
            return a_b.grad.flatten().numpy().copy()

        constraints = [
            NonlinearConstraint(
                kl_fn, lb=-np.inf, ub=self.cfg.kl_ub - 1e-5,
                jac=kl_jac, keep_feasible=True,
            ),
        ]
        bounds = Bounds(lb=_MIN_BETA_PARAM, ub=_MAX_BETA_PARAM)
        x0 = self.dist.get_flat_params()

        try:
            result = minimize(
                neg_success_fn, x0, method="trust-constr", jac=True,
                constraints=constraints, bounds=bounds,
                options={"gtol": 1e-4, "xtol": 1e-6},
            )
            if result.success:
                return result.x, kl_fn(result.x), True
            else:
                logger.warning("[DORAEMON] Inverted problem not successful.")
                return None, 0.0, False
        except Exception as e:
            logger.warning("[DORAEMON] Inverted problem failed: %s", e)
            return None, 0.0, False

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def state_dict(self) -> dict:
        """Serialize scheduler state for checkpoint persistence."""
        return {
            "dist_a": self.dist._a.clone(),
            "dist_b": self.dist._b.clone(),
            "step_count": self._step_count,
            "total_episodes": self._total_episodes,
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
        self._total_episodes = state["total_episodes"]

        # Restore buffer
        n = state["buffer_xi"].shape[0]
        self.buffer.xi[:n] = state["buffer_xi"].to(self.device)
        self.buffer.returns[:n] = state["buffer_returns"].to(self.device)
        self.buffer.success[:n] = state["buffer_success"].to(self.device)
        self.buffer.log_probs[:n] = state["buffer_log_probs"].to(self.device)
        self.buffer._count = n
        self.buffer._write_idx = state["buffer_write_idx"]
