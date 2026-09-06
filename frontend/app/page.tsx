"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Activity, Database, Cpu, Sparkles, ArrowRight } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("INITIALIZING STOCKSENSE AI GATEWAY…");
  const [subText, setSubText] = useState("Loading neural biometric weights & market context engines");

  useEffect(() => {
    // Check if user is already authenticated
    let hasUser = false;
    try {
      if (typeof window !== "undefined") {
        const stored = sessionStorage.getItem("stocksense_user");
        if (stored) hasUser = true;
      }
    } catch {}

    // Stepped bootloader simulation
    const timer1 = setTimeout(() => {
      setProgress(25);
      setStatusText("CONNECTING MULTI-MARKET PRICE FEEDS…");
      setSubText("Pakistan PSX (2020-2026 Engine) · NYSE · NASDAQ · LSE");
    }, 350);

    const timer2 = setTimeout(() => {
      setProgress(60);
      setStatusText("MOUNTING BIOMETRIC NEURAL ENGINE…");
      setSubText("128D Face Vector Space · TinyFaceDetector · PostgreSQL Encryption");
    }, 850);

    const timer3 = setTimeout(() => {
      setProgress(90);
      setStatusText("SYSTEM ARMED & VERIFIED");
      setSubText("All quantitative prediction & risk gateways active");
    }, 1400);

    const timer4 = setTimeout(() => {
      setProgress(100);
      setTimeout(() => {
        if (hasUser) {
          router.replace("/dashboard");
        } else {
          router.replace("/auth");
        }
      }, 400);
    }, 1900);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    };
  }, [router]);

  return (
    <div className="min-h-[85vh] text-white flex flex-col items-center justify-center p-6 relative overflow-hidden select-none">
      {/* Dynamic Background Glows */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] bg-gradient-to-tr from-brand/20 to-teal-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#1E293B_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />

      <div className="relative z-10 max-w-lg w-full text-center space-y-8 animate-fadeIn">
        {/* Animated Brand Emblem */}
        <div className="relative inline-flex items-center justify-center">
          <div className="w-20 h-20 rounded-3xl bg-background-elevated/90 border border-border flex items-center justify-center text-brand shadow-2xl shadow-brand/20 backdrop-blur-xl">
            <ShieldCheck className="w-10 h-10 animate-pulse text-brand" />
          </div>
          {/* Outer glowing halo ring */}
          <div className="absolute -inset-2.5 rounded-full border border-brand/30 animate-spin [animation-duration:8s]" />
          <div className="absolute -inset-5 rounded-full border border-teal-500/20 animate-spin [animation-duration:14s] [animation-direction:reverse]" />
        </div>

        {/* Title & Tagline */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand/10 border border-brand/30 text-brand text-xs font-mono font-semibold tracking-wider uppercase">
            <Sparkles className="h-3.5 w-3.5" /> Institutional Gateway
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-gray-100 to-gray-400 bg-clip-text text-transparent">
            StockSense AI
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 font-mono">
            Quantitative Forecasting &amp; Biometric Security Terminal
          </p>
        </div>

        {/* Progress Display Card */}
        <div className="bg-background-elevated/70 border border-border/80 rounded-2xl p-6 text-left space-y-4 shadow-2xl backdrop-blur-md">
          <div className="flex items-center justify-between font-mono text-xs text-gray-400">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-brand animate-ping" />
              <span className="font-semibold text-gray-300">{statusText}</span>
            </div>
            <span className="font-bold text-brand">{progress}%</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-background rounded-full h-2 overflow-hidden border border-border/60 p-0.5">
            <div
              className="bg-gradient-to-r from-brand via-teal-400 to-emerald-400 h-full rounded-full transition-all duration-500 ease-out shadow-[0_0_12px_#3B82F6]"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="text-[11px] font-mono text-gray-500 leading-relaxed truncate">
            {subText}
          </div>

          {/* Subsystem Indicators Grid */}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border/50 font-mono text-[10px]">
            <div className={`p-2 rounded-lg border flex items-center gap-1.5 ${progress >= 25 ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300" : "bg-background border-border text-gray-600"}`}>
              <Activity className="h-3 w-3" />
              <span>MARKETS</span>
            </div>
            <div className={`p-2 rounded-lg border flex items-center gap-1.5 ${progress >= 60 ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300" : "bg-background border-border text-gray-600"}`}>
              <Cpu className="h-3 w-3" />
              <span>NEURAL AI</span>
            </div>
            <div className={`p-2 rounded-lg border flex items-center gap-1.5 ${progress >= 90 ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300" : "bg-background border-border text-gray-600"}`}>
              <Database className="h-3 w-3" />
              <span>DATABASE</span>
            </div>
          </div>
        </div>

        {/* Direct Bypass Link */}
        <div className="pt-1">
          <button
            onClick={() => router.push("/auth")}
            className="inline-flex items-center gap-1.5 text-xs font-mono text-gray-500 hover:text-gray-300 transition-colors"
          >
            Direct to Biometric Gateway <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
}

