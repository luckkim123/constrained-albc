"""E6 process-local remap: point the strict-editable finder's MAPPING at the worktree.

Process-isolated — only mutates THIS interpreter's in-memory finder MAPPING, never
the shared site-packages file. E5/main tree unaffected.
"""
import importlib
import importlib.util
import sys

WT = "/tmp/albc-e6-constraint/constrained_albc"

m = importlib.import_module("__editable___constrained_albc_0_1_0_finder")
for k in list(getattr(m, "MAPPING", {}).keys()):
    if k == "constrained_albc":
        m.MAPPING[k] = WT

# Some setuptools versions store MAPPING on the finder instance; update those too.
for f in sys.meta_path:
    mp = getattr(f, "_MAPPING", None) or getattr(f, "mapping", None)
    if isinstance(mp, dict) and "constrained_albc" in mp:
        mp["constrained_albc"] = WT

try:
    spec = importlib.util.find_spec("constrained_albc")
    loc = spec.submodule_search_locations[0] if spec and spec.submodule_search_locations else None
    print("[E6 REMAP] constrained_albc ->", loc)
except Exception as exc:  # find_spec may trigger deep imports (pxr) in some contexts
    print("[E6 REMAP] MAPPING patched; find_spec probe skipped:", type(exc).__name__)
