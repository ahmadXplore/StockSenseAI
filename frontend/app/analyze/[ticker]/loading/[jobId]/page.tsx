"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle2, Circle, Clock, AlertCircle } from "lucide-react";

export default function AnalysisLoadingPage() {
  const params = useParams();
  const router = useRouter();
  const ticker = (params.ticker as string || "AAPL").toUpperCase();
  const jobId = params.jobId as string;

  const [currentStep, setCurrentStep] = useState(3);
  const steps = [
    { id: 1, label: "Fetching real-time & historical price data (yfinance + Stooq)" },
    { id: 2, label: "Extracting point-in-time SEC EDGAR financial statements" },
    { id: 3, label: "Computing technical indicators & momentum oscillators" },
    { id: 4, label: "Executing multi-horizon ML ensemble predictions" },
    { id: 5, label: "Running News sentiment NLP & insider transaction checks" },
    { id: 6, label: "Applying Hard Veto Engine & anomaly classification" },
    { id: 7, label: "Generating explainable investment report & exit plan" },
  ];

  return (
    <div className="max-w-xl mx-auto py-12 space-y-8">
      <div className="text-center space-y-3">
        <div className="inline-flex p-3 bg-brand/10 text-brand rounded-full animate-spin">
          <Loader2 className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-bold text-white">
          Analyzing <span className="font-mono text-brand">{ticker}</span>
        </h1>
        <p className="text-sm text-gray-400">
          Running asynchronous quantitative models and valuation algorithms...
        </p>
      </div>

      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between text-xs text-gray-400 pb-2 border-b border-border">
          <span>Job ID: <span className="font-mono">{jobId}</span></span>
          <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Progress: ~45%</span>
        </div>

        <div className="space-y-3">
          {steps.map((step) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;

            return (
              <div key={step.id} className="flex items-center gap-3 text-xs">
                {isCompleted ? (
                  <CheckCircle2 className="h-4 w-4 text-signal-strongBuy shrink-0" />
                ) : isCurrent ? (
                  <Loader2 className="h-4 w-4 text-brand animate-spin shrink-0" />
                ) : (
                  <Circle className="h-4 w-4 text-gray-600 shrink-0" />
                )}
                <span className={isCurrent ? "font-semibold text-white" : isCompleted ? "text-gray-400" : "text-gray-600"}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
