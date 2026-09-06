"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ChevronLeft } from "lucide-react";

interface BackButtonProps {
  label?: string;
  fallbackHref?: string;
  className?: string;
  variant?: "button" | "pill" | "subtle" | "breadcrumb";
  breadcrumbParent?: { label: string; href: string };
  breadcrumbCurrent?: string;
}

export function BackButton({
  label = "Back",
  fallbackHref = "/dashboard",
  className = "",
  variant = "pill",
  breadcrumbParent,
  breadcrumbCurrent,
}: BackButtonProps) {
  const router = useRouter();

  const handleBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
    } else {
      router.push(fallbackHref);
    }
  };

  if (variant === "breadcrumb" && breadcrumbParent) {
    return (
      <div className={`flex items-center gap-2 text-xs font-mono text-gray-400 ${className}`}>
        <button
          onClick={handleBack}
          className="inline-flex items-center gap-1 text-gray-400 hover:text-white transition-colors group"
        >
          <ChevronLeft className="h-3.5 w-3.5 group-hover:-translate-x-0.5 transition-transform" />
          <span>{label}</span>
        </button>
        <span className="text-gray-600">/</span>
        <Link href={breadcrumbParent.href} className="hover:text-brand transition-colors">
          {breadcrumbParent.label}
        </Link>
        {breadcrumbCurrent && (
          <>
            <span className="text-gray-600">/</span>
            <span className="text-white font-semibold truncate max-w-[200px]">{breadcrumbCurrent}</span>
          </>
        )}
      </div>
    );
  }

  if (variant === "subtle") {
    return (
      <button
        onClick={handleBack}
        className={`inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-all group font-mono ${className}`}
      >
        <ArrowLeft className="h-3.5 w-3.5 group-hover:-translate-x-1 transition-transform text-brand" />
        <span>{label}</span>
      </button>
    );
  }

  return (
    <button
      onClick={handleBack}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-background-elevated/80 hover:bg-background-elevated border border-border/80 hover:border-brand/40 text-gray-300 hover:text-white text-xs font-semibold shadow-sm transition-all duration-200 group active:scale-95 ${className}`}
      title={label}
    >
      <ArrowLeft className="h-3.5 w-3.5 text-brand group-hover:-translate-x-1 transition-transform duration-200" />
      <span>{label}</span>
    </button>
  );
}
