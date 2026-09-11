#!/usr/bin/env python3
"""Plain-torch regression test for the ATDC leakage update."""

from __future__ import annotations

import dataclasses
import importlib.util
import pathlib
import sys
import types

try:
    import torch
except ImportError as exc:
    raise RuntimeError("test_atdc_leak.py requires torch; it must not be skipped") from exc


def _load_controller_module() -> types.ModuleType:
    """Load only the controller: neither Isaac Lab nor the MarineLab runtime is needed."""
    isaaclab = types.ModuleType("isaaclab")
    isaaclab_utils = types.ModuleType("isaaclab.utils")
    isaaclab_utils.configclass = dataclasses.dataclass
    marinelab = types.ModuleType("marinelab")
    assets = types.ModuleType("marinelab.assets")
    assets.ALBC_LINK1_LENGTH = 0.1
    assets.ALBC_LINK2_LENGTH = 0.1
    sys.modules.setdefault("isaaclab", isaaclab)
    sys.modules.setdefault("isaaclab.utils", isaaclab_utils)
    sys.modules.setdefault("marinelab", marinelab)
    sys.modules.setdefault("marinelab.assets", assets)
    source = pathlib.Path(__file__).resolve().parents[1] / "constrained_albc/envs/tdc/controllers/tdc.py"
    spec = importlib.util.spec_from_file_location("atdc_leak_controller", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}; ATDC leakage test cannot run")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass() resolves string annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def _controller(leak: float, adaptive: bool = True):
    module = _load_controller_module()
    cfg = module.TDCControllerCfg(adaptive_m_hat=adaptive, m_hat_leak=leak)
    return module.TDCController(num_envs=1, device="cpu", cfg=cfg, dt=0.02)


def _step(controller) -> None:
    target = torch.tensor([[0.2, 0.2, 0.0]])
    controller._u_pd[:] = 48.0 * 0.2  # e_dot=0, so u_pd = kp * e.
    if controller._adaptive_m_hat:
        controller._adapt_m_hat(torch.zeros(1), torch.zeros(1), target)


def main() -> int:
    no_leak = _controller(leak=0.0)
    steps = 0
    while float(no_leak._m_hat[0, 0]) < 0.60:
        _step(no_leak)
        steps += 1
        if steps > 1000:
            raise AssertionError("no-leak estimate did not reach the upper bound")
    assert abs(steps * no_leak.dt - 11.72) <= 0.05, steps * no_leak.dt

    leaked = _controller(leak=0.5)
    for _ in range(round(60.0 / leaked.dt)):
        _step(leaked)
    assert float(leaked._m_hat.max()) < 0.30, leaked._m_hat

    disabled = _controller(leak=0.5, adaptive=False)
    before = disabled._m_hat.clone()
    _step(disabled)
    assert torch.equal(disabled._m_hat, before), disabled._m_hat
    print("ATDC leakage regression checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
