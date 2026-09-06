"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy, Terminal, Info } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="markdown-content text-gray-200 text-sm leading-relaxed space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-xl font-bold text-white mt-4 mb-2 pb-1 border-b border-border/80 flex items-center gap-2" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-lg font-bold text-white mt-3 mb-2 pb-1 border-b border-border/60 text-blue-400" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-base font-bold text-white mt-3 mb-1 text-emerald-400" {...props} />
          ),
          h4: ({ node, ...props }) => (
            <h4 className="text-sm font-bold text-gray-100 mt-2 mb-1" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="mb-2 leading-relaxed text-gray-200" {...props} />
          ),
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-white tracking-wide" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic text-gray-300" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc pl-5 my-2 space-y-1.5 marker:text-brand" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal pl-5 my-2 space-y-1.5 marker:text-brand font-medium" {...props} />
          ),
          li: ({ node, ...props }) => (
            <li className="leading-relaxed pl-0.5" {...props} />
          ),
          blockquote: ({ node, children }) => (
            <blockquote className="my-3 p-3 bg-brand/10 border-l-4 border-brand rounded-r-lg text-xs sm:text-sm text-gray-200 flex items-start gap-2 shadow-sm">
              <Info className="w-4 h-4 text-brand shrink-0 mt-0.5" />
              <div className="flex-1 italic">{children}</div>
            </blockquote>
          ),
          table: ({ node, ...props }) => (
            <div className="my-3 overflow-x-auto rounded-lg border border-border/80 bg-background-elevated/80 shadow-md">
              <table className="w-full text-left border-collapse text-xs sm:text-sm" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => (
            <thead className="bg-[#121B2F] border-b border-border text-gray-200 uppercase tracking-wider text-[11px] font-semibold" {...props} />
          ),
          tbody: ({ node, ...props }) => (
            <tbody className="divide-y divide-border/60" {...props} />
          ),
          tr: ({ node, ...props }) => (
            <tr className="hover:bg-background-hover/50 transition-colors" {...props} />
          ),
          th: ({ node, ...props }) => (
            <th className="px-3 py-2.5 font-bold text-gray-200" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="px-3 py-2 text-gray-300" {...props} />
          ),
          code: ({ node, inline, className, children, ...props }: any) => {
            const codeString = String(children).replace(/\n$/, "");
            if (inline) {
              return (
                <code className="bg-background-elevated px-1.5 py-0.5 rounded text-xs font-mono text-cyan-300 border border-border/60" {...props}>
                  {children}
                </code>
              );
            }
            return <CodeBlock code={codeString} language={className?.replace("language-", "")} />;
          },
          hr: () => <hr className="my-3 border-border/70" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function CodeBlock({ code, language }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-lg overflow-hidden border border-border/80 bg-[#080C15] font-mono text-xs shadow-lg">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#0F172A] border-b border-border/70 text-gray-400">
        <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
          <Terminal className="w-3.5 h-3.5 text-brand" />
          <span>{language || "code"}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white transition-colors px-1.5 py-0.5 rounded hover:bg-white/5"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3 overflow-x-auto text-gray-200">
        <code>{code}</code>
      </pre>
    </div>
  );
}
