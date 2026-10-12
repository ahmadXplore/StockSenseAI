/**
 * StockSense AI — LAN Device Authentication & Fingerprinting Client Service
 * Handles device UUID generation, secret token persistence, client polling,
 * friendly name detection, and local host loopback recognition.
 */

const STORAGE_DEVICE_ID = "stocksense_device_id";
const STORAGE_DEVICE_TOKEN = "stocksense_device_token";
const STORAGE_DEVICE_NAME = "stocksense_device_name";

export interface DeviceStatusResult {
  deviceId: string;
  deviceName: string;
  status: "APPROVED" | "PENDING" | "REJECTED" | "REVOKED" | "NOT_REGISTERED";
  isApproved: boolean;
  isServerHost: boolean;
  token?: string | null;
  rejectionReason?: string | null;
}

export interface DeviceRegisterResult {
  status: string;
  isApproved: boolean;
  isServerHost: boolean;
  deviceId: string;
  deviceName: string;
  token?: string | null;
  message: string;
}

/** Cookie helper to read a specific cookie */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(^|;\\s*)(${name})=([^;]*)`));
  return match ? decodeURIComponent(match[3]) : null;
}

/** Cookie helper to write a persistent cookie */
function setCookie(name: string, value: string, maxAgeDays = 365): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeDays * 86400}; SameSite=Lax`;
}

/** Removes a cookie */
function removeCookie(name: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; path=/; max-age=0`;
}

/**
 * Detects whether the current browser is running locally on the Windows laptop server.
 */
export function isLocalHost(): boolean {
  if (typeof window === "undefined") return false;
  const h = window.location.hostname.toLowerCase();
  return h === "localhost" || h === "127.0.0.1" || h === "::1" || h === "0.0.0.0";
}

/**
 * Generates a human-friendly device label based on the browser User-Agent.
 */
export function detectDeviceFriendlyName(): string {
  if (typeof navigator === "undefined") return "Client Terminal";

  const ua = navigator.userAgent;
  let os = "Device";
  if (/iPhone/i.test(ua)) os = "iPhone";
  else if (/iPad/i.test(ua)) os = "iPad";
  else if (/Android/i.test(ua)) os = "Android";
  else if (/Macintosh|Mac OS/i.test(ua)) os = "Mac";
  else if (/Windows/i.test(ua)) os = "Windows PC";
  else if (/Linux/i.test(ua)) os = "Linux";

  let browser = "Browser";
  if (/Edg\//i.test(ua)) browser = "Edge";
  else if (/Chrome\//i.test(ua)) browser = "Chrome";
  else if (/Safari\//i.test(ua) && !/Chrome\//i.test(ua)) browser = "Safari";
  else if (/Firefox\//i.test(ua)) browser = "Firefox";

  return `${browser} on ${os}`;
}

/**
 * Returns or generates a persistent device UUID.
 */
export function getDeviceId(): string {
  if (typeof window === "undefined") return "server-side-host";

  // Check localStorage then cookie
  let deviceId = localStorage.getItem(STORAGE_DEVICE_ID) || getCookie(STORAGE_DEVICE_ID);
  if (!deviceId) {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      deviceId = `dev_${crypto.randomUUID()}`;
    } else {
      deviceId = `dev_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    }
    localStorage.setItem(STORAGE_DEVICE_ID, deviceId);
    setCookie(STORAGE_DEVICE_ID, deviceId);
  }

  return deviceId;
}

/**
 * Retrieves the cryptographic device authorization token if approved.
 */
export function getDeviceToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_DEVICE_TOKEN) || getCookie(STORAGE_DEVICE_TOKEN) || null;
}

/**
 * Stores the issued device authorization token.
 */
export function setDeviceToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_DEVICE_TOKEN, token);
  setCookie(STORAGE_DEVICE_TOKEN, token);
}

/**
 * Clears stored device authentication credentials.
 */
export function clearDeviceAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_DEVICE_TOKEN);
  removeCookie(STORAGE_DEVICE_TOKEN);
}

/**
 * Checks the current device authorization status against the LAN backend.
 */
export async function checkDeviceStatus(): Promise<DeviceStatusResult> {
  const deviceId = getDeviceId();
  const token = getDeviceToken();

  // Localhost laptop is always immediately approved
  if (isLocalHost()) {
    return {
      deviceId,
      deviceName: "Host Laptop (Local Server)",
      status: "APPROVED",
      isApproved: true,
      isServerHost: true,
      token,
    };
  }

  try {
    const headers: Record<string, string> = {
      "X-Device-ID": deviceId,
      "X-Client-Type": "remote-lan",
    };
    if (token) {
      headers["X-Device-Token"] = token;
    }

    const res = await fetch(`/api/v1/lan/devices/check?device_id=${encodeURIComponent(deviceId)}`, {
      method: "GET",
      headers,
    });

    if (res.ok) {
      const data = await res.json();
      if (data.status === "APPROVED" && data.token) {
        setDeviceToken(data.token);
      }
      return {
        deviceId: data.device_id || deviceId,
        deviceName: data.device_name || detectDeviceFriendlyName(),
        status: data.status,
        isApproved: data.is_approved,
        isServerHost: data.is_server_host || false,
        token: data.token || getDeviceToken(),
        rejectionReason: data.rejection_reason,
      };
    }

    // Handled non-200 responses
    return {
      deviceId,
      deviceName: detectDeviceFriendlyName(),
      status: "NOT_REGISTERED",
      isApproved: false,
      isServerHost: false,
    };
  } catch {
    return {
      deviceId,
      deviceName: detectDeviceFriendlyName(),
      status: "NOT_REGISTERED",
      isApproved: false,
      isServerHost: false,
    };
  }
}

/**
 * Submits an access request for the current device.
 */
export async function requestDeviceAccess(customName?: string): Promise<DeviceRegisterResult> {
  const deviceId = getDeviceId();
  const friendlyName = customName?.trim() || detectDeviceFriendlyName();
  localStorage.setItem(STORAGE_DEVICE_NAME, friendlyName);

  const res = await fetch("/api/v1/lan/devices/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Device-ID": deviceId,
      "X-Client-Type": "remote-lan",
    },
    body: JSON.stringify({
      device_identifier: deviceId,
      device_name: friendlyName,
      user_agent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to submit device access request." }));
    throw new Error(err.detail || "Device registration failed");
  }

  const data: DeviceRegisterResult = await res.json();
  if (data.token) {
    setDeviceToken(data.token);
  }
  return data;
}
