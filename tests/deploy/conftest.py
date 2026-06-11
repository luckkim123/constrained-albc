"""Pytest configuration for deploy tests.

Stubs the top-level constrained_albc package so that its __init__.py
(which imports albc_env -> isaaclab.sim, requiring a full Isaac Sim runtime)
is never executed. The deploy subpackage loads normally from disk.
"""
import sys
import types


def _stub_constrained_albc():
    if "constrained_albc" in sys.modules:
        return  # already loaded (e.g. real runtime), leave it alone
    m = types.ModuleType("constrained_albc")
    m.__path__ = [str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent / "constrained_albc")]
    m.__package__ = "constrained_albc"
    sys.modules["constrained_albc"] = m


_stub_constrained_albc()
