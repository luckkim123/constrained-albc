"""Tests for the pure per-env DR snapshot transform in _eval_dr/dr_snapshot.py.

eval.py reads the post-randomize physics tensors off the env (sim-bound) and hands
them — already as numpy arrays plus the hydro base offsets — to a PURE transform that
shapes them into the dr_<name>[num_envs] schema saved into data_<level>.npz. Only the
PURE transform is tested here (no sim, no GPU): naming, added-mass diagonal extraction,
CoB/CoG offset back-out (value - base), and per-env shape [N].

The motivation (rule03 differential diagnosis at env level): the dr_<name> arrays let a
later analysis join "which DR did the worst-roll envs commonly get" — the encoder z-sweep
flagged lateral CoG/CoB + body mass, so those channels must come through cleanly.

Run headless: python3 -m pytest test_dr_snapshot.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

# _eval_dr is pure numpy (Isaac-Sim-free); import it directly without booting sim.
_PKG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "constrained_albc",
    "analysis",
)
sys.path.insert(0, _PKG)
from _eval_dr import dr_snapshot as ds  # noqa: E402


def _raw(n=4):
    """Synthetic post-randomize tensors as numpy, mimicking what eval.py reads off env.

    Each env i gets distinct values so the transform's per-env mapping is checkable.
    """
    rng = np.arange(n, dtype=np.float32)
    # added_mass: (N, 6, 6) full matrix; the transform must extract the diagonal.
    am = np.zeros((n, 6, 6), dtype=np.float32)
    for i in range(n):
        np.fill_diagonal(am[i], np.arange(6, dtype=np.float32) + i)  # diag = [i, i+1, ..., i+5]
    return {
        "payload_mass": 1.5 + rng,                      # (N,)
        "payload_cog_offset": np.stack(                  # (N, 3)
            [rng * 0.01, rng * 0.02, rng * 0.03], axis=1
        ),
        "cob": np.stack([rng * 0.1, rng * 0.2, rng * 0.3], axis=1),   # (N,3) absolute
        "cob_base": np.array([0.0, 0.0, 0.05], dtype=np.float32),     # (3,) nominal
        "cog": np.stack([rng * 0.11, rng * 0.22, rng * 0.33], axis=1),
        "cog_base": np.array([0.0, 0.0, 0.0], dtype=np.float32),
        "body_mass": 30.0 + rng,                         # (N,)
        "added_mass": am,                                # (N, 6, 6)
        "linear_damping": np.stack(                      # (N, 6)
            [rng + j for j in range(6)], axis=1
        ),
    }


# ---- 1. schema: every channel becomes a dr_<name>[N] scalar array ----

def test_all_keys_are_per_env_scalar_arrays():
    out = ds.per_env_dr_from_tensors(_raw(4))
    for k, v in out.items():
        assert k.startswith("dr_"), f"key {k} missing dr_ prefix"
        assert v.shape == (4,), f"{k} must be per-env scalar [N], got {v.shape}"


def test_scalar_channels_passthrough():
    out = ds.per_env_dr_from_tensors(_raw(4))
    assert np.allclose(out["dr_payload_mass"], [1.5, 2.5, 3.5, 4.5])
    assert np.allclose(out["dr_body_mass"], [30.0, 31.0, 32.0, 33.0])


# ---- 2. vector channels split into per-axis scalar keys ----

def test_payload_cog_splits_xyz():
    out = ds.per_env_dr_from_tensors(_raw(4))
    assert np.allclose(out["dr_payload_cog_x"], [0.0, 0.01, 0.02, 0.03])
    assert np.allclose(out["dr_payload_cog_y"], [0.0, 0.02, 0.04, 0.06])
    assert np.allclose(out["dr_payload_cog_z"], [0.0, 0.03, 0.06, 0.09])


# ---- 3. CoB/CoG come through as OFFSET (value - base), the DR quantity ----

def test_cob_is_offset_from_base():
    out = ds.per_env_dr_from_tensors(_raw(4))
    # env 1: cob = [0.1, 0.2, 0.3]; base = [0, 0, 0.05] -> offset z = 0.25
    assert np.allclose(out["dr_cob_x"], [0.0, 0.1, 0.2, 0.3])
    assert np.allclose(out["dr_cob_y"], [0.0, 0.2, 0.4, 0.6])
    assert np.allclose(out["dr_cob_z"], [-0.05, 0.25, 0.55, 0.85])


def test_cog_is_offset_from_base():
    out = ds.per_env_dr_from_tensors(_raw(4))
    assert np.allclose(out["dr_cog_x"], [0.0, 0.11, 0.22, 0.33])
    assert np.allclose(out["dr_cog_z"], [0.0, 0.33, 0.66, 0.99])


# ---- 4. added_mass diagonal extracted; 6 per-DOF keys ----

def test_added_mass_diagonal_per_dof():
    out = ds.per_env_dr_from_tensors(_raw(4))
    # env i diag = [i, i+1, ..., i+5]; dr_added_mass_0 = [0,1,2,3], _5 = [5,6,7,8]
    assert np.allclose(out["dr_added_mass_0"], [0, 1, 2, 3])
    assert np.allclose(out["dr_added_mass_3"], [3, 4, 5, 6])  # roll DOF
    assert np.allclose(out["dr_added_mass_5"], [5, 6, 7, 8])  # yaw DOF


def test_linear_damping_per_dof():
    out = ds.per_env_dr_from_tensors(_raw(4))
    assert np.allclose(out["dr_lin_damp_0"], [0, 1, 2, 3])
    assert np.allclose(out["dr_lin_damp_5"], [5, 6, 7, 8])


# ---- 5. robustness: missing optional channels are skipped, not crashed ----

def test_missing_channels_skipped_gracefully():
    raw = _raw(4)
    del raw["added_mass"]
    del raw["linear_damping"]
    out = ds.per_env_dr_from_tensors(raw)
    assert "dr_payload_mass" in out          # present channels still emit
    assert not any(k.startswith("dr_added_mass") for k in out)  # absent -> no fabricated keys
    assert not any(k.startswith("dr_lin_damp") for k in out)


def test_empty_input_yields_empty_dict():
    assert ds.per_env_dr_from_tensors({}) == {}


# ---- 6. dr_param_names helper enumerates what a full snapshot would contain ----

def test_dr_param_names_lists_emitted_keys():
    out = ds.per_env_dr_from_tensors(_raw(4))
    names = ds.dr_param_names(out)
    assert set(names) == set(out.keys())
    assert all(n.startswith("dr_") for n in names)


# ============================================================================
# Per-env FAULT snapshot (fault-injection infrastructure for FTC research)
# ============================================================================
# A fault is an actuator/sensor FAILURE (thruster dead, sensor noisy, joint
# degraded), distinct from DR (a physical-parameter spread). It gets its own
# fault_<name>[N] schema and its own pure transform so a later analysis can join
# "which fault did the worst-roll envs commonly carry" -- the same env-level
# differential-diagnosis pattern as dr_<name>, on a different axis. Missing input
# keys are skipped (never fabricated), mirroring per_env_dr_from_tensors.


def _raw_fault(n=4):
    """Synthetic per-env fault tensors as numpy, as eval.py reads them off the env."""
    rng = np.arange(n, dtype=np.float32)
    # thruster_health: (N, 6); env i -> [1, 1-0.1i, 1-0.2i, ...] so per-thruster differs.
    health = np.ones((n, 6), dtype=np.float32)
    for i in range(n):
        health[i] = np.clip(1.0 - 0.1 * i * np.arange(6, dtype=np.float32), 0.0, 1.0)
    return {
        "thruster_health": health,                       # (N, 6)
        "sensor_noise": 0.01 * rng,                       # (N,)
        "joint_health": np.clip(1.0 - 0.05 * rng, 0.0, 1.0),  # (N,)
    }


def test_fault_all_keys_are_per_env_scalar_arrays():
    out = ds.per_env_fault_from_tensors(_raw_fault(4))
    for k, v in out.items():
        assert k.startswith("fault_"), f"key {k} missing fault_ prefix"
        assert v.shape == (4,), f"{k} must be per-env scalar [N], got {v.shape}"


def test_fault_thruster_splits_per_thruster():
    out = ds.per_env_fault_from_tensors(_raw_fault(4))
    # 6 thrusters -> 6 keys; thruster 0 healthy for all envs, thruster 5 degrades by env.
    for j in range(6):
        assert f"fault_thruster_{j}" in out
    assert np.allclose(out["fault_thruster_0"], [1.0, 1.0, 1.0, 1.0])  # col 0 = health[:,0]
    # env i, thruster 5 -> clip(1 - 0.1*i*5, 0, 1): i=0->1, i=1->0.5, i=2->0, i=3->0
    assert np.allclose(out["fault_thruster_5"], [1.0, 0.5, 0.0, 0.0])


def test_fault_sensor_and_joint_passthrough():
    out = ds.per_env_fault_from_tensors(_raw_fault(4))
    assert np.allclose(out["fault_sensor_noise"], [0.0, 0.01, 0.02, 0.03])
    assert np.allclose(out["fault_joint"], [1.0, 0.95, 0.90, 0.85])


def test_fault_missing_channels_skipped():
    raw = _raw_fault(4)
    del raw["thruster_health"]
    out = ds.per_env_fault_from_tensors(raw)
    assert not any(k.startswith("fault_thruster") for k in out)  # absent -> no fabricated keys
    assert "fault_sensor_noise" in out                            # present channel still emits
    assert "fault_joint" in out


def test_fault_empty_input_yields_empty_dict():
    assert ds.per_env_fault_from_tensors({}) == {}


def test_fault_param_names_lists_emitted_keys():
    out = ds.per_env_fault_from_tensors(_raw_fault(4))
    names = ds.fault_param_names(out)
    assert set(names) == set(out.keys())
    assert all(n.startswith("fault_") for n in names)


def test_fault_and_dr_namespaces_disjoint():
    """fault_ and dr_ keys never collide -- they merge cleanly into one npz."""
    dr = ds.per_env_dr_from_tensors(_raw(4))
    fault = ds.per_env_fault_from_tensors(_raw_fault(4))
    assert set(dr).isdisjoint(set(fault))
