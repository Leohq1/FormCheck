CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE coaching_source (
    source_id text PRIMARY KEY,
    title text NOT NULL,
    author text NOT NULL,
    publisher text NOT NULL,
    publication_date text NOT NULL,
    license text NOT NULL,
    allowed_use text NOT NULL,
    stroke_tags text[] NOT NULL,
    fault_tags text[] NOT NULL,
    phase_tags text[] NOT NULL DEFAULT '{}',
    review_status text NOT NULL,
    reviewer text NOT NULL,
    review_date text NOT NULL,
    content_hash text NOT NULL,
    corpus_version text NOT NULL
);

CREATE TABLE coaching_chunk (
    chunk_id text PRIMARY KEY,
    source_id text NOT NULL REFERENCES coaching_source (source_id),
    locator text NOT NULL,
    text_content text NOT NULL,
    stroke_tags text[] NOT NULL,
    fault_tags text[] NOT NULL,
    phase_tags text[] NOT NULL DEFAULT '{}',
    review_status text NOT NULL,
    corpus_version text NOT NULL,
    embedding vector(1536),
    embedding_model text
);

CREATE INDEX coaching_chunk_embedding_hnsw
    ON coaching_chunk
    USING hnsw (embedding vector_cosine_ops);
