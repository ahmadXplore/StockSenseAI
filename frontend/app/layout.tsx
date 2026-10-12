import type { Metadata } from "next";
import "./globals.css";
import { MarketProvider } from "@/lib/marketContext";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "StockSense AI — Institutional Multi-Market Investment Analysis & Prediction",
  description: "AI-powered stock prediction, quantitative risk management, and point-in-time backtesting across PSX and global equity markets.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body suppressHydrationWarning className="min-h-screen bg-background text-gray-100 flex flex-col selection:bg-brand selection:text-white">
        <MarketProvider>
          <AppShell>
            {children}
          </AppShell>
        </MarketProvider>
      </body>
    </html>
  );
}

