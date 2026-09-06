"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ShieldCheck, ArrowLeft, AlertTriangle, CheckCircle, FileText } from "lucide-react";

export default function PositionThesisPage() {
  const params = useParams();
  const ticker = (params.ticker as string || "AAPL").toUpperCase();

  return (
    <div className="max-w-3xl mx-auto py-6 space-y-6">
      <Link href="/portfolio" className="text-xs text-gray-400 hover:text-white flex items-center gap-1.5 font-medium">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Portfolio
      </Link>

      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white font-mono">{ticker} Thesis Validation</h1>
            <p className="text-xs text-gray-400">Continuous check against initial entry hypotheses and risk parameters.</p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-signal-strongBuy/10 text-signal-strongBuy border border-signal-strongBuy/20">
            ✓ THESIS HEALTHY
          </span>
        </div>

        {/* Original Thesis Statement */}
        <div className="p-4 bg-background border border-border rounded-lg space-y-2">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-brand" /> Original Entry Hypothesis
          </div>
          <p className="text-xs text-gray-200 leading-relaxed font-sans">
            Bought at $195.00 based on strong Free Cash Flow expansion (+18% YoY), low debt-to-EBITDA ratio (0.8x), and favorable 1-year DCF upside potential.
          </p>
        </div>

        {/* Automated Health Audit Checkpoints */}
        <div className="space-y-3">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Automated Audit Checks</div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-3 bg-background border border-border rounded-lg">
              <span className="text-gray-300">Hard Veto Triggers Active</span>
              <span className="text-signal-strongBuy font-semibold font-mono">0 Triggered (Safe)</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-background border border-border rounded-lg">
              <span className="text-gray-300">Fundamental Health Score Shift</span>
              <span className="text-signal-strongBuy font-semibold font-mono">+4 pts (Improving)</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-background border border-border rounded-lg">
              <span className="text-gray-300">Stop-Loss Distance Buffer</span>
              <span className="text-signal-strongBuy font-semibold font-mono">+7.9% above Hard Stop</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
