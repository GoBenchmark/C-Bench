from __future__ import annotations


def compress(raw: bytes) -> bytes:
    try:
        import brotli  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("brotli is not installed") from exc
    return brotli.compress(raw)
