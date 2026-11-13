# Рабочее место

Соберите нужные образы командами из корневого README. Для локального запуска всех инструментов из `deploy/portal` задайте в `.env` теги:

```dotenv
PORTAL_IMAGE=kdfp-portal-shell:local
BOOKMARKS_IMAGE=kdfp-portal-bookmarks:local
SIGNATURES_IMAGE=kdfp-portal-signatures:local
TRENCH_IMAGE=kdfp-portal-trench:local
KAC_IMAGE=kdfp-portal-kac:local
```

```sh
docker compose -f compose.yaml -f compose.kac-linux.yaml up -d
```

Портал доступен на `http://127.0.0.1:8090/`. Чтобы обновить только КАЦ, укажите новый `KAC_IMAGE` и выполните:

```sh
docker compose -f compose.yaml -f compose.kac-linux.yaml up -d --no-deps kac
```

Для нового инструмента с собственным адресом добавьте ссылку в `catalog/tools.json`. Для встроенного инструмента также добавьте маршрут в `routes/`, проверьте конфигурацию `docker compose exec portal nginx -t` и примените её командой `docker compose exec portal nginx -s reload`.
