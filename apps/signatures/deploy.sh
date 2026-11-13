#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
bind=127.0.0.1
port=8087
if [ -f .env ]; then
    saved_bind=$(sed -n 's/^SIGNATURE_BIND=//p' .env | tail -n 1)
    saved_port=$(sed -n 's/^SIGNATURE_PORT=//p' .env | tail -n 1)
    [ -z "$saved_bind" ] || bind=$saved_bind
    [ -z "$saved_port" ] || port=$saved_port
fi
while [ "$#" -gt 0 ]; do
    case "$1" in
        --bind) [ "$#" -ge 2 ] || { echo 'Missing value for --bind' >&2; exit 2; }; bind=$2; shift 2 ;;
        --port) [ "$#" -ge 2 ] || { echo 'Missing value for --port' >&2; exit 2; }; port=$2; shift 2 ;;
        --help|-h) echo 'Usage: sh deploy.sh [--bind INTERNAL_IPV4] [--port PORT]'; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done
printf '%s\n' "$bind" | awk -F. 'NF!=4{exit 1}{for(i=1;i<=4;i++)if($i !~ /^[0-9]+$/ || length($i)>3 || $i+0>255)exit 1}' || { echo 'Invalid IPv4 address' >&2; exit 2; }
case "$port" in ''|*[!0-9]*) echo 'Invalid port' >&2; exit 2 ;; esac
[ "$port" -ge 1 ] && [ "$port" -le 65535 ] || { echo 'Port must be 1..65535' >&2; exit 2; }
command -v docker >/dev/null 2>&1 || { echo 'Docker is required' >&2; exit 1; }
docker compose version >/dev/null
if [ -f SHA256SUMS ]; then sha256sum -c SHA256SUMS; fi
printf 'SIGNATURE_BIND=%s\nSIGNATURE_PORT=%s\n' "$bind" "$port" > .env
docker compose -p kdfp-signatures config --quiet
if [ -f signature-checker-image.tar.gz ]; then
    docker image load --input signature-checker-image.tar.gz
    actual_platform=$(docker image inspect kdfp/signature-checker:1.0.1 --format '{{.Os}}/{{.Architecture}}')
    actual_version=$(docker image inspect kdfp/signature-checker:1.0.1 --format '{{index .Config.Labels "org.opencontainers.image.version"}}')
    [ "$actual_platform" = 'linux/amd64' ] && [ "$actual_version" = '1.0.1' ] || { echo 'Image platform/version does not match release' >&2; exit 1; }
else
    docker compose -p kdfp-signatures build
fi
docker compose -p kdfp-signatures up -d --no-build --wait --wait-timeout 60
docker compose -p kdfp-signatures ps
printf '\nReady: http://%s:%s/\n' "$bind" "$port"
