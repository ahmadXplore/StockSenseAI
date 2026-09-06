"use client";

import { Building2, Check } from "lucide-react";
import { SUPPORTED_MARKETS_CONFIG } from "@/lib/market";

interface ExchangeSelectorProps {
  selectedMarket: string;
  selectedExchange: string;
  onSelectExchange: (exchangeCode: string) => void;
  className?: string;
}

export function ExchangeSelector({
  selectedMarket,
  selectedExchange,
  onSelectExchange,
  className = "",
}: ExchangeSelectorProps) {
  const current = SUPPORTED_MARKETS_CONFIG[selectedMarket.toUpperCase()] || SUPPORTED_MARKETS_CONFIG.US;
  const exchanges = current.exchanges;

  if (exchanges.length <= 1) {
    return (
      <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-background-elevated border border-border text-xs text-gray-300 font-mono ${className}`}>
        <Building2 className="h-3 w-3 text-gray-400" />
        <span>{exchanges[0]}</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-1 bg-background-elevated border border-border p-1 rounded-lg ${className}`}>
      {exchanges.map((ex) => {
        const isSelected = ex.toUpperCase() === selectedExchange.toUpperCase();
        return (
          <button
            key={ex}
            onClick={() => onSelectExchange(ex)}
            className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors ${
              isSelected
                ? "bg-brand text-white shadow-sm"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {ex}
          </button>
        );
      })}
    </div>
  );
}
