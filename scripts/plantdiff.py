"""Flat key-by-key comparison of two dumped env.yaml configs.

Arm W must match the incumbent's plant, or the head-to-head against model_9998 is void.
Pickled buffers and path/name keys are excluded — they differ by construction.
"""
import sys, glob, yaml

SKIP = ('log_dir', 'run_name', 'seed', 'kl_ub', 'max_iterations', 'num_envs')


def flat(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f'{p}.{k}' if p else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f'{p}[{i}]')
    else:
        yield p, o


def load(path):
    with open(path) as f:
        d = yaml.unsafe_load(f)
    out = {}
    for k, v in flat(d):
        if any(s in k for s in SKIP):
            continue
        v = str(v)
        # pickled tensor blobs stringify to hundreds of chars; they carry no plant meaning
        if len(v) > 120:
            continue
        out[k] = v
    return out


a_path = glob.glob(sys.argv[1])[0]
b_path = glob.glob(sys.argv[2])[0]
a, b = load(a_path), load(b_path)
print(f'REF  : {a_path}\nARM W: {b_path}')
keys = sorted(set(a) | set(b))
diffs = [k for k in keys if a.get(k, '<absent>') != b.get(k, '<absent>')]
print(f'compared {len(keys)} keys, {len(diffs)} differ\n')
for k in diffs:
    print(f'  {k}\n      ref  = {a.get(k, "<absent>")}\n      armW = {b.get(k, "<absent>")}')
if not diffs:
    print('  IDENTICAL PLANT')
