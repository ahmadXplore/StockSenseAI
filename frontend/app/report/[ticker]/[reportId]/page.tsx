"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import { 
  ShieldCheck, AlertTriangle, TrendingUp, DollarSign, Activity, 
  BarChart, Compass, FileText, CheckCircle, Clock
} from "lucide-react";

export default function StockReportPage() {
  const params = useParams();
  const ticker = (params.ticker as string || "AAPL").toUpperCase();
  const reportId = params.reportId as string;

  const [activeSection, setActiveSection] = useState("executive");

  const sidebarLinks = [
    { id: "executive", label: "Executive Summary" },
    { id: "forecast", label: "Price Forecast Table" },
    { id: "scores", label: "Score Dashboard" },
    { id: "calculator", label: "Investment Calculator" },
    { id: "fundamentals", label: "Fundamental Analysis" },
    { id: "technicals", label: "Technical Analysis" },
    { id: "valuation", label: "Valuation Analysis" },
    { id: "sentiment", label: "News & Sentiment" },
    { id: "risk", label: "Risk Analysis" },
    { id: "exit", label: "Exit Strategy Plan" },
    { id: "backtesting", label: "Backtesting Validation" },
  ];

  return (
    <div className="flex flex-col lg:flex-row gap-8 py-4">
      {/* Sticky Desktop Navigation Sidebar */}
      <aside className="w-full lg:w-64 shrink-0 space-y-2">
        <div className="bg-background-elevated border border-border rounded-xl p-4 sticky top-24 space-y-1">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider px-3 py-2">
            Report Sections
          </div>
          {sidebarLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => setActiveSection(link.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                activeSection === link.id
                  ? "bg-brand text-white font-semibold"
                  : "text-gray-400 hover:text-white hover:bg-background-hover"
              }`}
            >
              <span>{link.label}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* Main Report Content */}
      <div className="flex-1 space-y-6">
        {/* Top Report Header Banner */}
        <div className="bg-background-elevated border border-border rounded-xl p-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold text-white font-mono">{ticker}</h1>
              <span className="text-sm text-gray-400">Apple Inc.</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-signal-strongBuy/10 text-signal-strongBuy border border-signal-strongBuy/20">
                🟢 BUY
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1 flex items-center gap-3">
              <span>Sector: Technology</span>
              <span>•</span>
              <span>Report ID: <span className="font-mono">{reportId}</span></span>
              <span>•</span>
              <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> Data as of: ~15m delayed</span>
            </div>
          </div>

          <div className="text-right">
            <div className="text-2xl font-bold font-mono text-white">$225.50</div>
            <div className="text-xs font-semibold text-signal-buy flex items-center justify-end gap-1">
              <TrendingUp className="h-3 w-3" /> +1.20% today
            </div>
          </div>
        </div>

        {/* Executive Summary Card */}
        <section className="bg-background-elevated border border-border rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="h-4 w-4 text-brand" />
            Executive Summary
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 tabular-nums">
            <div className="p-4 bg-background border border-border rounded-lg space-y-1">
              <div className="text-xs text-gray-400">Composite Health Score</div>
              <div className="text-2xl font-bold text-signal-strongBuy font-mono">78/100</div>
              <div className="text-[10px] text-gray-500">Strong fundamentals + low debt</div>
            </div>
            <div className="p-4 bg-background border border-border rounded-lg space-y-1">
              <div className="text-xs text-gray-400">1-Year Base Forecast</div>
              <div className="text-2xl font-bold text-white font-mono">$275.00 (+22%)</div>
              <div className="text-[10px] text-signal-buy">P(Gain): 61% (Calibrated)</div>
            </div>
            <div className="p-4 bg-background border border-border rounded-lg space-y-1">
              <div className="text-xs text-gray-400">Risk Assessment</div>
              <div className="text-2xl font-bold text-signal-hold font-mono">Moderate (44/100)</div>
              <div className="text-[10px] text-gray-500">Beta: 1.24 | Max DD: -27.3%</div>
            </div>
          </div>
        </section>

        {/* Backtesting Note (Mandatory MVP honesty badge) */}
        <div className="p-4 rounded-xl bg-background-elevated border border-border text-xs space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono text-[10px] uppercase font-bold">
              Current-Universe-Approximate
            </span>
            <span className="text-gray-400">Delisted price history gap disclosure</span>
          </div>
          <p className="text-gray-500 text-[11px]">
            Historical index constituents are tracked, but delisted company price data is omitted in MVP due to free-tier constraints.
          </p>
        </div>
      </div>
    </div>
  );
}
