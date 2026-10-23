#!/usr/bin/env bash
set -euo pipefail
umask 077
if [[ ${EUID} != 0 ]]; then
  echo 'Выполните команду от root или используйте curl ... | sudo bash.' >&2
  exit 1
fi
command -v curl >/dev/null 2>&1 || { echo 'Для загрузки нужен curl.' >&2; exit 1; }
stage=$(mktemp -d /tmp/sever-download.XXXXXXXX)
trap 'rm -rf -- "$stage"' EXIT
curl --proto '=https' --tlsv1.2 --fail --show-error --silent --location --retry 3 --connect-timeout 15 --max-time 300 https://github.com/gazuinezhaley-tech/sever-vpn/releases/download/v0.6.0/sever-install.run -o "$stage/sever-install.run"
printf '%s  %s
' 'f5d6d578d39dae724d625a2214f774684332d827b7ffc2fbdbd3f346fdc3a762' "$stage/sever-install.run" | sha256sum --check --status
bash "$stage/sever-install.run" "$@"
