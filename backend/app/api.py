import io
import secrets

from fastapi import APIRouter, Depends, File, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_session
from app.errors import AppError
from app.models import MapStatus, Venue
from app.schemas import (
    ClosureUpdate,
    DraftUpdate,
    FloorMapOut,
    FloorPlanUploadOut,
    VenueCreate,
    VenueOut,
)
from app.services import (
    current_draft,
    floor_out,
    floor_venue,
    latest_published,
    manager_venue,
    publish_draft,
    replace_draft_image,
    save_draft,
    update_closure_and_publish,
)
from app.storage import ObjectStorage, get_storage

router = APIRouter(prefix="/v1")


@router.post("/venues", response_model=VenueOut, status_code=201)
async def create_venue(
    body: VenueCreate,
    session: AsyncSession = Depends(get_session),
) -> Venue:
    venue = Venue(name=body.name)
    session.add(venue)
    await session.commit()
    return venue


@router.get("/venues", response_model=list[VenueOut])
async def list_published_venues(
    session: AsyncSession = Depends(get_session),
) -> list[Venue]:
    result = await session.scalars(select(Venue).order_by(Venue.name, Venue.id))
    return list(result)


@router.get("/venues/{venue_id}", response_model=VenueOut)
async def get_published_venue(
    venue_id: str,
    session: AsyncSession = Depends(get_session),
) -> Venue:
    venue = await session.get(Venue, venue_id)
    if venue is None:
        raise AppError(404, "NOT_FOUND", "Venue not found.")
    return venue


@router.post("/venues/{venue_id}/floor-plan", response_model=FloorPlanUploadOut)
async def upload_floor_plan(
    venue_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    storage: ObjectStorage = Depends(get_storage),
) -> FloorPlanUploadOut:
    venue = await manager_venue(session, venue_id)
    data = await file.read(settings.max_floor_plan_bytes + 1)
    if len(data) > settings.max_floor_plan_bytes:
        raise AppError(400, "VALIDATION_ERROR", "Floor plan exceeds the 15 MB limit.")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image_format = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise AppError(400, "VALIDATION_ERROR", "Floor plan must be a valid PNG or JPEG.") from exc
    accepted = {"PNG": ("image/png", "png"), "JPEG": ("image/jpeg", "jpg")}
    if image_format not in accepted:
        raise AppError(400, "VALIDATION_ERROR", "Floor plan must be a PNG or JPEG.")
    content_type, extension = accepted[image_format]
    key = f"floor-plans/{venue.id}/{secrets.token_urlsafe(24)}.{extension}"
    await storage.upload(key, data, content_type)
    draft = await replace_draft_image(
        session,
        venue,
        image_key=key,
        content_type=content_type,
        width_pixels=width,
        height_pixels=height,
    )
    return FloorPlanUploadOut(
        floor_id=draft.floor_id,
        image_url=storage.signed_url(key),
        width_pixels=width,
        height_pixels=height,
    )


@router.put("/floors/{floor_id}/draft", response_model=FloorMapOut)
async def put_draft(
    floor_id: str,
    body: DraftUpdate,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_storage),
) -> FloorMapOut:
    venue = await floor_venue(session, floor_id)
    floor = await save_draft(session, venue, body)
    return floor_out(floor, storage)


@router.get("/floors/{floor_id}/draft", response_model=FloorMapOut)
async def get_draft(
    floor_id: str,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_storage),
) -> FloorMapOut:
    await floor_venue(session, floor_id)
    floor = await current_draft(session, floor_id)
    if floor is None:
        raise AppError(404, "NOT_FOUND", "Draft floor not found.")
    return floor_out(floor, storage)


@router.post("/floors/{floor_id}/publish", response_model=FloorMapOut)
async def publish(
    floor_id: str,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_storage),
) -> FloorMapOut:
    venue = await floor_venue(session, floor_id)
    floor = await publish_draft(session, venue)
    return floor_out(floor, storage)


@router.get("/venues/{venue_id}/published-map", response_model=FloorMapOut)
async def published_map(
    venue_id: str,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_storage),
) -> FloorMapOut:
    venue = await session.get(Venue, venue_id)
    if venue is None or venue.published_version is None:
        raise AppError(404, "NOT_FOUND", "Published venue not found.")
    floor = await latest_published(session, venue_id)
    if floor is None or floor.status is not MapStatus.PUBLISHED:
        raise AppError(404, "NOT_FOUND", "Published map not found.")
    return floor_out(floor, storage)


@router.post("/floors/{floor_id}/edges/{edge_id}/closure", response_model=FloorMapOut)
async def change_closure(
    floor_id: str,
    edge_id: str,
    body: ClosureUpdate,
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_storage),
) -> FloorMapOut:
    venue = await floor_venue(session, floor_id)
    floor = await update_closure_and_publish(session, venue, edge_id, body.temporarily_closed)
    return floor_out(floor, storage)
