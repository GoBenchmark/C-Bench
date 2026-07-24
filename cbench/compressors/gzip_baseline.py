from __future__ import annotations

import gzip


def compress(raw: bytes) -> bytes:
    return gzip.compress(raw, mtime=0)
