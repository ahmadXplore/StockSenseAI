/**
 * StockSense AI — Formatting Utilities
 * Standardized locale-aware formatting for currencies, percentages, dates, and financial metrics.
 */

import { SUPPORTED_MARKETS_CONFIG } from "./market";

export function formatCurrency(
  value: number | null | undefined,
  currency: string = "USD",
  maximumFractionDigits: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  const curr = currency.toUpperCase();

  // Custom symbol prefixes for clarity across multi-market
  let symbol = "$";
  if (curr === "PKR") symbol = "Rs. ";
  else if (curr === "GBP") symbol = "£";
  else if (curr === "JPY") symbol = "¥";
  else if (curr === "INR") symbol = "₹";
  else if (curr === "HKD") symbol = "HK$";

  // JPY has no decimal places; clamp digits to valid [0, 20] range
  const isJPY = curr === "JPY";
  const maxDigits = isJPY ? 0 : Math.min(20, Math.max(0, maximumFractionDigits));
  const minDigits = isJPY ? 0 : Math.min(2, maxDigits);

  const numStr = value.toLocaleString("en-US", {
    minimumFractionDigits: minDigits,
    maximumFractionDigits: maxDigits,
  });

  return `${symbol}${numStr}`;
}


export function formatPercent(
  value: number | null | undefined,
  includePlus: boolean = true,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  const isPos = value > 0;
  const prefix = isPos && includePlus ? "+" : "";
  return `${prefix}${value.toFixed(decimals)}%`;
}

export function formatLargeNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (abs >= 1e12) return `${sign}${(abs / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(1)}K`;
  return value.toLocaleString("en-US");
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}
