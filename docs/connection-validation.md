# Sever 0.5.0 connection validation

- Exported owner xray.json passed Xray 26.3.27 configuration validation.
- A temporary local Xray client used the exported profile to connect via VLESS/REALITY to the live server and fetch https://example.com successfully. The temporary client was stopped afterward.
- Twelve automated tests pass, including all five platform selections, Base64/plain consistency, PNG/SVG creation, private output permissions, absence of the server private key and rejection of disabled, expired and exhausted users.
- Client recommendations were checked against official Happ and v2rayN pages on 2026-10-22.
- Native apps on actual iOS, Android, Windows and macOS devices, external mobile networks and TUN routing have not been exercised. The universal link is intended for compatible VLESS/REALITY clients.
- QR dependencies are bundled with license notices from official Ubuntu packages. No external QR service is used.
