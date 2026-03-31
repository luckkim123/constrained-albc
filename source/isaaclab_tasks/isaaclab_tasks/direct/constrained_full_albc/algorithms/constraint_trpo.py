# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""TRPO + IPO: Trust Region Policy Optimization with Interior-Point constraint enforcement.

Core algorithm:
    maximize  E[A(s,a)] + (1/t) * sum_k log(d_k^i - J_hat_Ck)
    s.t.      KL(pi || pi_i) <= delta

    - TRPO natural gradient via conjugate gradient + line search
    - IPO log-barrier for K constraint costs
    - Adaptive thresholding: d_k^i = max(d_k, J_Ck + alpha * d_k)

Reference:
    Kim et al., "NORBC", IROS 2024 (Modified IPO).
    Muller et al., "Truly Constrained TRPO", ICML 2025.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable

import torch
import torch.nn as nn
import torch.optim as optim
from rsl_rl.storage import RolloutStorage
from tensordict import TensorDict

logger = logging.getLogger(__name__)


class ConstraintTRPO:
    """TRPO + IPO (Interior-Point Optimization) with log-barrier constraints."""

    def __init__(
        self,
        policy: nn.Module,
        # TRPO
        max_kl: float = 0.002,
        cg_iters: int = 10,
        cg_damping: float = 0.1,
        line_search_max_backtracks: int = 10,
        line_search_shrink_factor: float = 0.5,
        # Value function
        num_learning_epochs: int = 5,
        num_mini_batches: int = 4,
        value_loss_coef: float = 1.0,
        cost_value_loss_coef: float = 1.0,
        value_lr: float = 1e-3,
        max_grad_norm: float = 1.0,
        # GAE
        gamma: float = 0.99,
        lam: float = 0.95,
        # Constraints (IPO)
        num_constraints: int = 3,
        constraint_budgets: tuple[float, ...] = (0.15, 0.02, 0.15),
        cost_gamma: float = 0.99,
        cost_lam: float = 0.95,
        line_search_kl_margin: float = 1.5,
        barrier_t: float = 100.0,
        barrier_alpha: float = 0.02,
        # Sigma (decoupled from TRPO trust region)
        min_std: float = 0.01,
        std_lr: float = 1e-3,
        # Device
        device: str = "cpu",
        **_kwargs,
    ) -> None:
        if _kwargs:
            logger.debug("ConstraintTRPO ignoring unexpected kwargs: %s", list(_kwargs.keys()))
        self.device = device
        self.policy = policy
        self.policy.to(self.device)

        # TRPO
        self.max_kl = max_kl
        self.cg_iters = cg_iters
        self.cg_damping = cg_damping
        self.line_search_max_backtracks = line_search_max_backtracks
        self.line_search_shrink_factor = line_search_shrink_factor
        self.line_search_kl_margin = line_search_kl_margin

        # Value function
        self.num_learning_epochs = num_learning_epochs
        self.num_mini_batches = num_mini_batches
        self.value_loss_coef = value_loss_coef
        self.cost_value_loss_coef = cost_value_loss_coef
        self.max_grad_norm = max_grad_norm

        # GAE
        self.gamma = gamma
        self.lam = lam

        # IPO barrier
        self.num_constraints = num_constraints
        self.cost_gamma = cost_gamma
        self.cost_lam = cost_lam
        self._barrier_t = barrier_t
        self._barrier_alpha = barrier_alpha
        self.min_std = min_std

        # Monitoring (read by ConstraintEncoderRunner)
        self._last_cost_returns = [0.0] * num_constraints
        self._last_violations = [0.0] * num_constraints
        self._last_barrier_margins = [0.0] * num_constraints
        self._last_line_search_success = 0.0
        self._last_barrier_penalty = 0.0
        self._last_mean_entropy = 0.0
        self._last_surrogate_loss = 0.0
        self._last_encoder_grad_norm = 0.0
        # Gradient decomposition: vanilla vs natural gradient for encoder
        self._last_enc_vanilla_norm = 0.0
        self._last_enc_natgrad_norm = 0.0
        self._last_enc_step_norm = 0.0
        self._last_actor_vanilla_norm = 0.0
        self._last_actor_natgrad_norm = 0.0
        self._last_actor_step_norm = 0.0
        self._last_enc_cos_vanilla_natgrad = 0.0
        self._last_enc_cos_vanilla_step = 0.0

        if cost_gamma >= 1.0:
            raise ValueError(f"cost_gamma must be < 1.0, got {cost_gamma}")

        # Discounted budgets: d_k = D_k / (1 - gamma)
        self.d_k = torch.tensor(
            [b / (1.0 - cost_gamma) for b in constraint_budgets],
            device=device,
            dtype=torch.float32,
        )

        # --- Parameter groups ---
        # Three groups:
        #   1. Policy (actor + encoder): TRPO natural gradient (no optimizer)
        #      Encoder decoupling was tested (run 2026-03-30_12-27-19) and failed:
        #      enc_grad dropped 85% because actor->z gradient path is too weak.
        #      Keeping encoder in TRPO where it gets indirect gradient from CG.
        #   2. Sigma (log_std): Decoupled Adam (score-function gradient)
        #      In 2D action space, sigma consumes ~33% of KL budget if inside TRPO.
        #   3. Value (critic + cost_critic): Adam
        value_prefixes = ("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")
        value_params = []
        self._policy_params = []
        self._encoder_param_offset = 0
        self._encoder_param_count = 0

        offset = 0
        enc_start = None
        for name, param in self.policy.named_parameters():
            if name == "log_std":
                continue  # handled by std_optimizer
            if any(name.startswith(p) for p in value_prefixes):
                value_params.append(param)
            else:
                self._policy_params.append(param)
                if name.startswith("encoder"):
                    if enc_start is None:
                        enc_start = offset
                    self._encoder_param_count += param.numel()
                offset += param.numel()
        self._encoder_param_offset = enc_start if enc_start is not None else 0

        self._value_params = value_params
        self.value_optimizer = optim.Adam(value_params, lr=value_lr)

        # Sigma optimizer: separate Adam for log_std with score-function gradient.
        self._std_lr = std_lr
        self.std_optimizer = optim.Adam([self.policy.log_std], lr=std_lr)

        logger.info(
            "ConstraintTRPO: %d policy params (TRPO), %d value params (Adam), "
            "log_std decoupled (Adam, lr=%.4f), encoder slice [%d:%d] (%d params)",
            sum(p.numel() for p in self._policy_params),
            sum(p.numel() for p in value_params),
            std_lr,
            self._encoder_param_offset,
            self._encoder_param_offset + self._encoder_param_count,
            self._encoder_param_count,
        )

        # RSL-RL OnPolicyRunner compatibility
        self.rnd = None
        self.learning_rate = value_lr
        self.optimizer = self.value_optimizer
        self.encoder_optimizer = None

        # Storage
        self.storage: RolloutStorage | None = None
        self.transition = RolloutStorage.Transition()

    # ==================================================================
    # Storage & Rollout Interface
    # ==================================================================

    def init_storage(
        self,
        training_type: str,
        num_envs: int,
        num_transitions_per_env: int,
        obs: TensorDict,
        actions_shape: tuple[int] | list[int],
    ) -> None:
        self.storage = RolloutStorage(training_type, num_envs, num_transitions_per_env, obs, actions_shape, self.device)
        T, N, K = num_transitions_per_env, num_envs, self.num_constraints
        self.storage.costs = torch.zeros(T, N, K, device=self.device)
        self.storage.cost_values = torch.zeros(T, N, K, device=self.device)
        self.storage.cost_returns = torch.zeros(T, N, K, device=self.device)
        self.storage.cost_advantages = torch.zeros(T, N, K, device=self.device)
        self._zero_costs = torch.zeros(N, K, device=self.device)

    def act(self, obs: TensorDict) -> torch.Tensor:
        if self.policy.is_recurrent:
            self.transition.hidden_states = self.policy.get_hidden_states()
        self.transition.actions = self.policy.act(obs).detach()
        self.transition.values = self.policy.evaluate(obs).detach()
        self.transition.actions_log_prob = self.policy.get_actions_log_prob(self.transition.actions).detach()
        self.transition.action_mean = self.policy.action_mean.detach()
        self.transition.action_sigma = self.policy.action_std.detach()
        self.transition.observations = obs
        if self.num_constraints > 0:
            self._current_cost_values = self.policy.evaluate_costs(obs).detach()
        return self.transition.actions

    def process_env_step(
        self,
        obs: TensorDict,
        rewards: torch.Tensor,
        dones: torch.Tensor,
        extras: dict[str, torch.Tensor],
    ) -> None:
        self.policy.update_normalization(obs)
        self.transition.rewards = rewards.clone()
        self.transition.dones = dones

        if "time_outs" in extras:
            self.transition.rewards += self.gamma * torch.squeeze(
                self.transition.values * extras["time_outs"].unsqueeze(1).to(self.device), 1
            )

        step = self.storage.step
        if self.num_constraints > 0:
            costs = extras.get("costs", self._zero_costs)
            if "time_outs" in extras:
                time_out_mask = extras["time_outs"].unsqueeze(1).to(self.device)
                costs = costs + self.cost_gamma * self._current_cost_values * time_out_mask
            self.storage.costs[step] = costs
            self.storage.cost_values[step] = self._current_cost_values

        self.storage.add_transitions(self.transition)
        self.transition.clear()
        self.policy.reset(dones)

    def compute_returns(self, obs: TensorDict) -> None:
        last_values = self.policy.evaluate(obs).detach()
        self.storage.compute_returns(last_values, self.gamma, self.lam)
        if self.num_constraints > 0:
            last_cost_values = self.policy.evaluate_costs(obs).detach()
            self._compute_cost_returns(last_cost_values)

    def _compute_cost_returns(self, last_cost_values: torch.Tensor) -> None:
        """Cost GAE for all K constraints."""
        T = self.storage.num_transitions_per_env
        N = self.storage.num_envs
        advantage = torch.zeros(N, self.num_constraints, device=self.device)
        for step in reversed(range(T)):
            next_cv = last_cost_values if step == T - 1 else self.storage.cost_values[step + 1]
            not_done = (1.0 - self.storage.dones[step].float().squeeze(-1)).unsqueeze(-1)
            delta = self.storage.costs[step] + not_done * self.cost_gamma * next_cv - self.storage.cost_values[step]
            advantage = delta + not_done * self.cost_gamma * self.cost_lam * advantage
            self.storage.cost_returns[step] = advantage + self.storage.cost_values[step]
        self.storage.cost_advantages = self.storage.cost_returns - self.storage.cost_values

        # Sanitize non-finite values
        finite_mask = torch.isfinite(self.storage.cost_advantages).all(dim=(0, 1))
        bad = ~finite_mask
        if bad.any():
            bad_ids = bad.nonzero(as_tuple=True)[0].tolist()
            logger.warning("Non-finite cost advantages for constraints %s, zeroing.", bad_ids)
            self.storage.cost_advantages[:, :, bad] = 0.0

    # ==================================================================
    # IPO: Adaptive Thresholding
    # ==================================================================

    def _compute_adaptive_thresholds(self, mean_cost_returns: torch.Tensor) -> torch.Tensor:
        """d_k^i = max(d_k, J_C_k + alpha * d_k)"""
        return torch.max(self.d_k, mean_cost_returns + self._barrier_alpha * self.d_k)

    # ==================================================================
    # TRPO Core
    # ==================================================================

    def _get_policy_params_flat(self) -> torch.Tensor:
        return torch.cat([p.view(-1) for p in self._policy_params])

    def _set_policy_params_flat(self, flat_params: torch.Tensor) -> None:
        offset = 0
        for p in self._policy_params:
            numel = p.numel()
            p.data.copy_(flat_params[offset : offset + numel].view_as(p))
            offset += numel

    @staticmethod
    def _gaussian_kl(
        mu: torch.Tensor, sigma: torch.Tensor, old_mu: torch.Tensor, old_sigma: torch.Tensor
    ) -> torch.Tensor:
        """Mean KL(pi_old || pi_new) for diagonal Gaussian."""
        kl = (
            torch.log((sigma / old_sigma).clamp(min=1e-5))
            + (old_sigma.pow(2) + (old_mu - mu).pow(2)) / (2.0 * sigma.pow(2))
            - 0.5
        )
        return kl.sum(dim=-1).mean()

    def _kl_divergence(self, obs: TensorDict, old_mu: torch.Tensor, old_sigma: torch.Tensor) -> torch.Tensor:
        self.policy.act(obs)
        return self._gaussian_kl(self.policy.action_mean, self.policy.action_std, old_mu, old_sigma)

    def _flat_grad(self, loss: torch.Tensor, params: list[nn.Parameter], retain_graph: bool = False) -> torch.Tensor:
        grads = torch.autograd.grad(loss, params, retain_graph=retain_graph, create_graph=False)
        return torch.cat([g.contiguous().view(-1) for g in grads])

    def _fisher_vector_product(
        self, obs: TensorDict, old_mu: torch.Tensor, old_sigma: torch.Tensor, vector: torch.Tensor
    ) -> torch.Tensor:
        """F @ v via double backprop on KL (pure KL Hessian, no constraint curvature)."""
        self.policy.act(obs)
        kl = self._gaussian_kl(self.policy.action_mean, self.policy.action_std, old_mu, old_sigma)
        kl_grads = torch.autograd.grad(kl, self._policy_params, create_graph=True)
        flat_kl_grad = torch.cat([g.contiguous().view(-1) for g in kl_grads])
        kl_v = (flat_kl_grad * vector).sum()
        hvp_grads = torch.autograd.grad(kl_v, self._policy_params, retain_graph=False)
        fvp = torch.cat([g.contiguous().view(-1) for g in hvp_grads])
        return fvp + self.cg_damping * vector

    def _conjugate_gradient(
        self, obs: TensorDict, old_mu: torch.Tensor, old_sigma: torch.Tensor, b: torch.Tensor
    ) -> torch.Tensor:
        """Solve F @ x = b via CG. Returns x = F^{-1} @ g."""
        x = torch.zeros_like(b)
        r = b.clone()
        p = b.clone()
        rdotr = r.dot(r)
        for _ in range(self.cg_iters):
            fvp = self._fisher_vector_product(obs, old_mu, old_sigma, p)
            alpha = rdotr / (p.dot(fvp) + 1e-8)
            x += alpha * p
            r -= alpha * fvp
            new_rdotr = r.dot(r)
            if new_rdotr < 1e-10:
                break
            beta = new_rdotr / (rdotr + 1e-8)
            p = r + beta * p
            rdotr = new_rdotr
        return x

    def _line_search(
        self,
        obs: TensorDict,
        old_mu: torch.Tensor,
        old_sigma: torch.Tensor,
        step_dir: torch.Tensor,
        old_loss: torch.Tensor,
        surrogate_fn: Callable[[], torch.Tensor],
    ) -> bool:
        """Backtracking line search: accept when surrogate improves and KL <= delta."""
        old_params = self._get_policy_params_flat()
        step_size = 1.0
        kl_limit = self.max_kl * self.line_search_kl_margin
        for _ in range(self.line_search_max_backtracks):
            self._set_policy_params_flat(old_params + step_size * step_dir)
            with torch.no_grad():
                new_loss = surrogate_fn()
                kl = self._kl_divergence(obs, old_mu, old_sigma)
            if (old_loss - new_loss) > 0 and kl <= kl_limit:
                return True
            step_size *= self.line_search_shrink_factor
        self._set_policy_params_flat(old_params)
        return False

    # ==================================================================
    # Main Update: TRPO + IPO
    # ==================================================================

    def update(self) -> dict[str, float]:
        """One iteration: TRPO step (actor+encoder) -> sigma (Adam) -> values."""
        obs_flat = self.storage.observations.flatten(0, 1).clone()
        actions_flat = self.storage.actions.flatten(0, 1).clone()
        returns_flat = self.storage.returns.flatten(0, 1).clone()
        advantages_flat = self.storage.advantages.flatten(0, 1).clone()

        # Standardize reward advantages
        adv_std = advantages_flat.std()
        if adv_std > 1e-8:
            advantages_flat = (advantages_flat - advantages_flat.mean()) / adv_std

        old_log_prob_flat = self.storage.actions_log_prob.flatten(0, 1).clone()
        old_mu_flat = self.storage.mu.flatten(0, 1).clone()
        old_sigma_flat = self.storage.sigma.flatten(0, 1).clone()

        cost_returns_flat = self.storage.cost_returns.flatten(0, 1).clone()
        cost_advantages_flat = self.storage.cost_advantages.flatten(0, 1).clone()

        # Per-constraint cost advantage standardization (NORBC Sec IV-B).
        # clamp(min=1.0): binary constraints can have near-zero std, causing 1e8 amplification.
        ca_std = cost_advantages_flat.std(dim=0, keepdim=True).clamp(min=1.0)
        cost_advantages_flat = (cost_advantages_flat - cost_advantages_flat.mean(dim=0, keepdim=True)) / ca_std

        batch_size = obs_flat.batch_size[0]

        # Mean cost returns (clamped non-negative)
        mean_cost_returns = cost_returns_flat.mean(dim=0).clamp(min=0.0)

        # --- 1. IPO: Adaptive barrier thresholds ---
        adaptive_d_k = self._compute_adaptive_thresholds(mean_cost_returns)
        violations = (mean_cost_returns - self.d_k).tolist()
        with torch.no_grad():
            self._last_barrier_margins = (adaptive_d_k - mean_cost_returns).tolist()

        # --- 2. TRPO + IPO surrogate (joint actor+encoder) ---
        old_lp = old_log_prob_flat.squeeze(-1)
        adv = advantages_flat.squeeze(-1)
        barrier_base = adaptive_d_k - mean_cost_returns  # (K,) static margin
        inv_one_minus_gamma = 1.0 / (1.0 - self.cost_gamma)

        def surrogate() -> torch.Tensor:
            self.policy.act(obs_flat)
            log_prob = self.policy.get_actions_log_prob(actions_flat)
            ratio = torch.exp(log_prob - old_lp)
            reward_surr = -(adv * ratio).mean()
            cost_surrs = inv_one_minus_gamma * (ratio.unsqueeze(-1) * cost_advantages_flat).mean(dim=0)
            margin = barrier_base - cost_surrs
            barrier = -torch.log(margin.clamp(min=1e-8)).sum() / self._barrier_t
            self._last_barrier_penalty = barrier.item()
            self._last_mean_entropy = self.policy.entropy.mean().item()
            return reward_surr + barrier

        ls_success = self._trpo_step(obs_flat, old_mu_flat, old_sigma_flat, surrogate)

        # --- 3. Sigma update (decoupled from TRPO) ---
        with torch.no_grad():
            self.policy.act(obs_flat)
            post_trpo_lp = self.policy.get_actions_log_prob(actions_flat).detach()

        self.policy.act(obs_flat)
        sigma_log_prob = self.policy.get_actions_log_prob(actions_flat)
        sigma_ratio = torch.exp(sigma_log_prob - post_trpo_lp)
        sigma_surrogate = -(adv * sigma_ratio).mean()

        self.std_optimizer.zero_grad()
        sigma_grad = torch.autograd.grad(sigma_surrogate, self.policy.log_std)[0]
        self.policy.log_std.grad = sigma_grad
        self.std_optimizer.step()

        with torch.no_grad():
            self.policy.log_std.data.clamp_(min=math.log(self.min_std))

        # --- 4. KL after joint update ---
        with torch.no_grad():
            mean_kl = self._kl_divergence(obs_flat, old_mu_flat, old_sigma_flat).item()

        # --- 5. Value function update (MSE) ---
        mean_value_loss, mean_cost_value_loss = self._update_values(
            obs_flat, returns_flat, cost_returns_flat, batch_size
        )

        # Store monitoring metrics
        self._last_cost_returns = mean_cost_returns.tolist()
        self._last_violations = violations
        self._last_line_search_success = float(ls_success)

        self.storage.clear()
        return {"value_function": mean_value_loss, "kl": mean_kl, "cost_value": mean_cost_value_loss}

    # ==================================================================
    # Internal
    # ==================================================================

    def _trpo_step(
        self,
        obs_flat: TensorDict,
        old_mu_flat: torch.Tensor,
        old_sigma_flat: torch.Tensor,
        surrogate_fn: Callable[[], torch.Tensor],
    ) -> bool:
        """TRPO natural gradient step: surrogate -> CG -> step size -> line search."""
        loss = surrogate_fn()
        self._last_surrogate_loss = loss.item()
        g = self._flat_grad(loss, self._policy_params)

        # Store encoder gradient norm (pre-clip) for logging
        if self._encoder_param_count > 0:
            enc_slice = g[self._encoder_param_offset : self._encoder_param_offset + self._encoder_param_count]
            self._last_encoder_grad_norm = enc_slice.norm().item()

        # Clip gradient norm before CG
        g_norm = g.norm()
        if g_norm > self.max_grad_norm:
            g = g * (self.max_grad_norm / g_norm)

        # Natural gradient: x = F^{-1} g
        nat_grad = self._conjugate_gradient(obs_flat, old_mu_flat, old_sigma_flat, g)

        # Step size: sqrt(2 * delta / (g^T F^{-1} g))
        shs = 0.5 * nat_grad.dot(g)
        if shs <= 0 or not torch.isfinite(shs):
            logger.warning("TRPO: shs=%.6e non-positive/non-finite, skipping", shs.item())
            return False

        step_dir = -torch.sqrt(self.max_kl / shs) * nat_grad
        if not torch.isfinite(step_dir).all():
            logger.warning("TRPO: step_dir contains NaN/Inf, skipping")
            return False

        # --- Gradient decomposition: encoder vs actor ---
        if self._encoder_param_count > 0:
            s, e = self._encoder_param_offset, self._encoder_param_offset + self._encoder_param_count
            g_enc = g[s:e]
            g_actor = torch.cat([g[:s], g[e:]])
            ng_enc = nat_grad[s:e]
            ng_actor = torch.cat([nat_grad[:s], nat_grad[e:]])
            sd_enc = step_dir[s:e]
            sd_actor = torch.cat([step_dir[:s], step_dir[e:]])

            self._last_enc_vanilla_norm = g_enc.norm().item()
            self._last_enc_natgrad_norm = ng_enc.norm().item()
            self._last_enc_step_norm = sd_enc.norm().item()
            self._last_actor_vanilla_norm = g_actor.norm().item()
            self._last_actor_natgrad_norm = ng_actor.norm().item()
            self._last_actor_step_norm = sd_actor.norm().item()

            # Cosine similarity: vanilla vs natural gradient (encoder)
            # < 0 means FIM rotates encoder gradient direction
            g_enc_norm = g_enc.norm()
            ng_enc_norm = ng_enc.norm()
            sd_enc_norm = sd_enc.norm()
            if g_enc_norm > 1e-10 and ng_enc_norm > 1e-10:
                self._last_enc_cos_vanilla_natgrad = (g_enc.dot(ng_enc) / (g_enc_norm * ng_enc_norm)).item()
            else:
                self._last_enc_cos_vanilla_natgrad = 0.0
            if g_enc_norm > 1e-10 and sd_enc_norm > 1e-10:
                self._last_enc_cos_vanilla_step = (g_enc.dot(sd_enc) / (g_enc_norm * sd_enc_norm)).item()
            else:
                self._last_enc_cos_vanilla_step = 0.0

        with torch.no_grad():
            old_loss = surrogate_fn()
        ls_success = self._line_search(obs_flat, old_mu_flat, old_sigma_flat, step_dir, old_loss, surrogate_fn)
        if not ls_success:
            # Recalculate _last_barrier_penalty / _last_mean_entropy with reverted params.
            # Line search calls surrogate() up to 10 times with rejected candidates,
            # overwriting monitoring vars with values that don't reflect actual policy state.
            with torch.no_grad():
                surrogate_fn()
        return ls_success

    def _update_values(
        self,
        obs_flat: TensorDict,
        returns_flat: torch.Tensor,
        cost_returns_flat: torch.Tensor,
        batch_size: int,
    ) -> tuple[float, float]:
        """Update reward critic + cost critic via MSE."""
        mean_value_loss = 0.0
        mean_cost_value_loss = 0.0
        count = 0
        for _ in range(self.num_learning_epochs):
            indices = torch.randperm(batch_size, device=self.device)
            mb_size = batch_size // self.num_mini_batches
            for mb in range(self.num_mini_batches):
                idx = indices[mb * mb_size : (mb + 1) * mb_size]
                obs_mb = obs_flat[idx]

                value_loss = (returns_flat[idx] - self.policy.evaluate(obs_mb)).pow(2).mean()

                if self.num_constraints > 0:
                    cost_pred = self.policy.evaluate_costs(obs_mb)
                    target = cost_returns_flat[idx]
                    per_k_mse = (target - cost_pred).pow(2).mean(dim=0)
                    cost_value_loss = per_k_mse.mean()
                else:
                    cost_value_loss = torch.zeros_like(value_loss)

                total = self.value_loss_coef * value_loss + self.cost_value_loss_coef * cost_value_loss
                self.value_optimizer.zero_grad()
                total.backward()
                nn.utils.clip_grad_norm_(self._value_params, self.max_grad_norm)
                self.value_optimizer.step()

                mean_value_loss += value_loss.item()
                mean_cost_value_loss += cost_value_loss.item()
                count += 1

        if count > 0:
            mean_value_loss /= count
            mean_cost_value_loss /= count
        return mean_value_loss, mean_cost_value_loss

    def set_max_iterations(self, max_iterations: int) -> None:
        logger.info(
            "[ConstraintTRPO] barrier_t=%.1f, barrier_alpha=%.2f, max_iterations=%d",
            self._barrier_t,
            self._barrier_alpha,
            max_iterations,
        )
