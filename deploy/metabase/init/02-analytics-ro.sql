-- 02-analytics-ro.sql — read-only role for the BUSINESS database.
-- Run against EACH business database Metabase may read, as a superuser or
-- the schema owner:
--
--   psql "host=<pg-host> user=postgres dbname=<business>" \
--     -v biz_db='<business>' -v biz_owner='<schema-owner-role>' \
--     -v reader_password='R3AD0NLY' -f 02-analytics-ro.sql
--
-- What this grants, nothing more:
--   CONNECT on the database, USAGE on schema public, SELECT on present and
--   FUTURE tables/views in schema public, plus a read-only default
--   transaction so even an accidental write query fails inside Metabase.
-- Metabase connects with this role, never with an owner/superuser.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analytics_reader') THEN
    CREATE ROLE analytics_reader LOGIN;
  END IF;
END
$$;

ALTER ROLE analytics_reader WITH LOGIN PASSWORD :'reader_password';
ALTER ROLE analytics_reader SET default_transaction_read_only = on;

GRANT CONNECT ON DATABASE :"biz_db" TO analytics_reader;
GRANT USAGE ON SCHEMA public TO analytics_reader;
REVOKE CREATE ON SCHEMA public FROM analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE :"biz_owner" IN SCHEMA public
  GRANT SELECT ON TABLES TO analytics_reader;

-- If the business DB later needs a restricted analytics surface instead of
-- raw public-schema access, add an `analytics` schema with views and grant
-- SELECT on it the same way, e.g.:
--
--   CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION :"biz_owner";
--   CREATE OR REPLACE VIEW analytics.orders AS
--     SELECT id, created_at, total FROM public.orders;
--   GRANT USAGE ON SCHEMA analytics TO analytics_reader;
--   GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO analytics_reader;
--   ALTER DEFAULT PRIVILEGES FOR ROLE :"biz_owner" IN SCHEMA analytics
--     GRANT SELECT ON TABLES TO analytics_reader;
