"use client";

/**
 * AppShell — wraps authenticated app pages with Navbar, DeviceGate, etc.
 * Auth pages (/auth, /login) are rendered bare (no nav/gate).
 */
import { usePathname } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { MarketContextBar } from "@/components/MarketContextBar";
import { SplashWrapper } from "@/components/SplashWrapper";
import { DeviceGate } from "@/components/DeviceGate";
import { QueryChatbot } from "@/components/chatbot/QueryChatbot";

const BARE_PATHS = ["/", "/auth", "/login"];

const CURRENT_YEAR = new Date().getFullYear();

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isBarePage = BARE_PATHS.some(p => pathname === p || (p !== "/" && pathname.startsWith(p + "/")));

  if (isBarePage) {
    // Landing gateway & auth pages: render completely bare — no navbar, no market bar, no gate, no footer
    return <>{children}</>;
  }

  return (
    <DeviceGate>
      <SplashWrapper>
        <Navbar />
        <MarketContextBar />
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-border py-6 px-4 sm:px-8 bg-background-elevated/50 text-xs text-gray-500 text-center">
          <div className="max-w-7xl mx-auto space-y-2">
            <p>StockSense AI is an analytical decision-support tool. It does not provide personalized financial advice. All investments involve risk of loss. Past performance does not guarantee future results.</p>
            <p className="text-gray-600">© {CURRENT_YEAR} StockSense AI. All rights reserved.</p>
          </div>
        </footer>
        <QueryChatbot />
      </SplashWrapper>
    </DeviceGate>
  );
}
