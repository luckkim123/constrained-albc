"""Deployment export: torch .pt checkpoints -> numpy .npz for a torch-free board runtime.

The .npz key names/shapes/dtypes are a hard contract with the deployment runtime
(npforward.py reads them by hardcoded name).
"""
from constrained_albc.deploy.spec import ExportContractError, ExportSpec, ShapeSpec

__all__ = ["ExportSpec", "ShapeSpec", "ExportContractError"]
