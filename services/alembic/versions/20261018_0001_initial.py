"""Initial analyses, deletion outbox, audit, idempotency.

Revision ID: 20261018_0001
Revises:
Create Date: 2026-10-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261018_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stage", sa.String(64), nullable=True),
        sa.Column("progress", sa.Float(), nullable=True),
        sa.Column("message_key", sa.String(128), nullable=True),
        sa.Column("stroke", sa.String(64), nullable=False),
        sa.Column("handedness", sa.String(16), nullable=False),
        sa.Column("view_hint", sa.String(64), nullable=False),
        sa.Column("consent", sa.Boolean(), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("source_object_key", sa.String(1024), nullable=False),
        sa.Column("upload_completed", sa.Boolean(), nullable=False),
        sa.Column("result_json", postgresql.JSONB(), nullable=True),
        sa.Column("pipeline_version", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "deletion_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_deletion_outbox_analysis_id", "deletion_outbox", ["analysis_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event", sa.String(128), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_analysis_id", "audit_events", ["analysis_id"])
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("route", sa.String(128), primary_key=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_index("ix_audit_events_analysis_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_deletion_outbox_analysis_id", table_name="deletion_outbox")
    op.drop_table("deletion_outbox")
    op.drop_table("analyses")
