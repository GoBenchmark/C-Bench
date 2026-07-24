from __future__ import annotations


def compress(raw: bytes) -> bytes:
    try:
        import zstandard as zstd  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("zstandard is not installed") from exc
    return zstd.ZstdCompressor().compress(raw)
