"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  TrendingUp, LayoutDashboard, Star, Briefcase, Globe,
  Settings, Database, Brain, ShieldCheck, LogOut, LineChart,
  Scale, Layers, Shield
} from "lucide-react";
import { FaceUser } from "@/lib/api";
import { MarketSelector } from "./market/MarketSelector";
import { useMarket } from "@/lib/marketContext";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<FaceUser | null>(null);
  const { activeMarket, setActiveMarket } = useMarket();

  useEffect(() => {
    try {
      const storedUser = sessionStorage.getItem("stocksense_user");
      if (storedUser) {
        setCurrentUser(JSON.parse(storedUser));
      }
    } catch {}
  }, [pathname]);

  const handleLogout = () => {
    sessionStorage.removeItem("stocksense_auth_token");
    sessionStorage.removeItem("stocksense_user");
    setCurrentUser(null);
    router.push("/auth");
  };

  const navLinks = [
    { href: "/dashboard",      label: "Dashboard",   icon: LayoutDashboard },
    { href: "/chat",           label: "AI Copilot",  icon: Brain },
    { href: "/markets",        label: "Markets",     icon: Globe },
    { href: "/watchlist",      label: "Watchlist",   icon: Star },
    { href: "/portfolio",      label: "Portfolio",   icon: Briefcase },
    { href: "/backtesting",    label: "Backtest",    icon: LineChart },
    { href: "/compare",        label: "Compare",     icon: Scale },
    { href: "/models",         label: "AI Models",   icon: Layers },
    { href: "/admin",          label: "Admin Panel", icon: Shield },
    { href: "/data-explorer",  label: "Data Health", icon: Database },
    { href: "/settings",       label: "Settings",    icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-[#0A0E1A]/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between px-3 sm:px-6 max-w-7xl mx-auto gap-2">
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-brand flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
              <TrendingUp className="h-5 w-5" />
            </div>
            <span className="font-bold text-base sm:text-lg tracking-tight text-white">
              StockSense <span className="text-brand">AI</span>
            </span>
          </Link>

          {/* Quick Market Selector */}
          <div className="hidden sm:block pl-2 border-l border-border/60">
            <MarketSelector selectedMarket={activeMarket} onSelectMarket={setActiveMarket} />
          </div>
        </div>

        {/* Center: Navigation Links */}
        <nav className="hidden lg:flex items-center gap-0.5 overflow-x-auto py-1">
          {navLinks
            .filter((link) => link.href !== "/admin" || currentUser?.is_admin)
            .map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                  isActive
                    ? "bg-background-elevated text-white border border-border"
                    : "text-gray-400 hover:text-white hover:bg-background-hover"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right: User Profile & Face Biometric Auth */}
        <div className="flex items-center gap-2 shrink-0">
          {currentUser ? (
            <div className="flex items-center gap-2 bg-background-elevated border border-border px-3 py-1.5 rounded-lg text-xs">
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-white truncate max-w-[90px] sm:max-w-[120px]">{currentUser.name}</span>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-red-400 p-0.5 ml-1 transition-colors"
                title="Log Out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/auth"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                pathname === "/auth"
                  ? "bg-brand text-white shadow-md shadow-blue-500/20"
                  : "bg-brand/10 hover:bg-brand/20 border border-brand/30 text-brand"
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Face Access
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
