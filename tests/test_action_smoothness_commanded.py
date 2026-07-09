"""Task 7 (M-A fix): action_smoothness reads the COMMANDED action stream, not
the delayed (plant-applied) stream.

Skipped if importing isaaclab.utils.buffers boots Isaac Sim (structural-only test) --
same pxr-unavailable situation as test_latency_dr_env.py. See that file's docstring
for the full explanation of the sys.modules purge below (sibling tests leak import
state across the pytest session; this purge makes the skip reason trustworthy).
"""

import sys

import pytest

sys.modules.pop("isaaclab.utils.buffers", None)

for _name in (
    "isaaclab.utils",
    "isaaclab",
    "constrained_albc.envs.main",
    "constrained_albc.envs",
    "constrained_albc",
):
    _mod = sys.modules.get(_name)
    if _mod is not None and not hasattr(_mod, "__path__"):
        del sys.modules[_name]

pytest.importorskip("isaaclab.utils.buffers")

import torch

from constrained_albc.envs.main.albc_env import _apply_control_delay, _draw_control_delay


def test_off_commanded_equals_delayed_triple():
    """control_delay_steps=(0,0): commanded triple must equal the delayed
    triple exactly, every step -- this is the byte-identical-when-off invariant
    that guarantees action_smoothness is unchanged from the pre-Task-7 baseline.
    """
    num_envs = 4
    action_dim = 8
    _, delay_buf = _draw_control_delay((0, 0), num_envs, device="cpu")
    assert delay_buf is None  # off = no buffer allocated, pass-through path

    actions = torch.zeros(num_envs, action_dim)
    prev_actions = torch.zeros(num_envs, action_dim)
    prev_prev_actions = torch.zeros(num_envs, action_dim)
    cmd_actions = torch.zeros(num_envs, action_dim)
    prev_cmd_actions = torch.zeros(num_envs, action_dim)
    prev_prev_cmd_actions = torch.zeros(num_envs, action_dim)

    torch.manual_seed(0)
    for _ in range(6):
        raw = torch.randn(num_envs, action_dim)

        # --- mirror _update_action_buffers (:507-509) ---
        cmd = raw.clone().clamp(-1.0, 1.0)
        prev_prev_actions = prev_actions.clone()
        prev_actions = actions.clone()
        actions = cmd
        prev_prev_cmd_actions = prev_cmd_actions.clone()
        prev_cmd_actions = cmd_actions.clone()
        cmd_actions = cmd

        # --- mirror the delay overwrite (:586) ---
        actions = _apply_control_delay(delay_buf, actions)

        assert torch.equal(cmd_actions, actions)
        assert torch.equal(prev_cmd_actions, prev_actions)
        assert torch.equal(prev_prev_cmd_actions, prev_prev_actions)

    # action_smoothness computed on either triple must be identical when off.
    da_delayed = actions - prev_actions
    d2a_delayed = actions - 2.0 * prev_actions + prev_prev_actions
    smoothness_delayed = da_delayed.pow(2).mean(dim=-1) + d2a_delayed.pow(2).mean(dim=-1)

    da_cmd = cmd_actions - prev_cmd_actions
    d2a_cmd = cmd_actions - 2.0 * prev_cmd_actions + prev_prev_cmd_actions
    smoothness_cmd = da_cmd.pow(2).mean(dim=-1) + d2a_cmd.pow(2).mean(dim=-1)

    assert torch.equal(smoothness_delayed, smoothness_cmd)


def test_on_smoothness_reads_commanded_not_delayed():
    """control_delay_steps=(3,3): action_smoothness computed on the commanded
    triple must equal the jerk of the COMMANDED sequence, not the delayed one.
    Proves it would differ if it read the delayed triple (_actions) instead.
    """
    num_envs = 2
    action_dim = 8
    lag, delay_buf = _draw_control_delay((3, 3), num_envs, device="cpu")
    assert torch.equal(lag, torch.full((num_envs,), 3, dtype=torch.int))

    actions = torch.zeros(num_envs, action_dim)
    prev_actions = torch.zeros(num_envs, action_dim)
    prev_prev_actions = torch.zeros(num_envs, action_dim)
    cmd_actions = torch.zeros(num_envs, action_dim)
    prev_cmd_actions = torch.zeros(num_envs, action_dim)
    prev_prev_cmd_actions = torch.zeros(num_envs, action_dim)

    # A deliberately jerky commanded sequence: alternating +1/-1 scalar broadcast.
    commanded_seq = [torch.full((num_envs, action_dim), float((-1) ** t)) for t in range(6)]

    smoothness_cmd_history = []
    smoothness_delayed_history = []
    for raw in commanded_seq:
        cmd = raw.clone().clamp(-1.0, 1.0)
        prev_prev_actions = prev_actions.clone()
        prev_actions = actions.clone()
        actions = cmd
        prev_prev_cmd_actions = prev_cmd_actions.clone()
        prev_cmd_actions = cmd_actions.clone()
        cmd_actions = cmd

        actions = _apply_control_delay(delay_buf, actions)

        da_cmd = cmd_actions - prev_cmd_actions
        d2a_cmd = cmd_actions - 2.0 * prev_cmd_actions + prev_prev_cmd_actions
        smoothness_cmd_history.append(da_cmd.pow(2).mean(dim=-1) + d2a_cmd.pow(2).mean(dim=-1))

        da_delayed = actions - prev_actions
        d2a_delayed = actions - 2.0 * prev_actions + prev_prev_actions
        smoothness_delayed_history.append(
            da_delayed.pow(2).mean(dim=-1) + d2a_delayed.pow(2).mean(dim=-1)
        )

    # With lag=3, the delayed stream is still warmup-clamped to 0.0 for the
    # first several steps (see test_latency_dr_env.py::test_on_delays_by_drawn_lag),
    # so it has NOT yet observed the alternating jerky pattern the commanded
    # stream has -- the two smoothness histories must diverge.
    diverged = any(
        not torch.equal(smoothness_cmd_history[i], smoothness_delayed_history[i])
        for i in range(len(commanded_seq))
    )
    assert diverged, "commanded and delayed smoothness must differ when delay is on"

    # The commanded-triple smoothness must match the jerk of the KNOWN commanded
    # sequence exactly (alternating +1/-1 -> da=+-2, d2a=+-4 after warmup).
    da_expected = commanded_seq[-1] - commanded_seq[-2]
    d2a_expected = commanded_seq[-1] - 2.0 * commanded_seq[-2] + commanded_seq[-3]
    expected_final = da_expected.pow(2).mean(dim=-1) + d2a_expected.pow(2).mean(dim=-1)
    assert torch.equal(smoothness_cmd_history[-1], expected_final)
