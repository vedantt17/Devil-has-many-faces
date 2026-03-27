CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    corpus      TEXT NOT NULL,
    filename    TEXT NOT NULL UNIQUE,
    source_url  TEXT,
    file_path   TEXT,
    page_count  INTEGER DEFAULT 0,
    date_filed  TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- Entities extracted by spaCy NER
CREATE TABLE IF NOT EXISTS entities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(name, type)
);

-- Every mention of an entity in a document
CREATE TABLE IF NOT EXISTS mentions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id   INTEGER NOT NULL REFERENCES entities(id),
    doc_id      TEXT NOT NULL REFERENCES documents(id),
    page_num    INTEGER NOT NULL,
    context     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- Redaction data per page
CREATE TABLE IF NOT EXISTS redactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id          TEXT NOT NULL REFERENCES documents(id),
    page_num        INTEGER NOT NULL,
    redaction_count INTEGER DEFAULT 0,
    estimated_chars INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Changelog of ingestion runs
CREATE TABLE IF NOT EXISTS releases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus          TEXT NOT NULL,
    run_date        TEXT DEFAULT (datetime('now')),
    docs_added      INTEGER DEFAULT 0,
    entities_found  INTEGER DEFAULT 0,
    notes           TEXT
);

-- Full text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    doc_id,
    page_num,
    text,
    content='',
    tokenize='porter ascii'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_mentions_entity ON mentions(entity_id);
CREATE INDEX IF NOT EXISTS idx_mentions_doc ON mentions(doc_id);
CREATE INDEX IF NOT EXISTS idx_redactions_doc ON redactions(doc_id);
CREATE INDEX IF NOT EXISTS idx_documents_corpus ON documents(corpus);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);