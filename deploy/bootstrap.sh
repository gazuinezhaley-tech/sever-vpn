#!/usr/bin/env bash
set -euo pipefail
umask 077
usage() {
  cat <<'HELP'
Sever — установка одной командой на чистый Linux x86_64

sudo bash sever-install.run
sudo bash sever-install.run --host ПУБЛИЧНЫЙ_IP
bash sever-install.run --check

Вариант --check только проверяет целостность встроенного архива.
Для установки нужны root, systemd 247+, свободные порты 443, 10085 и 18081.
Если Python и системные утилиты отсутствуют, они устанавливаются через apt.
Существующая установка Sever не перезаписывается.
HELP
}
if [[ ${1:-} == --help || ${1:-} == -h ]]; then usage; exit 0; fi
if [[ ! -f "$0" ]]; then echo 'Сначала сохраните установщик в файл.' >&2; exit 1; fi
payload_line=$(awk '/^__SEVER_PAYLOAD_BELOW__$/{print NR+1; exit}' "$0")
[[ -n $payload_line ]] || { echo 'Архив установщика отсутствует.' >&2; exit 1; }
expected='@SHA256@'
if command -v sha256sum >/dev/null 2>&1; then
  actual=$(tail -n +"$payload_line" "$0" | sha256sum); actual=${actual%% *}
elif command -v shasum >/dev/null 2>&1; then
  actual=$(tail -n +"$payload_line" "$0" | shasum -a 256); actual=${actual%% *}
else
  echo 'Не найдена утилита SHA-256.' >&2; exit 1
fi
[[ $actual == "$expected" ]] || { echo 'Проверка целостности не пройдена. Установка остановлена.' >&2; exit 1; }
if [[ ${1:-} == --check ]]; then echo 'Sever: целостность архива подтверждена.'; exit 0; fi
host=''
if (( $# )); then
  if [[ ${1:-} != --host || $# != 2 ]]; then usage; exit 2; fi
  host=$2
fi
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || { echo 'Требуется Linux x86_64.' >&2; exit 1; }
[[ $EUID == 0 ]] || { echo 'Запустите команду через sudo или от root.' >&2; exit 1; }
[[ -d /run/systemd/system ]] || { echo 'Требуется сервер с systemd.' >&2; exit 1; }
if [[ -e /opt/sever || -L /opt/sever || -e /usr/local/bin/sever || -L /usr/local/bin/sever ]]; then
  echo 'Sever уже установлен. Для управления выполните sever. Данные не изменены.' >&2; exit 1
fi
for unit in sever-xray.service sever-sub.service sever-enforce.service sever-enforce.timer; do
  [[ ! -e /etc/systemd/system/$unit ]] || { echo "Уже существует служба $unit. Установка остановлена." >&2; exit 1; }
done
missing=()
command -v python3 >/dev/null 2>&1 || missing+=(python3)
command -v useradd >/dev/null 2>&1 || missing+=(passwd)
command -v tar >/dev/null 2>&1 || missing+=(tar)
command -v gzip >/dev/null 2>&1 || missing+=(gzip)
if (( ${#missing[@]} )); then
  command -v apt-get >/dev/null 2>&1 || { echo 'Установите Python 3.10+, tar, gzip и useradd средствами вашей ОС.' >&2; exit 1; }
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
fi
python3 -c 'import sys; assert sys.version_info >= (3,10), "Нужен Python 3.10+"'
staging=$(mktemp -d /tmp/sever-bootstrap.XXXXXXXX)
trap 'rm -rf -- "$staging"' EXIT
printf 'Проверка пройдена. Устанавливаю Sever…\n'
tail -n +"$payload_line" "$0" | tar -xz -C "$staging"
if [[ -z $host ]]; then
  host=$(python3 "$staging/sever/src/public_ip.py")
else
  host=$(PYTHONPATH="$staging/sever/src" python3 -c 'import sys; from public_ip import public_ipv4; print(public_ipv4(sys.argv[1]))' "$host")
fi
printf 'Публичный IPv4: %s\n' "$host"
python3 "$staging/sever/install.py" --host "$host"
if command -v ufw >/dev/null 2>&1 && LC_ALL=C ufw status | grep -q '^Status: active'; then
  ufw allow 443/tcp comment 'Sever VPN'
fi
/usr/local/bin/sever connect owner
printf '\nСсылка подключения (скопируйте в VPN-приложение):\n'
/usr/local/bin/sever link owner
/usr/local/bin/sever qr owner
printf '\nГотово. Меню: sever\nЕсли у хостинга есть отдельный firewall, разрешите входящий TCP 443.\n' 
exit 0
__SEVER_PAYLOAD_BELOW__
