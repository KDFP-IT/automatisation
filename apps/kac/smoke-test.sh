#!/usr/bin/env bash
set -euo pipefail

container=$(docker run -d --read-only --tmpfs /tmp:mode=1777 --tmpfs /data:uid=10001,gid=10001,mode=0700 -p 127.0.0.1::8080 "$1")
trap 'docker logs "$container"; docker rm -f "$container" >/dev/null' EXIT
address=$(docker port "$container" 8080/tcp)
base="http://$address/kac"
health=$(curl --retry 12 --retry-all-errors --retry-delay 1 -fsS "$base/api/health")
grep -Eq '"available"[[:space:]]*:[[:space:]]*true' <<< "$health"
docker exec "$container" python -c '
from urllib.request import urlopen
for path in ("/", "/ui/fonts/montserrat-400.ttf"):
    with urlopen("http://127.0.0.1:8080/kac" + path, timeout=5) as response:
        assert response.read(1)
with urlopen("http://127.0.0.1:8080/kac/", timeout=5) as response:
    page = response.read().decode("utf-8")
assert "/kac/ui/assets/" in page, page
'
docker exec "$container" /usr/bin/python3 -c 'import uno'
docker exec "$container" python -c 'import lxml.etree, PIL.Image, pypdf, pypdfium2'
docker exec "$container" libreoffice --version
docker exec "$container" tesseract --list-langs | grep -x rus
