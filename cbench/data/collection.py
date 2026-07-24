from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from cbench import __version__

MAX_SOURCE_BYTES = 25 * 1024 * 1024
USER_AGENT = f"C-Bench/{__version__} dataset collector (+https://github.com/)"


@dataclass(frozen=True)
class CollectedDocument:
    output_path: Path
    raw: bytes
    manifest_row: dict[str, Any]


def load_source_catalog(path: str | Path) -> dict[str, Any]:
    catalog_path = Path(path).resolve()
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise ValueError(f"{catalog_path} must contain a top-level 'sources' list")
    return data


def collect_catalog(
    catalog_path: str | Path,
    output_dir: str | Path,
    manifest_path: str | Path,
    *,
    force: bool = False,
) -> list[dict[str, Any]]:
    catalog = load_source_catalog(catalog_path)
    output_root = Path(output_dir).resolve()
    manifest = Path(manifest_path).resolve()
    if not output_root.is_relative_to(manifest.parent):
        raise ValueError("output_dir must be inside the manifest directory")
    accessed_at = str(catalog.get("accessed_at", ""))
    documents: list[CollectedDocument] = []

    for index, source in enumerate(catalog["sources"], start=1):
        if not isinstance(source, dict):
            raise ValueError(f"Source catalog entry {index} must be a JSON object")
        documents.append(
            _prepare_document(
                source,
                output_root=output_root,
                manifest_dir=manifest.parent,
                accessed_at=accessed_at,
            )
        )

    if not documents:
        raise ValueError("Source catalog must contain at least one source")
    ids = [document.manifest_row["id"] for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Source catalog contains duplicate document IDs")
    output_paths = [document.output_path for document in documents]
    if len(output_paths) != len(set(output_paths)):
        raise ValueError("Source catalog contains duplicate output paths")

    manifest_text = "".join(
        json.dumps(document.manifest_row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for document in documents
    )
    _check_replace(manifest, manifest_text.encode("utf-8"), force=force)
    for document in documents:
        _check_replace(document.output_path, document.raw, force=force)

    output_root.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    for document in documents:
        document.output_path.parent.mkdir(parents=True, exist_ok=True)
        document.output_path.write_bytes(document.raw)
    manifest.write_text(manifest_text, encoding="utf-8")
    return [document.manifest_row for document in documents]


def download_source(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS sources are allowed: {url}")
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_SOURCE_BYTES:
            raise ValueError(f"Source exceeds {MAX_SOURCE_BYTES} bytes: {url}")
        raw = response.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError(f"Source exceeds {MAX_SOURCE_BYTES} bytes: {url}")
    return raw


def apply_transform(raw: bytes, transform: dict[str, Any]) -> bytes:
    kind = transform.get("kind", "identity")
    if kind == "identity":
        return raw
    if kind == "first_lines":
        return _first_lines(raw, int(transform["count"]))
    if kind == "gutenberg_body":
        return _gutenberg_body(
            raw,
            skip_lines=int(transform.get("skip_lines", 0)),
            max_bytes=int(transform["max_bytes"]),
        )
    raise ValueError(f"Unknown transform kind: {kind}")


def _prepare_document(
    source: dict[str, Any],
    *,
    output_root: Path,
    manifest_dir: Path,
    accessed_at: str,
) -> CollectedDocument:
    required = [
        "id",
        "domain",
        "title",
        "language",
        "url",
        "source_sha256",
        "license",
        "license_url",
        "output",
        "transform",
    ]
    missing = [key for key in required if key not in source]
    if missing:
        raise ValueError(f"Source is missing required fields: {', '.join(missing)}")
    if not isinstance(source["transform"], dict):
        raise ValueError(f"{source['id']}: transform must be a JSON object")

    relative_output = PurePosixPath(str(source["output"]))
    if (
        not relative_output.parts
        or relative_output.is_absolute()
        or ".." in relative_output.parts
    ):
        raise ValueError(f"Output must stay within the output directory: {source['output']}")
    output_path = output_root.joinpath(*relative_output.parts).resolve()
    if not output_path.is_relative_to(output_root):
        raise ValueError(f"Output must stay within the output directory: {source['output']}")

    source_raw = download_source(str(source["url"]))
    source_sha256 = _sha256(source_raw)
    if source_sha256 != source["source_sha256"]:
        raise ValueError(
            f"{source['id']}: upstream hash changed; "
            f"expected {source['source_sha256']}, got {source_sha256}"
        )

    output_raw = apply_transform(source_raw, source["transform"])
    if not output_raw:
        raise ValueError(f"{source['id']}: extraction produced an empty document")
    output_raw.decode("utf-8")

    relative_manifest_path = Path(os.path.relpath(output_path, manifest_dir))
    row = {
        "id": str(source["id"]),
        "domain": str(source["domain"]),
        "path": relative_manifest_path.as_posix(),
        "mode": "streaming",
        "sha256": _sha256(output_raw),
        "license": str(source["license"]),
        "bytes": len(output_raw),
        "title": str(source["title"]),
        "language": str(source["language"]),
        "source_url": str(source["url"]),
        "source_sha256": source_sha256,
        "license_url": str(source["license_url"]),
        "accessed_at": accessed_at,
        "extraction": _describe_transform(source["transform"]),
    }
    return CollectedDocument(output_path=output_path, raw=output_raw, manifest_row=row)


def _gutenberg_body(raw: bytes, *, skip_lines: int, max_bytes: int) -> bytes:
    if skip_lines < 0:
        raise ValueError("skip_lines must be non-negative")
    lines = raw.splitlines(keepends=True)
    start = next(
        (index + 1 for index, line in enumerate(lines) if b"*** START OF THE PROJECT GUTENBERG EBOOK" in line),
        None,
    )
    end = next(
        (index for index, line in enumerate(lines) if b"*** END OF THE PROJECT GUTENBERG EBOOK" in line),
        None,
    )
    if start is None or end is None or end <= start:
        raise ValueError("Could not find Project Gutenberg body markers")
    body = _whole_lines_within(lines[start + skip_lines : end], max_bytes).strip()
    if not body:
        raise ValueError("Gutenberg extraction produced no complete lines")
    return body + b"\n"


def _first_lines(raw: bytes, count: int) -> bytes:
    if count <= 0:
        raise ValueError("Line count must be positive")
    return b"".join(raw.splitlines(keepends=True)[:count])


def _whole_lines_within(lines: list[bytes], max_bytes: int) -> bytes:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    selected: list[bytes] = []
    size = 0
    for line in lines:
        if selected and size + len(line) > max_bytes:
            break
        if not selected and len(line) > max_bytes:
            break
        selected.append(line)
        size += len(line)
    return b"".join(selected)


def _describe_transform(transform: dict[str, Any]) -> str:
    kind = str(transform.get("kind", "identity"))
    if kind == "identity":
        return "verbatim source bytes"
    if kind == "first_lines":
        return f"first {int(transform['count'])} lines"
    if kind == "gutenberg_body":
        return (
            "body between ebook markers; "
            f"skip {int(transform.get('skip_lines', 0))} lines; "
            f"whole lines up to {int(transform['max_bytes'])} bytes"
        )
    return kind


def _check_replace(path: Path, expected: bytes, *, force: bool) -> None:
    if not path.exists():
        return
    if path.read_bytes() == expected:
        return
    if not force:
        raise ValueError(f"Refusing to replace changed file without --force: {path}")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
