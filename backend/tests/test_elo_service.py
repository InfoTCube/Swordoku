from backend.services.elo_service import K_FACTOR, calculate_elo


def test_k_factor_is_32():
    assert K_FACTOR == 32


def test_equal_ratings_win_gains_16():
    new_a, new_b = calculate_elo(1200, 1200, 1.0)
    assert new_a == 1216
    assert new_b == 1184


def test_equal_ratings_draw_no_change():
    new_a, new_b = calculate_elo(1200, 1200, 0.5)
    assert new_a == 1200
    assert new_b == 1200


def test_equal_ratings_loss_loses_16():
    new_a, new_b = calculate_elo(1200, 1200, 0.0)
    assert new_a == 1184
    assert new_b == 1216


def test_higher_rated_winner_gains_less_than_16():
    new_a, _ = calculate_elo(1600, 1200, 1.0)
    assert (new_a - 1600) < 16


def test_lower_rated_winner_gains_more_than_16():
    new_a, _ = calculate_elo(1200, 1600, 1.0)
    assert (new_a - 1200) > 16


def test_win_increases_winner_decreases_loser():
    new_a, new_b = calculate_elo(1300, 1200, 1.0)
    assert new_a > 1300
    assert new_b < 1200


def test_total_points_conserved_within_one():
    new_a, new_b = calculate_elo(1400, 1200, 1.0)
    assert abs((new_a + new_b) - (1400 + 1200)) <= 1


def test_custom_k_factor_scales_delta():
    new_a_k32, _ = calculate_elo(1200, 1200, 1.0, k=32)
    new_a_k16, _ = calculate_elo(1200, 1200, 1.0, k=16)
    assert (new_a_k32 - 1200) == 2 * (new_a_k16 - 1200)


def test_symmetry_of_result():
    # A wins against B should mirror B winning against A (swapped)
    new_a, new_b = calculate_elo(1200, 1400, 1.0)
    new_b2, new_a2 = calculate_elo(1400, 1200, 0.0)
    assert new_a == new_a2
    assert new_b == new_b2
