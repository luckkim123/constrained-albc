"""Core abstractions: the per-architecture export contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import torch.nn as nn


class ExportContractError(Exception):
    """Raised when an exported .npz violates its key contract (missing/extra key,
    wrong shape, or wrong dtype). The export STOPS -- never coerce/reshape."""


@dataclass(frozen=True)
class ShapeSpec:
    """Expected numpy shape + dtype for one contract key."""

    shape: tuple[int, ...]
    dtype: str = "float32"  # board numpy 1.11.0: always float32


class ExportSpec(ABC):
    """One model architecture's export contract.

    Subclasses bind together the three inseparable per-architecture facts:
    the output key contract, how to build the torch model, and how to rename
    its state_dict to the contract keys.
    """

    name: str
    npz_filename: str
    key_contract: dict[str, ShapeSpec]

    @abstractmethod
    def build_model(self, ckpt: dict, device) -> nn.Module:
        """Construct the torch model and load weights from a loaded checkpoint dict."""

    @abstractmethod
    def map_state_dict(self, model: nn.Module) -> dict[str, np.ndarray]:
        """Return {contract_key: fp32 ndarray}; rename source keys to contract keys."""
