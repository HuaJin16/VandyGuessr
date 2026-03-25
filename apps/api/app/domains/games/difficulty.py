from typing import Literal, TypedDict

Difficulty = Literal["easy", "medium", "hard"]
DEFAULT_DIFFICULTY: Difficulty = "medium"


class DifficultySettings(TypedDict):
    decay: int
    proximity_meters: int


DIFFICULTY_SETTINGS: dict[Difficulty, DifficultySettings] = {
    "easy": {"decay": 3, "proximity_meters": 25},
    "medium": {"decay": 5, "proximity_meters": 15},
    "hard": {"decay": 8, "proximity_meters": 8},
}
