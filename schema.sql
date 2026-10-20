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

-- ---------- Security findings (Provably Secure changelog) ----------
-- One row per vulnerability found in our own hardened database, from any
-- channel. Timestamps are ISO 8601 UTC, e.g. '2026-10-20T14:05:00Z'.
-- 'description' is internal triage detail and is never published;
-- 'public_summary' is the only free text that reaches security_changelog.

CREATE TABLE finding (
    id                      INTEGER PRIMARY KEY,
    finding_code            TEXT UNIQUE NOT NULL,  -- e.g. 'F1'
    title                   TEXT NOT NULL,
    description             TEXT,                  -- internal only
    public_summary          TEXT,                  -- required before disclosure
    affected_component      TEXT,
    cvss_version            TEXT CHECK (cvss_version IN ('3.1','4.0')),
    cvss_vector             TEXT,
    cvss_score              REAL CHECK (cvss_score BETWEEN 0 AND 10),
    discovery_channel       TEXT NOT NULL CHECK (discovery_channel IN
                                ('internal','private_pentest','invite_only_bounty','public_bounty','external_report')),
    actively_exploited      INTEGER NOT NULL DEFAULT 0 CHECK (actively_exploited IN (0,1)),  -- 1 triggers CRA Art. 14 reporting
    status                  TEXT NOT NULL CHECK (status IN
                                ('reported','triaged','fixing','fixed','disclosed','rejected','duplicate')),
    risk_id                 INTEGER REFERENCES risk(id),  -- optional link back to the matrix's risk taxonomy
    reported_at             TEXT NOT NULL,         -- when we became aware: starts the CRA clock
    triaged_at              TEXT,
    fix_available_at        TEXT,                  -- corrective/mitigating measure available: starts the 14-day final-report clock
    disclosed_at            TEXT,
    cra_early_warning_at    TEXT,                  -- due within 24h of reported_at
    cra_notification_at     TEXT,                  -- due within 72h of reported_at
    cra_final_report_at     TEXT,                  -- due within 14 days of fix_available_at
    CHECK (triaged_at       IS NULL OR julianday(triaged_at)       >= julianday(reported_at)),
    CHECK (fix_available_at IS NULL OR julianday(fix_available_at) >= julianday(reported_at)),
    CHECK (disclosed_at     IS NULL OR julianday(disclosed_at)     >= julianday(reported_at)),
    CHECK (disclosed_at IS NULL OR public_summary IS NOT NULL),
    CHECK (status <> 'disclosed' OR disclosed_at IS NOT NULL),
    CHECK (status NOT IN ('fixed','disclosed') OR fix_available_at IS NOT NULL)
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

-- ---------- Read-side views for the security changelog ----------

-- Public changelog: disclosed findings only, public fields only.
-- Severity uses the CVSS qualitative rating scale (same bands in 3.1 and 4.0).
CREATE VIEW security_changelog AS
SELECT
    f.finding_code,
    f.disclosed_at,
    CASE
        WHEN f.cvss_score IS NULL THEN NULL
        WHEN f.cvss_score = 0     THEN 'none'
        WHEN f.cvss_score < 4     THEN 'low'
        WHEN f.cvss_score < 7     THEN 'medium'
        WHEN f.cvss_score < 9     THEN 'high'
        ELSE 'critical'
    END                     AS severity,
    f.cvss_version,
    f.cvss_score,
    f.cvss_vector,
    f.affected_component,
    f.public_summary,
    f.discovery_channel,
    f.reported_at,
    f.fix_available_at,
    ROUND(julianday(f.fix_available_at) - julianday(f.reported_at), 1) AS days_to_fix
FROM finding f
WHERE f.disclosed_at IS NOT NULL
ORDER BY f.disclosed_at DESC;

-- CRA Art. 14 deadline tracking for actively exploited vulnerabilities.
-- Each *_state is 'met', 'late', 'open' (due, not yet passed), 'overdue',
-- or 'not started' (final report only: no fix available yet).
CREATE VIEW cra_deadline_check AS
WITH d AS (
    SELECT
        finding_code,
        status,
        reported_at,
        cra_early_warning_at,
        strftime('%Y-%m-%dT%H:%M:%SZ', reported_at, '+24 hours') AS early_warning_due,
        cra_notification_at,
        strftime('%Y-%m-%dT%H:%M:%SZ', reported_at, '+72 hours') AS notification_due,
        cra_final_report_at,
        strftime('%Y-%m-%dT%H:%M:%SZ', fix_available_at, '+14 days') AS final_report_due
    FROM finding
    WHERE actively_exploited = 1
)
SELECT
    d.*,
    CASE
        WHEN cra_early_warning_at IS NOT NULL THEN
            CASE WHEN julianday(cra_early_warning_at) <= julianday(early_warning_due) THEN 'met' ELSE 'late' END
        WHEN julianday('now') > julianday(early_warning_due) THEN 'overdue'
        ELSE 'open'
    END AS early_warning_state,
    CASE
        WHEN cra_notification_at IS NOT NULL THEN
            CASE WHEN julianday(cra_notification_at) <= julianday(notification_due) THEN 'met' ELSE 'late' END
        WHEN julianday('now') > julianday(notification_due) THEN 'overdue'
        ELSE 'open'
    END AS notification_state,
    CASE
        WHEN final_report_due IS NULL THEN 'not started'
        WHEN cra_final_report_at IS NOT NULL THEN
            CASE WHEN julianday(cra_final_report_at) <= julianday(final_report_due) THEN 'met' ELSE 'late' END
        WHEN julianday('now') > julianday(final_report_due) THEN 'overdue'
        ELSE 'open'
    END AS final_report_state
FROM d;
