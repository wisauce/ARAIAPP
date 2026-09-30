from __future__ import annotations

import math
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import MapStatus, NodeType


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class ErrorEnvelope(ApiModel):
    code: str
    message: str


class VenueCreate(ApiModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class VenueOut(ApiModel):
    id: str
    name: str
    published_version: int | None
    floor_id: str | None


class FloorPlanUploadOut(ApiModel):
    floor_id: str
    image_url: str
    width_pixels: int
    height_pixels: int


class Point2D(ApiModel):
    x: float
    y: float

    @field_validator("x", "y")
    @classmethod
    def finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Coordinate must be finite.")
        return value


class Polygon2D(ApiModel):
    id: Annotated[str, Field(min_length=1, max_length=80)]
    points: Annotated[list[Point2D], Field(min_length=3)]


class DestinationData(ApiModel):
    id: Annotated[str, Field(min_length=1, max_length=80)]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    x: float
    y: float
    node_id: Annotated[str, Field(min_length=1, max_length=80)]

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("x", "y")
    @classmethod
    def finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Coordinate must be finite.")
        return value


class RouteNodeData(ApiModel):
    id: Annotated[str, Field(min_length=1, max_length=80)]
    x: float
    y: float
    type: NodeType

    @field_validator("x", "y")
    @classmethod
    def finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Coordinate must be finite.")
        return value


class RouteEdgeData(ApiModel):
    id: Annotated[str, Field(min_length=1, max_length=80)]
    from_node_id: Annotated[str, Field(min_length=1, max_length=80)]
    to_node_id: Annotated[str, Field(min_length=1, max_length=80)]
    distance_meters: float | None = None
    accessible: bool = True
    temporarily_closed: bool = False


class DraftUpdate(ApiModel):
    width_meters: float
    height_meters: float
    walkable_areas: list[Polygon2D] = Field(default_factory=list)
    obstacles: list[Polygon2D] = Field(default_factory=list)
    destinations: list[DestinationData] = Field(default_factory=list)
    route_nodes: list[RouteNodeData] = Field(default_factory=list)
    route_edges: list[RouteEdgeData] = Field(default_factory=list)


class FloorMapOut(ApiModel):
    id: str
    venue_id: str
    version: int
    status: MapStatus
    width_meters: float | None
    height_meters: float | None
    image_url: str
    walkable_areas: list[Polygon2D]
    obstacles: list[Polygon2D]
    destinations: list[DestinationData]
    route_nodes: list[RouteNodeData]
    route_edges: list[RouteEdgeData]


class ClosureUpdate(ApiModel):
    temporarily_closed: bool
