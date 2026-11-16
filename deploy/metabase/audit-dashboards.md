# Дашборд «Использование инструментов» в Metabase

Вопросы — `questions/q1..q6.sql` (SQLite-диалект, переменные `{{start}}`/`{{end}}`
заводятся в Metabase как Date-фильтры дашборда).

## 1. Подключить базы

`compose.audit.yaml` монтирует файлы в контейнер Metabase (только чтение).
В Metabase: Settings → Admin → Databases → Add, тип SQLite:

| База | Путь в контейнере |
| --- | --- |
| audit | `/audit/audit.sqlite3` |
| trench | `/trench-data/trench.sqlite3` |

Chat (`q6`) живёт вне portal compose: скопируйте sqlite чата рядом или
подмонтируйте так же. 403 по матрице в audit не пишутся (auth отвечает
синхронно, запись в audit задержала бы каждый запрос): кандидаты на выдачу
прав сейчас — `docker compose logs auth | grep "no base group\\|403"`.

WAL: trench и audit работают в WAL-режиме. Для чтения через `:ro`-маунт
хватает файлов `*.sqlite3` + `*-wal`/`*-shm` из того же volume (монтируем
volume целиком, а не файл). Если драйвер пожалуется — чекпоинт на исходнике:
`sqlite3 trench.sqlite3 'PRAGMA wal_checkpoint(TRUNCATE);'`. Metabase в
источники не пишет никогда.

## 2. Собрать дашборд

Dashboard → New → карточки из q1..q6:

- число: суммарные часы (`SUM saved_hours`, q1), событий всего, активных
  пользователей (q2 `COUNT`)
- столбцы: часы по инструментам (q1), топ-10 пользователей (q2)
- линия: динамика по неделям (q3)
- таблица: ошибки (q4), активность trench (q5), чат (q6)

Фильтр дашборда: Date range → связать с `{{start}}`/`{{end}}` во всех вопросах.

## 3. Доступ через AD-группу

Metabase умеет LDAP из коробки, заводится на тот же AD:

Settings → Admin → Authentication → LDAP: host `ldap://192.168.30.200:389`
(или `ldaps://…:636`), base DN `DC=kdfp,DC=ru`, user filter
`(userPrincipalName={login}@kdfp.ru)` — по аналогии с portal-auth.
Создайте в AD группу `KDFP-Analytics` (состав = кому можно смотреть цифры),
в Metabase заведите группу с тем же именем и выдайте ей коллекцию дашборда,
всем остальным — без доступа к коллекции. Синхронизация членства — штатной
настройкой LDAP group mapping.
