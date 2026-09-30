from __future__ import annotations

import secrets
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.geometry import PolygonGeometry


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12)}"


def utcnow() -> datetime:
    return datetime.now(UTC)


class MapStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NodeType(StrEnum):
    INTERSECTION = "INTERSECTION"
    DOOR = "DOOR"
    ENDPOINT = "ENDPOINT"


class PolygonKind(StrEnum):
    WALKABLE = "WALKABLE"
    OBSTACLE = "OBSTACLE"


enum_options = {"native_enum": False, "validate_strings": True}


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("ven"))
    name: Mapped[str] = mapped_column(String(200))
    floor_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    published_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    floor_versions: Mapped[list[FloorVersion]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )


class FloorVersion(Base):
    __tablename__ = "floor_versions"
    __table_args__ = (
        UniqueConstraint("venue_id", "version", "status", name="venue_version_status"),
        Index("ix_floor_versions_floor_status", "floor_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    floor_id: Mapped[str] = mapped_column(String(40), index=True)
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[MapStatus] = mapped_column(Enum(MapStatus, **enum_options))
    image_key: Mapped[str] = mapped_column(String(500))
    image_content_type: Mapped[str] = mapped_column(String(50))
    width_pixels: Mapped[int] = mapped_column(Integer)
    height_pixels: Mapped[int] = mapped_column(Integer)
    width_meters: Mapped[float | None] = mapped_column(Float)
    height_meters: Mapped[float | None] = mapped_column(Float)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    venue: Mapped[Venue] = relationship(back_populates="floor_versions")
    polygons: Mapped[list[MapPolygon]] = relationship(
        back_populates="floor_version", cascade="all, delete-orphan", lazy="selectin"
    )
    destinations: Mapped[list[Destination]] = relationship(
        back_populates="floor_version", cascade="all, delete-orphan", lazy="selectin"
    )
    route_nodes: Mapped[list[RouteNode]] = relationship(
        back_populates="floor_version", cascade="all, delete-orphan", lazy="selectin"
    )
    route_edges: Mapped[list[RouteEdge]] = relationship(
        back_populates="floor_version", cascade="all, delete-orphan", lazy="selectin"
    )


class MapPolygon(Base):
    __tablename__ = "polygons"

    floor_version_id: Mapped[int] = mapped_column(
        ForeignKey("floor_versions.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    kind: Mapped[PolygonKind] = mapped_column(Enum(PolygonKind, **enum_options))
    points: Mapped[list[list[float]]] = mapped_column(PolygonGeometry())

    floor_version: Mapped[FloorVersion] = relationship(back_populates="polygons")


class Destination(Base):
    __tablename__ = "destinations"

    floor_version_id: Mapped[int] = mapped_column(
        ForeignKey("floor_versions.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    node_id: Mapped[str] = mapped_column(String(80))

    floor_version: Mapped[FloorVersion] = relationship(back_populates="destinations")


class RouteNode(Base):
    __tablename__ = "route_nodes"

    floor_version_id: Mapped[int] = mapped_column(
        ForeignKey("floor_versions.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    type: Mapped[NodeType] = mapped_column(Enum(NodeType, **enum_options))

    floor_version: Mapped[FloorVersion] = relationship(back_populates="route_nodes")


class RouteEdge(Base):
    __tablename__ = "route_edges"

    floor_version_id: Mapped[int] = mapped_column(
        ForeignKey("floor_versions.id", ondelete="CASCADE"), primary_key=True
    )
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    from_node_id: Mapped[str] = mapped_column(String(80))
    to_node_id: Mapped[str] = mapped_column(String(80))
    distance_meters: Mapped[float] = mapped_column(Float)
    accessible: Mapped[bool] = mapped_column(Boolean, default=True)
    temporarily_closed: Mapped[bool] = mapped_column(Boolean, default=False)

    floor_version: Mapped[FloorVersion] = relationship(back_populates="route_edges")
