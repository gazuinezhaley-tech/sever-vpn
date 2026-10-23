# Automatic install validation — 2026-10-23

Sever 0.6.0 self-contained installer was run without arguments in a disposable systemd-nspawn root, with read-only /usr and separate writable /usr/local, PID, mount and network namespaces. A public-format address was assigned only inside its private network to exercise automatic local address discovery without sending traffic to that address.

Passed: embedded checksum, auto-discovered host, full installation, active Xray/subscription/timer services, generated link/PNG/SVG/Xray profiles, rejection of repeated installation without modifying the user database. The container was stopped afterward; live host services remained active.

Limitations: shared host kernel/OS binaries; no independent provider network; dependency installation via apt and active UFW branch not exercised; HTTPS IP lookup fallback covered by mocked unit tests. Fifteen unit tests pass. GUI imports and physical devices require separate checks.
