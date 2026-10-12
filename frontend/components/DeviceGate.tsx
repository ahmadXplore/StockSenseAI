"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  isLocalHost,
  getDeviceId,
  getDeviceToken,
  clearDeviceAuth,
  checkDeviceStatus,
  requestDeviceAccess,
  detectDeviceFriendlyName,
  DeviceStatusResult,
} from "@/lib/deviceAuth";

interface DeviceGateProps {
  children: React.ReactNode;
}

export function DeviceGate({ children }: DeviceGateProps) {
  const [isClient, setIsClient] = useState(false);
  const [status, setStatus] = useState<"CHECKING" | "APPROVED" | "PENDING" | "REJECTED" | "REVOKED" | "NOT_REGISTERED">("CHECKING");
  const [deviceId, setDeviceId] = useState<string>("");
  const [deviceName, setDeviceName] = useState<string>("");
  const [customName, setCustomName] = useState<string>("");
  const [rejectionReason, setRejectionReason] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pollCount, setPollCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Initial client check
  useEffect(() => {
    setIsClient(true);
    const id = getDeviceId();
    setDeviceId(id);
    const defaultName = detectDeviceFriendlyName();
    setDeviceName(defaultName);
    setCustomName(defaultName);

    // Host laptop running directly on localhost bypasses the gate instantly
    if (isLocalHost()) {
      setStatus("APPROVED");
      return;
    }

    // Remote LAN client: check initial status
    checkDeviceStatus()
      .then((res: DeviceStatusResult) => {
        if (res.isApproved) {
          setStatus("APPROVED");
        } else if (res.status === "PENDING") {
          setStatus("PENDING");
          if (res.deviceName) setDeviceName(res.deviceName);
        } else if (res.status === "REJECTED" || res.status === "REVOKED") {
          setStatus(res.status);
          setRejectionReason(res.rejectionReason || null);
        } else {
          setStatus("NOT_REGISTERED");
        }
      })
      .catch(() => {
        setStatus("NOT_REGISTERED");
      });
  }, []);

  // Polling loop when device is PENDING — checks every 3s for approval
  useEffect(() => {
    if (status !== "PENDING" || !isClient || isLocalHost()) return;

    const interval = setInterval(async () => {
      try {
        const res = await checkDeviceStatus();
        setPollCount((prev) => prev + 1);
        if (res.isApproved) {
          setStatus("APPROVED");
        } else if (res.status === "REJECTED" || res.status === "REVOKED") {
          setStatus(res.status);
          setRejectionReason(res.rejectionReason || null);
        }
      } catch {
        // Silently retry polling
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [status, isClient]);

  // Re-validation poll for APPROVED remote devices — every 30s
  // This ensures revoke/reject takes effect immediately without page refresh.
  useEffect(() => {
    if (status !== "APPROVED" || !isClient || isLocalHost()) return;

    const interval = setInterval(async () => {
      try {
        const res = await checkDeviceStatus();
        if (res.status === "REVOKED" || res.status === "REJECTED") {
          setStatus(res.status);
          setRejectionReason(res.rejectionReason || null);
        } else if (!res.isApproved && res.status !== "APPROVED") {
          // Device was de-registered or invalidated
          setStatus("NOT_REGISTERED");
        }
      } catch {
        // Silently skip — no network disruption
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [status, isClient]);


  const handleRequestAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await requestDeviceAccess(customName);
      if (res.isApproved) {
        setStatus("APPROVED");
      } else {
        setStatus("PENDING");
        setDeviceName(res.deviceName || customName);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit device access request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    clearDeviceAuth();
    setStatus("NOT_REGISTERED");
    setRejectionReason(null);
    setErrorMessage(null);
  };

  const handleCopyId = () => {
    if (typeof navigator !== "undefined" && deviceId) {
      navigator.clipboard.writeText(deviceId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // 1. Server-side rendering fallback or instant localhost approval
  if (!isClient || status === "APPROVED") {
    return <>{children}</>;
  }

  // 2. Initial checking state
  if (status === "CHECKING") {
    return (
      <div className="min-h-screen bg-[#0a0d14] flex flex-col items-center justify-center p-4">
        <div className="relative flex flex-col items-center max-w-md w-full p-8 rounded-2xl bg-[#111622] border border-[#1e2638] shadow-2xl text-center">
          <div className="w-12 h-12 rounded-full border-2 border-emerald-500/30 border-t-emerald-400 animate-spin mb-4" />
          <h2 className="text-lg font-semibold text-white tracking-wide">StockSense AI Terminal</h2>
          <p className="text-xs text-gray-400 mt-1">Verifying LAN device credentials...</p>
        </div>
      </div>
    );
  }

  // 3. Pending approval state
  if (status === "PENDING") {
    return (
      <div className="min-h-screen bg-[#07090e] flex flex-col items-center justify-center p-4 sm:p-6">
        {/* Glow ambient background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-amber-500/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative max-w-lg w-full rounded-2xl bg-[#0f1420] border border-amber-500/30 p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
          {/* Header */}
          <div className="flex items-center justify-between pb-6 border-b border-border/40">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <svg className="w-5 h-5 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-wide">Access Authorization Pending</h1>
                <p className="text-xs text-amber-400/90 font-mono">STATUS: AWAITING_ADMIN_APPROVAL</p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
              LAN Gate
            </span>
          </div>

          {/* Body */}
          <div className="py-6 space-y-4">
            <p className="text-sm text-gray-300 leading-relaxed">
              Your device has submitted an authorization request to the <span className="text-white font-medium">StockSense AI Server</span>.
              Please approve this device from the <span className="text-emerald-400 font-medium">Admin Panel</span> on your host laptop.
            </p>

            {/* Device Info Card */}
            <div className="p-4 rounded-xl bg-[#090d16] border border-border/60 space-y-2.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Device Name:</span>
                <span className="text-white font-medium">{deviceName}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Device ID:</span>
                <div className="flex items-center space-x-1.5">
                  <span className="font-mono text-emerald-400">{deviceId.substring(0, 16)}...</span>
                  <button
                    onClick={handleCopyId}
                    type="button"
                    className="p-1 text-gray-400 hover:text-white transition-colors"
                    title="Copy full Device ID"
                  >
                    {copied ? (
                      <span className="text-[10px] text-emerald-400">Copied!</span>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Network Host:</span>
                <span className="font-mono text-gray-300">{typeof window !== "undefined" ? window.location.host : ""}</span>
              </div>
            </div>

            {/* Polling indicator */}
            <div className="flex items-center justify-center space-x-2.5 py-2 text-xs text-gray-400">
              <div className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500" />
              </div>
              <span>Listening for approval ({pollCount > 0 ? `checked ${pollCount}x` : "live connection"})...</span>
            </div>
          </div>

          {/* Footer actions */}
          <div className="pt-4 border-t border-border/40 flex justify-between items-center text-xs">
            <button
              type="button"
              onClick={handleRetry}
              className="text-gray-400 hover:text-gray-200 transition-colors"
            >
              Cancel / Edit Device Name
            </button>
            <span className="text-gray-500 font-mono">Auto-refreshes on approval</span>
          </div>
        </div>
      </div>
    );
  }

  // 4. Blocked / Revoked / Rejected state
  if (status === "REJECTED" || status === "REVOKED") {
    return (
      <div className="min-h-screen bg-[#07090e] flex flex-col items-center justify-center p-4 sm:p-6">
        <div className="relative max-w-lg w-full rounded-2xl bg-[#0f1420] border border-red-500/30 p-6 sm:p-8 shadow-2xl">
          <div className="flex items-center space-x-3 pb-6 border-b border-border/40">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-wide">Access Restricted</h1>
              <p className="text-xs text-red-400 font-mono">STATUS: {status}</p>
            </div>
          </div>

          <div className="py-6 space-y-4">
            <p className="text-sm text-gray-300">
              Access to this StockSense AI LAN terminal was {status.toLowerCase()} by an administrator.
            </p>
            {rejectionReason && (
              <div className="p-3.5 rounded-xl bg-red-950/20 border border-red-800/40 text-xs text-red-300">
                <span className="font-semibold text-red-200">Reason:</span> {rejectionReason}
              </div>
            )}
            <div className="p-3.5 rounded-xl bg-[#090d16] border border-border/60 text-xs text-gray-400 space-y-1">
              <div>Device ID: <span className="font-mono text-gray-300">{deviceId}</span></div>
            </div>
          </div>

          <div className="pt-4 border-t border-border/40 flex justify-end">
            <button
              onClick={handleRetry}
              type="button"
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/20 text-white transition-colors"
            >
              Submit New Request
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 5. Not Registered — Registration Form
  return (
    <div className="min-h-screen bg-[#07090e] flex flex-col items-center justify-center p-4 sm:p-6">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/5 blur-[150px] rounded-full pointer-events-none" />

      <div className="relative max-w-lg w-full rounded-2xl bg-[#0f1420] border border-border/60 p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
        {/* Header */}
        <div className="flex items-center space-x-3 pb-6 border-b border-border/40">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-wide">StockSense AI LAN Gate</h1>
            <p className="text-xs text-gray-400 font-mono">Private Network Security</p>
          </div>
        </div>

        {/* Content */}
        <form onSubmit={handleRequestAccess} className="py-6 space-y-4">
          <p className="text-sm text-gray-300 leading-relaxed">
            This server is hosted natively on your local network. Remote devices must be authorized by an administrator before accessing financial data or running predictions.
          </p>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-300" htmlFor="deviceName">
              Device Name / Identification:
            </label>
            <input
              id="deviceName"
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="e.g. Ahmad's iPhone, Living Room Tablet"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#090d16] border border-border/80 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
              required
              minLength={2}
              maxLength={100}
            />
            <p className="text-[11px] text-gray-500">
              This label will appear on the administrator's terminal for one-click approval.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#090d16] border border-border/60 space-y-1.5 text-xs text-gray-400">
            <div className="flex justify-between">
              <span>Device Fingerprint:</span>
              <span className="font-mono text-emerald-400">{deviceId.substring(0, 18)}...</span>
            </div>
            <div className="flex justify-between">
              <span>Host Address:</span>
              <span className="font-mono text-gray-300">{typeof window !== "undefined" ? window.location.host : ""}</span>
            </div>
          </div>

          {errorMessage && (
            <div className="p-3 rounded-xl bg-red-950/30 border border-red-800/40 text-xs text-red-300">
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !customName.trim()}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black shadow-lg shadow-emerald-500/10 transition-all flex items-center justify-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                <span>Submitting Request...</span>
              </>
            ) : (
              <span>Request Device Access</span>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-border/40 text-center text-[11px] text-gray-500">
          StockSense AI Native LAN Perimeter Protection
        </div>
      </div>
    </div>
  );
}
