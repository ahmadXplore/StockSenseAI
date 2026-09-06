"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useState, Suspense } from "react";
import { DollarSign, Compass, Shield, ArrowRight, Loader2 } from "lucide-react";

function AnalyzeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const ticker = (searchParams.get("ticker") || "").toUpperCase();

  // If we have a ticker, redirect directly to the analysis page
  if (ticker) {
    router.replace(`/analyze/${ticker}`);
    return (
      <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
        <Loader2 className="h-5 w-5 animate-spin mr-2" /> Redirecting to analysis for {ticker}…
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-8 space-y-8 text-center">
      <h1 className="text-2xl font-bold text-white">Analyze a Stock</h1>
      <p className="text-gray-400 text-sm">Use the search bar on the Dashboard to find a ticker.</p>
      <button
        onClick={() => router.push("/dashboard")}
        className="inline-flex items-center gap-2 px-6 py-3 bg-brand hover:bg-brand-hover text-white rounded-lg font-semibold text-sm transition-all"
      >
        Go to Dashboard <ArrowRight className="h-4 w-4" />
      </button>
    </div>
  );
}

export default function AnalyzeConfigurePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
        <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading…
      </div>
    }>
      <AnalyzeContent />
    </Suspense>
  );
}
