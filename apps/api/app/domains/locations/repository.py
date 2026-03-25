"""Location repository for geospatial database operations."""

from typing import Protocol

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domains.locations.entities import LocationEntity


class ILocationRepository(Protocol):
    """Protocol defining the location repository interface."""

    async def find_by_coordinates(
        self,
        lng: float,
        lat: float,
        max_distance_m: float = 15,
    ) -> dict | None:
        """Find a location containing or nearest to the given coordinates."""
        ...

    async def upsert(self, location: LocationEntity) -> None:
        """Insert or update a location by osm_id."""
        ...

    async def ensure_indexes(self) -> None:
        """Create geospatial and unique indexes."""
        ...


class LocationRepository:
    """MongoDB implementation of the location repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db.locations

    async def find_by_coordinates(
        self,
        lng: float,
        lat: float,
        max_distance_m: float = 15,
    ) -> dict | None:
        """Find a location containing or nearest to the given coordinates.

        Uses a two-step lookup: exact polygon intersection first,
        then a configurable proximity fallback.
        """
        point = {"type": "Point", "coordinates": [lng, lat]}

        result = await self.collection.find_one(
            {"geometry": {"$geoIntersects": {"$geometry": point}}}
        )
        if result:
            return result

        return await self.collection.find_one(
            {
                "geometry": {
                    "$near": {"$geometry": point, "$maxDistance": max_distance_m}
                }
            }
        )

    async def upsert(self, location: LocationEntity) -> None:
        """Insert or update a location by osm_id."""
        await self.collection.update_one(
            {"osm_id": location.osm_id},
            {"$set": location.model_dump(by_alias=True, exclude={"id"})},
            upsert=True,
        )

    async def ensure_indexes(self) -> None:
        """Create geospatial and unique indexes."""
        await self.collection.create_index([("geometry", "2dsphere")])
        await self.collection.create_index("osm_id", unique=True)
