/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./layouts/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#0A0E1A",
          elevated: "#111827",
          hover: "#1C2333",
        },
        border: {
          DEFAULT: "#1F2937",
          active: "#374151",
        },
        brand: {
          DEFAULT: "#3B82F6",
          hover: "#2563EB",
        },
        signal: {
          strongBuy: "#10B981",
          buy: "#34D399",
          hold: "#F59E0B",
          highRiskBuy: "#F97316",
          avoid: "#EF4444",
          strongAvoid: "#DC2626",
          veto: "#7F1D1D",
        },
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};
