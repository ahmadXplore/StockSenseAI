# StockSense AI — LAN Troubleshooting & Diagnostics Guide

This guide addresses common network, firewall, and device authorization questions when hosting StockSense AI natively on a Windows laptop.

---

## 1. Quick Diagnostic Checklist

| Check | Expected Value | How to Verify |
| :--- | :--- | :--- |
| **Server Running?** | 2 CMD windows active | Look for `StockSense AI - LAN Backend` and `StockSense AI - LAN Frontend` |
| **Local Host Works?** | Opens terminal | On laptop: visit `http://localhost:3000` |
| **Same Wi-Fi Network?** | Same SSID | Verify laptop and phone are on the exact same Wi-Fi name |
| **Windows Network Profile** | **Private** | Windows Settings -> Network & internet -> Wi-Fi -> Properties |
| **Firewall Rule Active?** | `StockSense-AI-LAN-Server` | Run PowerShell test command below |

---

## 2. Issue: Phone shows "This site can't be reached" / Connection Timed Out

### Cause A: Windows Network is Set to "Public"
By default, Windows classifies new Wi-Fi networks as **Public**, which aggressively blocks all incoming connections from other devices on the network.

**Fix**:
1. Open Windows **Settings** (`Win + I`).
2. Go to **Network & internet** -> **Wi-Fi** (or **Ethernet**).
3. Click on your active network name.
4. Under **Network profile type**, change from **Public network** to **Private network**.
5. Try opening `http://<LAPTOP_LAN_IP>:3000` on your phone again.

---

### Cause B: Windows Firewall Blocking Ports
If you haven't run the firewall script with Administrator privileges, Windows Firewall will block port 3000.

**Fix**:
1. Open PowerShell as Administrator.
2. Run:
   ```powershell
   cd d:\StockSenseAI
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\setup_windows_firewall.ps1
   ```
3. To verify the rule is active, run:
   ```powershell
   Get-NetFirewallRule -DisplayName "StockSense-AI-LAN-Server" | Select-Object DisplayName, Enabled, Profile, Action
   ```

---

### Cause C: Router AP Isolation (Client Isolation)
Some guest Wi-Fi networks or router security settings enable **AP Isolation** (also called **Client Isolation** or **Guest Network Mode**). This setting prevents Wi-Fi devices from talking to one another.

**Fix**:
- Connect both devices to your main 2.4 GHz or 5 GHz home Wi-Fi network rather than a "Guest" network.
- In router settings, disable "AP Isolation" / "Client Isolation" if enabled.

---

## 3. Issue: Laptop LAN IP Address Changed

When your laptop reconnects to Wi-Fi, the router's DHCP server may assign a new IP address (e.g., changing from `192.168.1.140` to `192.168.1.185`).

**Fix**:
1. Run `start_stocksense_lan.bat` — it automatically re-detects the active IP and prints the new URL.
2. Alternatively, check your current IP in PowerShell:
   ```powershell
   (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*").IPAddress
   ```
3. Update your mobile browser bookmark to the new IP address.
4. *(Optional)* In your router's administration page, assign a **DHCP Static Lease / Reserved IP** to your laptop's MAC address so its IP never changes.

---

## 4. Issue: "Port 3000 or 8000 already in use"

If another program or a previous instance of Node/Python is running:

**Fix**:
Find and terminate the occupying process in PowerShell:
```powershell
# Find what is using port 3000
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess

# Find what is using port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess

# Kill process if necessary (replace <PID> with process ID)
Stop-Process -Id <PID> -Force
```
Then restart `start_stocksense_lan.bat`.

---

## 5. Issue: Device Access Pending Screen Never Updates

If you approved the device in the Admin Panel, but the mobile screen continues showing "Pending Approval":

**Checks**:
1. Verify the device is listed as **APPROVED** in `http://localhost:3000/admin` (LAN Access tab).
2. Tap **Cancel / Edit Device Name** on the mobile screen and submit the access request again.
3. If using Private Browsing / Incognito mode on mobile, cookies or `localStorage` might be reset when closing tabs. Use normal browsing mode for persistent authorization.

---

## 6. Diagnostic API Endpoints

You can verify the backend health directly from any browser on the LAN:

| URL | Expected Response |
| :--- | :--- |
| `http://<LAPTOP_LAN_IP>:3000/health` | `{"status":"healthy","app":"StockSense AI",...}` |
| `http://<LAPTOP_LAN_IP>:3000/api/v1/lan/status` | `{"status":"online","host_ip":"...",...}` |
| `http://<LAPTOP_LAN_IP>:3000/docs` | Interactive Swagger API Documentation |
