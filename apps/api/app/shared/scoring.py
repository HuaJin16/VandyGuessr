"""Scoring and distance utilities for the game."""

import math

# Vanderbilt campus bounding box (approximate)
# SW corner: 36.1395, -86.8105
# NE corner: 36.1510, -86.7935
CAMPUS_SW = (36.1395, -86.8105)
CAMPUS_NE = (36.1510, -86.7935)

EARTH_RADIUS_M = 6_371_000


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute the geodesic distance in meters between two lat/lng points."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    )
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def campus_diagonal() -> float:
    """Return the diagonal distance of the campus bounding box in meters."""
    return haversine(CAMPUS_SW[0], CAMPUS_SW[1], CAMPUS_NE[0], CAMPUS_NE[1])


# Pre-compute once at import time
_CAMPUS_SIZE = campus_diagonal()


MAX_SCORE = 5000
_DECAY_CONSTANT = 5


def compute_score(distance_meters: float, *, same_building: bool = False) -> int:
    """Compute the round score from the distance.

    If the guess is inside the same building as the actual location, the player
    receives a perfect score regardless of distance.  Otherwise the score
    follows an exponential-decay curve:

        Score = 5000 * e ^ (-5 * distance / campus_size)
    """
    if same_building:
        return MAX_SCORE
    raw = MAX_SCORE * math.exp(-_DECAY_CONSTANT * distance_meters / _CAMPUS_SIZE)
    return max(0, round(raw))
