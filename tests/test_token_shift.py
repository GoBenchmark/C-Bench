from cbench.scoring.logprob import target_prediction_positions


def test_logits_at_position_i_score_token_i_plus_one() -> None:
    assert target_prediction_positions(context_len=3, target_count=3) == [
        (2, 3),
        (3, 4),
        (4, 5),
    ]


def test_no_context_cannot_score_first_token() -> None:
    assert target_prediction_positions(context_len=0, target_count=3) == [
        (0, 1),
        (1, 2),
    ]
