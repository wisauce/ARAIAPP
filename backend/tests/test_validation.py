from copy import deepcopy

import pytest

from app.errors import AppError
from app.schemas import DraftUpdate
from app.validation import validate_draft


def test_destination_outside_walkable_area_is_rejected(valid_draft: dict) -> None:
    payload = deepcopy(valid_draft)
    payload["destinations"][0]["x"] = 11.0
    with pytest.raises(AppError, match="walkable polygon") as raised:
        validate_draft(DraftUpdate.model_validate(payload))
    assert raised.value.status_code == 400


def test_destination_snap_over_one_metre_is_rejected(valid_draft: dict) -> None:
    payload = deepcopy(valid_draft)
    payload["destinations"][0]["x"] = 3.0
    with pytest.raises(AppError, match="more than 1.0 metre"):
        validate_draft(DraftUpdate.model_validate(payload))


def test_duplicate_directed_edge_is_rejected(valid_draft: dict) -> None:
    payload = deepcopy(valid_draft)
    duplicate = deepcopy(payload["routeEdges"][0])
    duplicate["id"] = "e3"
    payload["routeEdges"].append(duplicate)
    with pytest.raises(AppError, match="Duplicate directed edge"):
        validate_draft(DraftUpdate.model_validate(payload))


def test_publish_requires_walkable_area_and_destination() -> None:
    empty = DraftUpdate(
        width_meters=10,
        height_meters=5,
        walkable_areas=[],
        obstacles=[],
        destinations=[],
        route_nodes=[],
        route_edges=[],
    )
    with pytest.raises(AppError, match="walkable polygon"):
        validate_draft(empty, for_publish=True)
