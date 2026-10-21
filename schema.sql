-- ============================================================
-- Regtech Cybersecurity Decision Tool — normalized schema (SQLite)
-- Core entities: risk, innovation, mitigation, regulation, sector, source
-- Junction tables express all many-to-many relationships.
-- Populated so far: risk, innovation, risk_innovation (Chapters 1-2);
-- mitigation, risk_mitigation, mitigation_barrier (Chapter 11); source plus
-- all *_source junctions (citation numbers only). regulation, sector,
-- risk_sector, mitigation_regulation and mitigation_innovation are
-- schema-only, awaiting Appendix G and the curated regulation overlay.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------- Core entities ----------

CREATE TABLE risk (
    id              INTEGER PRIMARY KEY,
    risk_code       TEXT UNIQUE NOT NULL,      -- e.g. 'R1', stable human-readable key
    name            TEXT NOT NULL,
    description     TEXT,
    category        TEXT,                      -- taxonomy value, not an enum -- see 'taxonomy' note below
    source_chapter  INTEGER
);

CREATE TABLE innovation (
    id                  INTEGER PRIMARY KEY,
    innovation_code     TEXT UNIQUE NOT NULL,  -- e.g. 'I1'
    name                TEXT NOT NULL,
    technique_category  TEXT,
    description         TEXT,
    quantified_result   TEXT,
    dual_use_flag       INTEGER NOT NULL DEFAULT 0 CHECK (dual_use_flag IN (0,1)),
    dual_use_note       TEXT,                  -- metadata only, per decision -- no separate dual-use table
    source_chapter      INTEGER
);

CREATE TABLE mitigation (
    id                  INTEGER PRIMARY KEY,
    mitigation_code     TEXT UNIQUE NOT NULL,  -- e.g. 'M1'
    name                TEXT NOT NULL,
    description         TEXT,
    category            TEXT,                  -- technical / organizational / process
    maturity_level      TEXT,
    effort_tier         TEXT,
    source_chapter      INTEGER,
    valid_from          TEXT,                  -- effective-dating: guards against presenting stale guidance as current
    valid_to            TEXT,
    superseded_by_id    INTEGER REFERENCES mitigation(id)
);

CREATE TABLE regulation (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,         -- e.g. 'GDPR', 'AI Act', 'NIS2', 'CRA'
    jurisdiction        TEXT,
    article_ref         TEXT,
    effective_date      TEXT,
    valid_to            TEXT,
    superseded_by_id    INTEGER REFERENCES regulation(id),
    notes               TEXT
);

CREATE TABLE sector (
    id      INTEGER PRIMARY KEY,
    name    TEXT UNIQUE NOT NULL              -- e.g. 'ticketing/live events', 'HR-tech/recruitment AI'
);

CREATE TABLE source (
    id          INTEGER PRIMARY KEY,
    ref_number  INTEGER UNIQUE NOT NULL,       -- matches the book's numbered citations, e.g. [45]
    citation    TEXT,                          -- filled in once Appendix G is extracted
    year        INTEGER,
    url         TEXT
);

-- ---------- Junction tables (many-to-many) ----------

CREATE TABLE risk_innovation (
    risk_id         INTEGER NOT NULL REFERENCES risk(id),
    innovation_id   INTEGER NOT NULL REFERENCES innovation(id),
    PRIMARY KEY (risk_id, innovation_id)
);

CREATE TABLE risk_mitigation (
    risk_id             INTEGER NOT NULL REFERENCES risk(id),
    mitigation_id       INTEGER NOT NULL REFERENCES mitigation(id),
    mitigation_status   TEXT,                  -- 'on track' / 'poor' / 'in progress, less than sufficient' -- from Ch.11's status table (current mitigations only)
    contingency_status  TEXT,                  -- 'not required' / 'poor' / 'not applicable'
    comments            TEXT,
    PRIMARY KEY (risk_id, mitigation_id)
);

CREATE TABLE mitigation_barrier (
    id              INTEGER PRIMARY KEY,
    barrier_code    TEXT UNIQUE NOT NULL,      -- e.g. 'B1'
    description     TEXT NOT NULL              -- systemic reason a mitigation may fail to hold -- distinct from Risk (a threat) and Mitigation (a countermeasure)
);

CREATE TABLE mitigation_barrier_source (
    barrier_id  INTEGER NOT NULL REFERENCES mitigation_barrier(id),
    source_id   INTEGER NOT NULL REFERENCES source(id),
    PRIMARY KEY (barrier_id, source_id)
);

CREATE TABLE mitigation_innovation (
    mitigation_id   INTEGER NOT NULL REFERENCES mitigation(id),
    innovation_id   INTEGER NOT NULL REFERENCES innovation(id),
    PRIMARY KEY (mitigation_id, innovation_id)
);

CREATE TABLE mitigation_regulation (
    mitigation_id   INTEGER NOT NULL REFERENCES mitigation(id),
    regulation_id   INTEGER NOT NULL REFERENCES regulation(id),
    PRIMARY KEY (mitigation_id, regulation_id)
);

CREATE TABLE risk_sector (
    risk_id     INTEGER NOT NULL REFERENCES risk(id),
    sector_id   INTEGER NOT NULL REFERENCES sector(id),
    PRIMARY KEY (risk_id, sector_id)
);

CREATE TABLE risk_source (
    risk_id     INTEGER NOT NULL REFERENCES risk(id),
    source_id   INTEGER NOT NULL REFERENCES source(id),
    PRIMARY KEY (risk_id, source_id)
);

CREATE TABLE innovation_source (
    innovation_id   INTEGER NOT NULL REFERENCES innovation(id),
    source_id       INTEGER NOT NULL REFERENCES source(id),
    PRIMARY KEY (innovation_id, source_id)
);

CREATE TABLE mitigation_source (
    mitigation_id   INTEGER NOT NULL REFERENCES mitigation(id),
    source_id       INTEGER NOT NULL REFERENCES source(id),
    PRIMARY KEY (mitigation_id, source_id)
);

-- ---------- Read-side view for the searchable matrix UI ----------
-- Denormalized join, generated from the normalized tables above --
-- this is what the search/filter interface actually queries against.

CREATE VIEW matrix_view AS
SELECT
    r.risk_code,
    r.name              AS risk_name,
    r.category          AS risk_category,
    i.innovation_code,
    i.name              AS innovation_name,
    i.technique_category,
    i.dual_use_flag,
    i.quantified_result
FROM risk r
LEFT JOIN risk_innovation ri ON ri.risk_id = r.id
LEFT JOIN innovation i ON i.id = ri.innovation_id;
