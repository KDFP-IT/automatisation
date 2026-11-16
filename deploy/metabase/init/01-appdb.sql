-- 01-appdb.sql — Metabase application database and owner role.
-- Run ONCE as a superuser (e.g. postgres) BEFORE first `docker compose up`:
--
--   psql "host=<pg-host> user=postgres dbname=postgres" \
--     -v app_password='S3CR3T' -f 01-appdb.sql
--
-- The application DB is separate from the business DB: Metabase stores its
-- own users, questions and dashboards here, so a Metabase bug can never
-- touch production tables through this database.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'metabase') THEN
    CREATE ROLE metabase LOGIN;
  END IF;
END
$$;

ALTER ROLE metabase WITH LOGIN PASSWORD :'app_password';

SELECT 'CREATE DATABASE metabase OWNER metabase ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'metabase')\gexec
