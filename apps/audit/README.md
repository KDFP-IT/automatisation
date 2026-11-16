# audit — единая таблица событий использования инструментов

SQLite-файл на persistent volume (`audit-data:/data`): переживает рестарты,
читается Metabase напрямую (см. slice 4). Пишут kac/bookmarks/trench с
сервера, signatures — beacon'ом из браузера; все идут через nginx портала,
который уже проверил сессию и подставил `X-Auth-User`.

## Формат события

`ts, user_id (UPN), ad_login, tool, action, status, pages, duration_ms,
saved_minutes, error, details(JSON)`. `user_id` берётся из заголовка
`X-Auth-User` (он побеждает тело запроса — от спуфинга защищает nginx:
у audit нет публикуемых портов). `saved_minutes` считается по таблице
норм, если не передан явно.

## Нормы времени

Минуты ручной работы, сэкономленные одним действием (`norms`).
Начальные значения — оценки, править под замеры:

| tool | action | min |
| --- | --- | --- |
| kac | build / download | 60 / 2 |
| bookmarks | process / download | 15 / 2 |
| trench | project_create / scheme_create / scheme_save / state_change | 5 / 10 / 10 / 2 |
| signatures | check / export | 20 / 2 |

Правка (только админы матрицы, nginx проверяет `?tool=_admin`):

```sh
curl -X PUT https://<portal>/audit/norms -H 'Content-Type: application/json' \
  -d '{"tool":"kac","action":"build","minutes":90}'
```

## Что шлёт каждый инструмент

- kac: `build` (done/error, pages/sections/duration), `download` (kind pdf/zip)
- bookmarks: `process` (done/error, pages/added/warnings), `download` (kind pdf/csv)
- trench: `project_create`, `scheme_create`, `scheme_save` (ok/conflict),
  `state_change` (archive/unarchive/trash/restore)
- signatures: `check` (агрегаты: страницы/фамилии/подписи/исходы, без содержимого PDF), `export`

Отправка fire-and-forget (`AUDIT_URL`, таймаут 2с): недоступность audit
не ломает инструменты, событие теряется с записью в лог.

## Проверка

```sh
curl https://<portal>/audit/norms
sqlite3 /var/lib/docker/volumes/*audit-data*/_data/audit.sqlite3 \
  "SELECT tool, action, COUNT(*), SUM(saved_minutes)/60.0 FROM events GROUP BY tool, action;"
```
