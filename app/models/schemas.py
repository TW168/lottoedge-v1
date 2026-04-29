from datetime import date
from typing import Optional
from pydantic import BaseModel


class DrawSchema(BaseModel):
    game: str
    draw_date: date
    n1: int
    n2: int
    n3: int
    n4: int
    n5: Optional[int] = None
    n6: Optional[int] = None
    bonus: Optional[int] = None
    power_play: Optional[int] = None
    era: str
    is_bonus_era: bool = False

    model_config = {"from_attributes": True}


class JackpotUpdate(BaseModel):
    game: str
    amount: float
    next_draw_date: Optional[date] = None
    is_annuity: bool = True


class PickRequest(BaseModel):
    game: str
    count: int = 5
    include_era2: bool = False
    diversity_level: int = 60
    # Module weights (0–100, normalized internally)
    weight_frequency: int = 15
    weight_positional: int = 12
    weight_cluster: int = 10
    weight_due_score: int = 12
    weight_momentum: int = 8
    weight_heat: int = 8
    weight_group: int = 5
    weight_lstm: int = 10
    weight_ensemble: int = 10
    weight_monte_carlo: int = 5
    weight_coverage: int = 5


class GeneratedPick(BaseModel):
    numbers: list[int]
    bonus: Optional[int] = None
    composite_score: float
    sum_value: int
    odd_count: int
    even_count: int
    low_count: int
    high_count: int
    passes_sum_gate: bool
    filter_notes: list[str]
