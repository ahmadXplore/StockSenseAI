"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Wifi, Shield, Server, Smartphone, Laptop, Radio, Copy,
  CheckCircle2, AlertTriangle, ExternalLink, ArrowLeft, RefreshCw
} from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId, detectDeviceFriendlyName, isLocalHost } from "@/lib/deviceAuth";
import { BackButton } from "@/components/BackButton";

export default function LanSettingsPage() {
  const [lanStatus, setLanStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [deviceId, setDeviceId] = useState("");
  const [friendlyName, setFriendlyName] = useState("");
  const [isHost, setIsHost] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const data = await api.lan.getStatus();
      setLanStatus(data);
    } catch (err) {
      console.error("Failed to load LAN status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setDeviceId(getDeviceId());
    setFriendlyName(detectDeviceFriendlyName());
    setIsHost(isLocalHost());
    fetchStatus();
  }, []);

  const lanUrl = lanStatus?.lan_access_url || `http://${lanStatus?.host_ip || "127.0.0.1"}:3005`;

  return (
    <div className="space-y-8 py-4 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/settings" label="Back to Settings" />
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold uppercase tracking-wider">
              <Wifi className="h-3 w-3" />
              <span>Native Private LAN Server</span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            LAN Server &amp; Controlled Device Access
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
            Host StockSense AI on your local Wi-Fi/Ethernet network. Connect phones, tablets, and secondary laptops with zero cloud exposure or Docker overhead.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-background-elevated border border-border text-gray-300 hover:text-white text-xs font-semibold transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-brand" : ""}`} />
            <span>Refresh</span>
          </button>
          <Link
            href="/admin"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20"
          >
            <Shield className="h-4 w-4" />
            <span>Open Admin Panel</span>
          </Link>
        </div>
      </div>

      {/* Network Server Card */}
      <div className="bg-[#0B0F19] border border-border/80 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center justify-between border-b border-border/50 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span>Windows Native Host Status</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  {lanStatus?.status === "online" ? "ONLINE" : "INITIALIZING"}
                </span>
              </h2>
              <p className="text-xs text-gray-400 font-mono">
                Unified Port Architecture: Web &amp; API on Port 3005
              </p>
            </div>
          </div>
        </div>

        {/* Server Endpoints Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-[#080B13] border border-border/60 space-y-2">
            <div className="text-gray-400 font-sans flex items-center justify-between">
              <span>LAN Access URL</span>
              <Radio className="h-3.5 w-3.5 text-emerald-400" />
            </div>
            <div className="text-sm font-extrabold text-white break-all">
              {lanUrl}
            </div>
            <div className="pt-1 font-sans flex justify-end">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(lanUrl);
                  setCopiedUrl(true);
                  setTimeout(() => setCopiedUrl(false), 2000);
                }}
                className="text-[11px] text-brand hover:text-brand-hover flex items-center gap-1 font-mono"
              >
                <Copy className="h-3 w-3" />
                <span>{copiedUrl ? "Copied to Clipboard!" : "Copy LAN URL"}</span>
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#080B13] border border-border/60 space-y-2">
            <div className="text-gray-400 font-sans flex items-center justify-between">
              <span>Local Loopback</span>
              <Laptop className="h-3.5 w-3.5 text-brand" />
            </div>
            <div className="text-sm font-extrabold text-gray-200">
              http://localhost:3005
            </div>
            <p className="text-[11px] text-gray-500 font-sans">
              Auto-approved on laptop host (Never locked out)
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#080B13] border border-border/60 space-y-2">
            <div className="text-gray-400 font-sans flex items-center justify-between">
              <span>Internal Services</span>
              <Shield className="h-3.5 w-3.5 text-blue-400" />
            </div>
            <div className="text-[11px] text-gray-300 space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-400">FastAPI Backend:</span>
                <span className="text-white">Port 8005 (Internal)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Next.js Proxy:</span>
                <span className="text-emerald-400">Port 3005 (Unified)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Storage:</span>
                <span className="text-white">Native SQLite / PG</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Current Device Profile */}
      <div className="bg-[#0B0F19] border border-border/80 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-border/50 pb-3">
          <div className="flex items-center gap-2">
            <Smartphone className="h-4 w-4 text-brand" />
            <h3 className="text-sm font-bold text-white">Current Client Terminal Profile</h3>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            {isHost ? "HOST SERVER DEVICE" : "AUTHORIZED REMOTE CLIENT"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-[#080B13] border border-border/60 space-y-1">
            <span className="text-gray-400 font-sans">Detected Device Name</span>
            <div className="text-sm font-bold text-white">{friendlyName}</div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#080B13] border border-border/60 space-y-1">
            <div className="flex justify-between items-center font-sans">
              <span className="text-gray-400">Device Fingerprint UUID</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(deviceId);
                  setCopiedId(true);
                  setTimeout(() => setCopiedId(false), 2000);
                }}
                className="text-[10px] text-brand hover:text-brand-hover flex items-center gap-1 font-mono"
              >
                <Copy className="h-3 w-3" />
                <span>{copiedId ? "Copied!" : "Copy"}</span>
              </button>
            </div>
            <div className="text-xs text-emerald-400 truncate">{deviceId}</div>
          </div>
        </div>
      </div>

      {/* Step-by-Step Mobile / LAN Connection Guide */}
      <div className="bg-[#0B0F19] border border-border/80 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex items-center gap-2 border-b border-border/50 pb-3">
          <Wifi className="h-4 w-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white">
            Connecting Phones, Tablets &amp; Other Laptops
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs text-gray-300">
          <div className="p-4 rounded-xl bg-[#080B13] border border-border/60 space-y-2.5">
            <div className="flex items-center gap-2 text-white font-bold">
              <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono text-[11px]">1</span>
              <span>Connect to Same Wi-Fi</span>
            </div>
            <p className="text-gray-400 leading-relaxed">
              Make sure your smartphone or tablet is connected to the same private home or office Wi-Fi network as this laptop.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#080B13] border border-border/60 space-y-2.5">
            <div className="flex items-center gap-2 text-white font-bold">
              <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono text-[11px]">2</span>
              <span>Open the Server URL</span>
            </div>
            <p className="text-gray-400 leading-relaxed">
              On mobile Chrome or Safari, navigate to:
              <br />
              <span className="font-mono text-emerald-400 font-semibold">{lanUrl}</span>
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#080B13] border border-border/60 space-y-2.5">
            <div className="flex items-center gap-2 text-white font-bold">
              <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono text-[11px]">3</span>
              <span>Approve from Laptop</span>
            </div>
            <p className="text-gray-400 leading-relaxed">
              The mobile screen will display the pending authorization screen. Click <Link href="/admin" className="text-brand font-semibold underline">Approve Device</Link> on your laptop admin panel to immediately unlock the terminal on the phone!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
