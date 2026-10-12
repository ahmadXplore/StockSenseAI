# StockSense AI — LAN Security & Access Control Architecture

This document describes the security model, cryptographic protocols, perimeter gating, and threat mitigations implemented for StockSense AI's native LAN server deployment.

---

## 1. Security Overview & Perimeter Model

```
                    PRIVATE LOCAL AREA NETWORK (WI-FI / ETHERNET)
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
     HOST LAPTOP CLIENT                                        REMOTE LAN DEVICE
    (127.0.0.1 / Loopback)                                  (e.g. 192.168.1.105)
            │                                                           │
            │ Auto-Approved                                             ▼
            │ (Host Safeguard)                               [LANDeviceAccessMiddleware]
            │                                                           │
            │                                    ┌──────────────────────┴──────────────────────┐
            │                                    │                                             │
            │                         Valid Token & Approved                         Unapproved / Pending
            │                                    │                                             │
            ▼                                    ▼                                             ▼
    FULL TERMINAL ACCESS               AUTHORIZED LAN ACCESS                     403 PERIMETER GATE
 (FastAPI + ML + Backtesting)       (FastAPI + ML + Backtesting)             (Pending / Blocked Notice)
```

StockSense AI operates under a **Zero-Trust LAN Perimeter Model**:
- Being connected to the same Wi-Fi router **does not** automatically grant access to financial data, models, or portfolio state.
- Every remote device must present a valid, cryptographically verified authorization token issued by an administrator.
- Unauthorized devices are quarantined at the perimeter gate.

---

## 2. Device Fingerprinting & Token Architecture

### A. Client Device Identification
When a device visits StockSense AI for the first time:
1. The client library (`frontend/lib/deviceAuth.ts`) checks for an existing device identifier in `localStorage` and HTTP cookies.
2. If absent, a cryptographically random UUID is generated (`dev_<UUID4>`), stored persistently, and set as a long-lived cookie (`SameSite=Lax`).
3. The device queries `/api/v1/lan/devices/check` with its `X-Device-ID`.

### B. Administrator Token Issuance
1. When an administrator approves a device from the Admin Console (`POST /api/v1/lan/devices/{device_id}/approve`):
   - A high-entropy random token (`ss_dev_<token_urlsafe(32)>`) is generated using `secrets.token_urlsafe`.
   - The server computes the **SHA-256 hash** of the raw token:
     $$\text{TokenHash} = \text{SHA-256}(\text{RawToken})$$
   - Only the SHA-256 hash is permanently retained in the database (`lan_devices.token_hash`).
   - The plain token is temporarily set in `lan_devices.pending_claim_token` until the client polls and claims it, at which point the plain token is scrubbed from the server database permanently.
2. The remote device stores the token in `localStorage` and sends it on all subsequent requests in the `X-Device-Token` header.

### C. Request Verification Pipeline
On every incoming API request:
1. `LANDeviceAccessMiddleware` extracts client IP (`x-forwarded-for`, `x-real-ip`, or socket host).
2. If loopback (`127.0.0.1`, `::1`, `localhost`), request is allowed immediately.
3. For remote clients, `X-Device-ID` and `X-Device-Token` are extracted.
4. The server queries the database:
   - If not found or status is `PENDING`: returns HTTP `403` with code `DEVICE_PENDING`.
   - If status is `REJECTED` or `REVOKED`: returns HTTP `403` with code `DEVICE_BLOCKED`.
   - If status is `APPROVED`: compares `SHA-256(X-Device-Token)` with `lan_devices.token_hash`.
   - If matching, updates `last_seen_at` and `current_ip`, and forwards the request.

---

## 3. Host Laptop Safety Guarantee

To eliminate any risk of locking yourself out of your own laptop:
- Requests originating from `127.0.0.1`, `::1`, `localhost`, or the server's own LAN IP are identified as **Loopback / Local Host**.
- When `lan_auto_approve_local = True` (default), loopback requests bypass device gating automatically.
- The administrator console and database can always be managed directly from the laptop.

---

## 4. Network Boundary & Firewall Enforcement

1. **Private Network Profile Only**:
   - `setup_windows_firewall.ps1` restricts the inbound rule strictly to the **Private** Windows network profile.
   - If your laptop connects to a public coffee shop, airport, or hotel Wi-Fi, Windows classifies the interface as **Public**, and all inbound access to ports `3000` and `8000` is **automatically blocked at the OS kernel level**.
2. **No Port Forwarding**:
   - The server requires **no router port-forwarding**, **no dynamic DNS**, and **no public tunnels** (e.g. ngrok, Cloudflare tunnels).
   - Traffic never leaves your local physical subnet.
3. **Database Isolation**:
   - SQLite (`backend/stocksense.db`) or PostgreSQL remains internal to the laptop host filesystem and is never exposed on external ports.

---

## 5. Security Audit Logging (`LANAccessLog`)

Every critical network event is permanently recorded in the database:

| Action Code | Trigger Event | Status |
| :--- | :--- | :--- |
| `DEVICE_REQUESTED` | New device self-registers from device gate | `PENDING` |
| `DEVICE_APPROVED` | Administrator grants device access | `SUCCESS` |
| `DEVICE_REJECTED` | Administrator rejects device request | `BLOCKED` |
| `DEVICE_REVOKED` | Administrator terminates active device access | `BLOCKED` |
| `UNAUTHORIZED_ACCESS_ATTEMPT` | Unregistered or blocked client attempts to call protected API | `BLOCKED` |

Administrators can inspect these logs in real-time under `http://localhost:3000/admin` (LAN Access tab).

---

## 6. AI & Copilot Safety Guardrails

- The StockSense AI assistant (`/api/chat` and `QueryChatbot`) operates strictly as an educational financial analysis and decision-support tool.
- It possesses **no autonomous execution agents**, **no automated trading capabilities**, and **no brokerage order execution APIs**.
- All portfolio actions (adding watchlists, logging positions) require explicit manual user input.
