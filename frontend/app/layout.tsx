import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { MarketContextBar } from "@/components/MarketContextBar";
import { SplashWrapper } from "@/components/SplashWrapper";
import { MarketProvider } from "@/lib/marketContext";
import { QueryChatbot } from "@/components/chatbot/QueryChatbot";

export const metadata: Metadata = {
  title: "StockSense AI — Institutional Multi-Market Investment Analysis & Prediction",
  description: "AI-powered stock prediction, quantitative risk management, and point-in-time backtesting across PSX and global equity markets.",
};

const CURRENT_YEAR = new Date().getFullYear();

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body suppressHydrationWarning className="min-h-screen bg-background text-gray-100 flex flex-col selection:bg-brand selection:text-white">
        <MarketProvider>
          <SplashWrapper>
            <Navbar />
            <MarketContextBar />
            <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-8 py-6">
              {children}
            </main>
            <footer className="border-t border-border py-6 px-4 sm:px-8 bg-background-elevated/50 text-xs text-gray-500 text-center">
              <div className="max-w-7xl mx-auto space-y-2">
                <p>
                  StockSense AI is an analytical decision-support tool. It does not provide personalized financial advice.
                  All investments involve risk of loss. Past performance does not guarantee future results.
                </p>
                <p className="text-gray-600">
                  © {CURRENT_YEAR} StockSense AI. All rights reserved.
                </p>
              </div>
            </footer>
            <QueryChatbot />
          </SplashWrapper>
        </MarketProvider>
      </body>
    </html>
  );
}
