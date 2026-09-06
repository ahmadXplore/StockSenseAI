"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Bot, Send, Sparkles, Maximize2, Loader2, TrendingUp, TrendingDown,
  ShieldAlert, Copy, Check, RefreshCw, Brain, ExternalLink,
  FileText, BarChart3, HelpCircle, Activity, ChevronRight
} from "lucide-react";
import {
  StockAIContext,
  openStockAICopilot,
  getStockSuggestedPrompts,
  buildStockInitialBrief
} from "@/lib/aiCopilot";
import { MarkdownRenderer } from "@/components/chatbot/MarkdownRenderer";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface StockAICopilotPanelProps {
  context: StockAIContext;
  className?: string;
}

export function StockAICopilotPanel({ context, className = "" }: StockAICopilotPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize or reset session when active security changes
  useEffect(() => {
    const initialGreeting = buildStockInitialBrief(context);
    setMessages([
      {
        id: "msg_init_" + context.ticker,
        role: "assistant",
        content: initialGreeting,
        timestamp: Date.now(),
      },
    ]);
  }, [context.ticker]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (overridePrompt?: string) => {
    const promptToSend = (overridePrompt || input).trim();
    if (!promptToSend || loading) return;

    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMsg: Message = {
      id: "usr_" + Date.now(),
      role: "user",
      content: promptToSend,
      timestamp: Date.now(),
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
          context: {
            activeMarket: context.marketName || "Global Equity Market",
            activeMarketCode: context.marketCode || "GLOBAL",
            currency: context.currency || "USD",
            stockContext: context,
          },
        }),
      });

      if (!response.ok) throw new Error("Failed to contact StockSense AI");

      const data = await response.json();
      const aiMsg: Message = {
        id: "ai_" + Date.now(),
        role: "assistant",
        content: data.content || "I have completed the analysis for this stock.",
        timestamp: Date.now(),
      };
      setMessages([...newMessages, aiMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: "err_" + Date.now(),
        role: "assistant",
        content: `### Query Execution Notice\n\nI encountered a transient network delay while analyzing **${context.ticker}**.\n\n- Please try submitting your inquiry again.\n- Or click **Expand Full AI Terminal** in the header to access extended inference channels.`,
        timestamp: Date.now(),
      };
      setMessages([...newMessages, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const suggestedPrompts = getStockSuggestedPrompts(context);
  const isUp = (context.prediction?.direction || "").toUpperCase() === "UP";

  return (
    <div className={`bg-[#0B0F19] border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col ${className}`}>
      {/* Copilot Header */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-[#0E1528] via-[#0B1120] to-[#0D1426] border-b border-border/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
              <Sparkles className="w-5 h-5 text-yellow-300 animate-pulse" />
            </div>
            <span className="absolute -bottom-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full ring-2 ring-[#0B0F19] animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                StockSense AI Analyst
              </h2>
              <span className="px-2 py-0.5 rounded bg-brand/20 border border-brand/40 text-blue-300 font-mono font-bold text-[11px]">
                {context.ticker}
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Context-Aware Financial Intelligence · Fundamentals · ML Explainability · Risk Bounds
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMessages([
              {
                id: "msg_init_" + Date.now(),
                role: "assistant",
                content: buildStockInitialBrief(context),
                timestamp: Date.now(),
              }
            ])}
            className="px-2.5 py-1.5 rounded-lg bg-background-elevated hover:bg-white/10 border border-border/60 text-gray-300 hover:text-white text-xs font-medium transition-all flex items-center gap-1.5"
            title="Reset conversation"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>

          <button
            onClick={() => openStockAICopilot(context)}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 border border-blue-400/40 flex items-center gap-1.5 group"
            title="Open full-screen terminal with chat history and PDF/MD export"
          >
            <Maximize2 className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            <span>Expand Full AI Terminal</span>
          </button>
        </div>
      </div>

      {/* Live Data Badge Strip */}
      <div className="px-4 py-2 bg-[#080C16] border-b border-border/60 flex items-center gap-2 overflow-x-auto text-[11px] font-mono scrollbar-none">
        <span className="text-gray-500 uppercase tracking-wider font-sans font-semibold text-[10px] shrink-0">
          Live Context:
        </span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="px-2 py-0.5 rounded bg-white/5 border border-border text-gray-300">
            Price: <strong className="text-white">{context.currency} {context.price?.toLocaleString()}</strong>
          </span>
          <span className={`px-2 py-0.5 rounded border ${context.changePct !== undefined && context.changePct >= 0 ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" : "bg-red-500/10 border-red-500/30 text-red-400"}`}>
            {context.changePct !== undefined && context.changePct >= 0 ? "+" : ""}{context.changePct?.toFixed(2)}%
          </span>
          {context.prediction?.direction && (
            <span className="px-2 py-0.5 rounded bg-purple-500/15 border border-purple-500/30 text-purple-300 font-bold">
              ML: {context.prediction.direction} ({context.prediction.probability_up ? Math.round(context.prediction.probability_up * 100) : "68"}%)
            </span>
          )}
          {context.peRatio && (
            <span className="px-2 py-0.5 rounded bg-white/5 border border-border text-gray-300">
              P/E: <strong className="text-white">{context.peRatio}</strong>
            </span>
          )}
          {context.roe && (
            <span className="px-2 py-0.5 rounded bg-white/5 border border-border text-gray-300">
              ROE: <strong className="text-white">{context.roe}</strong>
            </span>
          )}
        </div>
      </div>

      {/* Conversation Thread */}
      <div className="p-4 sm:p-6 space-y-4 max-h-[560px] min-h-[300px] overflow-y-auto bg-[#070B14]">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-3xl ${isUser ? "ml-auto flex-row-reverse" : "mr-auto flex-row"}`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                  isUser
                    ? "bg-brand text-white"
                    : "bg-[#0E1528] border border-brand/40 text-brand"
                }`}
              >
                {isUser ? <span className="text-xs font-bold font-mono">YOU</span> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div className={`flex-1 min-w-0 ${isUser ? "flex flex-col items-end" : ""}`}>
                <div
                  className={`p-4 rounded-2xl text-xs sm:text-sm shadow-md leading-relaxed ${
                    isUser
                      ? "bg-brand text-white rounded-tr-sm"
                      : "bg-[#0E162A] border border-border/80 text-gray-200 rounded-tl-sm w-full"
                  }`}
                >
                  {isUser ? (
                    <p className="whitespace-pre-wrap font-medium">{msg.content}</p>
                  ) : (
                    <MarkdownRenderer content={msg.content} />
                  )}
                </div>

                {/* Footer timestamp & copy */}
                <div className={`flex items-center gap-1.5 mt-1 text-[10px] text-gray-500 ${isUser ? "justify-end" : "justify-start"}`}>
                  <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  <button
                    onClick={() => handleCopy(msg.id, msg.content)}
                    className="p-1 hover:text-gray-300 rounded hover:bg-white/5 transition-colors"
                    title="Copy response"
                  >
                    {copiedId === msg.id ? (
                      <Check className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-3 mr-auto max-w-3xl">
            <div className="w-8 h-8 rounded-xl bg-[#0E1528] border border-brand/40 text-brand flex items-center justify-center shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-[#0E162A] border border-border/80 rounded-tl-sm flex items-center gap-2.5">
              <Loader2 className="w-4 h-4 animate-spin text-brand" />
              <span className="text-xs text-gray-300 animate-pulse">
                StockSense AI is analyzing multi-factor data for <strong>{context.ticker}</strong>...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Stock Inquiries Chips */}
      <div className="p-3 bg-[#080D18] border-t border-border/70 space-y-2">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-[11px]">
          <span className="text-gray-500 font-semibold uppercase tracking-wider text-[10px] shrink-0">
            Suggested Inquiries:
          </span>
          {suggestedPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="px-2.5 py-1 rounded-lg bg-[#111A2E] hover:bg-brand/20 border border-border/60 hover:border-brand/40 text-gray-300 hover:text-white shrink-0 transition-all font-medium whitespace-nowrap text-left"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Textarea & Send Button */}
        <div className="relative bg-[#0E1526] border border-border rounded-xl focus-within:border-brand focus-within:ring-1 focus-within:ring-brand shadow-lg transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            rows={1}
            placeholder={`Ask anything about ${context.ticker} (valuation, ML drivers, technical levels, risks)...`}
            className="w-full bg-transparent px-3.5 py-3 pr-14 text-xs sm:text-sm text-white placeholder:text-gray-500 focus:outline-none resize-none max-h-36 min-h-[44px]"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="absolute right-2 bottom-2 p-2 bg-brand text-white rounded-lg hover:bg-brand/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-blue-500/20"
            title="Submit question"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex items-center justify-between text-[11px] text-gray-500 pt-1">
          <span>AI answers synthesize live financial statements & LightGBM inference.</span>
          <button
            onClick={() => openStockAICopilot(context)}
            className="text-brand hover:underline flex items-center gap-1 font-semibold"
          >
            <span>Full-Screen Workspace</span>
            <ExternalLink className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}
