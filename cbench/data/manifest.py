from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SuiteConfig:
    name: str
    manifest_path: Path
    config_path: Path


@dataclass(frozen=True)
class ManifestEntry:
    id: str
    domain: str
    mode: str
    path: str | None = None
    sha256: str | None = None
    license: str | None = None
    bytes: int | None = None
    context_path: str | None = None
    target_path: str | None = None
    context_sha256: str | None = None
    target_sha256: str | None = None
    target_bytes: int | None = None
    title: str | None = None
    language: str | None = None
    source_url: str | None = None
    source_sha256: str | None = None
    license_url: str | None = None
    accessed_at: str | None = None
    extraction: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManifestEntry":
        if not isinstance(data, dict):
            raise ValueError("Manifest entry must be a JSON object")
        required = ["id", "domain", "mode"]
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"Manifest entry missing required fields: {', '.join(missing)}")
        for field in ("domain", "mode", "path", "sha256"):
            value = data.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Manifest entry field '{field}' must be a string")
        if data.get("bytes") is not None and (
            isinstance(data["bytes"], bool) or not isinstance(data["bytes"], int)
        ):
            raise ValueError("Manifest entry field 'bytes' must be an integer")
        return cls(
            id=str(data["id"]),
            domain=str(data["domain"]),
            mode=str(data["mode"]),
            path=data.get("path"),
            sha256=data.get("sha256"),
            license=data.get("license"),
            bytes=data.get("bytes"),
            context_path=data.get("context_path"),
            target_path=data.get("target_path"),
            context_sha256=data.get("context_sha256"),
            target_sha256=data.get("target_sha256"),
            target_bytes=data.get("target_bytes"),
            title=data.get("title"),
            language=data.get("language"),
            source_url=data.get("source_url"),
            source_sha256=data.get("source_sha256"),
            license_url=data.get("license_url"),
            accessed_at=data.get("accessed_at"),
            extraction=data.get("extraction"),
        )


def _parse_simple_yaml(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"Unsupported config line: {line!r}")
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def load_suite_config(path: str | Path) -> SuiteConfig:
    config_path = Path(path).resolve()
    text = config_path.read_text(encoding="utf-8")
    data: dict[str, Any]
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        data = loaded if isinstance(loaded, dict) else {}
    except ModuleNotFoundError:
        data = _parse_simple_yaml(text)

    name = str(data.get("suite") or data.get("name") or config_path.stem)
    manifest_value = data.get("manifest")
    if not manifest_value:
        raise ValueError(f"Suite config {config_path} must define 'manifest'")
    manifest_path = Path(str(manifest_value))
    if not manifest_path.is_absolute():
        manifest_path = (config_path.parent / manifest_path).resolve()
    return SuiteConfig(name=name, manifest_path=manifest_path, config_path=config_path)


def load_manifest(path: str | Path) -> list[ManifestEntry]:
    manifest_path = Path(path).resolve()
    entries: list[ManifestEntry] = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {manifest_path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Manifest row on {manifest_path}:{line_number} must be a JSON object")
            entries.append(ManifestEntry.from_dict(row))
    return entries


def resolve_entry_path(entry_path: str, manifest_path: str | Path) -> Path:
    raw = Path(entry_path)
    if raw.is_absolute():
        return raw
    manifest_dir = Path(manifest_path).resolve().parent
    return (manifest_dir / raw).resolve()
