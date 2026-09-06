"use client";

import { useEffect } from "react";
import { Bot, Sparkles, TrendingUp, Shield, BarChart3, Layers, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { QueryChatbot } from "@/components/chatbot/QueryChatbot";

export default function ChatPage() {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand/10 border border-brand/30 text-brand text-xs font-semibold">
          <Sparkles className="w-4 h-4 text-yellow-400" />
          StockSense AI Copilot Suite
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Institutional Market Intelligence & Quantitative Copilot
        </h1>

        <p className="text-sm sm:text-base text-gray-400 leading-relaxed">
          Access full-spectrum financial intelligence covering PSX & Global equity valuation, 
          80% Conformal Prediction intervals, technical indicator confluence, and exchange microstructure.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left pt-4">
          <div className="p-4 rounded-xl bg-background-elevated border border-border">
            <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm mb-1">
              <TrendingUp className="w-4 h-4" />
              <span>Fundamental Analysis</span>
            </div>
            <p className="text-xs text-gray-400">
              Deep dive into P/E, PEG, EV/EBITDA, ROE, FCF yields, and financial statements.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-background-elevated border border-border">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm mb-1">
              <Shield className="w-4 h-4" />
              <span>PSX & Exchange Rules</span>
            </div>
            <p className="text-xs text-gray-400">
              Circuit breakers (±7.5%), T+2 rolling settlement, deliverable futures, and SECP limits.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-background-elevated border border-border">
            <div className="flex items-center gap-2 text-purple-400 font-semibold text-sm mb-1">
              <BarChart3 className="w-4 h-4" />
              <span>Quantitative Risk Bounds</span>
            </div>
            <p className="text-xs text-gray-400">
              Non-parametric 80% Conformal Prediction intervals, Value at Risk (VaR), and Sharpe ratios.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-background-elevated border border-border">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm mb-1">
              <Layers className="w-4 h-4" />
              <span>Strategy Backtesting</span>
            </div>
            <p className="text-xs text-gray-400">
              Mean-reversion, breakout strategies, trend filters, and portfolio rebalancing.
            </p>
          </div>
        </div>

        <div className="pt-4 flex items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-4 py-2 bg-background-elevated hover:bg-background-hover border border-border rounded-xl text-xs font-semibold text-gray-300 hover:text-white transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Embedded Copilot Interface */}
      <QueryChatbot />
    </div>
  );
}
