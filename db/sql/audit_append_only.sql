-- Audit trail is append-only (NFR-3):
--   1. application roles have no UPDATE, DELETE or TRUNCATE rights (db_roles.sql);
--   2. triggers reject UPDATE, DELETE and TRUNCATE for every role, the owner included;
--   3. a per-vendor SHA-256 hash chain links each row to the previous one.
-- seq, created_at, prev_hash and hash are always set by the trigger; client values are ignored.

CREATE SEQUENCE IF NOT EXISTS audit_event_seq;

CREATE OR REPLACE FUNCTION audit_payload(a audit_event) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT concat_ws('|', a.seq::text, a.vendor_tenant_id::text,
        to_char(a.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        coalesce(a.actor_id::text, ''), coalesce(a.actor_tenant_id::text, ''), a.actor_name, a.actor_role,
        a.shared_as, a.area, a.action, a.target_type, a.target_id, a.target_label,
        coalesce(a.old_value::text, ''), coalesce(a.new_value::text, ''), a.reason,
        a.is_incident_detail::text, a.is_drill::text,
        coalesce(a.import_id::text, ''), coalesce(a.export_id::text, ''))
$$;

CREATE OR REPLACE FUNCTION audit_event_chain() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    prev text;
BEGIN
    -- Serialise appends per vendor so the chain has no forks.
    PERFORM pg_advisory_xact_lock(hashtextextended('audit:' || NEW.vendor_tenant_id::text, 0));
    SELECT a.hash INTO prev FROM audit_event a
     WHERE a.vendor_tenant_id = NEW.vendor_tenant_id ORDER BY a.seq DESC LIMIT 1;
    NEW.seq := nextval('audit_event_seq');
    NEW.created_at := statement_timestamp();
    NEW.prev_hash := coalesce(prev, '');
    NEW.hash := encode(sha256(convert_to(NEW.prev_hash || '|' || audit_payload(NEW), 'UTF8')), 'hex');
    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION audit_event_reject_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_event is append-only (% rejected)', TG_OP USING ERRCODE = 'insufficient_privilege';
END $$;

DROP TRIGGER IF EXISTS audit_event_chain ON audit_event;
CREATE TRIGGER audit_event_chain BEFORE INSERT ON audit_event
    FOR EACH ROW EXECUTE FUNCTION audit_event_chain();
DROP TRIGGER IF EXISTS audit_event_no_update_delete ON audit_event;
CREATE TRIGGER audit_event_no_update_delete BEFORE UPDATE OR DELETE ON audit_event
    FOR EACH ROW EXECUTE FUNCTION audit_event_reject_change();
DROP TRIGGER IF EXISTS audit_event_no_truncate ON audit_event;
CREATE TRIGGER audit_event_no_truncate BEFORE TRUNCATE ON audit_event
    FOR EACH STATEMENT EXECUTE FUNCTION audit_event_reject_change();

-- Returns the seq of the first row whose hash doesn't verify, or NULL if the chain is intact.
CREATE OR REPLACE FUNCTION audit_verify_chain(tenant uuid) RETURNS bigint
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    r audit_event;
    prev text := '';
BEGIN
    FOR r IN SELECT * FROM audit_event WHERE vendor_tenant_id = tenant ORDER BY seq LOOP
        IF r.prev_hash <> prev
           OR r.hash <> encode(sha256(convert_to(r.prev_hash || '|' || audit_payload(r), 'UTF8')), 'hex') THEN
            RETURN r.seq;
        END IF;
        prev := r.hash;
    END LOOP;
    RETURN NULL;
END $$;

-- QA-09: operator-only (manage.py verify_audit_chain). Vendor sessions can't call it
-- for arbitrary tenant IDs.
REVOKE ALL ON FUNCTION audit_verify_chain(uuid) FROM PUBLIC, app_vendor, app_customer, app_auth;
