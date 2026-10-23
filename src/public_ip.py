"""Discover the advertised IPv4 without collecting machine credentials."""
import ipaddress
import socket
import urllib.request


def public_ipv4(value):
    address = ipaddress.ip_address(value.strip())
    if address.version != 4 or not address.is_global:
        raise ValueError('Нужен публичный IPv4 сервера')
    return str(address)


def detect():
    # A directly assigned public address needs no external lookup.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('1.1.1.1', 443))
            return public_ipv4(sock.getsockname()[0])
    except (OSError, ValueError):
        pass
    for endpoint in ('https://api.ipify.org', 'https://checkip.amazonaws.com'):
        try:
            with urllib.request.urlopen(endpoint, timeout=8) as response:
                return public_ipv4(response.read(64).decode('ascii'))
        except (OSError, ValueError, UnicodeError):
            continue
    raise ValueError('Не удалось определить IP. Повторите с параметром --host ПУБЛИЧНЫЙ_IP')


if __name__ == '__main__':
    try:
        print(detect())
    except ValueError as error:
        raise SystemExit(str(error))
