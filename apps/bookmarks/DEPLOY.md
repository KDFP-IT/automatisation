# Развёртывание «Закладки PDF»

Соберите образ из каталога инструмента. Для общего рабочего места укажите его тег в переменной `BOOKMARKS_IMAGE` по [инструкции портала](../../deploy/portal/README.md).

```sh
docker build -t kdfp-portal-bookmarks:local .
docker run --rm -p 127.0.0.1:8080:8080 kdfp-portal-bookmarks:local
```

Для локальной проверки откройте `http://127.0.0.1:8080/bookmarks/`. Для запуска без Docker используйте [README](README.md).
