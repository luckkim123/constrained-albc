# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""CLI shim for the encoder_tools package (debug / sweep / train subcommands).

The implementation lives in the sibling `_encoder/` package. This shim keeps the
historical invocation path (`python constrained_albc/analysis/encoder_tools.py
<subcommand>`) working and puts the analysis directory on sys.path so both this
module's `import _encoder` and `_encoder`'s `from common import ...` resolve.

Usage:
    python3 constrained_albc/analysis/encoder_tools.py debug --run 0
    python3 constrained_albc/analysis/encoder_tools.py sweep --checkpoint logs/.../model_4999.pt
    python3 constrained_albc/analysis/encoder_tools.py train --data rollouts.pt --output enc.pt
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from _encoder import main  # type: ignore[import-not-found]

if __name__ == "__main__":
    main()
