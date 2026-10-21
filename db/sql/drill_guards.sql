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
