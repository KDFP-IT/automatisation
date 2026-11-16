# Metabase (self-hosted business analytics)

Reads the business PostgreSQL through a read-only role; its own state lives
in a separate `metabase` application database. Published on its own
subdomain over HTTPS, bound to localhost on the box.

## 0. Preflight (decide before starting)

| Check | Command / question | Minimum |
| --- | --- | --- |
| Docker | `docker --version && docker compose version` | Docker 24+ |
| PostgreSQL | `SELECT version();` on the VPS instance | 12+ |
| Free RAM | `free -g` | ~2 GB for the container (`-Xmx2g` needs ~3 GB on the box) |
| Hostname | pick the subdomain, e.g. `bi.<domain>` | reverse-proxy slot + certificate |
| Analytics surface | raw `public` schema or restricted `analytics` views | see `init/02-analytics-ro.sql` |

Metabase is NOT embedded in the portal iframe: it has its own auth and
needs a top-level host (its login flow breaks under `frame-ancestors`).

## 1. Application DB

```sh
psql "host=<pg-host> user=postgres dbname=postgres" \
  -v app_password='S3CR3T' -f init/01-appdb.sql
```

## 2. Read-only business access

Per business database:

```sh
psql "host=<pg-host> user=postgres dbname=<business>" \
  -v biz_db='<business>' -v biz_owner='<schema-owner-role>' \
  -v reader_password='R3AD0NLY' -f init/02-analytics-ro.sql
```

Verify the role cannot write (expect `42501`):

```sql
SET ROLE analytics_reader;
CREATE TABLE public.probe(id int);  -- must fail: permission denied
RESET ROLE;
```

## 3. Start

```sh
cp .env.example .env   # fill in real values; .env is gitignored
docker compose up -d
docker compose ps      # healthy after a few minutes (first start migrates)
```

Open `https://<metabase-host>/`, create the first admin, then
Settings → Admin → Databases → Add: PostgreSQL with host/port/db/user from
step 2 (`analytics_reader`).

## 4. First dashboard + backup

1. New → Question on the business database, save to a dashboard, confirm
   real rows render.
2. Take the first app-DB dump the same day:

```sh
MB_DB_HOST=<pg-host> BACKUP_DIR=/var/backups/metabase ./backup-metabase.sh
```

Schedule the cron line from the script header afterwards.

## Operations

- Restore: commented `pg_restore` one-liner in `backup-metabase.sh`;
  `MB_ENCRYPTION_SECRET_KEY` must match the dump or saved DB credentials
  are unreadable.
- Upgrade: back up, bump the image tag in `compose.yaml`,
  `docker compose pull && docker compose up -d`.
- Logs: `docker compose logs -f metabase`.
