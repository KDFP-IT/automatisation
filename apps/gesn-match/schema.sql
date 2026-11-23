-- gesn-match schema: ФСНБ-2022 norms catalog with editions.
-- Applied at service startup (CREATE IF NOT EXISTS idiom, no migration framework).
-- Requires: pg_trgm, unaccent, vector (pgvector image).

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS editions(
  id TEXT PRIMARY KEY,
  base_name TEXT NOT NULL,
  price_level TEXT NOT NULL DEFAULT '',
  creation_date TEXT NOT NULL DEFAULT '',
  decree TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS norms(
  code TEXT NOT NULL,
  collection TEXT NOT NULL,
  table_code TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL,
  unit TEXT NOT NULL DEFAULT '',
  work_composition TEXT[] NOT NULL DEFAULT '{}',
  tech_conditions TEXT[] NOT NULL DEFAULT '{}',
  edition_id TEXT NOT NULL REFERENCES editions(id),
  source_ref TEXT NOT NULL DEFAULT '',
  needs_review BOOLEAN NOT NULL DEFAULT FALSE,
  search_tsv tsvector,
  PRIMARY KEY (code, collection, edition_id)
);
CREATE INDEX IF NOT EXISTS norms_collection_idx ON norms(collection);
CREATE INDEX IF NOT EXISTS norms_edition_idx ON norms(edition_id);
CREATE INDEX IF NOT EXISTS norms_search_gin ON norms USING gin(search_tsv);
CREATE INDEX IF NOT EXISTS norms_code_trgm ON norms USING gin(code gin_trgm_ops);
CREATE INDEX IF NOT EXISTS norms_title_trgm ON norms USING gin(title gin_trgm_ops);

CREATE TABLE IF NOT EXISTS norm_resources(
  norm_code TEXT NOT NULL,
  collection TEXT NOT NULL,
  edition_id TEXT NOT NULL,
  res_code TEXT NOT NULL DEFAULT '',
  res_name TEXT,
  quantity TEXT NOT NULL DEFAULT '',
  res_kind TEXT NOT NULL DEFAULT 'material'
      CHECK (res_kind IN ('labor','machine','material')),
  PRIMARY KEY (norm_code, collection, edition_id, res_code, quantity),
  FOREIGN KEY (norm_code, collection, edition_id)
    REFERENCES norms(code, collection, edition_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS norm_resources_norm_idx
  ON norm_resources(norm_code, collection, edition_id);

CREATE TABLE IF NOT EXISTS norm_embeddings(
  norm_code TEXT NOT NULL,
  collection TEXT NOT NULL,
  edition_id TEXT NOT NULL,
  embedding vector(384) NOT NULL,
  PRIMARY KEY (norm_code, collection, edition_id),
  FOREIGN KEY (norm_code, collection, edition_id)
    REFERENCES norms(code, collection, edition_id) ON DELETE CASCADE
);


-- Read-only analytics role for Metabase (pattern: deploy/metabase/init/02-analytics-ro.sql).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analytics_reader') THEN
    CREATE ROLE analytics_reader LOGIN;
  END IF;
END
$$;
GRANT CONNECT ON DATABASE norms TO analytics_reader;
GRANT USAGE ON SCHEMA public TO analytics_reader;
REVOKE CREATE ON SCHEMA public FROM analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE CURRENT_USER IN SCHEMA public
  GRANT SELECT ON TABLES TO analytics_reader;
