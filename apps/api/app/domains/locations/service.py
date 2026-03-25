"""Location service for geospatial lookups."""

from app.domains.games.difficulty import (
    DEFAULT_DIFFICULTY,
    DIFFICULTY_SETTINGS,
    Difficulty,
)
from app.domains.locations.repository import ILocationRepository


class LocationService:
    """Resolves coordinates to campus location names."""

    def __init__(self, location_repository: ILocationRepository) -> None:
        self.location_repository = location_repository

    async def resolve_location_name(
        self,
        lat: float,
        lng: float,
        difficulty: Difficulty = DEFAULT_DIFFICULTY,
    ) -> str | None:
        """Return the building/landmark name for the given coordinates, or None."""
        proximity_meters = DIFFICULTY_SETTINGS[difficulty]["proximity_meters"]
        result = await self.location_repository.find_by_coordinates(
            lng,
            lat,
            max_distance_m=proximity_meters,
        )
        return result["name"] if result else None
