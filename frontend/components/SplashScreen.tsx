"use client";

import { useEffect, useState } from "react";

const TICKERS = [
  "AAPL +1.2%","MSFT +0.8%","NVDA +3.2%","TSLA -2.1%","AMZN +0.9%",
  "META +1.5%","GOOGL +0.6%","SPY +0.45%","QQQ +0.62%","VIX -0.35",
  "GOLD +0.2%","BTC +2.4%","JPM +0.7%","DIS -0.3%","BA +1.1%",
];

const STEPS = [
  "Connecting to market data streams",
  "Loading AI prediction models",
  "Verifying portfolio integrity",
  "System ready",
];

export function SplashScreen({ onDone }: { onDone: () => void }) {
  const [progress, setProgress] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const [fadeOut, setFadeOut] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Slight delay before starting animations (ensures CSS is ready)
    const mountTimer = setTimeout(() => setMounted(true), 60);

    const timers = [
      setTimeout(() => setProgress(25),   300),
      setTimeout(() => setStepIdx(1),     700),
      setTimeout(() => setProgress(55),   800),
      setTimeout(() => setStepIdx(2),    1400),
      setTimeout(() => setProgress(85),  1500),
      setTimeout(() => setStepIdx(3),    2100),
      setTimeout(() => setProgress(100), 2200),
      setTimeout(() => setFadeOut(true), 2700),
      setTimeout(() => onDone(),         3400),
    ];

    return () => { clearTimeout(mountTimer); timers.forEach(clearTimeout); };
  }, [onDone]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        backgroundColor: "#060912",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: fadeOut ? 0 : 1,
        transition: fadeOut ? "opacity 0.7s cubic-bezier(0.4,0,0.2,1)" : "none",
      }}
    >
      {/* ── Background grid ── */}
      <div style={{
        position: "absolute", inset: 0, opacity: 0.035,
        backgroundImage: "linear-gradient(#3b82f6 1px,transparent 1px),linear-gradient(90deg,#3b82f6 1px,transparent 1px)",
        backgroundSize: "48px 48px",
      }} />

      {/* ── Ambient glow orbs ── */}
      <div style={{
        position: "absolute", top: "30%", left: "50%",
        transform: "translate(-50%,-50%)",
        width: 600, height: 600,
        background: "radial-gradient(circle,rgba(59,130,246,0.12) 0%,transparent 70%)",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", bottom: "20%", left: "20%",
        width: 320, height: 320,
        background: "radial-gradient(circle,rgba(99,102,241,0.09) 0%,transparent 70%)",
        pointerEvents: "none",
      }} />

      {/* ── Ticker tape (top) ── */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        height: 32, overflow: "hidden",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        display: "flex", alignItems: "center",
        opacity: mounted ? 1 : 0, transition: "opacity 0.6s ease 0.3s",
      }}>
        <div style={{ animation: "spl_marquee 20s linear infinite", display: "flex", gap: 40, whiteSpace: "nowrap" }}>
          {[...TICKERS, ...TICKERS, ...TICKERS].map((t, i) => {
            const up = t.includes("+");
            return (
              <span key={i} style={{
                fontSize: 11, fontFamily: "monospace",
                color: up ? "rgba(52,211,153,0.55)" : "rgba(248,113,113,0.55)",
              }}>{t}</span>
            );
          })}
        </div>
      </div>

      {/* ── Main content ── */}
      <div style={{
        position: "relative", zIndex: 10,
        display: "flex", flexDirection: "column", alignItems: "center", gap: 36,
        opacity: mounted ? 1 : 0, transform: mounted ? "translateY(0)" : "translateY(16px)",
        transition: "opacity 0.8s cubic-bezier(0.4,0,0.2,1), transform 0.8s cubic-bezier(0.4,0,0.2,1)",
      }}>

        {/* Logo */}
        <div style={{ position: "relative" }}>
          <div style={{
            position: "absolute", inset: -8, borderRadius: 28,
            background: "rgba(59,130,246,0.15)", filter: "blur(20px)", transform: "scale(1.4)",
            animation: "spl_pulse 2s ease-in-out infinite",
          }} />
          <div style={{
            position: "relative",
            width: 80, height: 80, borderRadius: 22,
            background: "linear-gradient(135deg,rgba(59,130,246,0.15),rgba(99,102,241,0.1))",
            border: "1px solid rgba(59,130,246,0.25)",
            display: "flex", alignItems: "center", justifyContent: "center",
            backdropFilter: "blur(12px)",
            boxShadow: "0 0 40px rgba(59,130,246,0.15),inset 0 1px 0 rgba(255,255,255,0.08)",
          }}>
            <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
              <polyline
                points="4,32 13,18 22,25 31,11 40,16"
                stroke="#3b82f6" strokeWidth="2.5"
                strokeLinecap="round" strokeLinejoin="round"
                style={{ strokeDasharray: 130, strokeDashoffset: mounted ? 0 : 130, transition: "stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1) 0.2s" }}
              />
              <circle cx="40" cy="16" r="3" fill="#60a5fa"
                style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.4s ease 1.4s" }}
              />
            </svg>
          </div>
        </div>

        {/* Brand */}
        <div style={{ textAlign: "center", display: "flex", flexDirection: "column", gap: 8 }}>
          <h1 style={{
            fontSize: "clamp(2.2rem,5vw,3.5rem)",
            fontWeight: 800, letterSpacing: "-0.03em",
            color: "#fff", margin: 0, lineHeight: 1.1,
          }}>
            StockSense{" "}
            <span style={{ background: "linear-gradient(135deg,#60a5fa,#818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              AI
            </span>
          </h1>
          <p style={{
            fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase",
            color: "rgba(148,163,184,0.6)", fontWeight: 500, margin: 0,
          }}>
            Institutional-Grade Investment Intelligence
          </p>
        </div>

        {/* Status text */}
        <div style={{ height: 20, display: "flex", alignItems: "center" }}>
          <p
            key={stepIdx}
            style={{
              fontSize: 12, fontFamily: "monospace",
              color: "rgba(96,165,250,0.75)", margin: 0,
              animation: "spl_fade_up 0.5s cubic-bezier(0.4,0,0.2,1)",
            }}
          >
            {STEPS[stepIdx]}
            <span style={{ animation: "spl_blink 1s step-end infinite" }}>_</span>
          </p>
        </div>

        {/* Progress bar */}
        <div style={{ width: "min(320px, 80vw)", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{
            height: 2, borderRadius: 9999,
            background: "rgba(255,255,255,0.06)",
            overflow: "hidden",
          }}>
            <div style={{
              height: "100%", borderRadius: 9999,
              background: "linear-gradient(90deg,#3b82f6,#818cf8)",
              width: `${progress}%`,
              transition: "width 0.7s cubic-bezier(0.4,0,0.2,1)",
              boxShadow: "0 0 10px rgba(59,130,246,0.7)",
            }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontSize: 10, fontFamily: "monospace", color: "rgba(100,116,139,0.7)" }}>
              INITIALIZING
            </span>
            <span style={{ fontSize: 10, fontFamily: "monospace", color: "rgba(100,116,139,0.7)" }}>
              {progress}%
            </span>
          </div>
        </div>

        {/* Dot indicators */}
        <div style={{ display: "flex", gap: 8 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{
              width: 5, height: 5, borderRadius: "50%",
              background: "#3b82f6",
              animation: `spl_bounce 1.2s ${i * 0.22}s ease-in-out infinite alternate`,
            }} />
          ))}
        </div>
      </div>

      {/* ── Bottom footer ── */}
      <div style={{
        position: "absolute", bottom: 20,
        fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase",
        color: "rgba(71,85,105,0.7)", fontWeight: 500,
        opacity: mounted ? 1 : 0, transition: "opacity 0.8s ease 1s",
      }}>
        Capital Preservation · AI Forecasting · Hard Veto Engine
      </div>

      {/* ── Keyframes ── */}
      <style>{`
        @keyframes spl_marquee  { from{transform:translateX(0)} to{transform:translateX(-33.33%)} }
        @keyframes spl_pulse    { 0%,100%{opacity:0.6} 50%{opacity:1} }
        @keyframes spl_fade_up  { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spl_blink    { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes spl_bounce   { from{opacity:0.25;transform:translateY(3px) scale(0.7)} to{opacity:1;transform:translateY(-3px) scale(1.2)} }
      `}</style>
    </div>
  );
}
