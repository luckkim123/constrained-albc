"""Contract gate: load an exported .npz and assert it matches the key contract.

This is the STOP gate. Any mismatch raises ExportContractError — the guide forbids
coercing/reshaping. Verification is a round-trip: it re-reads the saved file with
numpy, exactly as the board runtime will."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from constrained_albc.deploy.spec import ExportContractError, ShapeSpec


@dataclass
class ContractReport:
    """Result of verifying one .npz against its contract."""

    path: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    entries: list[tuple[str, tuple[int, ...], str]] = field(default_factory=list)
    # entries: (key, shape, dtype) for human-readable report (guide line 100)


def verify_npz(path: str, contract: dict[str, ShapeSpec]) -> ContractReport:
    """Round-trip verify a saved .npz against its key contract.

    Raises ExportContractError on any missing/extra key, shape mismatch, or
    non-float32 dtype. Returns a passing ContractReport otherwise."""
    data = np.load(path)
    found = set(data.keys())
    expected = set(contract.keys())
    errors: list[str] = []

    missing = sorted(expected - found)
    extra = sorted(found - expected)
    if missing:
        errors.append(f"missing keys: {missing}")
    if extra:
        errors.append(f"extra keys: {extra}")

    entries: list[tuple[str, tuple[int, ...], str]] = []
    for key in sorted(found):
        arr = data[key]
        entries.append((key, tuple(arr.shape), str(arr.dtype)))
        if key in contract:
            spec = contract[key]
            if tuple(arr.shape) != spec.shape:
                errors.append(f"{key}: shape {tuple(arr.shape)} != expected {spec.shape}")
            if str(arr.dtype) != spec.dtype:
                errors.append(f"{key}: dtype {arr.dtype} != expected {spec.dtype}")

    report = ContractReport(path=path, ok=not errors, errors=errors, entries=entries)
    if errors:
        raise ExportContractError(f"{path} violates contract:\n  " + "\n  ".join(errors))
    return report
