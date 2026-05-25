# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Maintain a `latest` symlink pointing at the most recent run directory.

A run lands in ``<parent>/<run_name>/`` (e.g. ``logs/rsl_rl/albc_trpo/
2026-05-25_16-34-13``). This keeps a sibling ``latest`` symlink so tools can
reach the newest run without knowing its timestamp::

    tensorboard --logdir logs/rsl_rl/albc_trpo/latest
"""

from __future__ import annotations

import os

LATEST = "latest"


def update_latest_symlink(run_dir: str) -> None:
    """(Re)point ``<parent>/latest`` at ``run_dir``.

    Uses a relative target (run basename) so the link survives moving or
    copying the parent directory. Replacement is atomic via a temp link +
    ``os.replace``. Never raises on a symlink-hostile filesystem -- a missing
    convenience link must not abort training/eval.
    """
    run_dir = os.path.abspath(run_dir)
    parent = os.path.dirname(run_dir)
    target = os.path.basename(run_dir)  # relative link target
    link_path = os.path.join(parent, LATEST)
    tmp_path = os.path.join(parent, f".{LATEST}.tmp")

    try:
        if os.path.lexists(tmp_path):
            os.unlink(tmp_path)
        os.symlink(target, tmp_path)
        os.replace(tmp_path, link_path)  # atomic swap, overwrites old link
    except OSError as exc:  # noqa: BLE001 - convenience link is best-effort
        print(f"[WARN] could not update '{LATEST}' symlink at {link_path}: {exc}")
