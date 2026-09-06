"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, X, ArrowRight, Building2, TrendingUp } from "lucide-react";
import { api, SecuritySearchResult } from "@/lib/api";
import { SUPPORTED_MARKETS_CONFIG, parseSecurityId } from "@/lib/market";

interface SecuritySearchProps {
  currentMarket?: string;
  placeholder?: string;
  className?: string;
  onSelectSecurity?: (sec: SecuritySearchResult) => void;
  autoFocus?: boolean;
}

export function SecuritySearch({
  currentMarket,
  placeholder = "Search multi-market securities (e.g. ENGRO, AAPL, AZN.L, 7203.T, RELIANCE)...",
  className = "",
  onSelectSecurity,
  autoFocus = false,
}: SecuritySearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SecuritySearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = query.trim();
    if (!q) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        // Try canonical securities search first
        let list: SecuritySearchResult[] = [];
        try {
          list = await api.securities.search(q, currentMarket);
        } catch {
          // Fallback to market search endpoint if available
          const raw = await api.market.search(q, currentMarket);
          list = raw.map((r) => {
            const parsed = parseSecurityId(r.ticker, currentMarket);
            return {
              security_id: parsed.canonicalId,
              ticker: r.ticker,
              name: r.name || r.ticker,
              market_code: parsed.marketCode,
              exchange_code: (r.exchange || parsed.exchangeCode) as any,
              currency: parsed.marketCode === "PK" ? "PKR" : parsed.marketCode === "UK" ? "GBP" : parsed.marketCode === "JP" ? "JPY" : parsed.marketCode === "HK" ? "HKD" : parsed.marketCode === "IN" ? "INR" : "USD",
              sector: r.sector,
              is_active: true,
            };
          });
        }

        if (currentMarket) {
          const mUpper = currentMarket.toUpperCase();
          list = list.filter((s) => s.market_code === mUpper || (mUpper === "PK" && s.exchange_code === "PSX"));
        }

        setResults(list.slice(0, 15));
        setIsOpen(list.length > 0);
      } catch (err) {
        console.error("Search failed:", err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, currentMarket]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (sec: SecuritySearchResult) => {
    setIsOpen(false);
    setQuery("");
    if (onSelectSecurity) {
      onSelectSecurity(sec);
    } else {
      router.push(`/stocks/${encodeURIComponent(sec.security_id)}`);
    }
  };

  return (
    <div className={`relative w-full ${className}`} ref={dropdownRef}>
      <div className="relative flex items-center">
        {loading ? (
          <Loader2 className="absolute left-3.5 h-4 w-4 text-brand animate-spin pointer-events-none" />
        ) : (
          <Search className="absolute left-3.5 h-4 w-4 text-gray-400 pointer-events-none" />
        )}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          autoFocus={autoFocus}
          placeholder={placeholder}
          className="w-full bg-[#0E1422] border border-border focus:border-brand/60 focus:ring-1 focus:ring-brand/40 text-white placeholder-gray-500 text-xs sm:text-sm pl-10 pr-10 py-3 rounded-xl transition-all shadow-inner"
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setResults([]);
              setIsOpen(false);
            }}
            className="absolute right-3 text-gray-500 hover:text-white p-1"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute left-0 right-0 mt-2 bg-[#0E1422] border border-border rounded-xl shadow-2xl z-50 overflow-hidden max-h-96 overflow-y-auto">
          <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-border/50 flex justify-between">
            <span>Multi-Market Securities Found</span>
            <span>{results.length} results</span>
          </div>
          {results.map((sec) => {
            const mkt = SUPPORTED_MARKETS_CONFIG[sec.market_code] || SUPPORTED_MARKETS_CONFIG.US;
            return (
              <button
                key={sec.security_id}
                onClick={() => handleSelect(sec)}
                className="w-full px-4 py-3 text-left hover:bg-white/5 border-b border-border/30 last:border-0 flex items-center justify-between group transition-colors"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{mkt.flag}</span>
                    <span className="font-bold text-white group-hover:text-brand font-mono text-sm">
                      {sec.ticker}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-background-elevated border border-border text-gray-400">
                      {sec.exchange_code}
                    </span>
                    <span className="text-[10px] text-gray-500">· {sec.currency}</span>
                  </div>
                  <div className="text-xs text-gray-400 truncate max-w-sm">
                    {sec.name}
                  </div>
                </div>
                <div className="flex items-center gap-2 text-gray-500 group-hover:text-white text-xs">
                  <span className="font-mono text-[10px] text-gray-500 hidden sm:inline">
                    {sec.security_id}
                  </span>
                  <ArrowRight className="h-3.5 w-3.5 transform group-hover:translate-x-0.5 transition-transform" />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
