from __future__ import annotations

from pathlib import Path


def read_bytes(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def decode_utf8(raw: bytes, *, allow_invalid_utf8: bool = False) -> str:
    if allow_invalid_utf8:
        return raw.decode("utf-8", errors="replace")
    return raw.decode("utf-8", errors="strict")
