"use client";

import Link from "next/link";
import { ArrowLeft, Check, Shield } from "lucide-react";

export default function SubscriptionSettingsPage() {
  return (
    <div className="max-w-2xl mx-auto py-6 space-y-6">
      <Link href="/settings" className="text-xs text-gray-400 hover:text-white flex items-center gap-1.5 font-medium">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Settings
      </Link>

      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-white">Subscription & Usage Limits</h1>
          <p className="text-xs text-gray-400">StockSense AI is 100% free and built with open-source and free data providers.</p>
        </div>

        <div className="p-4 bg-background border border-border rounded-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-white text-sm">Community Tier</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-signal-strongBuy/10 text-signal-strongBuy border border-signal-strongBuy/20">
              Active Forever
            </span>
          </div>

          <ul className="space-y-2 text-xs text-gray-300">
            <li className="flex items-center gap-2">
              <Check className="h-3.5 w-3.5 text-signal-strongBuy" />
              <span>Full 6-horizon ML ensemble forecasting</span>
            </li>
            <li className="flex items-center gap-2">
              <Check className="h-3.5 w-3.5 text-signal-strongBuy" />
              <span>Point-in-time SEC EDGAR fundamental health scoring</span>
            </li>
            <li className="flex items-center gap-2">
              <Check className="h-3.5 w-3.5 text-signal-strongBuy" />
              <span>Hard Veto safety rules & drop anomaly detection</span>
            </li>
            <li className="flex items-center gap-2">
              <Check className="h-3.5 w-3.5 text-signal-strongBuy" />
              <span>100 full analysis reports per day quota</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
