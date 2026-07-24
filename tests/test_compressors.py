from cbench.compressors.gzip_baseline import compress


def test_repeated_text_compresses_better_than_random_like_text() -> None:
    repeated = (b"abc123\n" * 200)
    random_like = bytes((i * 37 + 11) % 256 for i in range(len(repeated)))
    repeated_bpb = len(compress(repeated)) * 8 / len(repeated)
    random_bpb = len(compress(random_like)) * 8 / len(random_like)
    assert repeated_bpb < random_bpb


def test_gzip_output_is_deterministic() -> None:
    raw = b"stable benchmark bytes\n"
    assert compress(raw) == compress(raw)
