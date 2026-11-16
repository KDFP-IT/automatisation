# @kdfp/kac-ui — экран «Собрать КАЦ», общий для портала и стендалона

Исходники не копировать: оба хоста импортируют `src/KacAssemble.vue` напрямую
(`apps/kac/ui` и `apps/portal` видят каталог через корень сборки Docker
и `server.fs.allow` в dev).

## Что хост обязан дать компоненту

- Vue 3 + Vue Router, Nuxt UI (`ui()` в Vite-плагине).
- Тему: токены `packages/tokens/tokens.css`, шрифт Manrope, алиасы
  `primary: brand`, `neutral: zinc` в `ui.colors`.
- В бандл иконок — полный список из `Icon`-пропсов компонента
  (сейчас: arrow-right, circle-check, download, file-archive, file-check,
  file-text, files, folder, folder-open, folder-up, info, loader-circle,
  triangle-alert, upload, x, vscode-icons:file-type-word).
- `initIcons(addIcon)` из `virtual:nuxt-ui-icons` в точке входа.
- `UApp` с `UToaster` выше по дереву — тосты (`useToast`) не рендерятся без него.
- Тот же origin: API вызывается как `/kac/api`, портал проксирует его на сервис КАЦ.

## Файлы

- `src/KacAssemble.vue` — экран целиком: форма, прогресс (`stageLabel`), «Готово».
- `src/composables/useOffers.js` — разбор выбранных папок, правила именования.
- `src/composables/useKacJob.js` — загрузка, опрос `/kac/api/jobs`, прогресс 0–100.
- `tests/offers.test.mjs` — правила отбора, запуск `node --test tests/*.test.mjs`.
