# Sever 0.4.1 validation — 2026-10-22

Two disposable systemd-nspawn environments on Ubuntu 26.04 x86_64, with separate roots, PID and network namespaces. Host /usr mounted read-only; /usr/local isolated. These share the host kernel and OS binaries and do not replace validation on an independent VPS.

Passed:
- Offline fresh installation, real systemd services and TCP listener on port 443.
- Expiry, quota exhaustion, re-enable and manual disable reflected in Xray clients.
- Backup and full installation into a second empty environment with a changed host address.
- Preserved REALITY keys, user UUIDs, enabled flags, expiry, quota, accumulated bytes and subscription tokens.
- Restored services active; ports 443, 10085 and 18081 reachable inside the environment.
- Local subscription resolves to the new host; disabled user returns 404.
- Repeated sync waits for actual Xray sockets, correcting a service startup race.
- Nine unit tests pass.

HTTPS subscription remains disabled. The container tests did not exercise an external VPN tunnel, mobile clients or an independent provider network. Test environments were stopped after checks.
