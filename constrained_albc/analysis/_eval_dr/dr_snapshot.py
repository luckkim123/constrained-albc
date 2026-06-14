# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Pure (Isaac-Sim-free) transform: post-randomize physics tensors -> per-env DR schema.

eval.py reads the physics tensors off the env AFTER the throwaway reset has fixed each
env's domain randomization (sim-bound: it needs a booted env). It hands them here — as
plain numpy arrays plus the hydro base offsets — and this PURE function shapes them into
the ``dr_<name>[num_envs]`` schema that lands in ``data_<level>.npz``.

Keeping the shaping pure (no env, no torch, no sim) lets it be unit-tested on plain
python3, and isolates the one place that decides naming / diagonal extraction / offset
back-out. The values are POST-CLAMP (what the policy actually experienced), which is what
env-level causal analysis wants: a later analysis joins "which DR did the worst-roll envs
commonly receive" against these arrays (the encoder z-sweep flagged lateral CoG/CoB +
body mass; those channels come through as dr_cog_*/dr_cob_*/dr_body_mass).

Input dict keys (all optional; absent -> skipped, never fabricated):
    payload_mass        (N,)        scalar passthrough
    payload_cog_offset  (N, 3)      -> dr_payload_cog_{x,y,z}
    cob, cob_base       (N,3),(3,)  -> dr_cob_{x,y,z} = cob - cob_base  (DR offset)
    cog, cog_base       (N,3),(3,)  -> dr_cog_{x,y,z} = cog - cog_base
    body_mass           (N,)        scalar passthrough
    added_mass          (N, 6, 6)   -> dr_added_mass_{0..5} (diagonal per DOF)
    linear_damping      (N, 6)      -> dr_lin_damp_{0..5}

A SECOND, namespace-disjoint transform shapes per-env FAULT tensors into a
``fault_<name>[N]`` schema (per_env_fault_from_tensors). A fault is an actuator /
sensor FAILURE (not a DR physical-parameter spread), so it lives on its own axis:
analysis joins "which fault did the worst-roll envs carry" the same way it joins DR.

Fault input dict keys (all optional; absent -> skipped, never fabricated):
    thruster_health  (N, 6)  -> fault_thruster_{0..5}  (0=dead..1=nominal, per thruster)
    sensor_noise     (N,)    -> fault_sensor_noise     (per-env obs noise scale)
    joint_health     (N,)    -> fault_joint            (per-env arm response, 0..1)
"""
from __future__ import annotations

import numpy as np

_XYZ = ("x", "y", "z")


def per_env_dr_from_tensors(tensors: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Shape post-randomize physics tensors into the dr_<name>[N] per-env schema.

    Every emitted value is a per-env scalar array of shape (N,). Missing input channels
    are silently skipped (a level with that channel disabled, or a future schema change),
    never filled with fabricated keys.
    """
    out: dict[str, np.ndarray] = {}
    if not tensors:
        return out

    # --- scalar passthrough channels ---
    for key in ("payload_mass", "body_mass"):
        arr = tensors.get(key)
        if arr is not None:
            out[f"dr_{key}"] = np.asarray(arr, dtype=np.float32).reshape(-1)

    # --- payload CoG: absolute XYZ offset (already relative to attachment) ---
    cog_off = tensors.get("payload_cog_offset")
    if cog_off is not None:
        cog_off = np.asarray(cog_off, dtype=np.float32)
        for ax, name in enumerate(_XYZ):
            out[f"dr_payload_cog_{name}"] = cog_off[:, ax]

    # --- hydro CoB/CoG: emit as DR OFFSET (value - nominal base) ---
    for src, prefix in (("cob", "dr_cob"), ("cog", "dr_cog")):
        val = tensors.get(src)
        base = tensors.get(f"{src}_base")
        if val is not None and base is not None:
            val = np.asarray(val, dtype=np.float32)
            base = np.asarray(base, dtype=np.float32).reshape(-1)
            offset = val - base[None, :]
            for ax, name in enumerate(_XYZ):
                out[f"{prefix}_{name}"] = offset[:, ax]

    # --- added mass: extract the per-DOF diagonal from the (N,6,6) matrix ---
    am = tensors.get("added_mass")
    if am is not None:
        am = np.asarray(am, dtype=np.float32)
        diag = np.diagonal(am, axis1=1, axis2=2)  # (N, 6)
        for dof in range(diag.shape[1]):
            out[f"dr_added_mass_{dof}"] = diag[:, dof]

    # --- linear damping: per-DOF (N,6) ---
    ld = tensors.get("linear_damping")
    if ld is not None:
        ld = np.asarray(ld, dtype=np.float32)
        for dof in range(ld.shape[1]):
            out[f"dr_lin_damp_{dof}"] = ld[:, dof]

    return out


def dr_param_names(snapshot: dict[str, np.ndarray]) -> list[str]:
    """List the dr_<name> keys present in a snapshot (stable order)."""
    return [k for k in snapshot if k.startswith("dr_")]


def per_env_fault_from_tensors(tensors: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Shape per-env fault tensors into the fault_<name>[N] schema.

    Namespace-disjoint from per_env_dr_from_tensors (dr_ vs fault_), so the two merge
    cleanly into one npz. Every emitted value is a per-env scalar array of shape (N,).
    Missing input channels are silently skipped (a level with that fault disabled, or a
    future schema change), never filled with fabricated keys.
    """
    out: dict[str, np.ndarray] = {}
    if not tensors:
        return out

    # --- thruster health: per-thruster (N,6) -> one scalar key per thruster ---
    health = tensors.get("thruster_health")
    if health is not None:
        health = np.asarray(health, dtype=np.float32)
        for thr in range(health.shape[1]):
            out[f"fault_thruster_{thr}"] = health[:, thr]

    # --- scalar per-env fault channels ---
    noise = tensors.get("sensor_noise")
    if noise is not None:
        out["fault_sensor_noise"] = np.asarray(noise, dtype=np.float32).reshape(-1)

    joint = tensors.get("joint_health")
    if joint is not None:
        out["fault_joint"] = np.asarray(joint, dtype=np.float32).reshape(-1)

    return out


def fault_param_names(snapshot: dict[str, np.ndarray]) -> list[str]:
    """List the fault_<name> keys present in a snapshot (stable order)."""
    return [k for k in snapshot if k.startswith("fault_")]
