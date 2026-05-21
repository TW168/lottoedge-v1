"""Unit tests for reinforcement-learning number ranking."""

from app.services.reinforcement_learning import LotteryRLAgent


def test_lottery_rl_agent_training_and_prediction() -> None:
    draw_history = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [3, 4, 5]]
    agent = LotteryRLAgent(pool_size=5, num_picks=2, seed=7)
    agent.train(draw_history=draw_history, episodes=120)

    predictions = agent.predict()
    scores = agent.number_scores()

    assert len(predictions) == 2
    assert all(1 <= num <= 5 for num in predictions)
    assert len(scores) == 5
    assert all(0.0 <= value <= 1.0 for value in scores.values())