"""Build a self-contained installer and an HTTPS download launcher."""
import argparse
import hashlib
import pathlib
import shlex
import urllib.parse

root = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--release-url', required=True)
args = parser.parse_args()
url = urllib.parse.urlsplit(args.release_url)
if url.scheme != 'https' or not url.hostname or url.username or url.password:
    parser.error('A public HTTPS release URL is required')
archive = root / 'dist/sever-0.6.0-linux-x86_64.tar.gz'
payload = archive.read_bytes()
header = (root / 'deploy/bootstrap.sh').read_text()
assert header.count('@SHA256@') == 1
installer = root / 'dist/sever-install.run'
installer.write_bytes(header.replace('@SHA256@', hashlib.sha256(payload).hexdigest()).encode() + payload)
installer.chmod(0o755)
digest = hashlib.sha256(installer.read_bytes()).hexdigest()
(installer.parent / (installer.name + '.sha256')).write_text(digest + '  ' + installer.name + '\n')
launcher = '''#!/usr/bin/env bash
set -euo pipefail
umask 077
if [[ ${EUID} != 0 ]]; then
  echo 'Выполните команду от root или используйте curl ... | sudo bash.' >&2
  exit 1
fi
command -v curl >/dev/null 2>&1 || { echo 'Для загрузки нужен curl.' >&2; exit 1; }
stage=$(mktemp -d /tmp/sever-download.XXXXXXXX)
trap 'rm -rf -- "$stage"' EXIT
curl --proto '=https' --tlsv1.2 --fail --show-error --silent --location --retry 3 --connect-timeout 15 --max-time 300 RELEASE_URL -o "$stage/sever-install.run"
printf '%s  %s\n' 'INSTALLER_SHA' "$stage/sever-install.run" | sha256sum --check --status
bash "$stage/sever-install.run" "$@"
'''.replace('RELEASE_URL', shlex.quote(args.release_url)).replace('INSTALLER_SHA', digest)
(root / 'dist/install.sh').write_text(launcher)
print(installer)
