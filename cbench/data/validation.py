from __future__ import annotations

import hashlib
from pathlib import Path

from cbench.data.manifest import ManifestEntry, SuiteConfig, load_manifest, resolve_entry_path


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate_streaming_entry(entry: ManifestEntry, manifest_path: str | Path) -> None:
    if entry.mode != "streaming":
        raise ValueError(f"{entry.id}: only streaming mode is supported")
    if not entry.path:
        raise ValueError(f"{entry.id}: streaming entry must include path")
    if not entry.sha256:
        raise ValueError(f"{entry.id}: streaming entry must include sha256")
    if entry.bytes is None:
        raise ValueError(f"{entry.id}: streaming entry must include bytes")
    if entry.bytes <= 0:
        raise ValueError(f"{entry.id}: streaming entry must contain at least one byte")
    if Path(entry.path).is_absolute() or ".." in Path(entry.path).parts:
        raise ValueError(f"{entry.id}: streaming path must stay relative to the manifest directory")

    path = resolve_entry_path(entry.path, manifest_path)
    manifest_dir = Path(manifest_path).resolve().parent
    if not path.is_relative_to(manifest_dir):
        raise ValueError(f"{entry.id}: streaming path resolves outside the manifest directory")
    if not path.exists():
        raise ValueError(f"{entry.id}: file does not exist: {path}")
    raw = path.read_bytes()
    actual_sha = sha256_bytes(raw)
    if actual_sha != entry.sha256:
        raise ValueError(f"{entry.id}: sha256 mismatch: expected {entry.sha256}, got {actual_sha}")
    if len(raw) != entry.bytes:
        raise ValueError(f"{entry.id}: byte count mismatch: expected {entry.bytes}, got {len(raw)}")


def validate_suite(config: SuiteConfig) -> list[ManifestEntry]:
    entries = load_manifest(config.manifest_path)
    if not entries:
        raise ValueError(f"{config.manifest_path} contains no manifest entries")
    ids = [entry.id for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{config.manifest_path} contains duplicate entry IDs")
    if any(not entry.domain.strip() for entry in entries):
        raise ValueError(f"{config.manifest_path} contains an entry with an empty domain")
    for entry in entries:
        validate_streaming_entry(entry, config.manifest_path)
    return entries
