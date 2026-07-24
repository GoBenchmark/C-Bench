from __future__ import annotations

import lzma


def compress(raw: bytes) -> bytes:
    return lzma.compress(raw, format=lzma.FORMAT_XZ)
