#!/usr/bin/env bash
set -euo pipefail

container=$(docker run -d --read-only --tmpfs /tmp:mode=1777 --tmpfs /data:uid=10001,gid=10001,mode=0700 -p 127.0.0.1::8080 "$1")
trap 'docker logs "$container"; docker rm -f "$container" >/dev/null' EXIT
address=$(docker port "$container" 8080/tcp)
base="http://$address/kac"
health=$(curl --retry 12 --retry-all-errors --retry-delay 1 -fsS "$base/api/health")
grep -Eq '"available"[[:space:]]*:[[:space:]]*true' <<< "$health"
docker exec "$container" python -c '
import re
from urllib.request import urlopen
host = "http://127.0.0.1:8080"
base = host + "/kac"
with urlopen(base + "/", timeout=5) as response:
    assert response.read(1)
with urlopen(base + "/", timeout=5) as response:
    page = response.read().decode("utf-8")
assets = sorted(set(re.findall(r"/kac/ui/assets/[A-Za-z0-9_][A-Za-z0-9_.-]*", page)))
assert assets, page
for asset in assets:
    with urlopen(host + asset, timeout=10) as response:
        data = response.read()
    assert data, asset
    if asset.endswith(".css"):
        for ref in sorted(set(re.findall(r"url\\((/kac/ui/assets/[^)]+)\\)", data.decode("utf-8", "replace")))):
            with urlopen(host + ref, timeout=10) as response:
                assert response.read(1), ref
print("ui ok:", len(assets), "assets")
'
docker exec "$container" python -c 'import lxml.etree, PIL.Image, pypdf, pypdfium2'
docker exec "$container" libreoffice --version
docker exec "$container" tesseract --list-langs | grep -x rus
