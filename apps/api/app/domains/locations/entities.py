"""Location entity for MongoDB documents."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class LocationEntity(BaseModel):
    """Represents a campus location document in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    name: str
    osm_id: str
    building_type: str | None = None
    geometry: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"populate_by_name": True}
