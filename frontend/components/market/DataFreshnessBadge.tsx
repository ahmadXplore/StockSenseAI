"use client";

import { Activity, Clock, Database, ShieldCheck } from "lucide-react";
import { DataFreshnessStatus, DataFreshnessInfo } from "@/lib/types";

interface DataFreshnessBadgeProps {
  status?: DataFreshnessStatus;
  asOfDate?: string;
  source?: string;
  delayMinutes?: number;
  info?: DataFreshnessInfo;
  className?: string;
}

export function DataFreshnessBadge({
  status,
  asOfDate,
  source,
  delayMinutes = 15,
  info,
  className = "",
}: DataFreshnessBadgeProps) {
  const currentStatus = info?.status || status || "LATEST_AVAILABLE_EOD";
  const effectiveSource = info?.source || source || "Canonical Market Data Layer";
  const effectiveDate = info?.asOfDate || asOfDate;

  if (currentStatus === "LIVE") {
    return (
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 ${className}`}
        title={`Live Real-Time Market Feed · ${effectiveSource}`}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span>LIVE</span>
      </div>
    );
  }

  if (currentStatus === "DELAYED") {
    return (
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-500/10 border border-amber-500/20 text-amber-400 ${className}`}
        title={`Market feed delayed by ~${delayMinutes}m · ${effectiveSource}`}
      >
        <Clock className="h-3 w-3" />
        <span>DELAYED ({delayMinutes}m)</span>
      </div>
    );
  }

  // LATEST_AVAILABLE_EOD
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-500/10 border border-blue-500/20 text-blue-300 ${className}`}
      title={`Latest historical daily bar · ${effectiveSource}`}
    >
      <Database className="h-3 w-3 text-blue-400" />
      <span>
        LATEST EOD{effectiveDate ? ` (${effectiveDate})` : ""}
      </span>
    </div>
  );
}
