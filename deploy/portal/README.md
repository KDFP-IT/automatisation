# Рабочее место

Оболочка портала — SPA на Vue 3 + Nuxt UI (`apps/portal/src`), собирается в образ стадией `node:24-alpine`. Меню по-прежнему берётся из `/portal/tools.json`, инструменты открываются в iframe с `?embed=1`.

Локальная разработка оболочки:

```sh
cd apps/portal
npm ci
npm run dev   # http://127.0.0.1:5173/
```

Для локальной разработки с живыми инструментами поднимите Compose и проксируйте `/bookmarks`, `/signatures`, `/trench`, `/kac` на `127.0.0.1:8090` (см. `server.proxy` в `vite.config.mjs`).

Соберите нужные образы командами из корневого README. Для локального запуска всех инструментов из `deploy/portal` задайте в `.env` теги:

```dotenv
PORTAL_IMAGE=kdfp-portal-shell:local
BOOKMARKS_IMAGE=kdfp-portal-bookmarks:local
SIGNATURES_IMAGE=kdfp-portal-signatures:local
TRENCH_IMAGE=kdfp-portal-trench:local
KAC_IMAGE=kdfp-portal-kac:local
AUTH_IMAGE=kdfp-portal-auth:local
AUDIT_IMAGE=kdfp-portal-audit:local
```

```sh
docker compose -f compose.yaml -f compose.kac-linux.yaml up -d
```

Портал доступен на `http://127.0.0.1:8090/`. Чтобы обновить только КАЦ, укажите новый `KAC_IMAGE` и выполните:

```sh
docker compose -f compose.yaml -f compose.kac-linux.yaml up -d --no-deps kac
```

Для нового инструмента с собственным адресом добавьте ссылку в `catalog/tools.json`. Для встроенного инструмента также добавьте маршрут в `routes/`, проверьте конфигурацию `docker compose exec portal nginx -t` и примените её командой `docker compose exec portal nginx -s reload`.

## Встраивание инструмента

Портал открывает встроенные инструменты в iframe с параметром `?embed=1` и сам не трогает их документ. Инструмент отвечает за свой вид в обоих режимах:

```js
// embed.js, подключается в <head> до стилей
if (window.self !== window.top || new URLSearchParams(window.location.search).has("embed")) {
  document.documentElement.dataset.embedded = "";
}
```

```css
/* embedded.css */
[data-embedded] header > .brand { display: none; }
```

Правила: собственная шапка инструмента скрывается только при `[data-embedded]`; самостоятельный запуск (`docker run`) её сохраняет. Портал не вставляет стили в чужой документ и не требует доступа к `contentDocument`.

Дополнительно: инструмент должен разрешать встраивание заголовком `Content-Security-Policy: frame-ancestors 'self'` и блокировать встраивание себя на чужих сайтах — `'self'`, а не `*`. У портала `frame-ancestors 'none'`.

## Times New Roman для PDF КАЦ

При запуске с `compose.kac-linux.yaml` контейнер читает шрифты из папки `deploy/portal/fonts/` только для чтения. Для другой папки укажите её абсолютный путь в `KAC_FONT_DIR` в серверном `.env`.

Поместите в папку файлы Times New Roman, которые разрешено использовать на сервере: обычный, жирный, курсив и жирный курсив. При первом подключении пересоздайте контейнер КАЦ. Последующие запуски CD используют ту же папку.

Проверить выбор шрифта можно командами `docker exec portal-kac-1 fc-match 'Times New Roman'` и `docker exec portal-kac-1 fc-match 'Times New Roman:style=Bold'`. Обе должны вернуть семейство Times New Roman.

## Доступ через Active Directory

Сервис `auth` (`apps/auth`): вход по паре local либо bind `login@kdfp.ru` в AD, сессии — подписанные cookie. nginx проверяет каждый инструмент через `auth_request /auth/check?tool=<id>`: без сессии — 401, без права — 403. Меню фильтруется по `/auth/me`.

```sh
docker build -t kdfp-portal-auth:local -f apps/auth/Dockerfile .
```

Матрица доступов — `access/access.toml` (DN групп под реальный AD, см. `apps/auth/README.md`). Переменные — в `compose.yaml` (`AUTH_MODE`, `LDAP_URL`, `LDAP_BASE_DN`, `SESSION_SECRET`, …): секреты только из окружения/сейфа, не в git. Проверка AD с VPS: `python3 apps/auth/scripts/verify-ad.py --url ldap://192.168.30.200:389 --base-dn DC=kdfp,DC=ru --login <sAMAccountName> --group-dn '<DN>'.
