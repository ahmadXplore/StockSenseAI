import { NextRequest, NextResponse } from "next/server";
import psxData from "@/lib/static/psx_companies.json";
import usData from "@/lib/static/us_companies.json";
import ukData from "@/lib/static/uk_companies.json";

interface CompanyEntry {
  ticker: string;
  name: string;
  exchange: string;
  market: string;
  sector: string;
  currency: string;
}

// Combine supported datasets (PSX, US, UK) into a cached master directory
const ALL_COMPANIES: CompanyEntry[] = [
  ...psxData,
  ...usData,
  ...ukData,
];

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get("q") || "").trim().toUpperCase();
  const marketFilter = (searchParams.get("market") || "").trim().toUpperCase();
  const limit = parseInt(searchParams.get("limit") || "25", 10);

  if (!q) {
    return NextResponse.json([]);
  }

  // Filter by market if supplied
  const pool = marketFilter
    ? ALL_COMPANIES.filter((c) => c.market.toUpperCase() === marketFilter)
    : ALL_COMPANIES;

  // Score each entry
  const scored: Array<{ entry: CompanyEntry; score: number }> = [];

  for (const item of pool) {
    const tickerUpper = item.ticker.toUpperCase();
    const nameUpper = item.name.toUpperCase();
    // Normalize ticker without suffix (e.g. AZN.L -> AZN, FFC.KA -> FFC)
    const baseTicker = tickerUpper.replace(/\.(L|KA)$/, "");

    let score = 0;

    if (tickerUpper === q || baseTicker === q) {
      score = 1000;
    } else if (tickerUpper.startsWith(q) || baseTicker.startsWith(q)) {
      score = 500;
    } else if (tickerUpper.includes(q) || baseTicker.includes(q)) {
      score = 250;
    } else if (nameUpper.startsWith(q)) {
      score = 200;
    } else if (nameUpper.includes(" " + q)) {
      score = 150;
    } else if (nameUpper.includes(q)) {
      score = 80;
    }

    if (score > 0) {
      // Small boost if ticker is shorter (closer exact match)
      score += Math.max(0, 30 - baseTicker.length);
      scored.push({ entry: item, score });
    }
  }

  // Sort descending by score
  scored.sort((a, b) => b.score - a.score);

  const results = scored.slice(0, limit).map(({ entry }) => {
    const cleanSym = entry.ticker.replace(/\.(L|KA)$/, "");
    return {
      security_id: `${entry.market}.${entry.exchange}.${cleanSym}`,
      ticker: entry.ticker,
      name: entry.name,
      market_code: entry.market,
      exchange_code: entry.exchange,
      currency: entry.currency,
      sector: entry.sector,
      is_active: true,
    };
  });

  return NextResponse.json(results);
}
