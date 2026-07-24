import json
from pathlib import Path

import pytest

from cbench.data.manifest import SuiteConfig, load_manifest, resolve_entry_path
from cbench.data.validation import sha256_bytes, validate_suite


def test_manifest_hash_validation_fails_on_mismatch(tmp_path: Path) -> None:
    fixture = tmp_path / "doc.txt"
    fixture.write_text("hello\n", encoding="utf-8")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "id": "doc",
                "domain": "prose",
                "path": "doc.txt",
                "mode": "streaming",
                "sha256": "0" * 64,
                "license": "fixture",
                "bytes": len(fixture.read_bytes()),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = SuiteConfig(name="tmp", manifest_path=manifest, config_path=tmp_path / "suite.yaml")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        validate_suite(config)


def test_manifest_validation_passes_for_matching_hash(tmp_path: Path) -> None:
    fixture = tmp_path / "doc.txt"
    raw = b"hello\n"
    fixture.write_bytes(raw)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "id": "doc",
                "domain": "prose",
                "path": "doc.txt",
                "mode": "streaming",
                "sha256": sha256_bytes(raw),
                "license": "fixture",
                "bytes": len(raw),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = SuiteConfig(name="tmp", manifest_path=manifest, config_path=tmp_path / "suite.yaml")
    assert len(validate_suite(config)) == 1


def test_entry_paths_are_resolved_from_manifest_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir = tmp_path / "suite"
    caller_dir = tmp_path / "caller"
    manifest_dir.mkdir()
    caller_dir.mkdir()
    (caller_dir / "doc.txt").write_text("wrong file", encoding="utf-8")
    manifest = manifest_dir / "manifest.jsonl"
    monkeypatch.chdir(caller_dir)

    assert resolve_entry_path("doc.txt", manifest) == manifest_dir / "doc.txt"


def test_manifest_validation_rejects_duplicate_ids(tmp_path: Path) -> None:
    raw = b"hello\n"
    fixture = tmp_path / "doc.txt"
    fixture.write_bytes(raw)
    row = {
        "id": "duplicate",
        "domain": "prose",
        "path": "doc.txt",
        "mode": "streaming",
        "sha256": sha256_bytes(raw),
        "bytes": len(raw),
    }
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    config = SuiteConfig(name="tmp", manifest_path=manifest, config_path=tmp_path / "suite.yaml")

    with pytest.raises(ValueError, match="duplicate entry IDs"):
        validate_suite(config)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"domain": "   "}, "empty domain"),
        ({"bytes": 0}, "at least one byte"),
        ({"path": "../doc.txt"}, "must stay relative"),
    ],
)
def test_manifest_validation_rejects_invalid_rows(
    tmp_path: Path, changes: dict[str, object], message: str
) -> None:
    raw = b"hello\n"
    fixture = tmp_path / "doc.txt"
    fixture.write_bytes(raw)
    row: dict[str, object] = {
        "id": "doc",
        "domain": "prose",
        "path": "doc.txt",
        "mode": "streaming",
        "sha256": sha256_bytes(raw),
        "bytes": len(raw),
    }
    row.update(changes)
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
    config = SuiteConfig(name="tmp", manifest_path=manifest, config_path=tmp_path / "suite.yaml")

    with pytest.raises(ValueError, match=message):
        validate_suite(config)


def test_manifest_loader_rejects_non_object_rows(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        load_manifest(manifest)
