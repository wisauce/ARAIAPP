from copy import deepcopy

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import FloorVersion, MapStatus, Venue


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def create_floor(
    client: AsyncClient,
    png_bytes: bytes,
) -> tuple[str, str]:
    venue_response = await client.post("/v1/venues", json={"name": "Main building"})
    assert venue_response.status_code == 201
    venue_id = venue_response.json()["id"]
    upload_response = await client.post(
        f"/v1/venues/{venue_id}/floor-plan",
        files={"file": ("plan.png", png_bytes, "image/png")},
    )
    assert upload_response.status_code == 200
    return venue_id, upload_response.json()["floorId"]


@pytest.mark.asyncio
async def test_manager_can_publish_and_visitors_only_see_published(
    client: AsyncClient,
    png_bytes: bytes,
    valid_draft: dict,
) -> None:
    venue_id, floor_id = await create_floor(client, png_bytes)

    listed = (await client.get("/v1/venues")).json()
    assert listed[0]["id"] == venue_id
    assert listed[0]["publishedVersion"] is None
    assert (await client.get(f"/v1/venues/{venue_id}")).status_code == 200
    assert (await client.get(f"/v1/venues/{venue_id}")).json()["publishedVersion"] is None
    uncalibrated = await client.get(f"/v1/floors/{floor_id}/draft")
    assert uncalibrated.status_code == 200
    assert uncalibrated.json()["widthMeters"] is None

    saved = await client.put(
        f"/v1/floors/{floor_id}/draft",
        json=valid_draft,
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["status"] == "DRAFT"
    assert saved.json()["routeEdges"][0]["distanceMeters"] == 8.0

    published = await client.post(f"/v1/floors/{floor_id}/publish")
    assert published.status_code == 200, published.text
    package = published.json()
    assert package["version"] == 1
    assert package["status"] == "PUBLISHED"
    assert package["imageUrl"].startswith("https://objects.test/")

    public_map = await client.get(f"/v1/venues/{venue_id}/published-map")
    assert public_map.status_code == 200
    assert public_map.json()["version"] == 1
    assert (await client.get("/v1/venues")).json()[0]["publishedVersion"] == 1

    unchanged = await client.post(f"/v1/floors/{floor_id}/publish")
    assert unchanged.status_code == 409
    assert unchanged.json() == {
        "code": "PUBLISH_CONFLICT",
        "message": "The draft has no changes to publish.",
    }


@pytest.mark.asyncio
async def test_closure_publishes_new_immutable_version(
    client: AsyncClient,
    png_bytes: bytes,
    valid_draft: dict,
    session_factory,
) -> None:
    venue_id, floor_id = await create_floor(client, png_bytes)
    await client.put(f"/v1/floors/{floor_id}/draft", json=valid_draft)
    await client.post(f"/v1/floors/{floor_id}/publish")

    response = await client.post(
        f"/v1/floors/{floor_id}/edges/e1/closure",
        json={"temporarilyClosed": True},
    )
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2
    assert next(edge for edge in response.json()["routeEdges"] if edge["id"] == "e1")[
        "temporarilyClosed"
    ]

    async with session_factory() as session:
        rows = list(
            await session.scalars(
                select(FloorVersion)
                .where(FloorVersion.status == MapStatus.PUBLISHED)
                .order_by(FloorVersion.version)
            )
        )
        assert [row.version for row in rows] == [1, 2]
        assert not next(edge for edge in rows[0].route_edges if edge.id == "e1").temporarily_closed
        venue = await session.scalar(select(Venue).where(Venue.id == venue_id))
        assert venue is not None and venue.published_version == 2


@pytest.mark.asyncio
async def test_validation_and_error_envelope(
    client: AsyncClient,
    png_bytes: bytes,
    valid_draft: dict,
) -> None:
    _, floor_id = await create_floor(client, png_bytes)
    invalid = deepcopy(valid_draft)
    invalid["walkableAreas"][0]["points"] = [
        {"x": 0, "y": 0},
        {"x": 10, "y": 5},
        {"x": 0, "y": 5},
        {"x": 10, "y": 0},
    ]
    response = await client.put(
        f"/v1/floors/{floor_id}/draft",
        json=invalid,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "invalid" in response.json()["message"]

    bad_scale = deepcopy(valid_draft)
    bad_scale["heightMeters"] = 6.0
    response = await client.put(
        f"/v1/floors/{floor_id}/draft",
        json=bad_scale,
    )
    assert response.status_code == 400
    assert "aspect ratio" in response.json()["message"]

    malformed = await client.post("/v1/venues", json={"name": ""})
    assert malformed.status_code == 400
    assert set(malformed.json()) == {"code", "message"}


@pytest.mark.asyncio
async def test_floor_plan_rejects_non_image(
    client: AsyncClient,
) -> None:
    venue = await client.post("/v1/venues", json={"name": "Main"})
    response = await client.post(
        f"/v1/venues/{venue.json()['id']}/floor-plan",
        files={"file": ("plan.pdf", b"%PDF-1.7", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_framework_404_uses_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"code": "NOT_FOUND", "message": "Not Found"}
