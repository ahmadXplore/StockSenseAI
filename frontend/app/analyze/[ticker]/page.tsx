"use client";

import { useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { parseSecurityId } from "@/lib/market";

export default function AnalyzeRedirectPage({ params }: { params: Promise<{ ticker: string }> | { ticker: string } }) {
  const resolvedParams = typeof (params as any)?.then === "function" ? use(params as Promise<{ ticker: string }>) : (params as { ticker: string });
  const raw = resolvedParams.ticker || "AAPL";
  const parsed = parseSecurityId(raw);
  const router = useRouter();

  useEffect(() => {
    router.replace(`/stocks/${encodeURIComponent(parsed.canonicalId)}`);
  }, [parsed.canonicalId, router]);

  return (
    <div className="flex flex-col items-center justify-center py-24 text-gray-400 text-sm space-y-3">
      <Loader2 className="h-6 w-6 animate-spin text-brand" />
      <span>Loading multi-market security {parsed.canonicalId}…</span>
    </div>
  );
}
