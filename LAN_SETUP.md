# StockSense AI — LAN Server Setup Guide (Native Windows / No Docker)

Transform your Windows laptop into a high-performance, private LAN financial terminal server accessible by authorized smartphones, tablets, and secondary computers on your home or office Wi-Fi.

---

## 1. Quick Start (1-Click Startup)

If you have already configured the Windows Firewall once:

```cmd
start_stocksense_lan.bat
```

This single batch script:
1. Detects your laptop's active Wi-Fi/Ethernet IPv4 address automatically (e.g. `192.168.1.243`).
2. Launches the FastAPI backend on `0.0.0.0:8000` inside your virtual environment (`backend\.venv`).
3. Launches the Next.js frontend on `0.0.0.0:3000` with native internal reverse-proxy rewrites to FastAPI.
4. Outputs the exact URLs to access the terminal from your laptop and mobile devices.

---

## 2. Prerequisites

1. **Operating System**: Windows 10 or Windows 11.
2. **Python Environment**: Python 3.11+ installed with virtual environment at `backend\.venv`.
3. **Node.js**: Node.js 18+ and npm installed.
4. **Local Network**: Windows laptop and all client devices must be connected to the **same** private Wi-Fi or Ethernet network.

---

## 3. Step-by-Step Installation

### Step 1: Configure Windows Defender Firewall (One-Time)

To allow incoming connections from your private Wi-Fi network without exposing your machine to public networks, run the included PowerShell setup script as Administrator:

1. Right-click the Windows Start menu and select **Terminal (Admin)** or **PowerShell (Run as Administrator)**.
2. Navigate to your project folder:
   ```powershell
   cd d:\StockSenseAI
   ```
3. Run the firewall rule script:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\setup_windows_firewall.ps1
   ```
4. You will receive confirmation that inbound TCP ports `3000` and `8000` are permitted **exclusively on the Private network profile**.

---

### Step 2: Start the LAN Server

Double-click `start_stocksense_lan.bat` or run it from Command Prompt:

```cmd
start_stocksense_lan.bat
```

You will see:
```text
===============================================================================
                STOCKSENSE AI — NATIVE LAN SERVER (NO DOCKER)
===============================================================================

[1/3] Detecting laptop active LAN IPv4 address...
      Host LAN IP Detected: 192.168.1.243

[2/3] Launching FastAPI Backend (0.0.0.0:8000)...
[3/3] Launching Next.js Unified Frontend (0.0.0.0:3000)...

===============================================================================
                     SERVER SUCCESSFULLY INITIALIZED!
===============================================================================

  * Host Laptop URL (Local):    http://localhost:3000
  * Remote LAN URL (Mobile/PC): http://192.168.1.243:3000
  * API & Swagger Docs:         http://192.168.1.243:3000/docs
  * Admin LAN Console:          http://localhost:3000/admin
```

---

### Step 3: Accessing from Your Laptop (Server Host)

Open your browser on the host laptop and visit:
```text
http://localhost:3000
```
- **Local Loopback Auto-Approval**: The host machine (`127.0.0.1`, `::1`, `localhost`) is recognized as the server host device. You are immediately granted full access and will never be locked out of your own laptop.

---

### Step 4: Connecting from Mobile Devices (Smartphones & Tablets)

1. Connect your smartphone (iPhone, iPad, Android) to the **same Wi-Fi network** as the laptop.
2. Open Chrome or Safari and enter the LAN URL displayed by the launcher, for example:
   ```text
   http://192.168.1.243:3000
   ```
3. **Device Access Gate Appears**:
   - The device automatically generates a unique cryptographic fingerprint.
   - You can enter a friendly label (e.g., *"Ahmad's iPhone 15"*).
   - Tap **Request Device Access**.
   - The screen transitions to **Access Authorization Pending** and begins polling the server.

---

### Step 5: Approving Connecting Devices (1-Click Admin)

1. On your laptop, open:
   ```text
   http://localhost:3000/admin
   ```
2. Navigate to the **LAN Access & Devices** tab.
3. Under **Pending Authorization Requests**, you will see the incoming device with its friendly name, client IP address, and request time.
4. Click **[Approve Device]**.
5. Within 2–3 seconds, the smartphone screen will automatically detect the approval, securely save its device token, and transition straight into the StockSense AI financial terminal!

---

## 4. Administrative Device Actions

From `http://localhost:3000/admin` (LAN Access tab), you can:

| Action | Description |
| :--- | :--- |
| **Approve** | Issues a cryptographic token and grants full terminal access. |
| **Reject** | Declines access with an optional custom reason displayed on the device. |
| **Revoke** | Immediately blocks an active device. The remote client is disconnected on the next request. |
| **Rename** | Customize the friendly name for clear tracking in your records. |
| **Delete** | Permanently removes the device and its associated security audit logs. |

---

## 5. Summary of Network Ports

| Port | Service | Bound To | Accessible By | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **3000** | Next.js Unified Gateway | `0.0.0.0` | Laptop + Remote LAN | Serves Web UI & reverse-proxies `/api/v1/*` |
| **8000** | FastAPI Backend | `0.0.0.0` | Laptop + Internal Proxy | Core ML engine, backtesting & REST endpoints |
| **5432 / SQLite** | Database | Local Host | Internal Only | SQLite `backend/stocksense.db` or local PostgreSQL |
