"""Unit tests for game-theoretic split-avoidance scoring."""

from app.services.game_theory import (
    calculate_number_popularity,
    compute_split_avoidance_utility,
    game_theoretic_selection,
)


def test_calculate_number_popularity() -> None:
    draw_history = [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
    popularity = calculate_number_popularity(draw_history=draw_history, pool_size=5)

    assert len(popularity) == 5
    assert popularity[3] > popularity[1]


def test_game_theoretic_selection_prefers_low_popularity() -> None:
    popularity = {1: 0.1, 2: 0.2, 3: 0.9, 4: 1.0, 5: 0.8}
    utility = compute_split_avoidance_utility(popularity)
    selected = game_theoretic_selection(utility_scores=utility, num_picks=2)

    assert selected == [1, 2]