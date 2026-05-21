"""Reinforcement-learning utilities for lottery number ranking.

The model intentionally uses a lightweight tabular approach instead of deep
learning so it can run fast in-request and in tests without optional runtime
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

import numpy as np


@dataclass
class LotteryRLAgent:
    """Epsilon-greedy tabular learner over lottery numbers.

    Args:
        pool_size: Total count of selectable numbers in the game.
        num_picks: Number of numbers returned by :meth:`predict`.
        seed: Random seed for reproducible training behavior.
    """

    pool_size: int
    num_picks: int
    seed: int = 42
    q_values: np.ndarray = field(init=False, repr=False)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize Q-table and deterministic RNG."""
        self.q_values = np.zeros(self.pool_size, dtype=float)
        self._rng = random.Random(self.seed)

    def train(
        self,
        draw_history: list[list[int]],
        episodes: int = 250,
        alpha: float = 0.08,
        epsilon: float = 0.15,
    ) -> None:
        """Train the tabular learner from historical draws.

        Args:
            draw_history: Ordered draw history where each row is one drawing.
            episodes: Number of replay passes over history.
            alpha: Learning rate for Q-value updates.
            epsilon: Exploration probability for epsilon-greedy policy.
        """
        if not draw_history:
            return

        valid_rows = [
            sorted({n for n in row if 1 <= int(n) <= self.pool_size})
            for row in draw_history
            if row
        ]
        if len(valid_rows) < 2:
            return

        for _ in range(max(1, episodes)):
            for t in range(len(valid_rows) - 1):
                next_draw = set(valid_rows[t + 1])
                action = self._choose_action(epsilon=epsilon)
                reward = 1.0 if action in next_draw else 0.0

                idx = action - 1
                td_error = reward - self.q_values[idx]
                self.q_values[idx] += alpha * td_error

    def number_scores(self) -> dict[int, float]:
        """Return normalized per-number RL scores in the range [0, 1]."""
        lo = float(np.min(self.q_values))
        hi = float(np.max(self.q_values))
        if hi <= lo:
            return {n: 0.5 for n in range(1, self.pool_size + 1)}
        return {
            n: float((self.q_values[n - 1] - lo) / (hi - lo))
            for n in range(1, self.pool_size + 1)
        }

    def predict(self) -> list[int]:
        """Return the highest-ranked numbers from current Q-values."""
        ranked = np.argsort(self.q_values)[::-1][: self.num_picks]
        return sorted(int(i) + 1 for i in ranked)

    def _choose_action(self, epsilon: float) -> int:
        """Choose one number via epsilon-greedy sampling."""
        if self._rng.random() < epsilon:
            return self._rng.randint(1, self.pool_size)
        return int(np.argmax(self.q_values)) + 1