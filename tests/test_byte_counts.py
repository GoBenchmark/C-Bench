from cbench.metrics import bits_per_byte


def test_utf8_byte_count_differs_from_character_count() -> None:
    text = "压缩"
    raw = text.encode("utf-8")
    assert len(text) == 2
    assert len(raw) == 6
    assert bits_per_byte(12.0, len(raw)) == 2.0
