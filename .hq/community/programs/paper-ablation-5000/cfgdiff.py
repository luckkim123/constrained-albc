"""Semantic diff of two IsaacLab run params YAMLs (env.yaml or agent.yaml).

A text diff is unusable: tensors are dumped as pickled blobs whose storage key is a per-process id, so
identical tensors differ byte-wise (DGX seed-30 vs seed-31 reference, 2026-09-14), and a key of another
length shifts the base64 wrapping of the whole blob. This loads both files, compares tensors by value and
everything else by equality, skips keys that differ by construction (seed, run_name, log_dir) and maps the
DGX path prefixes onto the container ones.
Usage: python cfgdiff.py A.yaml B.yaml   -> prints differing paths, exit 1 if any.
"""
import math
import sys

import torch
import yaml

IGNORE = {"seed", "run_name", "log_dir"}
PREFIXES = [("/home/seungmin/workspace/marinelab-xyz", "/workspace/marinelab-r3a"),
            ("/home/seungmin/workspace/constrained-albc-r3a", "/workspace/constrained-albc-r3a")]


def norm(s):
    for a, b in PREFIXES:
        s = s.replace(a, b)
    return s


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k in IGNORE:
                continue
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in {'A' if k in a else 'B'}")
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} != {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", out)
    elif torch.is_tensor(a) or torch.is_tensor(b):
        same = (torch.is_tensor(a) and torch.is_tensor(b) and a.shape == b.shape and a.dtype == b.dtype
                and torch.equal(a.detach().cpu(), b.detach().cpu()))
        if not same:
            out.append(f"{path}: tensor differs")
    elif isinstance(a, str) and isinstance(b, str):
        if norm(a) != norm(b):
            out.append(f"{path}: {a!r} != {b!r}")
    elif isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        pass
    elif a != b:
        out.append(f"{path}: {a!r} != {b!r}")


def load(p):
    with open(p) as f:
        return yaml.unsafe_load(f)


if __name__ == "__main__":
    diffs = []
    walk(load(sys.argv[1]), load(sys.argv[2]), "", diffs)
    print("\n".join(diffs) if diffs else "identical (ignoring seed/run_name/log_dir and machine path prefixes)")
    sys.exit(1 if diffs else 0)
