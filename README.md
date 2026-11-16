# Автоматизации КДФП

Каждый инструмент хранит исходники и зависимости в своём каталоге. Оболочка портала подключает инструменты через меню и маршруты прокси.

| Каталог | Инструмент | Сборка образа из корня |
| --- | --- | --- |
| [apps/kac](apps/kac) | Собрать КАЦ | `docker build -t kdfp-portal-kac:local -f apps/kac/Dockerfile .` |
| [apps/bookmarks](apps/bookmarks) | Закладки PDF | `docker build -t kdfp-portal-bookmarks:local apps/bookmarks` |
| [apps/signatures](apps/signatures) | Проверка подписантов | `docker build -t kdfp-portal-signatures:local apps/signatures` |
| [apps/trench](apps/trench) | Калькулятор траншей | `docker build -f apps/trench/Dockerfile.portal -t kdfp-portal-trench:local apps/trench` |
| [apps/portal](apps/portal) | Рабочее место | `docker build -t kdfp-portal-shell:local -f apps/portal/Dockerfile .` |
| [apps/auth](apps/auth) | Вход через AD/local, матрица доступов | `docker build -t kdfp-portal-auth:local -f apps/auth/Dockerfile .` |
| [apps/audit](apps/audit) | Учёт действий, нормы saved_minutes | `docker build -t kdfp-portal-audit:local -f apps/audit/Dockerfile .` |
| [apps/office-chat](apps/office-chat) | Офисный чат | Сервер Python и клиент Windows |

GitHub Actions собирает и проверяет КАЦ при изменениях в `apps/kac` и при изменении его workflow. Сборка основной ветки или ручной запуск сохраняет образ Linux amd64 с контрольной суммой в Artifacts. Образ можно импортировать командой `docker load -i kac-linux-amd64.tar.gz`.

В [deploy/portal](deploy/portal) лежат Compose, меню и маршруты. Базы, рабочие документы и конфигурации с секретами хранятся вне Git. На действующем сервере сохраняйте имя Compose-проекта и привязки томов при обновлениях, включая `portal-data` калькулятора.

Общие токены оформления — [packages/tokens/tokens.css](packages/tokens/tokens.css). Интерфейс КАЦ подключает их копией `apps/kac/ui/src/assets/tokens.css` (импорт в `main.css`); совпадение копии с каноном проверяет `npm test` в `apps/kac/ui`. Остальные инструменты переходят на токены по мере переноса интерфейса на Vue.
