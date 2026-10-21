-- Art. 14 integrity guards (D7, D8).
--   * is_drill, vendor_tenant_id, ref_number and started_* can't change after creation;
--   * drills can never be released to a customer or given a customer reference;
--   * stored times are UTC and truncated to the minute;
--   * filing times can't be earlier than awareness (CHECK constraints in the model).

CREATE OR REPLACE FUNCTION art14_event_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.is_drill IS DISTINCT FROM OLD.is_drill THEN
        RAISE EXCEPTION 'is_drill cannot change after creation' USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.vendor_tenant_id IS DISTINCT FROM OLD.vendor_tenant_id
       OR NEW.ref_number IS DISTINCT FROM OLD.ref_number
       OR NEW.started_by_id IS DISTINCT FROM OLD.started_by_id
       OR NEW.started_via IS DISTINCT FROM OLD.started_via
       OR NEW.started_at IS DISTINCT FROM OLD.started_at THEN
        RAISE EXCEPTION 'event identity fields cannot change' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS art14_event_guard ON art14_event;
CREATE TRIGGER art14_event_guard BEFORE UPDATE ON art14_event
    FOR EACH ROW EXECUTE FUNCTION art14_event_guard();

CREATE OR REPLACE FUNCTION art14_no_drill_release() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
    -- PL/pgSQL doesn't short-circuit OR, so only touch NEW.released on the table that has it.
    IF TG_TABLE_NAME = 'art14_users_informed' THEN
        IF NOT NEW.released THEN
            RETURN NEW;
        END IF;
    END IF;
    IF EXISTS (SELECT 1 FROM art14_event e WHERE e.id = NEW.event_id AND e.is_drill) THEN
        RAISE EXCEPTION 'drills cannot be released to customers' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS art14_users_informed_no_drill ON art14_users_informed;
CREATE TRIGGER art14_users_informed_no_drill BEFORE INSERT OR UPDATE ON art14_users_informed
    FOR EACH ROW EXECUTE FUNCTION art14_no_drill_release();
DROP TRIGGER IF EXISTS art14_customer_reference_no_drill ON art14_customer_reference;
CREATE TRIGGER art14_customer_reference_no_drill BEFORE INSERT OR UPDATE ON art14_customer_reference
    FOR EACH ROW EXECUTE FUNCTION art14_no_drill_release();

-- Minute truncation (NFR-4), checked on UTC wall time so it doesn't depend on the session zone.
DO $$
DECLARE
    col text;
BEGIN
    FOREACH col IN ARRAY ARRAY['awareness_at', 'fix_available_at', 'early_warning_filed_at',
                               'notification_filed_at', 'final_report_filed_at']
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'art14_' || col || '_minute') THEN
            EXECUTE format($c$ALTER TABLE art14_event ADD CONSTRAINT %I
                CHECK (%I IS NULL OR date_trunc('minute', %I AT TIME ZONE 'UTC') = (%I AT TIME ZONE 'UTC'))$c$,
                'art14_' || col || '_minute', col, col, col);
        END IF;
    END LOOP;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'art14_informed_at_minute') THEN
        ALTER TABLE art14_users_informed ADD CONSTRAINT art14_informed_at_minute
            CHECK (date_trunc('minute', informed_at AT TIME ZONE 'UTC') = (informed_at AT TIME ZONE 'UTC'));
    END IF;
END $$;

-- QA-02: a closed event's record can't change without reopening it.
-- While OLD.status is closed, the only permitted change is a reopen
-- (status -> 'open', clearing closed_at / close_rationale, bumping row_version).
CREATE OR REPLACE FUNCTION art14_closed_event_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status <> 'open' THEN
        IF (NEW.event_type, NEW.awareness_at, NEW.product_id, NEW.product_version_id, NEW.assigned_responder_id,
            NEW.awaiting_responder, NEW.fix_available_at, NEW.early_warning_filed_at, NEW.notification_filed_at,
            NEW.final_report_filed_at, NEW.awareness_edit_count, NEW.last_recalculated_at)
           IS DISTINCT FROM
           (OLD.event_type, OLD.awareness_at, OLD.product_id, OLD.product_version_id, OLD.assigned_responder_id,
            OLD.awaiting_responder, OLD.fix_available_at, OLD.early_warning_filed_at, OLD.notification_filed_at,
            OLD.final_report_filed_at, OLD.awareness_edit_count, OLD.last_recalculated_at)
           OR (NEW.status <> 'open' AND (NEW.status, NEW.closed_at, NEW.close_rationale)
                                         IS DISTINCT FROM (OLD.status, OLD.closed_at, OLD.close_rationale)) THEN
            RAISE EXCEPTION 'closed event: reopen it first' USING ERRCODE = 'check_violation';
        END IF;
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS art14_closed_event_guard ON art14_event;
CREATE TRIGGER art14_closed_event_guard BEFORE UPDATE ON art14_event
    FOR EACH ROW EXECUTE FUNCTION art14_closed_event_guard();

CREATE OR REPLACE FUNCTION art14_closed_child_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
    ev uuid := CASE WHEN TG_OP = 'DELETE' THEN OLD.event_id ELSE NEW.event_id END;
BEGIN
    IF EXISTS (SELECT 1 FROM art14_event e WHERE e.id = ev AND e.status <> 'open') THEN
        RAISE EXCEPTION 'closed event: reopen it first' USING ERRCODE = 'check_violation';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END $$;

DROP TRIGGER IF EXISTS art14_event_detail_closed_guard ON art14_event_detail;
CREATE TRIGGER art14_event_detail_closed_guard BEFORE INSERT OR UPDATE OR DELETE ON art14_event_detail
    FOR EACH ROW EXECUTE FUNCTION art14_closed_child_guard();
DROP TRIGGER IF EXISTS art14_event_deployment_closed_guard ON art14_event_deployment;
CREATE TRIGGER art14_event_deployment_closed_guard BEFORE INSERT OR UPDATE OR DELETE ON art14_event_deployment
    FOR EACH ROW EXECUTE FUNCTION art14_closed_child_guard();
