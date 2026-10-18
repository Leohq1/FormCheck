"""Coaching corpus tables for local retrieval.

Revision ID: 20261018_0002
Revises: 20261018_0001
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20261018_0002"
down_revision: Union[str, None] = "20261018_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS coaching_source (
            source_id text PRIMARY KEY,
            title text NOT NULL,
            author text NOT NULL,
            publisher text NOT NULL,
            publication_date text NOT NULL,
            license text NOT NULL,
            allowed_use text NOT NULL,
            source_version text NOT NULL,
            stroke_tags text[] NOT NULL,
            fault_tags text[] NOT NULL,
            phase_tags text[] NOT NULL DEFAULT '{}',
            body_region_tags text[] NOT NULL,
            audience text NOT NULL,
            skill_level text NOT NULL,
            page_locator text NOT NULL,
            review_status text NOT NULL,
            reviewer text NOT NULL,
            review_date text NOT NULL,
            content_hash text NOT NULL,
            corpus_version text NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS coaching_chunk (
            chunk_id text PRIMARY KEY,
            source_id text NOT NULL REFERENCES coaching_source (source_id),
            locator text NOT NULL,
            text_content text NOT NULL,
            source_version text NOT NULL,
            stroke_tags text[] NOT NULL,
            fault_tags text[] NOT NULL,
            phase_tags text[] NOT NULL DEFAULT '{}',
            body_region_tags text[] NOT NULL,
            audience text NOT NULL,
            skill_level text NOT NULL,
            page_locator text NOT NULL,
            review_status text NOT NULL,
            corpus_version text NOT NULL,
            embedding vector(1536),
            embedding_model text
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS coaching_chunk")
    op.execute("DROP TABLE IF EXISTS coaching_source")
