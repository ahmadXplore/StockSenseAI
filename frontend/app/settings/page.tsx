"use client";

import Link from "next/link";
import { useState } from "react";
import { Settings, Bell, Sliders, Shield, DollarSign, ExternalLink } from "lucide-react";
import { BackButton } from "@/components/BackButton";

export default function SettingsPage() {
  const [defaultAmount, setDefaultAmount] = useState(10000);
  const [defaultRisk, setDefaultRisk] = useState("moderate");
  const [earningsAlerts, setEarningsAlerts] = useState(true);
  const [stopLossAlerts, setStopLossAlerts] = useState(true);
  const [anomalyAlerts, setAnomalyAlerts] = useState(true);

  return (
    <div className="max-w-2xl mx-auto py-6 space-y-8">
      <div className="space-y-2 border-b border-border/60 pb-4">
        <div className="flex items-center gap-2">
          <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
          <span className="text-xs font-mono text-brand font-semibold uppercase">Preferences</span>
        </div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="h-5 w-5 text-brand" />
          Platform Settings &amp; Preferences
        </h1>
        <p className="text-xs text-gray-400">Configure default analysis values, notification triggers, and data feeds.</p>
      </div>

      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-6">
        {/* Default Analysis Parameters */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border pb-2">
            <Sliders className="h-4 w-4 text-brand" /> Default Analysis Parameters
          </h2>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-gray-300">Default Simulation Capital (USD)</label>
            <input
              type="number"
              value={defaultAmount}
              onChange={(e) => setDefaultAmount(Number(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-white font-mono text-sm focus:outline-none focus:border-brand"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-gray-300">Default Risk Profile</label>
            <select
              value={defaultRisk}
              onChange={(e) => setDefaultRisk(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-white text-sm focus:outline-none focus:border-brand"
            >
              <option value="conservative">Conservative (Capital preservation priority)</option>
              <option value="moderate">Moderate (Balanced risk-reward)</option>
              <option value="aggressive">Aggressive (Higher return targets)</option>
            </select>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-border pb-2">
            <Bell className="h-4 w-4 text-brand" /> In-App Alert Subscriptions
          </h2>

          <div className="space-y-3 text-xs">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-gray-300">Earnings Announcement Proximity (&lt;14 days)</span>
              <input
                type="checkbox"
                checked={earningsAlerts}
                onChange={(e) => setEarningsAlerts(e.target.checked)}
                className="rounded bg-background border-border text-brand focus:ring-0"
              />
            </label>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-gray-300">Stop-Loss Threshold Proximity Warnings</span>
              <input
                type="checkbox"
                checked={stopLossAlerts}
                onChange={(e) => setStopLossAlerts(e.target.checked)}
                className="rounded bg-background border-border text-brand focus:ring-0"
              />
            </label>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-gray-300">Statistical Anomaly Drop Detection Alerts</span>
              <input
                type="checkbox"
                checked={anomalyAlerts}
                onChange={(e) => setAnomalyAlerts(e.target.checked)}
                className="rounded bg-background border-border text-brand focus:ring-0"
              />
            </label>
          </div>
        </div>

        {/* Plan / Subscription Route Link */}
        <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
          <span className="text-gray-400">Account Plan: <strong className="text-white">Community Free Tier</strong></span>
          <Link href="/settings/subscription" className="text-brand hover:underline flex items-center gap-1">
            View details <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </div>
    </div>
  );
}
