import hashlib
import json
import math
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import AppError
from app.models import (
    Destination,
    FloorVersion,
    MapPolygon,
    MapStatus,
    PolygonKind,
    RouteEdge,
    RouteNode,
    Venue,
    new_id,
)
from app.schemas import (
    DestinationData,
    DraftUpdate,
    FloorMapOut,
    Point2D,
    Polygon2D,
    RouteEdgeData,
    RouteNodeData,
)
from app.storage import ObjectStorage
from app.validation import validate_draft


async def manager_venue(session: AsyncSession, venue_id: str) -> Venue:
    venue = await session.get(Venue, venue_id)
    if venue is None:
        raise AppError(404, "NOT_FOUND", "Venue not found.")
    return venue


async def floor_venue(session: AsyncSession, floor_id: str) -> Venue:
    venue = await session.scalar(select(Venue).where(Venue.floor_id == floor_id))
    if venue is None:
        raise AppError(404, "NOT_FOUND", "Floor not found.")
    return venue


async def current_draft(session: AsyncSession, floor_id: str) -> FloorVersion | None:
    return await session.scalar(
        select(FloorVersion).where(
            FloorVersion.floor_id == floor_id,
            FloorVersion.status == MapStatus.DRAFT,
        )
    )


async def latest_published(session: AsyncSession, venue_id: str) -> FloorVersion | None:
    return await session.scalar(
        select(FloorVersion)
        .where(
            FloorVersion.venue_id == venue_id,
            FloorVersion.status == MapStatus.PUBLISHED,
        )
        .order_by(FloorVersion.version.desc())
        .limit(1)
    )


def floor_to_update(floor: FloorVersion) -> DraftUpdate:
    walkable: list[Polygon2D] = []
    obstacles: list[Polygon2D] = []
    for polygon in floor.polygons:
        item = Polygon2D(
            id=polygon.id,
            points=[Point2D(x=point[0], y=point[1]) for point in polygon.points],
        )
        (walkable if polygon.kind is PolygonKind.WALKABLE else obstacles).append(item)
    return DraftUpdate(
        width_meters=floor.width_meters or 0,
        height_meters=floor.height_meters or 0,
        walkable_areas=sorted(walkable, key=lambda item: item.id),
        obstacles=sorted(obstacles, key=lambda item: item.id),
        destinations=sorted(
            [
                DestinationData(
                    id=item.id,
                    name=item.name,
                    x=item.x,
                    y=item.y,
                    node_id=item.node_id,
                )
                for item in floor.destinations
            ],
            key=lambda item: item.id,
        ),
        route_nodes=sorted(
            [
                RouteNodeData(id=item.id, x=item.x, y=item.y, type=item.type)
                for item in floor.route_nodes
            ],
            key=lambda item: item.id,
        ),
        route_edges=sorted(
            [
                RouteEdgeData(
                    id=item.id,
                    from_node_id=item.from_node_id,
                    to_node_id=item.to_node_id,
                    distance_meters=item.distance_meters,
                    accessible=item.accessible,
                    temporarily_closed=item.temporarily_closed,
                )
                for item in floor.route_edges
            ],
            key=lambda item: item.id,
        ),
    )


def floor_hash(floor: FloorVersion) -> str:
    payload = floor_to_update(floor).model_dump(mode="json", by_alias=True)
    payload["imageKey"] = floor.image_key
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def floor_out(floor: FloorVersion, storage: ObjectStorage) -> FloorMapOut:
    data = floor_to_update(floor)
    values = data.model_dump()
    values["width_meters"] = floor.width_meters
    values["height_meters"] = floor.height_meters
    return FloorMapOut(
        id=floor.floor_id,
        venue_id=floor.venue_id,
        version=floor.version,
        status=floor.status,
        image_url=storage.signed_url(floor.image_key),
        **values,
    )


def replace_entities(floor: FloorVersion, data: DraftUpdate) -> None:
    nodes = {node.id: node for node in data.route_nodes}
    floor.width_meters = data.width_meters
    floor.height_meters = data.height_meters
    floor.polygons = [
        MapPolygon(
            id=item.id,
            kind=kind,
            points=[[point.x, point.y] for point in item.points],
        )
        for kind, items in (
            (PolygonKind.WALKABLE, data.walkable_areas),
            (PolygonKind.OBSTACLE, data.obstacles),
        )
        for item in items
    ]
    floor.destinations = [
        Destination(
            id=item.id,
            name=item.name,
            x=item.x,
            y=item.y,
            node_id=item.node_id,
        )
        for item in data.destinations
    ]
    floor.route_nodes = [
        RouteNode(id=item.id, x=item.x, y=item.y, type=item.type) for item in data.route_nodes
    ]
    floor.route_edges = [
        RouteEdge(
            id=item.id,
            from_node_id=item.from_node_id,
            to_node_id=item.to_node_id,
            distance_meters=math.hypot(
                nodes[item.to_node_id].x - nodes[item.from_node_id].x,
                nodes[item.to_node_id].y - nodes[item.from_node_id].y,
            ),
            accessible=item.accessible,
            temporarily_closed=item.temporarily_closed,
        )
        for item in data.route_edges
    ]


def clone_floor(source: FloorVersion, *, status: MapStatus, version: int) -> FloorVersion:
    clone = FloorVersion(
        floor_id=source.floor_id,
        venue_id=source.venue_id,
        version=version,
        status=status,
        image_key=source.image_key,
        image_content_type=source.image_content_type,
        width_pixels=source.width_pixels,
        height_pixels=source.height_pixels,
        width_meters=source.width_meters,
        height_meters=source.height_meters,
        revision=source.revision,
        content_hash=source.content_hash,
        published_at=datetime.now(UTC) if status is MapStatus.PUBLISHED else None,
    )
    if source.width_meters and source.height_meters:
        replace_entities(clone, floor_to_update(source))
    return clone


async def ensure_draft(session: AsyncSession, venue: Venue) -> FloorVersion:
    if venue.floor_id is None:
        raise AppError(404, "NOT_FOUND", "Floor plan not found.")
    draft = await current_draft(session, venue.floor_id)
    if draft is not None:
        return draft
    published = await latest_published(session, venue.id)
    if published is None:
        raise AppError(404, "NOT_FOUND", "Draft floor not found.")
    draft = clone_floor(
        published,
        status=MapStatus.DRAFT,
        version=(venue.published_version or 0) + 1,
    )
    session.add(draft)
    await session.flush()
    return draft


async def replace_draft_image(
    session: AsyncSession,
    venue: Venue,
    *,
    image_key: str,
    content_type: str,
    width_pixels: int,
    height_pixels: int,
) -> FloorVersion:
    if venue.floor_id is None:
        venue.floor_id = new_id("flr")
    existing = await current_draft(session, venue.floor_id)
    if existing is not None:
        await session.delete(existing)
        await session.flush()
    draft = FloorVersion(
        floor_id=venue.floor_id,
        venue_id=venue.id,
        version=(venue.published_version or 0) + 1,
        status=MapStatus.DRAFT,
        image_key=image_key,
        image_content_type=content_type,
        width_pixels=width_pixels,
        height_pixels=height_pixels,
        width_meters=None,
        height_meters=None,
        revision=1,
    )
    session.add(draft)
    await session.commit()
    return draft


async def save_draft(
    session: AsyncSession,
    venue: Venue,
    data: DraftUpdate,
) -> FloorVersion:
    validate_draft(data)
    draft = await ensure_draft(session, venue)
    if not math.isclose(
        data.width_meters / data.height_meters,
        draft.width_pixels / draft.height_pixels,
        rel_tol=1e-4,
    ):
        raise AppError(
            400,
            "VALIDATION_ERROR",
            "Calibrated dimensions must preserve the floor-plan image aspect ratio.",
        )
    replace_entities(draft, data)
    draft.revision += 1
    await session.flush()
    draft.content_hash = floor_hash(draft)
    await session.commit()
    return draft


async def publish_draft(
    session: AsyncSession,
    venue: Venue,
) -> FloorVersion:
    draft = await ensure_draft(session, venue)
    data = floor_to_update(draft)
    validate_draft(data, for_publish=True)
    draft.content_hash = floor_hash(draft)
    previous = await latest_published(session, venue.id)
    if previous is not None and previous.content_hash == draft.content_hash:
        raise AppError(409, "PUBLISH_CONFLICT", "The draft has no changes to publish.")

    next_version = (venue.published_version or 0) + 1
    published = clone_floor(draft, status=MapStatus.PUBLISHED, version=next_version)
    published.content_hash = draft.content_hash
    session.add(published)
    venue.published_version = next_version
    draft.version = next_version + 1
    await session.commit()
    return published


async def update_closure_and_publish(
    session: AsyncSession,
    venue: Venue,
    edge_id: str,
    temporarily_closed: bool,
) -> FloorVersion:
    draft = await ensure_draft(session, venue)
    edge = next((item for item in draft.route_edges if item.id == edge_id), None)
    if edge is None:
        raise AppError(404, "NOT_FOUND", "Route edge not found.")
    edge.temporarily_closed = temporarily_closed
    draft.revision += 1
    await session.flush()
    draft.content_hash = floor_hash(draft)
    return await publish_draft(session, venue)
