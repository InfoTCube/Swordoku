K_FACTOR = 32


def calculate_elo(
    rating_a: int,
    rating_b: int,
    result: float,
    k: int = K_FACTOR,
) -> tuple[int, int]:
    """
    Standard ELO update for a pairwise match.

    result is the outcome for player A: 1.0 win, 0.5 draw, 0.0 loss.
    Returns (new_rating_a, new_rating_b), rounded to the nearest integer.
    """
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 - expected_a

    new_a = rating_a + k * (result - expected_a)
    new_b = rating_b + k * ((1 - result) - expected_b)

    return round(new_a), round(new_b)
