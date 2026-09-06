"use client";

import { Globe, Check, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { SUPPORTED_MARKETS_CONFIG, MarketMeta } from "@/lib/market";

interface MarketSelectorProps {
  selectedMarket: string;
  onSelectMarket: (marketCode: string) => void;
  className?: string;
}

export function MarketSelector({
  selectedMarket,
  onSelectMarket,
  className = "",
}: MarketSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const current = SUPPORTED_MARKETS_CONFIG[selectedMarket.toUpperCase()] || SUPPORTED_MARKETS_CONFIG.US;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-background-elevated border border-border hover:border-brand/40 text-xs font-semibold text-white transition-all shadow-sm"
      >
        <span className="text-sm">{current.flag}</span>
        <span>{current.name}</span>
        <span className="text-gray-500 font-mono text-[10px]">({current.currency})</span>
        <ChevronDown className="h-3 w-3 text-gray-400 ml-1" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-1.5 w-56 rounded-xl bg-[#0F1422] border border-border shadow-2xl z-50 overflow-hidden py-1">
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-border/50">
            Select Active Market
          </div>
          {Object.values(SUPPORTED_MARKETS_CONFIG).map((m: MarketMeta) => {
            const isSelected = m.code === current.code;
            return (
              <button
                key={m.code}
                onClick={() => {
                  onSelectMarket(m.code);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 text-xs transition-colors ${
                  isSelected
                    ? "bg-brand/15 text-brand font-semibold"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">{m.flag}</span>
                  <span>{m.name}</span>
                  <span className="text-gray-500 text-[10px]">({m.code})</span>
                </div>
                {isSelected && <Check className="h-3.5 w-3.5 text-brand" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
