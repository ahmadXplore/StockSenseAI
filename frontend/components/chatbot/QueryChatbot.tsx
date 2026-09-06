"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  MessageSquare, Plus, Trash2, X, Send, Bot, User, Loader2,
  Maximize2, Minimize2, Copy, Check, ThumbsUp, ThumbsDown,
  Sparkles, RefreshCw, Search, Download, ChevronLeft, ChevronRight,
  TrendingUp, Shield, BarChart3, HelpCircle, Layers, ArrowUpRight,
  FileText, FileCode, Printer, FileType
} from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { useMarket } from "@/lib/marketContext";
import {
  StockAIContext,
  OpenStockChatDetail,
  getStockSuggestedPrompts,
  buildStockInitialBrief,
} from "@/lib/aiCopilot";

export interface ChatMessage {
  id: string;
  role: "system" | "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: number;
  messages: ChatMessage[];
}

const STORAGE_KEY = "stocksense_chat_sessions_v2";

const STARTER_PROMPTS = [
  {
    category: "Fundamental Valuation",
    icon: TrendingUp,
    color: "from-blue-500/20 to-cyan-500/20 border-blue-500/30 text-blue-400",
    title: "Valuation & Financial Health",
    description: "Analyze P/E, ROE, FCF Yield, and growth metrics for target companies.",
    prompt: "Provide a comprehensive fundamental valuation framework. Explain how to evaluate P/E ratio, ROE, Debt-to-Equity, and Free Cash Flow yield with concrete benchmark criteria.",
  },
  {
    category: "PSX & Market Rules",
    icon: Shield,
    color: "from-emerald-500/20 to-teal-500/20 border-emerald-500/30 text-emerald-400",
    title: "PSX Rules & Settlement",
    description: "Understand circuit breakers (±7.5%), T+2 rolling settlement & futures.",
    prompt: "Explain the Pakistan Stock Exchange (PSX) trading mechanics, including ±7.5% daily circuit breakers, T+2 settlement cycle, and deliverable futures contracts.",
  },
  {
    category: "Quantitative Risk",
    icon: BarChart3,
    color: "from-purple-500/20 to-indigo-500/20 border-purple-500/30 text-purple-400",
    title: "Quant Risk & Conformal Bands",
    description: "Learn how 80% Conformal Prediction and VaR quantify non-normal tail risk.",
    prompt: "Explain how 80% Conformal Prediction intervals and Value at Risk (VaR) quantify downside risk and handle fat-tailed financial market distributions.",
  },
  {
    category: "Technical & Momentum",
    icon: Layers,
    color: "from-amber-500/20 to-orange-500/20 border-amber-500/30 text-amber-400",
    title: "Technical Indicator Confluence",
    description: "Master RSI momentum divergence, MACD histogram, and Bollinger squeezes.",
    prompt: "How do you combine RSI momentum divergence, MACD crossovers, and Bollinger Band volatility squeezes to construct high-probability technical setups?",
  },
];

const QUICK_TOPIC_PILLS = [
  "Explain P/E vs PEG Ratio",
  "PSX ±7.5% Circuit Breakers",
  "80% Conformal Prediction",
  "RSI Bullish Divergence",
  "Calculate Sharpe & Sortino",
  "T+2 vs T+1 Settlement",
  "Backtest Mean Reversion",
  "Inflation & Interest Rates",
];

export function QueryChatbot({ context }: { context?: any }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [activeStockContext, setActiveStockContext] = useState<StockAIContext | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const [likedMsgIds, setLikedMsgIds] = useState<Record<string, "up" | "down">>({});

  const { activeMarket, marketMeta } = useMarket();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize and load sessions from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed: ChatSession[] = JSON.parse(saved);
        if (parsed.length > 0) {
          setSessions(parsed);
          setActiveSessionId(parsed[0].id);
          return;
        }
      }
    } catch (e) {
      console.error("Failed to load chat sessions:", e);
    }

    // Default new session
    const defaultSession: ChatSession = {
      id: "session_" + Date.now(),
      title: "New Market Research",
      updatedAt: Date.now(),
      messages: [
        {
          id: "msg_init",
          role: "assistant",
          content: `### Welcome to StockSense AI Copilot

I am your institutional financial intelligence assistant and multi-market analyst. I provide deep insights into:

- **Fundamental & Valuation Analysis:** P/E, PEG, EV/EBITDA, ROE, Free Cash Flow.
- **PSX & Global Market Rules:** Circuit breakers, T+2 settlement, Deliverable Futures, Margin rules.
- **Quantitative Risk & Prediction:** 80% Conformal Intervals, Value at Risk (VaR), Sharpe & Sortino metrics.
- **Technical & Algorithmic Strategies:** RSI momentum, MACD, Bollinger Bands, and Backtesting.

Select a prompt below or type your question to get started!`,
          timestamp: Date.now(),
        },
      ],
    };
    setSessions([defaultSession]);
    setActiveSessionId(defaultSession.id);
  }, []);

  // Event listener for opening stock-specific copilot
  useEffect(() => {
    const handleOpenStockChat = (e: Event) => {
      const customEvt = e as CustomEvent<OpenStockChatDetail>;
      const stockCtx = customEvt.detail?.context;
      const initialPrompt = customEvt.detail?.initialPrompt;
      if (!stockCtx) return;

      setActiveStockContext(stockCtx);
      setIsOpen(true);
      setIsMinimized(false);

      const targetTitle = `🎯 ${stockCtx.ticker} Analysis`;
      const existing = sessions.find((s) => s.title === targetTitle);

      if (existing) {
        setActiveSessionId(existing.id);
        if (initialPrompt) {
          setTimeout(() => handleSend(initialPrompt), 150);
        }
      } else {
        const newSession: ChatSession = {
          id: "session_stock_" + stockCtx.ticker + "_" + Date.now(),
          title: targetTitle,
          updatedAt: Date.now(),
          messages: [
            {
              id: "msg_brief_" + Date.now(),
              role: "assistant",
              content: buildStockInitialBrief(stockCtx),
              timestamp: Date.now(),
            },
          ],
        };
        const updated = [newSession, ...sessions];
        saveSessions(updated);
        setActiveSessionId(newSession.id);
        if (initialPrompt) {
          setTimeout(() => handleSend(initialPrompt), 150);
        }
      }
    };

    window.addEventListener("stocksense:open-stock-chat", handleOpenStockChat as EventListener);
    return () => window.removeEventListener("stocksense:open-stock-chat", handleOpenStockChat as EventListener);
  }, [sessions]);

  // Save sessions to localStorage
  const saveSessions = (updatedSessions: ChatSession[]) => {
    setSessions(updatedSessions);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedSessions));
    } catch (e) {
      console.error("Failed to save chat sessions:", e);
    }
  };

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [activeSession?.messages, isOpen, isLoading]);

  // Adjust textarea height automatically
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: "session_" + Date.now(),
      title: "New Market Analysis",
      updatedAt: Date.now(),
      messages: [
        {
          id: "msg_" + Date.now(),
          role: "assistant",
          content: `### StockSense AI Copilot Ready

How can I help you analyze equities, quantitative risk, or trading mechanics today? You can choose one of the starter topics below or enter any financial inquiry.`,
          timestamp: Date.now(),
        },
      ],
    };
    const updated = [newSession, ...sessions];
    saveSessions(updated);
    setActiveSessionId(newSession.id);
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  const deleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const filtered = sessions.filter((s) => s.id !== sessionId);
    if (filtered.length === 0) {
      createNewSession();
    } else {
      saveSessions(filtered);
      if (activeSessionId === sessionId) {
        setActiveSessionId(filtered[0].id);
      }
    }
  };

  const clearAllSessions = () => {
    if (window.confirm("Are you sure you want to clear all chat history?")) {
      localStorage.removeItem(STORAGE_KEY);
      createNewSession();
    }
  };

  const handleSend = async (overridePrompt?: string) => {
    const promptToSend = (overridePrompt || input).trim();
    if (!promptToSend || isLoading) return;

    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMessage: ChatMessage = {
      id: "usr_" + Date.now(),
      role: "user",
      content: promptToSend,
      timestamp: Date.now(),
    };

    // Auto-update session title if it's the default
    let sessionTitle = activeSession?.title || "Market Analysis";
    if (sessionTitle === "New Market Analysis" || sessionTitle === "New Market Research") {
      sessionTitle = promptToSend.slice(0, 32) + (promptToSend.length > 32 ? "..." : "");
    }

    const currentMessages = activeSession ? activeSession.messages : [];
    const updatedMessages = [...currentMessages, userMessage];

    const updatedSessions = sessions.map((s) =>
      s.id === activeSessionId
        ? { ...s, title: sessionTitle, updatedAt: Date.now(), messages: updatedMessages }
        : s
    );
    saveSessions(updatedSessions);
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updatedMessages.map((m) => ({ role: m.role, content: m.content })),
          context: {
            activeMarket: marketMeta?.name || "PSX (Pakistan)",
            activeMarketCode: activeMarket || "PK",
            currency: marketMeta?.currency || "PKR",
            stockContext: activeStockContext,
            ...context,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch response");
      }

      const data = await response.json();
      const aiMessage: ChatMessage = {
        id: "ai_" + Date.now(),
        role: "assistant",
        content: data.content || "I have processed your query. Let me know if you would like deeper details.",
        timestamp: Date.now(),
      };

      const finalSessions = sessions.map((s) =>
        s.id === activeSessionId
          ? { ...s, updatedAt: Date.now(), messages: [...updatedMessages, aiMessage] }
          : s
      );
      saveSessions(finalSessions);
    } catch (error) {
      console.error(error);
      const errorMessage: ChatMessage = {
        id: "err_" + Date.now(),
        role: "assistant",
        content: `### Network Connectivity Notice

I experienced an issue reaching the primary inference engine. 

- **Please verify your connection.**
- You can retry your request using the **Regenerate** button below.`,
        timestamp: Date.now(),
      };
      const finalSessions = sessions.map((s) =>
        s.id === activeSessionId
          ? { ...s, messages: [...updatedMessages, errorMessage] }
          : s
      );
      saveSessions(finalSessions);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!activeSession || activeSession.messages.length < 2 || isLoading) return;
    const lastUserIdx = activeSession.messages.map((m) => m.role).lastIndexOf("user");
    if (lastUserIdx === -1) return;
    const lastUserMsg = activeSession.messages[lastUserIdx].content;
    const trimmed = activeSession.messages.slice(0, lastUserIdx);
    
    const updatedSessions = sessions.map((s) =>
      s.id === activeSessionId ? { ...s, messages: trimmed } : s
    );
    saveSessions(updatedSessions);
    handleSend(lastUserMsg);
  };

  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close export dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCopyMessage = (msgId: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const exportAsMarkdown = () => {
    if (!activeSession) return;
    const exportText = `# ${activeSession.title}\n*Generated by StockSense AI Copilot on ${new Date().toLocaleString()}*\n*Market: ${marketMeta?.name || "PSX Pakistan"}*\n\n---\n\n` +
      activeSession.messages
        .map((m) => `### ${m.role === "user" ? "🧑 User" : "🤖 StockSense AI"} *(${new Date(m.timestamp).toLocaleTimeString()})*\n\n${m.content}\n`)
        .join("\n---\n\n") +
      `\n\n---\n*Disclaimer: StockSense AI provides analytical and model-based probabilistic estimates for decision support. It does not constitute personalized financial advice.*`;
    
    const blob = new Blob([exportText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeSession.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_report.md`;
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportAsPDF = () => {
    if (!activeSession) return;
    setShowExportMenu(false);
    
    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      alert("Please allow popups to generate the PDF report.");
      return;
    }

    const title = activeSession.title || "StockSense AI Financial Analysis";
    const dateStr = new Date().toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

    const messagesHtml = activeSession.messages
      .map((m) => {
        const isUser = m.role === "user";
        const sender = isUser ? "User" : "StockSense AI Copilot";
        const time = new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        
        let formatted = m.content
          .replace(/### (.*?)\n/g, '<h3 style="color:#0f766e;font-size:15px;margin-top:14px;margin-bottom:6px;font-weight:700;">$1</h3>')
          .replace(/## (.*?)\n/g, '<h2 style="color:#1d4ed8;font-size:17px;margin-top:16px;margin-bottom:8px;font-weight:700;">$1</h2>')
          .replace(/# (.*?)\n/g, '<h1 style="color:#0f172a;font-size:20px;margin-top:18px;margin-bottom:10px;font-weight:800;">$1</h1>')
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/^- (.*?)$/gm, '<li style="margin-bottom:4px;margin-left:16px;">$1</li>')
          .replace(/> \*\*Key Takeaway:\*\* (.*?)\n/g, '<div style="background:#f0fdf4;border-left:4px solid #16a34a;padding:10px 14px;margin:12px 0;border-radius:6px;font-size:12px;color:#166534;"><strong>Key Takeaway:</strong> $1</div>')
          .replace(/> (.*?)\n/g, '<blockquote style="background:#f8fafc;border-left:4px solid #3b82f6;padding:8px 12px;margin:10px 0;color:#334155;font-style:italic;">$1</blockquote>')
          .replace(/```([\s\S]*?)```/g, '<pre style="background:#0f172a;color:#f8fafc;padding:12px;border-radius:6px;font-size:11px;overflow-x:auto;"><code>$1</code></pre>')
          .replace(/`([^`]+)`/g, '<code style="background:#e2e8f0;padding:2px 4px;border-radius:4px;font-size:11px;color:#0f172a;">$1</code>')
          .replace(/\n\n/g, '<p style="margin-bottom:8px;line-height:1.6;"></p>');

        return `
          <div style="margin-bottom: 20px; page-break-inside: avoid;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
              <span style="font-weight: 700; font-size: 13px; color: ${isUser ? '#1d4ed8' : '#059669'};">
                ${isUser ? '🧑 ' : '🤖 '}${sender}
              </span>
              <span style="font-size: 11px; color: #64748b;">${time}</span>
            </div>
            <div style="background: ${isUser ? '#eff6ff' : '#f8fafc'}; border: 1px solid ${isUser ? '#bfdbfe' : '#e2e8f0'}; border-radius: 8px; padding: 14px 16px; font-size: 13px; line-height: 1.6; color: #1e293b;">
              ${formatted}
            </div>
          </div>
        `;
      })
      .join("");

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${title} — StockSense AI</title>
          <meta charset="utf-8" />
          <style>
            @page { margin: 15mm; size: A4; }
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
              color: #0f172a; 
              margin: 0; 
              padding: 24px; 
              background: #fff;
            }
            .header { 
              border-bottom: 2px solid #2563eb; 
              padding-bottom: 14px; 
              margin-bottom: 20px; 
              display: flex; 
              justify-content: space-between; 
              align-items: flex-end; 
            }
            .brand { font-size: 22px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }
            .brand span { color: #2563eb; }
            .meta { font-size: 11px; color: #64748b; text-align: right; line-height: 1.4; }
            .disclaimer { 
              margin-top: 32px; 
              padding: 12px; 
              border-top: 1px solid #e2e8f0; 
              font-size: 10px; 
              color: #94a3b8; 
              text-align: center; 
              line-height: 1.4;
            }
            table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12px; }
            th, td { border: 1px solid #cbd5e1; padding: 7px 10px; text-align: left; }
            th { background: #f1f5f9; font-weight: 700; color: #334155; }
            ul, ol { margin: 6px 0; padding-left: 20px; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <div class="brand">StockSense <span>AI</span></div>
              <div style="font-size: 14px; font-weight: 600; color: #334155; margin-top: 3px;">${title}</div>
            </div>
            <div class="meta">
              <div><strong>Generated:</strong> ${dateStr}</div>
              <div><strong>Market:</strong> ${marketMeta?.name || "PSX Pakistan"}</div>
              <div><strong>Engine:</strong> Groq Ultra-Fast (120B / Qwen)</div>
            </div>
          </div>
          <main>
            ${messagesHtml}
          </main>
          <div class="disclaimer">
            StockSense AI is an institutional multi-market financial decision support system. Analytical estimates and predictions are probabilistic and do not constitute personalized financial advice.
          </div>
          <script>
            window.onload = function() {
              setTimeout(function() {
                window.print();
              }, 400);
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const exportAsText = () => {
    if (!activeSession) return;
    const textContent = `${activeSession.title}\nStockSense AI Copilot Report\nDate: ${new Date().toLocaleString()}\nMarket: ${marketMeta?.name || "PSX Pakistan"}\n\n` +
      activeSession.messages
        .map((m) => `[${m.role === "user" ? "USER" : "STOCKSENSE AI"}] - ${new Date(m.timestamp).toLocaleTimeString()}\n${m.content}\n`)
        .join("\n" + "=".repeat(50) + "\n\n");
    
    const blob = new Blob([textContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeSession.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_report.txt`;
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportAsJSON = () => {
    if (!activeSession) return;
    const jsonData = {
      sessionId: activeSession.id,
      title: activeSession.title,
      exportedAt: new Date().toISOString(),
      market: marketMeta?.name || "PSX Pakistan",
      messages: activeSession.messages,
    };
    const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeSession.title.replace(/[^a-z0-9]/gi, "_").toLowerCase()}_session.json`;
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.messages.some((m) => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <>
      {/* Floating Orb / Launcher */}
      {!isOpen && (
        <button
          onClick={() => {
            setIsOpen(true);
            setIsMinimized(false);
          }}
          className="fixed bottom-6 right-6 group flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-brand text-white rounded-full shadow-2xl hover:shadow-blue-500/30 hover:scale-105 transition-all duration-300 z-50 border border-white/20 backdrop-blur-md"
          title="Open StockSense AI Copilot"
        >
          <div className="relative">
            <Sparkles className="w-5 h-5 text-yellow-300 animate-pulse" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full ring-2 ring-[#0A0E1A] animate-ping" />
          </div>
          <span className="font-semibold text-sm tracking-wide hidden sm:inline">StockSense AI</span>
        </button>
      )}

      {/* Main Full-Screen / Modal Chat Workspace */}
      {isOpen && (
        <div className={`fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 md:p-6 bg-black/80 backdrop-blur-md transition-all duration-300 ${isMinimized ? "pointer-events-none opacity-0" : "opacity-100"}`}>
          <div className="relative w-full max-w-6xl h-[92vh] max-h-[900px] bg-[#0A0E1A] border border-border/80 rounded-2xl shadow-2xl flex overflow-hidden flex-col md:flex-row ring-1 ring-white/10">
            
            {/* Sidebar (History & Prompts) */}
            <aside className={`${sidebarOpen ? "w-full md:w-72 lg:w-80 flex" : "hidden"} flex-col bg-[#070B14] border-r border-border/70 shrink-0 transition-all duration-200 z-20`}>
              {/* Sidebar Header */}
              <div className="p-3.5 border-b border-border/70 flex items-center justify-between gap-2">
                <button
                  onClick={createNewSession}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-brand/20 hover:bg-brand/30 border border-brand/40 text-blue-300 hover:text-white rounded-xl text-xs font-semibold transition-all shadow-sm group"
                >
                  <Plus className="w-4 h-4 text-brand group-hover:rotate-90 transition-transform" />
                  <span>New Chat</span>
                </button>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="md:hidden p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Search History */}
              <div className="px-3 py-2 border-b border-border/50">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-[#0E1526] border border-border/60 rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-gray-200 placeholder:text-gray-500 focus:outline-none focus:border-brand"
                  />
                </div>
              </div>

              {/* Session List */}
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                <div className="text-[10px] font-semibold text-gray-500 uppercase px-2 py-1 tracking-wider">
                  Chat History ({filteredSessions.length})
                </div>
                {filteredSessions.map((session) => {
                  const isActive = session.id === activeSessionId;
                  return (
                    <div
                      key={session.id}
                      onClick={() => {
                        setActiveSessionId(session.id);
                        if (window.innerWidth < 768) setSidebarOpen(false);
                      }}
                      className={`group relative flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl cursor-pointer text-xs transition-all ${
                        isActive
                          ? "bg-brand/15 text-white font-medium border border-brand/30 shadow-sm"
                          : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? "text-brand" : "text-gray-500"}`} />
                        <span className="truncate">{session.title}</span>
                      </div>
                      <button
                        onClick={(e) => deleteSession(session.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-all"
                        title="Delete session"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Sidebar Footer */}
              <div className="p-3 border-t border-border/60 bg-[#060911] flex items-center justify-between text-[11px] text-gray-500">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Groq AI 120B / Qwen</span>
                </div>
                <button
                  onClick={clearAllSessions}
                  className="hover:text-red-400 transition-colors"
                  title="Clear all sessions"
                >
                  Clear all
                </button>
              </div>
            </aside>

            {/* Main Chat Panel */}
            <main className="flex-1 flex flex-col min-w-0 bg-[#0A0E1A] relative">
              
              {/* Header Bar */}
              <header className="px-4 py-3 border-b border-border/80 bg-[#0D1322] flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 min-w-0">
                  <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                    title="Toggle sidebar"
                  >
                    {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  <div className="flex items-center gap-2 truncate">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand to-indigo-500 flex items-center justify-center text-white shrink-0 shadow-md">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <h2 className="text-sm font-semibold text-white truncate">
                        {activeSession?.title || "StockSense AI Copilot"}
                      </h2>
                      <p className="text-[11px] text-gray-400 flex items-center gap-1.5">
                        <span className="text-emerald-400 font-medium">Active Market:</span>
                        <span>{marketMeta?.name || "PSX Pakistan"}</span>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {/* Export Dropdown */}
                  <div className="relative" ref={exportMenuRef}>
                    <button
                      onClick={() => setShowExportMenu(!showExportMenu)}
                      className={`px-2.5 py-1.5 rounded-lg text-xs flex items-center gap-1.5 transition-all border ${
                        showExportMenu
                          ? "bg-brand text-white border-brand shadow-sm shadow-blue-500/20"
                          : "text-gray-300 hover:text-white bg-white/5 hover:bg-white/10 border-border/60"
                      }`}
                      title="Download or export research conversation"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span className="font-medium hidden sm:inline">Export</span>
                    </button>

                    {showExportMenu && (
                      <div className="absolute right-0 top-full mt-2 w-64 bg-[#0D1527] border border-border/80 rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150 ring-1 ring-white/10">
                        <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider px-2.5 py-1.5 border-b border-border/50">
                          Export Research Report
                        </div>

                        <div className="py-1 space-y-0.5">
                          {/* Markdown (.MD) */}
                          <button
                            onClick={exportAsMarkdown}
                            className="w-full flex items-center justify-between px-2.5 py-2 text-xs text-left rounded-lg text-gray-200 hover:text-white hover:bg-brand/15 hover:border-brand/30 transition-colors group"
                          >
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
                              <div>
                                <div className="font-semibold text-white">Markdown Document</div>
                                <div className="text-[10px] text-gray-400">Standard structured notes (.md)</div>
                              </div>
                            </div>
                            <span className="text-[10px] font-mono bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded border border-blue-500/30">.MD</span>
                          </button>

                          {/* PDF Document (.PDF) */}
                          <button
                            onClick={exportAsPDF}
                            className="w-full flex items-center justify-between px-2.5 py-2 text-xs text-left rounded-lg text-gray-200 hover:text-white hover:bg-emerald-500/15 hover:border-emerald-500/30 transition-colors group"
                          >
                            <div className="flex items-center gap-2">
                              <Printer className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                              <div>
                                <div className="font-semibold text-white">PDF Research Report</div>
                                <div className="text-[10px] text-gray-400">Institutional printable report (.pdf)</div>
                              </div>
                            </div>
                            <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-500/30">.PDF</span>
                          </button>

                          {/* Plain Text (.TXT) */}
                          <button
                            onClick={exportAsText}
                            className="w-full flex items-center justify-between px-2.5 py-2 text-xs text-left rounded-lg text-gray-200 hover:text-white hover:bg-white/5 transition-colors group"
                          >
                            <div className="flex items-center gap-2">
                              <FileType className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                              <div>
                                <div className="font-semibold text-white">Plain Text</div>
                                <div className="text-[10px] text-gray-400">Lightweight raw text (.txt)</div>
                              </div>
                            </div>
                            <span className="text-[10px] font-mono bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">.TXT</span>
                          </button>

                          {/* JSON (.JSON) */}
                          <button
                            onClick={exportAsJSON}
                            className="w-full flex items-center justify-between px-2.5 py-2 text-xs text-left rounded-lg text-gray-200 hover:text-white hover:bg-purple-500/15 transition-colors group"
                          >
                            <div className="flex items-center gap-2">
                              <FileCode className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
                              <div>
                                <div className="font-semibold text-white">Raw JSON Session</div>
                                <div className="text-[10px] text-gray-400">Programmatic data export (.json)</div>
                              </div>
                            </div>
                            <span className="text-[10px] font-mono bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded border border-purple-500/30">.JSON</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                    title="Close"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </header>

              {/* Active Stock Context Focus Banner */}
              {activeStockContext && (
                <div className="px-4 py-2.5 bg-gradient-to-r from-blue-950/70 via-indigo-950/50 to-[#0B1020] border-b border-blue-500/30 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex flex-wrap items-center gap-2 min-w-0">
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-brand/20 border border-brand/50 text-blue-300 font-mono font-bold text-xs shadow-sm">
                      <Sparkles className="w-3 h-3 text-yellow-300" />
                      {activeStockContext.ticker}
                    </span>
                    <span className="text-gray-200 font-medium truncate max-w-[220px] hidden sm:inline">
                      {activeStockContext.companyName}
                    </span>
                    {activeStockContext.price !== undefined && (
                      <span className="text-white font-mono font-bold">
                        {activeStockContext.currency || ""} {activeStockContext.price.toLocaleString()}
                      </span>
                    )}
                    {activeStockContext.changePct !== undefined && (
                      <span className={`font-mono text-xs font-semibold ${activeStockContext.changePct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        ({activeStockContext.changePct >= 0 ? "+" : ""}{activeStockContext.changePct.toFixed(2)}%)
                      </span>
                    )}
                    {activeStockContext.prediction?.direction && (
                      <span className="px-2 py-0.5 rounded bg-purple-500/20 border border-purple-500/40 text-purple-300 font-mono text-[11px] font-semibold">
                        ML: {activeStockContext.prediction.direction} {activeStockContext.prediction.probability_up ? `(${Math.round(activeStockContext.prediction.probability_up * 100)}%)` : ""}
                      </span>
                    )}
                    {activeStockContext.peRatio && (
                      <span className="text-gray-400 font-mono text-[11px] hidden md:inline">
                        P/E: <span className="text-gray-200">{activeStockContext.peRatio}</span>
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setActiveStockContext(null)}
                    className="text-gray-400 hover:text-white text-[11px] px-2 py-1 rounded bg-white/5 hover:bg-white/10 border border-border/40 transition-colors shrink-0"
                    title="Switch to general market questions"
                  >
                    Clear Focus
                  </button>
                </div>
              )}

              {/* Chat Messages Body */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
                
                {/* Starter Cards (Shown when active session has only 1 greeting) */}
                {activeSession && activeSession.messages.length <= 1 && (
                  <div className="max-w-4xl mx-auto my-4 space-y-6">
                    <div className="text-center space-y-2">
                      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 border border-brand/30 text-brand text-xs font-semibold">
                        <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
                        Next-Gen Market Intelligence Engine
                      </div>
                      <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                        How can StockSense AI assist your analysis?
                      </h1>
                      <p className="text-xs sm:text-sm text-gray-400 max-w-xl mx-auto">
                        Ask any question about PSX / Global stocks, quantitative risk bounds, technical setups, trading rules, or backtesting.
                      </p>
                    </div>

                    {/* 4 Rich Starter Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2">
                      {STARTER_PROMPTS.map((card, idx) => {
                        const Icon = card.icon;
                        return (
                          <div
                            key={idx}
                            onClick={() => handleSend(card.prompt)}
                            className="group p-4 rounded-xl bg-[#0D1424] hover:bg-[#121B30] border border-border/80 hover:border-brand/40 cursor-pointer transition-all duration-200 flex flex-col justify-between shadow-lg hover:shadow-brand/5 hover:-translate-y-0.5"
                          >
                            <div className="space-y-2">
                              <div className="flex items-center justify-between">
                                <div className={`p-2 rounded-lg bg-gradient-to-br ${card.color} border`}>
                                  <Icon className="w-4 h-4" />
                                </div>
                                <ArrowUpRight className="w-4 h-4 text-gray-500 group-hover:text-brand group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                              </div>
                              <h3 className="font-semibold text-sm text-white group-hover:text-brand transition-colors">
                                {card.title}
                              </h3>
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {card.description}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Messages Stream */}
                {activeSession?.messages.map((msg) => {
                  const isUser = msg.role === "user";
                  return (
                    <div
                      key={msg.id}
                      className={`flex gap-3.5 max-w-4xl mx-auto ${
                        isUser ? "flex-row-reverse" : "flex-row"
                      }`}
                    >
                      {/* Avatar */}
                      <div
                        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                          isUser
                            ? "bg-gradient-to-tr from-brand to-indigo-600 text-white"
                            : "bg-[#0D1424] border border-brand/40 text-brand ring-1 ring-brand/20"
                        }`}
                      >
                        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                      </div>

                      {/* Content Bubble */}
                      <div className={`flex-1 min-w-0 group/msg ${isUser ? "flex flex-col items-end" : ""}`}>
                        <div
                          className={`p-4 sm:p-5 rounded-2xl text-sm leading-relaxed shadow-lg max-w-3xl ${
                            isUser
                              ? "bg-brand text-white rounded-tr-sm"
                              : "bg-[#0E1528] border border-border/80 text-gray-200 rounded-tl-sm w-full"
                          }`}
                        >
                          {isUser ? (
                            <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
                          ) : (
                            <MarkdownRenderer content={msg.content} />
                          )}
                        </div>

                        {/* Action Bar */}
                        <div className={`flex items-center gap-1 mt-1.5 text-xs text-gray-500 ${isUser ? "justify-end" : "justify-start"}`}>
                          <span className="text-[10px] text-gray-500 px-1">
                            {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                          <button
                            onClick={() => handleCopyMessage(msg.id, msg.content)}
                            className="p-1 hover:text-gray-300 rounded hover:bg-white/5 transition-colors flex items-center gap-1"
                            title="Copy message"
                          >
                            {copiedMsgId === msg.id ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                          {!isUser && (
                            <>
                              <button
                                onClick={() => setLikedMsgIds({ ...likedMsgIds, [msg.id]: "up" })}
                                className={`p-1 rounded hover:bg-white/5 transition-colors ${likedMsgIds[msg.id] === "up" ? "text-emerald-400" : "hover:text-gray-300"}`}
                                title="Helpful"
                              >
                                <ThumbsUp className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => setLikedMsgIds({ ...likedMsgIds, [msg.id]: "down" })}
                                className={`p-1 rounded hover:bg-white/5 transition-colors ${likedMsgIds[msg.id] === "down" ? "text-red-400" : "hover:text-gray-300"}`}
                                title="Not helpful"
                              >
                                <ThumbsDown className="w-3 h-3" />
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {/* Loading / Thinking Indicator */}
                {isLoading && (
                  <div className="flex gap-3.5 max-w-4xl mx-auto">
                    <div className="w-8 h-8 rounded-xl bg-[#0D1424] border border-brand/40 text-brand flex items-center justify-center shrink-0 animate-pulse">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div className="p-4 rounded-2xl bg-[#0E1528] border border-border/80 rounded-tl-sm flex items-center gap-3">
                      <Loader2 className="w-4 h-4 animate-spin text-brand" />
                      <span className="text-xs text-gray-300 font-medium animate-pulse">
                        StockSense AI is synthesizing multi-factor intelligence & formulating response...
                      </span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Bottom Input Area */}
              <div className="p-3 sm:p-4 bg-[#080C16] border-t border-border/80">
                <div className="max-w-4xl mx-auto space-y-2.5">
                  
                  {/* Topic suggestion pills */}
                  <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-[11px]">
                    <span className="text-gray-500 font-semibold uppercase tracking-wider shrink-0 text-[10px]">
                      {activeStockContext ? `${activeStockContext.ticker} Inquiries:` : "Quick Prompts:"}
                    </span>
                    {(activeStockContext ? getStockSuggestedPrompts(activeStockContext) : QUICK_TOPIC_PILLS).map((pill, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSend(pill)}
                        className="px-2.5 py-1 rounded-lg bg-[#111A2E] hover:bg-brand/20 border border-border/60 hover:border-brand/40 text-gray-300 hover:text-white shrink-0 transition-all font-medium whitespace-nowrap"
                      >
                        {pill}
                      </button>
                    ))}
                  </div>

                  {/* Textarea + Action buttons */}
                  <div className="relative bg-[#0E1526] border border-border rounded-xl focus-within:border-brand focus-within:ring-1 focus-within:ring-brand shadow-xl transition-all">
                    <textarea
                      ref={textareaRef}
                      value={input}
                      onChange={handleInputChange}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSend();
                        }
                      }}
                      rows={1}
                      placeholder={
                        activeStockContext
                          ? `Ask anything about ${activeStockContext.ticker} (${activeStockContext.companyName || ""}), valuation, ML prediction, risks...`
                          : "Ask anything about PSX stocks, valuation ratios, technical setups, quant risk..."
                      }
                      className="w-full bg-transparent px-3.5 py-3 pr-20 text-sm text-white placeholder:text-gray-500 focus:outline-none resize-none max-h-40 min-h-[48px]"
                    />
                    
                    <div className="absolute right-2 bottom-2 flex items-center gap-1.5">
                      {activeSession && activeSession.messages.length > 2 && (
                        <button
                          onClick={handleRegenerate}
                          disabled={isLoading}
                          className="p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors disabled:opacity-40"
                          title="Regenerate last response"
                        >
                          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                        </button>
                      )}
                      <button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || isLoading}
                        className="p-2 bg-brand text-white rounded-lg hover:bg-brand/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-blue-500/20"
                        title="Send query"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <p className="text-[11px] text-gray-500 text-center">
                    StockSense AI is an institutional decision support system. Predictions are probabilistic and do not constitute financial advice.
                  </p>
                </div>
              </div>
            </main>
          </div>
        </div>
      )}
    </>
  );
}
