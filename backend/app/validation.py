import math
from collections import Counter

from shapely.geometry import Point, Polygon
from shapely.validation import explain_validity

from app.errors import AppError
from app.models import NodeType
from app.schemas import DraftUpdate


def invalid(message: str) -> None:
    raise AppError(400, "VALIDATION_ERROR", message)


def _require_unique(label: str, values: list[str]) -> None:
    duplicate = next((value for value, count in Counter(values).items() if count > 1), None)
    if duplicate:
        invalid(f"Duplicate {label} id: {duplicate}.")


def _shape(points: list) -> Polygon:
    return Polygon([(point.x, point.y) for point in points])


def validate_draft(data: DraftUpdate, *, for_publish: bool = False) -> None:
    if (
        not math.isfinite(data.width_meters)
        or not math.isfinite(data.height_meters)
        or data.width_meters <= 0
        or data.height_meters <= 0
    ):
        invalid("Scale has not been calibrated.")

    all_polygons = data.walkable_areas + data.obstacles
    _require_unique("polygon", [polygon.id for polygon in all_polygons])
    _require_unique("destination", [item.id for item in data.destinations])
    _require_unique("route node", [item.id for item in data.route_nodes])
    _require_unique("route edge", [item.id for item in data.route_edges])

    shapes: dict[str, Polygon] = {}
    for polygon in all_polygons:
        shape = _shape(polygon.points)
        if shape.area <= 0 or not shape.is_valid or not shape.exterior.is_simple:
            detail = explain_validity(shape)
            invalid(f"Polygon {polygon.id} is invalid: {detail}.")
        for point in polygon.points:
            if not (0 <= point.x <= data.width_meters and 0 <= point.y <= data.height_meters):
                invalid(f"Polygon {polygon.id} lies outside the calibrated floor bounds.")
        shapes[polygon.id] = shape

    if for_publish and not data.walkable_areas:
        invalid("At least one walkable polygon is required.")
    if for_publish and not data.destinations:
        invalid("At least one destination is required.")

    walkable_shapes = [shapes[item.id] for item in data.walkable_areas]
    obstacle_shapes = [shapes[item.id] for item in data.obstacles]
    nodes = {node.id: node for node in data.route_nodes}

    for node in data.route_nodes:
        if not (0 <= node.x <= data.width_meters and 0 <= node.y <= data.height_meters):
            invalid(f"Route node {node.id} lies outside the calibrated floor bounds.")

    directions: set[tuple[str, str]] = set()
    incoming: set[str] = set()
    for edge in data.route_edges:
        if edge.from_node_id not in nodes or edge.to_node_id not in nodes:
            invalid(f"Route edge {edge.id} references a missing node.")
        direction = (edge.from_node_id, edge.to_node_id)
        if direction in directions:
            invalid(f"Duplicate directed edge from {edge.from_node_id} to {edge.to_node_id}.")
        if edge.from_node_id == edge.to_node_id:
            invalid(f"Route edge {edge.id} must connect two different nodes.")
        directions.add(direction)
        incoming.add(edge.to_node_id)

    for destination in data.destinations:
        point = Point(destination.x, destination.y)
        if not any(shape.contains(point) for shape in walkable_shapes):
            invalid(f"Destination {destination.id} must be inside a walkable polygon.")
        if any(shape.covers(point) for shape in obstacle_shapes):
            invalid(f"Destination {destination.id} must be outside every obstacle.")
        node = nodes.get(destination.node_id)
        if node is None:
            invalid(f"Destination {destination.id} references a missing route node.")
        if node.type is not NodeType.DOOR:
            invalid(f"Destination {destination.id} must reference a DOOR node.")
        if math.hypot(node.x - destination.x, node.y - destination.y) > 1.0:
            invalid(f"Destination {destination.id} is more than 1.0 metre from its node.")
        if node.id not in incoming:
            invalid(f"Destination node {node.id} must have an incoming edge.")
