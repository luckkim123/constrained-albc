"""G0-I (retrain-simtoreal-2026-09 PLAN §5 (1)(2), §6 G0-I): fault-sampler exposure.

Loads faults.py by path (as test_doraemon.py does) so no Isaac import chain is needed.
Closed form at severity s with q = s * p0 * d over six i.i.d. channels:
  P(>=1 dead) = 1-(1-q)^6,  P(>=2 dead) = 1-(1-q)^6-6q(1-q)^5,  P(exactly m3,m4 dead) = q^2 (1-q)^4.
Implementation authored by agy (gemini-3.1-pro-high, 2026-09-04), test adapted to the repo's
by-path import pattern by the Mac session.
"""
import importlib.util
from pathlib import Path

import pytest
import torch

_FAULTS_PATH = Path(__file__).resolve().parents[1] / "constrained_albc" / "envs" / "main" / "mdp" / "faults.py"
_spec = importlib.util.spec_from_file_location("faults_under_test", _FAULTS_PATH)
faults = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(faults)
sample_thruster_health = faults.sample_thruster_health


class DummyFaultCfg:
    def __init__(self, p0, d):
        self.thruster_fail_prob = p0
        self.thruster_health_range = (0.0, 0.5)
        self.thruster_dead_frac = d
        self.thruster_fixed_health = None


N = 500_000
T = 6
DEV = "cpu"
P0, D = 0.15, 0.5  # user-decided values (PLAN §10 item 2)
TOL = 0.005        # +- 0.5 percentage points


def _closed_form(q):
    p1 = 1 - (1 - q) ** 6
    p2 = 1 - (1 - q) ** 6 - 6 * q * (1 - q) ** 5
    p34 = q**2 * (1 - q) ** 4
    return p1, p2, p34


def test_fixed_severity_one():
    cfg = DummyFaultCfg(P0, D)
    gen = torch.Generator(device=DEV).manual_seed(42)
    health = sample_thruster_health(N, T, cfg, DEV, gen, torch.ones(N, device=DEV))
    dead = health == 0.0
    cnt = dead.sum(dim=1)
    p1 = (cnt >= 1).float().mean().item()
    p2 = (cnt >= 2).float().mean().item()
    p34 = (dead[:, 3] & dead[:, 4] & ~(dead[:, 0] | dead[:, 1] | dead[:, 2] | dead[:, 5])).float().mean().item()
    e1, e2, e34 = _closed_form(P0 * D)  # q = 0.075 -> 37.4 % / 6.89 % / 0.41 %
    assert abs(p1 - e1) <= TOL, (p1, e1)
    assert abs(p2 - e2) <= TOL, (p2, e2)
    assert abs(p34 - e34) <= TOL, (p34, e34)
    # residual (non-dead failed) health stays inside thruster_health_range
    failed_alive = (health < 1.0) & ~dead
    assert failed_alive.any()
    assert torch.all(health[failed_alive] > 0.0) and torch.all(health[failed_alive] <= 0.5)


def test_severity_integrated_uniform():
    cfg = DummyFaultCfg(P0, D)
    gen = torch.Generator(device=DEV).manual_seed(7)
    s = torch.rand(N, device=DEV, generator=gen)
    health = sample_thruster_health(N, T, cfg, DEV, gen, s)
    p2 = ((health == 0.0).sum(dim=1) >= 2).float().mean().item()
    # E_s[P(>=2 dead | q = s*p0*d)] by fine quadrature
    ss = torch.linspace(0, 1, 100_001, dtype=torch.float64)
    e2 = _closed_form(ss * P0 * D)[1].mean().item()  # ~ 2.42 % (PLAN §5, review/307)
    assert abs(p2 - e2) <= TOL, (p2, e2)


def test_severity_zero_all_healthy():
    cfg = DummyFaultCfg(P0, D)
    gen = torch.Generator(device=DEV).manual_seed(3)
    health = sample_thruster_health(N, T, cfg, DEV, gen, torch.zeros(N, device=DEV))
    assert torch.all(health == 1.0)


def test_dead_frac_zero_is_bit_identical_to_incumbent_sampler():
    cfg = DummyFaultCfg(P0, 0.0)
    sev = torch.ones(N, device=DEV)
    gen = torch.Generator(device=DEV).manual_seed(1234)
    got = sample_thruster_health(N, T, cfg, DEV, gen, sev)
    gen.manual_seed(1234)  # incumbent three-line sampler, same draws in the same order
    shape = (N, T)
    fail = torch.rand(shape, device=DEV, generator=gen) < sev.unsqueeze(-1) * cfg.thruster_fail_prob
    lo, hi = cfg.thruster_health_range
    residual = torch.rand(shape, device=DEV, generator=gen) * (hi - lo) + lo
    ref = torch.where(fail, residual, torch.ones(shape, device=DEV))
    assert torch.equal(got, ref)
