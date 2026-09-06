# Frontend Architecture
StockSense AI uses a modern Next.js App Router frontend built with React, TypeScript, and Tailwind CSS.
It is designed as a manual financial analysis platform. No autonomous agent acts on behalf of the user.

## Core Stack
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + Lucide React for iconography
- **State Management:** React Context (MarketContext) & LocalStorage (for portfolios/watchlists)
- **Data Fetching:** Fetch API with centralized client (`lib/api.ts`)
- **Charting:** Recharts

## Structure
- `app/` - Next.js routes (Dashboard, Markets, Stocks, Portfolio, Backtesting, Chatbot)
- `components/` - Reusable UI components for forms, charts, tables, and navigation
- `lib/` - Formatting, Market utilities, API definitions
