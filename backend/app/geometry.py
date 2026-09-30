import json
from typing import Any

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement, WKTElement
from shapely import wkb, wkt
from shapely.geometry import Polygon
from sqlalchemy import Text
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class PolygonGeometry(TypeDecorator[list[list[float]]]):
    """PostGIS polygon in production, JSON coordinates in SQLite tests."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geometry("POLYGON", srid=-1, spatial_index=False))
        return dialect.type_descriptor(Text())

    def process_bind_param(
        self, value: list[list[float]] | None, dialect: Dialect
    ) -> str | WKTElement | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return WKTElement(Polygon(value).wkt, srid=-1)
        return json.dumps(value, separators=(",", ":"))

    def process_result_value(
        self, value: str | WKBElement | None, dialect: Dialect
    ) -> list[list[float]] | None:
        if value is None:
            return None
        if dialect.name != "postgresql":
            return json.loads(value)
        shape = wkb.loads(bytes(value.data)) if isinstance(value, WKBElement) else wkt.loads(value)
        return [[float(x), float(y)] for x, y in list(shape.exterior.coords)[:-1]]
