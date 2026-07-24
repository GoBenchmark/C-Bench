from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cbench.data.collection import apply_transform, collect_catalog


def test_gutenberg_transform_removes_license_wrapper() -> None:
    raw = (
        b"header\n"
        b"*** START OF THE PROJECT GUTENBERG EBOOK EXAMPLE ***\n"
        b"\n"
        b"title\n"
        b"body one\n"
        b"body two\n"
        b"*** END OF THE PROJECT GUTENBERG EBOOK EXAMPLE ***\n"
        b"license\n"
    )
    output = apply_transform(
        raw,
        {"kind": "gutenberg_body", "skip_lines": 1, "max_bytes": 100},
    )
    assert output == b"title\nbody one\nbody two\n"
    assert b"PROJECT GUTENBERG" not in output


def test_first_lines_preserves_source_line_endings() -> None:
    assert apply_transform(b"a\r\nb\r\nc\r\n", {"kind": "first_lines", "count": 2}) == b"a\r\nb\r\n"


def test_unknown_transform_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown transform"):
        apply_transform(b"data", {"kind": "mystery"})


def test_gutenberg_transform_does_not_truncate_an_oversized_line() -> None:
    raw = b"*** START OF THE PROJECT GUTENBERG EBOOK EXAMPLE ***\n" + b"abcdef\n" + b"*** END OF THE PROJECT GUTENBERG EBOOK EXAMPLE ***\n"
    with pytest.raises(ValueError, match="no complete lines"):
        apply_transform(raw, {"kind": "gutenberg_body", "skip_lines": 0, "max_bytes": 3})


def test_collector_emits_manifest_relative_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_raw = b"hello from source\n"
    catalog = tmp_path / "catalog.json"
    manifest = tmp_path / "suite" / "manifest.jsonl"
    output_dir = tmp_path / "suite" / "documents"
    catalog.write_text(
        json.dumps(
            {
                "accessed_at": "2026-07-24",
                "sources": [
                    {
                        "id": "doc",
                        "domain": "prose",
                        "title": "Fixture",
                        "language": "en",
                        "url": "https://example.test/doc",
                        "source_sha256": hashlib.sha256(source_raw).hexdigest(),
                        "license": "fixture",
                        "license_url": "https://example.test/license",
                        "output": "doc.txt",
                        "transform": {"kind": "identity"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("cbench.data.collection.download_source", lambda url: source_raw)

    rows = collect_catalog(catalog, output_dir, manifest)

    assert rows[0]["path"] == "documents/doc.txt"
    assert (manifest.parent / rows[0]["path"]).read_bytes() == source_raw


def test_collector_rejects_output_outside_manifest_directory(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"sources": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="inside the manifest directory"):
        collect_catalog(catalog, tmp_path / "outside", tmp_path / "suite" / "manifest.jsonl")


def test_collector_rejects_empty_catalog(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"sources": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="at least one source"):
        collect_catalog(
            catalog,
            tmp_path / "suite" / "documents",
            tmp_path / "suite" / "manifest.jsonl",
        )


def test_collector_rejects_duplicate_output_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = b"shared source\n"
    source = {
        "domain": "prose",
        "title": "Fixture",
        "language": "en",
        "url": "https://example.test/doc",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "license": "fixture",
        "license_url": "https://example.test/license",
        "output": "same.txt",
        "transform": {"kind": "identity"},
    }
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "sources": [
                    {"id": "one", **source},
                    {"id": "two", **source},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("cbench.data.collection.download_source", lambda url: raw)

    with pytest.raises(ValueError, match="duplicate output paths"):
        collect_catalog(
            catalog,
            tmp_path / "suite" / "documents",
            tmp_path / "suite" / "manifest.jsonl",
        )
