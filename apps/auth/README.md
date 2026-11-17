# auth — вход в портал: local-пара или LDAP/AD bind

Stateless-сервис (stdlib + `ldap3`): сессии — HMAC-cookie, серверного
хранилища нет, рестарт безопасен. `/auth/check` LDAP не трогает: упавший AD
ломает только новые логины (503), залогиненные продолжают работать.

## Режимы

- `AUTH_MODE=local` — миграционный fallback: одна пара
  `LOCAL_LOGIN`/`LOCAL_PASSWORD`, ей видны все инструменты матрицы.
- `AUTH_MODE=ldap` — bind напрямую `login@LDAP_DOMAIN` (или полный UPN),
  затем проверка членства в группах через `LDAP_MATCHING_RULE_IN_CHAIN`
  (вложенные группы учитываются). Сервисная учётка не нужна.

Вход только для членов `base_group` из `access.toml`, дальше матрица
`tools.<id>.groups`, `admin_groups` видят всё. Deny-by-default: неизвестный
инструмент в `/auth/check` — 403.

## Env

| Var | Назначение |
| --- | --- |
| `SESSION_SECRET` | HMAC-ключ cookie, обязателен (`openssl rand -hex 32`) |
| `AUTH_MODE` | `local` \| `ldap` |
| `ACCESS_FILE` | матрица, default `/etc/auth/access.toml` |
| `LDAP_URL` | `ldaps://host:636` или `ldap://host:389`, явный порт |
| `LDAP_TLS_MODE` | пусто = `ldaps`→LDAPS, `ldap`→обязательный STARTTLS; `none` только явный opt-in |
| `LDAP_BASE_DN`, `LDAP_DOMAIN` | база поиска и UPN-суффикс (`DC=kdfp,DC=ru`, `kdfp.ru`) |
| `LDAP_TIMEOUT_S` | connect-таймаут, default 5 |
| `LOCAL_LOGIN`, `LOCAL_PASSWORD` | fallback-пара для `local` |
| `SESSION_TTL_H` / `COOKIE_SECURE` | default 12 / 1 (для голого http dev — 0) |

| `LDAP_TIMEOUT_S` | connect-таймаут, default 5 |
| `LDAP_CA_FILE` | путь CA PEM внутри контейнера, пусто = системные CA (для самоподписанного AD смонтируйте CA и укажите путь) |

## Проверка AD (с VPS, где виден контроллер)

```sh
python3 scripts/verify-ad.py --url ldaps://kdfp-dc1:636 \
  --base-dn DC=kdfp,DC=ru --login nikita_g --group-dn 'CN=KDFP-Portal-Users,...'
# спросит пароль, сделает bind + in-chain проверку, молчит об ошибках пароля в логах
```

Throttle: 5 неверных паролей за 5 минут на логин — 429 (бережёт от
блокировки учётки в AD).
