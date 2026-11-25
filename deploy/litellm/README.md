# LiteLLM gateway for Open WebUI

Open WebUI → LiteLLM `127.0.0.1:4000` → RouterAI.
LiteLLM exports OTLP/HTTP traces to the existing Phoenix
`192.168.30.183:6006/v1/traces`, project `kdfp-openwebui`.

## Deploy

Run from this directory on `vor-smeta` as `nikita_g`:

```sh
cp .env.example .env
chmod 600 .env
# Generate LITELLM_MASTER_KEY, LITELLM_SALT_KEY and POSTGRES_PASSWORD with:
# openssl rand -hex 32
# Set ROUTERAI_API_KEY to an existing provider key with chat-completions access.
docker compose config --quiet
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1:4000/health/liveliness
```

The proxy and PostgreSQL have no LAN-published ports. PostgreSQL state is
the named volume `litellm_postgres_data`. Back up both `.env` and that volume;
losing `LITELLM_SALT_KEY` makes provider credentials stored by LiteLLM
unreadable.

`GET /models` alone does not prove provider key validity; verify one real
`/chat/completions` request before cutting over Open WebUI.

## Open WebUI

1. Create a LiteLLM virtual key restricted to `tencent/hy4-flash` in the
   Admin UI (`ssh -L 4000:127.0.0.1:4000 nikita_g@192.168.30.183`, then
   `http://127.0.0.1:4000/ui`). Username: `admin`; password:
   `LITELLM_MASTER_KEY`.
2. Copy `open-webui.env.example` to
   `~/.config/systemd/user/open-webui-litellm.env`, set the virtual key and
   `chmod 600` the file.
3. Add `~/.config/systemd/user/open-webui.service.d/litellm.conf`:

   ```ini
   [Service]
   EnvironmentFile=%h/.config/systemd/user/open-webui-litellm.env
   ```

4. Open WebUI persists connection settings in `webui.db`. In **Admin Panel →
   Settings → Connections**, set the OpenAI URL to
   `http://127.0.0.1:4000/v1` and the key to the virtual key. Environment
   variables alone do not override existing `ConfigVar` values.
5. Restart and verify:

   ```sh
   systemctl --user daemon-reload
   systemctl --user restart open-webui
   systemctl --user is-active open-webui
   ```

`ENABLE_FORWARD_USER_INFO_HEADERS=true` sends `X-OpenWebUI-User-Id`;
`config.yaml` maps it to LiteLLM's internal user for spend attribution.

## Phoenix

Open `http://192.168.30.183:6006/` and select project `kdfp-openwebui`.
Self-hosted Phoenix needs no API key. The collector URL must be reachable
from inside the LiteLLM container; `localhost` there would mean the container,
not the VPS. This deployment uses the VPS LAN address deliberately.

## Smoke test

```sh
set -a
. ./.env
. "$HOME/.config/systemd/user/open-webui-litellm.env"
set +a
curl -fsS http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"tencent/hy4-flash","messages":[{"role":"user","content":"Reply with exactly OK"}],"max_tokens":256}'
```

Then confirm the request in LiteLLM logs and Phoenix. The smoke test makes one
real RouterAI model call and consumes provider quota.

## Operations

```sh
docker compose logs -f litellm
docker compose pull
docker compose up -d
```

Update the pinned image digest in `compose.yaml` only after testing the new
release. Roll back Open WebUI by removing the `litellm.conf` drop-in, restoring
the previous connection in Admin Panel, and restarting `open-webui`.

References:
- https://docs.litellm.ai/docs/tutorials/openweb_ui
- https://docs.litellm.ai/docs/observability/phoenix_integration
- https://docs.openwebui.com/reference/env-configuration
