"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { SUPPORTED_MARKETS_CONFIG, MarketMeta } from "./market";

interface MarketContextType {
  activeMarket: string;
  setActiveMarket: (marketCode: string) => void;
  marketMeta: MarketMeta;
}

const MarketContext = createContext<MarketContextType | undefined>(undefined);

const STORAGE_KEY = "stocksense_active_market";
const CUSTOM_EVENT_NAME = "stocksense_market_change";

export function MarketProvider({ children }: { children: React.ReactNode }) {
  const [activeMarket, setActiveMarketState] = useState<string>("PK");

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && SUPPORTED_MARKETS_CONFIG[stored.toUpperCase()]) {
        setActiveMarketState(stored.toUpperCase());
      }
    } catch {}

    const handleCustomChange = (e: Event) => {
      const customEvent = e as CustomEvent<{ marketCode: string }>;
      if (customEvent.detail?.marketCode) {
        setActiveMarketState(customEvent.detail.marketCode.toUpperCase());
      }
    };

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        setActiveMarketState(e.newValue.toUpperCase());
      }
    };

    window.addEventListener(CUSTOM_EVENT_NAME, handleCustomChange);
    window.addEventListener("storage", handleStorageChange);
    return () => {
      window.removeEventListener(CUSTOM_EVENT_NAME, handleCustomChange);
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  const setActiveMarket = useCallback((marketCode: string) => {
    const clean = marketCode.trim().toUpperCase();
    if (!SUPPORTED_MARKETS_CONFIG[clean]) return;
    setActiveMarketState(clean);
    try {
      localStorage.setItem(STORAGE_KEY, clean);
      window.dispatchEvent(
        new CustomEvent(CUSTOM_EVENT_NAME, { detail: { marketCode: clean } })
      );
    } catch {}
  }, []);

  const marketMeta = SUPPORTED_MARKETS_CONFIG[activeMarket] || SUPPORTED_MARKETS_CONFIG.PK;

  return (
    <MarketContext.Provider value={{ activeMarket, setActiveMarket, marketMeta }}>
      {children}
    </MarketContext.Provider>
  );
}

export function useMarket(): MarketContextType {
  const context = useContext(MarketContext);
  if (!context) {
    // Graceful fallback if used outside provider
    const fallbackMeta = SUPPORTED_MARKETS_CONFIG.PK;
    return {
      activeMarket: "PK",
      setActiveMarket: () => {},
      marketMeta: fallbackMeta,
    };
  }
  return context;
}
