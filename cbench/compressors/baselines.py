from __future__ import annotations

from pathlib import Path
from typing import Callable

from cbench.data.manifest import ManifestEntry, resolve_entry_path


COMPRESSORS: dict[str, str] = {
    "gzip": "cbench.compressors.gzip_baseline",
    "zstd": "cbench.compressors.zstd_baseline",
    "brotli": "cbench.compressors.brotli_baseline",
    "xz": "cbench.compressors.xz_baseline",
}


def _load_compressor(name: str) -> Callable[[bytes], bytes]:
    if name not in COMPRESSORS:
        raise ValueError(f"Unknown compressor {name!r}; expected one of {', '.join(sorted(COMPRESSORS))}")
    module_name = COMPRESSORS[name]
    module = __import__(module_name, fromlist=["compress"])
    return module.compress


def score_document(entry: ManifestEntry, manifest_path: str | Path, compressor: str) -> dict[str, object]:
    if entry.mode != "streaming" or not entry.path:
        raise ValueError(f"{entry.id}: compressor baselines support streaming entries only")
    path = resolve_entry_path(entry.path, manifest_path)
    raw = path.read_bytes()
    compressed = _load_compressor(compressor)(raw)
    compressed_bytes = len(compressed)
    return {
        "compressor": compressor,
        "id": entry.id,
        "domain": entry.domain,
        "raw_bytes": len(raw),
        "compressed_bytes": compressed_bytes,
        "bits": compressed_bytes * 8.0,
        "bpb": (compressed_bytes * 8.0) / len(raw),
    }


def run_baselines(
    entries: list[ManifestEntry],
    manifest_path: str | Path,
    compressors: list[str],
) -> tuple[list[dict[str, object]], list[str]]:
    documents: list[dict[str, object]] = []
    warnings: list[str] = []
    for compressor in compressors:
        try:
            compress = _load_compressor(compressor)
            compress(b"")
        except RuntimeError as exc:
            warnings.append(f"Skipping {compressor}: {exc}")
            continue
        for entry in entries:
            try:
                documents.append(score_document(entry, manifest_path, compressor))
            except RuntimeError as exc:
                warnings.append(f"Skipping {compressor} for {entry.id}: {exc}")
    return documents, warnings
