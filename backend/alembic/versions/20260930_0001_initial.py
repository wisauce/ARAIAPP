"""Initial Araiap schema.

Revision ID: 20260930_0001
Revises:
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "venues",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("floor_id", sa.String(40)),
        sa.Column("published_version", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("floor_id", name="uq_venues_floor_id"),
    )

    op.create_table(
        "floor_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("floor_id", sa.String(40), nullable=False),
        sa.Column("venue_id", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="mapstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("image_key", sa.String(500), nullable=False),
        sa.Column("image_content_type", sa.String(50), nullable=False),
        sa.Column("width_pixels", sa.Integer(), nullable=False),
        sa.Column("height_pixels", sa.Integer(), nullable=False),
        sa.Column("width_meters", sa.Float()),
        sa.Column("height_meters", sa.Float()),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "venue_id", "version", "status", name="uq_floor_versions_venue_version_status"
        ),
    )
    op.create_index("ix_floor_versions_floor_id", "floor_versions", ["floor_id"])
    op.create_index(
        "ix_floor_versions_floor_status", "floor_versions", ["floor_id", "status"]
    )
    op.create_index("ix_floor_versions_venue_id", "floor_versions", ["venue_id"])

    op.create_table(
        "polygons",
        sa.Column("floor_version_id", sa.Integer(), primary_key=True),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column(
            "kind",
            sa.Enum("WALKABLE", "OBSTACLE", name="polygonkind", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "points",
            geoalchemy2.Geometry("POLYGON", srid=-1, spatial_index=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["floor_version_id"], ["floor_versions.id"], ondelete="CASCADE"
        ),
    )
    op.create_table(
        "destinations",
        sa.Column("floor_version_id", sa.Integer(), primary_key=True),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("node_id", sa.String(80), nullable=False),
        sa.ForeignKeyConstraint(
            ["floor_version_id"], ["floor_versions.id"], ondelete="CASCADE"
        ),
    )
    op.create_table(
        "route_nodes",
        sa.Column("floor_version_id", sa.Integer(), primary_key=True),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "INTERSECTION", "DOOR", "ENDPOINT", name="nodetype", native_enum=False
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["floor_version_id"], ["floor_versions.id"], ondelete="CASCADE"
        ),
    )
    op.create_table(
        "route_edges",
        sa.Column("floor_version_id", sa.Integer(), primary_key=True),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("from_node_id", sa.String(80), nullable=False),
        sa.Column("to_node_id", sa.String(80), nullable=False),
        sa.Column("distance_meters", sa.Float(), nullable=False),
        sa.Column("accessible", sa.Boolean(), nullable=False),
        sa.Column("temporarily_closed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["floor_version_id"], ["floor_versions.id"], ondelete="CASCADE"
        ),
    )


def downgrade() -> None:
    op.drop_table("route_edges")
    op.drop_table("route_nodes")
    op.drop_table("destinations")
    op.drop_table("polygons")
    op.drop_index("ix_floor_versions_venue_id", table_name="floor_versions")
    op.drop_index("ix_floor_versions_floor_status", table_name="floor_versions")
    op.drop_index("ix_floor_versions_floor_id", table_name="floor_versions")
    op.drop_table("floor_versions")
    op.drop_table("venues")
