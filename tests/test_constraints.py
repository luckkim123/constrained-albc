# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for IPO constraint cost functions (no Isaac Sim required).

The 10 cost functions silently gate the IPO barrier: if a clamp direction or
threshold comparison flips, the constraint inverts (fires during normal
operation, goes quiet on violation) while training still runs -- a silent
failure. These tests pin the violate / boundary / satisfy behavior of every
cost so a refactor that flips a sign is caught immediately.

constraints.py only imports ``configclass`` from isaaclab; we mock that one
symbol and drive the cost functions with lightweight tensor stand-ins for
``env`` / ``robot``.
"""

# ---------------------------------------------------------------------------
# Load constraints.py directly via importlib, bypassing constrained_albc.__init__
# (which imports albc_env -> isaaclab.sim, requiring a full Isaac Sim runtime).
# constraints.py only needs the `configclass` decorator from isaaclab.utils, so
# we mock that single symbol.
# ---------------------------------------------------------------------------
import dataclasses
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch


def _mock_configclass(cls):
    """Stand-in for isaaclab's @configclass: make the class a dataclass so it gets a real
    __init__ (the real decorator does this), converting mutable class-level defaults to
    default_factory so dataclass() accepts them (the real one also handles mutables)."""
    for name, value in list(vars(cls).items()):
        if name.startswith("__"):
            continue
        if isinstance(value, (list, dict, set)) and name in getattr(cls, "__annotations__", {}):
            default = value
            setattr(cls, name, dataclasses.field(default_factory=lambda d=default: type(d)(d)))
    return dataclasses.dataclass(cls)


for _pkg in ("isaaclab", "isaaclab.utils"):
    if _pkg not in sys.modules:
        sys.modules[_pkg] = types.ModuleType(_pkg)
sys.modules["isaaclab.utils"].configclass = _mock_configclass

_CONSTRAINTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc/envs/main/mdp/constraints.py"
)
_spec = importlib.util.spec_from_file_location("_albc_constraints_under_test", _CONSTRAINTS_PATH)
C = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = C
_spec.loader.exec_module(C)


# ---------------------------------------------------------------------------
# Lightweight env/robot stand-ins
# ---------------------------------------------------------------------------

JOINT_IDS = [0, 1]


def _robot(*, applied_torque=None, joint_vel=None, joint_pos=None, ang_vel=None, n=1, device="cpu"):
    """Build a robot mock exposing only the .data fields the costs read."""
    data = SimpleNamespace(
        applied_torque=applied_torque,
        joint_vel=joint_vel,
        joint_pos=joint_pos,
        root_ang_vel_b=ang_vel,
        root_pos_w=torch.zeros(n, 3, device=device),
    )
    return SimpleNamespace(data=data, device=device)


def _env(
    *,
    euler=None,
    cumulative_yaw=None,
    joint_pos_targets=None,
    nominal_joint_pos=None,
    att_rp_err=None,
    manipulability=None,
    thruster_state=None,
    albc_joint_ids=None,
):
    thruster = None if thruster_state is None else SimpleNamespace(state=thruster_state)
    if nominal_joint_pos is None:
        nominal_joint_pos = torch.zeros(2)
    if albc_joint_ids is None:
        albc_joint_ids = JOINT_IDS
    return SimpleNamespace(
        _albc_joint_ids=albc_joint_ids,
        _euler_cache=euler,
        _cumulative_yaw=cumulative_yaw,
        _joint_pos_targets=joint_pos_targets,
        _nominal_joint_pos=nominal_joint_pos,
        _att_rp_err=att_rp_err,
        _manipulability=manipulability,
        _thruster=thruster,
    )


# ---------------------------------------------------------------------------
# Probabilistic constraints (binary 0/1 indicator)
# ---------------------------------------------------------------------------


def test_attitude_limit_violate_boundary_satisfy():
    limit = 0.5
    # roll, pitch, yaw — one env per case: satisfy / boundary(==limit, not >) / violate
    roll = torch.tensor([0.1, 0.5, 0.6])
    pitch = torch.tensor([0.0, 0.0, 0.0])
    yaw = torch.zeros(3)
    env = _env(euler=(roll, pitch, yaw))
    cost = C.attitude_limit_cost(None, env, limit=limit)
    assert torch.equal(cost, torch.tensor([0.0, 0.0, 1.0]))  # boundary (==) is NOT a violation


def test_attitude_limit_uses_max_of_roll_pitch():
    # pitch exceeds while roll is fine -> still a violation (max over both)
    env = _env(euler=(torch.tensor([0.0]), torch.tensor([0.9]), torch.zeros(1)))
    assert C.attitude_limit_cost(None, env, limit=0.5).item() == 1.0


def test_torque_limit_any_joint():
    env = _env()
    # joint0 within, joint1 over -> any() -> violation
    robot = _robot(applied_torque=torch.tensor([[1.0, 9.0]]))
    assert C.torque_limit_cost(robot, env, limit_nm=5.0).item() == 1.0
    robot_ok = _robot(applied_torque=torch.tensor([[1.0, 4.9]]))
    assert C.torque_limit_cost(robot_ok, env, limit_nm=5.0).item() == 0.0


def test_velocity_limit_max_joint():
    env = _env()
    robot = _robot(joint_vel=torch.tensor([[0.1, 2.0]]))
    assert C.velocity_limit_cost(robot, env, limit_rad_per_s=1.0).item() == 1.0
    robot_ok = _robot(joint_vel=torch.tensor([[0.1, 0.9]]))
    assert C.velocity_limit_cost(robot_ok, env, limit_rad_per_s=1.0).item() == 0.0


def test_joint1_position_only_joint0():
    env = _env()
    # joint1 (index 0) over limit, joint2 (index 1) huge but ignored
    robot = _robot(joint_pos=torch.tensor([[3.5, 99.0]]))
    assert C.joint1_position_cost(robot, env, limit_rad=3.14).item() == 1.0
    robot_ok = _robot(joint_pos=torch.tensor([[1.0, 99.0]]))
    assert C.joint1_position_cost(robot_ok, env, limit_rad=3.14).item() == 0.0


def test_cumulative_yaw():
    env = _env(cumulative_yaw=torch.tensor([7.0, -7.0, 1.0]))
    cost = C.cumulative_yaw_cost(None, env, limit_rad=6.28)
    assert torch.equal(cost, torch.tensor([1.0, 1.0, 0.0]))  # abs, both signs count


# ---------------------------------------------------------------------------
# Average constraints (ReLU-style) -- sign/direction is the critical property
# ---------------------------------------------------------------------------


def test_rp_rate_relu_direction():
    """cost = max(0, max(|p|,|q|) - threshold): zero below, linear above."""
    th = 1.0
    # env0 below (0.5), env1 boundary (1.0 -> 0), env2 above (1.5 -> 0.5)
    ang_vel = torch.tensor([[0.5, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.5, 0.0]])
    cost = C.rp_rate_cost(_robot(ang_vel=ang_vel), None, soft_threshold=th)
    assert torch.allclose(cost, torch.tensor([0.0, 0.0, 0.5]))


def test_yaw_rate_relu_direction():
    th = 0.6
    ang_vel = torch.tensor([[0.0, 0.0, 0.3], [0.0, 0.0, 0.6], [0.0, 0.0, 1.0]])
    cost = C.yaw_rate_cost(_robot(ang_vel=ang_vel), None, soft_threshold=th)
    assert torch.allclose(cost, torch.tensor([0.0, 0.0, 0.4]))


def test_thruster_utilization_peak_and_none():
    env = _env(thruster_state=torch.tensor([[0.1, -0.7, 0.3, 0.0, 0.2, -0.4]]))
    assert C.thruster_utilization_cost(_robot(n=1), env).item() == pytest.approx(0.7)  # peak abs
    # no thruster -> zero, shaped to num_envs
    env_none = _env(thruster_state=None)
    out = C.thruster_utilization_cost(_robot(n=3), env_none)
    assert torch.equal(out, torch.zeros(3))


def test_rp_vel_settling_gated_by_attitude_error():
    """Active only when |att_err| <= settling_threshold (near target)."""
    th = 0.087  # ~5 deg
    ang_vel = torch.tensor([[0.4, 0.2, 0.0], [0.4, 0.2, 0.0]])  # rp_vel mean = 0.3 both
    # env0: in transit (err 0.5 > th) -> gated OFF; env1: settling (err 0.01 <= th) -> ON
    att_rp_err = torch.tensor([[0.5, 0.0], [0.01, 0.0]])
    env = _env(att_rp_err=att_rp_err)
    cost = C.rp_vel_settling_cost(_robot(ang_vel=ang_vel), env, settling_threshold=th)
    assert cost[0].item() == 0.0  # transit phase not penalized
    assert cost[1].item() == pytest.approx(0.3)  # settling phase penalized


def test_manipulability_inverse_direction():
    """cost = max(0, threshold - w): fires when w is SMALL (near singularity)."""
    th = 0.3
    # w=0.05 (near singular -> cost 0.25), w=0.3 (boundary -> 0), w=0.8 (good -> 0)
    env = _env(manipulability=torch.tensor([0.05, 0.3, 0.8]))
    cost = C.manipulability_cost(None, env, w_threshold=th)
    assert torch.allclose(cost, torch.tensor([0.25, 0.0, 0.0]))


# ---------------------------------------------------------------------------
# joint1 cumulative drift constraint (the redesign experiment).
# joint1_cumulative_cost: |unwrapped cumulative joint1| on the env accumulator.
# (The wrapped-instantaneous form, arm A / joint1_centering_cost, was removed 2026-07.)
# ---------------------------------------------------------------------------


def test_joint1_cumulative_cost_abs_displacement_from_nominal():
    """B: cost = |integrated command - nominal|, unwrapped -- a full turn is NOT free.

    Reads _joint_pos_targets[:,0] (the integrator drift lives in), not the measured
    angle. Displacement from nominal in either direction counts. With nominal=0 here:
    targets [0, 1.5, -1.5, 2*pi] -> cost [0, 1.5, 1.5, 2*pi].
    """
    import math

    targets = torch.tensor([[0.0, 0.0], [1.5, 0.0], [-1.5, 0.0], [2.0 * math.pi, 0.0]])
    env = _env(joint_pos_targets=targets, nominal_joint_pos=torch.zeros(2))
    cost = C.joint1_cumulative_cost(None, env)
    assert torch.allclose(cost, torch.tensor([0.0, 1.5, 1.5, 2.0 * math.pi]), atol=1e-6)


def test_joint1_cumulative_cost_relative_to_nonzero_nominal():
    """B: displacement is measured from nominal, not absolute zero."""
    targets = torch.tensor([[0.5, 0.0], [1.5, 0.0]])
    env = _env(joint_pos_targets=targets, nominal_joint_pos=torch.tensor([0.5, 0.0]))
    cost = C.joint1_cumulative_cost(None, env)
    assert torch.allclose(cost, torch.tensor([0.0, 1.0]), atol=1e-6)  # |0.5-0.5|, |1.5-0.5|


def test_joint1_cumulative_cost_uses_local_nominal_index_not_global_dof_id():
    """B: nominal must be read at LOCAL index 0, robust to a non-[0,1] global DOF layout.

    _nominal_joint_pos is a length-2 LOCAL tensor [joint1, joint2]; _albc_joint_ids are
    GLOBAL DOF ids. If the global id space differs from [0,1] (joints added/reordered in
    the USD), indexing the length-2 nominal with a global id reads the wrong value or
    IndexErrors. Here joint1's global id is 3, but its nominal must still come from local 0.
    """
    targets = torch.tensor([[1.5, 0.0]])  # joint1 command = 1.5
    env = _env(
        joint_pos_targets=targets,
        nominal_joint_pos=torch.tensor([0.5, 1.0]),  # local: joint1 nominal=0.5, joint2=1.0
        albc_joint_ids=[3, 4],  # global DOF ids != local [0,1]
    )
    cost = C.joint1_cumulative_cost(None, env)
    assert cost.item() == pytest.approx(1.0)  # |1.5 - 0.5(local joint1 nominal)|, NOT a [3] read


def test_joint1_cumulative_cost_full_turn_is_not_free():
    """A full turn of drift is a real cost: the unwrapped integrated command reports
    ~2*pi, NOT folded to ~0. This is the whole point of the cumulative form -- a
    wrapped-instantaneous cost (the removed arm A) would have folded it to zero.
    """
    import math

    targets = torch.tensor([[2.0 * math.pi, 0.0]])
    b = C.joint1_cumulative_cost(None, _env(joint_pos_targets=targets, nominal_joint_pos=torch.zeros(2))).item()
    assert b == pytest.approx(2.0 * math.pi, abs=1e-6)


def test_joint1_cumulative_cost_only_reads_joint1():
    """B: joint2 (index 1) target must not affect the cost."""
    a = C.joint1_cumulative_cost(
        None, _env(joint_pos_targets=torch.tensor([[1.0, 0.0]]), nominal_joint_pos=torch.zeros(2))
    ).item()
    b = C.joint1_cumulative_cost(
        None, _env(joint_pos_targets=torch.tensor([[1.0, 9.0]]), nominal_joint_pos=torch.zeros(2))
    ).item()
    assert a == pytest.approx(b)


def test_compute_all_costs_stacks_K():
    """compute_all_costs stacks per-term costs into (num_envs, K)."""

    def _c0(robot, env):
        return torch.tensor([1.0, 0.0])

    def _c1(robot, env, scale):
        return torch.tensor([0.0, scale])

    cfg = SimpleNamespace(
        terms=[
            SimpleNamespace(func=_c0, params={}),
            SimpleNamespace(func=_c1, params={"scale": 2.0}),
        ]
    )
    out = C.compute_all_costs(None, None, cfg)
    assert out.shape == (2, 2)
    assert torch.equal(out, torch.tensor([[1.0, 0.0], [0.0, 2.0]]))


# ---------------------------------------------------------------------------
# joint1-constraint-redesign wiring: apply_joint1_constraint_arm(env_cfg) appends
# exactly one Average term for arm 'B' and leaves arm 'none' byte-identical, WITHOUT
# mutating the shared module-level _FULL_DOF_CONSTRAINT_TERMS (also used by full_dof).
#
# These call the REAL helper (not a reproduction). The helper is invoked from
# ALBCEnv.__init__ (AFTER hydra applies overrides), NOT a cfg __post_init__ -- because
# __post_init__ runs pre-override and would always see arm='none', silently leaving the
# shipped 10-term set: a baseline-dup masquerading as arm B. A real run with
# joint1_constraint_arm=B that still showed only 10 constraints would be that failure;
# test_apply_arm_appends_real_term is the regression guard.
# ---------------------------------------------------------------------------


def _cfg_with_terms(arm, budget, n_shared=10):
    """A minimal env_cfg stand-in: a constraints object holding a shared term list."""
    shared = [SimpleNamespace(name=f"t{i}") for i in range(n_shared)]
    constraints = SimpleNamespace(terms=shared)
    cfg = SimpleNamespace(
        joint1_constraint_arm=arm,
        joint1_constraint_budget=budget,
        constraints=constraints,
    )
    return cfg, shared


def test_apply_arm_none_is_noop():
    """arm 'none' leaves the 10-term shipped set untouched (byte-identical)."""
    cfg, _ = _cfg_with_terms("none", 0.05)
    C.apply_joint1_constraint_arm(cfg)
    assert [t.name for t in cfg.constraints.terms] == [f"t{i}" for i in range(10)]


def test_apply_arm_appends_real_term():
    """arm 'B' appends exactly one continuous Average term with the given budget.

    Calls the real helper, so it would FAIL if the helper stopped materializing the term
    (the silent-baseline-dup failure a live arm=B run would exhibit).
    """
    cfg, _ = _cfg_with_terms("B", 0.07)
    C.apply_joint1_constraint_arm(cfg)
    terms = cfg.constraints.terms
    assert len(terms) == 11, "arm B did not append the 11th term"
    assert terms[-1].name == "joint1_cumulative"
    assert terms[-1].budget == 0.07
    assert terms[-1].func is C.joint1_cumulative_cost  # binary-indicator regression guard: continuous func


def test_apply_arm_rejects_unknown():
    """An unknown arm value is a loud error, not a silent no-op."""
    cfg, _ = _cfg_with_terms("X", 0.05)
    with pytest.raises(ValueError):
        C.apply_joint1_constraint_arm(cfg)


def test_apply_arm_does_not_mutate_shared_list():
    """Appending must NOT mutate the shared _FULL_DOF_CONSTRAINT_TERMS (full_dof reuses it)."""
    cfg, shared = _cfg_with_terms("B", 0.05)
    C.apply_joint1_constraint_arm(cfg)
    assert len(shared) == 10  # the original shared list object is untouched (new list built)
