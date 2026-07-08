"""Control-action latency DR config field.

Skipped if importing the env config boots Isaac Sim (structural-only test).
"""

from __future__ import annotations

import pytest

config = pytest.importorskip("constrained_albc.envs.main.config")


def test_control_delay_steps_default_off():
    """Default must be off (0,0) so a fresh env is byte-identical to baseline."""
    cfg = config.DomainRandomizationCfg()
    assert cfg.control_delay_steps == (0, 0)


def test_control_delay_steps_is_int_pair():
    cfg = config.DomainRandomizationCfg()
    lo, hi = cfg.control_delay_steps
    assert isinstance(lo, int) and isinstance(hi, int)
    assert 0 <= lo <= hi
