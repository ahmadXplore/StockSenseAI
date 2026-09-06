# UI/UX Design Brief
## AI Stock Prediction & Investment Analysis System
**Version:** 1.0 | **Date:** 2026

---

## 1. Design Philosophy

### 1.1 Core Principles

**Clarity over Complexity**
This system surfaces complex quantitative analysis. The UI must make complex data instantly readable — not impressive to engineers, but useful to investors making real decisions with real money.

**Trust Through Transparency**
Every number must feel earned. Show sources, show dates, show uncertainty. A clean number without context builds false confidence. Visible uncertainty builds appropriate trust.

**Action-Oriented**
Every screen should answer: "What should I do now?" The layout guides the user from insight to decision to action — not just information presentation.

**Calm Under Pressure**
When markets are moving fast, users are anxious. The UI must be calming, not exciting. No red flashing alerts for normal market movements. Reserve urgency (red, bold, prominent) for genuine risk signals.

**No Dark Patterns**
Never manipulate users toward buying decisions. Hard veto warnings must be prominent. Uncertainty must be visible. Disclaimers must be present — not buried in footprints.

---

## 2. Visual Identity

### 2.1 Color System

**Primary Palette — Finance-Grade Dark Theme (Default)**

```
Background (primary):      #0A0E1A    Deep Navy
Background (elevated):     #111827    Card background
Background (hover):        #1C2333    Hover states
Border (default):          #1F2937    Subtle dividers
Border (active):           #374151    Active states

Text (primary):            #F9FAFB    Near white
Text (secondary):          #9CA3AF    Muted
Text (tertiary):           #6B7280    Labels, timestamps

Accent (brand):            #3B82F6    Blue — primary actions, links
Accent (brand-hover):      #2563EB    Darker blue on hover
```

**Signal Colors — Consistent Across Entire App**

```
Strong Buy:     #10B981    Emerald green (calm, confident)
Buy:            #34D399    Lighter emerald
Hold:           #F59E0B    Amber (caution, not alarm)
High-Risk Buy:  #F97316    Orange (visible warning)
Avoid:          #EF4444    Red (clear negative)
Strong Avoid:   #DC2626    Dark red (serious concern)
Veto:           #7F1D1D    Deep red background, #FCA5A5 text
```

**Score Color Scale**

```
85–100:    #10B981  (Emerald — Exceptional)
70–84:     #34D399  (Green — Strong)
55–69:     #F59E0B  (Amber — Moderate)
40–54:     #F97316  (Orange — Concerning)
0–39:      #EF4444  (Red — Weak)
```

**Market Regime Colors**

```
Bull Market:        #10B981 background
Bear Market:        #EF4444 background
High Volatility:    #F59E0B background
Low Volatility:     #3B82F6 background
Recession Signal:   #DC2626 background with pulse animation
Mixed:              #6B7280 background
```

**Light Theme (Alternative)**
- All dark backgrounds flip to white/gray scale
- Signal colors remain identical (critical for consistency)
- Preferred for print/export/PDF reports

### 2.2 Typography

```
Font Stack:
  Headings:     'Inter', sans-serif  (weights: 600, 700)
  Body:         'Inter', sans-serif  (weights: 400, 500)
  Monospace:    'JetBrains Mono', 'Fira Code', monospace
                → All numbers, prices, tickers, percentages
                → Critical: all financial figures use tabular numerals
                  (font-variant-numeric: tabular-nums) for column alignment

Size Scale:
  xs:   12px   Labels, timestamps, footnotes
  sm:   14px   Secondary text, table cells
  base: 16px   Body text
  lg:   18px   Section subheadings
  xl:   20px   Card headings
  2xl:  24px   Section headings
  3xl:  30px   Page titles
  4xl:  36px   Hero metrics (current price, overall score)
```

### 2.3 Spacing System

```
Base unit: 4px
Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96px
Cards: 24px internal padding
Sections: 48px vertical spacing
```

### 2.4 Border Radius

```
Buttons:      8px
Cards:        12px
Modals:       16px
Badges:       9999px (pill)
Score bars:   9999px (pill)
```

---

## 3. Component Library

### 3.1 Score Card Component

Used for all 0–100 scores throughout the app.

```
┌──────────────────────────────────────┐
│  Fundamental Health                   │
│                                      │
│  ████████████████████░░░░  82        │
│  ▲ Strong                            │
│  Revenue +18% YoY · FCF $102B        │
└──────────────────────────────────────┘
```

- Animated fill on first render (300ms ease-out)
- Color changes by score range (green → amber → red)
- Sub-label shows interpretation in plain English
- Key metric shown inline

### 3.2 Recommendation Badge

```
Signal display:
🟢 STRONG BUY    → emerald pill badge
🟢 BUY           → green pill badge  
🟡 HOLD          → amber pill badge
🟠 HIGH-RISK BUY → orange pill badge (⚠ prefix)
🔴 AVOID         → red pill badge
🔴 STRONG AVOID  → dark red pill badge (⛔ prefix)
```

Never show just the badge. Always pair with confidence score and key reason.

### 3.2a Data Limitation Badge

```
Used on any Backtesting section/screen (MVP):
⚪ CURRENT-UNIVERSE-APPROXIMATE → grey pill badge, always visible, non-dismissible

Tooltip/expandable text:
"This backtest does not yet include delisted, bankrupt, or acquired companies'
price history — no free data source reliably provides it. Historical index
membership is tracked correctly, but results may look better than a fully
survivorship-bias-free backtest would show."
```

Same visual treatment tier as the Disclaimer footer (Section 7 below): always present, never collapsed by default, no dismiss/close control.

```
[ 🟢 BUY   71% conf ]   "Strong FCF + below avg. valuation"
```

### 3.3 Price Prediction Row

```
Horizon    Pred.     Return      P(Gain)    Conf.      Signal
7 Days     $229.10   +1.6%       62%        71%        🟢 BUY
           [$213—$245]           ← interval toggle
```

- All numbers right-aligned in monospace
- Positive returns in green, negative in red
- Interval shown as toggleable sub-row

### 3.4 Scenario Cards

Three cards: Bull / Base / Bear (+ optional Tail Risk)

```
Visual treatment:
Bull:  Subtle emerald background tint, upward arrow icon
Base:  Neutral background, horizontal bar icon
Bear:  Subtle red background tint, downward arrow icon
Tail:  Dark background, ⚡ icon, probability < 10%
```

Each card shows: Scenario name | Price target | Return % | Probability | Dollar profit/loss

### 3.5 Veto Banner

Highest-priority component. Must be impossible to miss.

```
Background: #7F1D1D (dark red)
Border-left: 4px solid #DC2626
Text: #FCA5A5

⛔  VETO TRIGGERED: Going Concern Doubt in Audit Opinion

    Explanation of what this means and why it's serious.
    The final recommendation has been overridden to STRONG AVOID
    regardless of all other analysis scores.

    [Learn More]  [Dismiss Warning (requires confirmation)]
```

Dismiss requires explicit confirmation dialog: "I understand this is a serious risk signal. I am dismissing this warning for informational purposes only."

### 3.6 Data Freshness Indicator

Shown next to every data-dependent section:

```
🟢  Price data: 3 minutes ago (real-time)
🟡  Fundamentals: 45 days ago (Q2 2025 earnings)  
🟢  News: 2 hours ago
🔴  Fundamentals STALE: 112 days ago ← flag if >95 days
```

### 3.7 Earnings Warning Component

```
┌─────────────────────────────────────────────────┐
│ 📅 EARNINGS WARNING                              │
│ Earnings announcement in 8 days (Sep 1, 2025)   │
│                                                  │
│ Last 8 quarters: ✅✅✅✅✅❌✅✅ (7 beats, 1 miss)  │
│ Consensus EPS estimate: $1.48                    │
│ Consensus Revenue estimate: $89.5B               │
│                                                  │
│ ⚠ Short-term BUY downgraded to HIGH-RISK BUY    │
│   due to binary earnings event                   │
│ Consider: Exit 50% position before earnings      │
└─────────────────────────────────────────────────┘
```

### 3.8 Technical Indicator Cards

Grid of compact cards, each showing:

```
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│ RSI (14)  │  │ MACD      │  │ BB Width  │  │ Volume    │
│   54.2    │  │ Positive  │  │ 3.2%      │  │ 1.4× avg  │
│ ⬛ Neutral │  │ 🟢 Signal │  │ 🟡 Normal │  │ 🟢 High   │
│           │  │ Cross ↑   │  │           │  │           │
└───────────┘  └───────────┘  └───────────┘  └───────────┘
```

Plain language label required. Never show just "RSI = 54.2" without interpretation.

### 3.9 Exit Plan Component

```
Visual treatment: Vertical timeline with colored markers

Entry ●──────────────────────────────────────────────
      $225.50

                            Trailing Stop activates
                        ┤   at $238.00 (+5.5%)

─────────────────── Hard Stop ────────────────── $209.00 (-7.3%)

Partial Exit ◆ at $247.00 (+9.5%)

Full Exit ★ at $275.00 (+22.0%)

If below $209 → EXIT. If above $247 → PARTIAL EXIT.
```

---

## 4. Page Layouts

### 4.1 Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  ◆ StockSense   [Dashboard] [Watchlist] [Portfolio]  👤 │
├─────────────────────────────────────────────────────────┤
│  Market Regime: 🟢 BULL MARKET  │ SPY +0.4% │ VIX 14.2 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│        Analyze a Stock                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │  🔍  Enter ticker or company name...               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Recent:  [AAPL ×] [MSFT ×] [NVDA ×]                   │
│                                                          │
├──────────────────────────┬──────────────────────────────┤
│  WATCHLIST               │  RECENT ANALYSES              │
│  ┌──────────────────┐    │  ┌──────────────────────┐    │
│  │ AAPL  78  🟢 BUY │    │  │ AAPL — 2h ago        │    │
│  │ MSFT  82  🟢 SBY │    │  │ Score: 78 | BUY      │    │
│  │ TSLA  52  🟡 HLD │    │  └──────────────────────┘    │
│  └──────────────────┘    │  ┌──────────────────────┐    │
│  [+ Add stock]           │  │ MSFT — 1d ago        │    │
│                          │  │ Score: 82 | STRONG BUY│   │
│                          │  └──────────────────────┘    │
└──────────────────────────┴──────────────────────────────┘
```

### 4.2 Report Layout

```
┌─────────────────────────────────────────────────────────┐
│  Navigation bar (sticky)                                 │
├──────────────────────────┬──────────────────────────────┤
│  SIDEBAR (sticky, 240px) │  MAIN CONTENT (scrollable)   │
│  ─────────────────────── │  ──────────────────────────  │
│  • Executive Summary     │  [Current active section     │
│  • Recommendations  ←    │   content renders here]      │
│  • Price Forecast        │                              │
│  • Score Dashboard       │  Each section has:           │
│  • Calculator            │  - Clear h2 heading          │
│  • Fundamental Analysis  │  - Data freshness badge      │
│  • Technical Analysis    │  - Visual chart/table        │
│  • Valuation             │  - Plain text interpretation │
│  • News & Sentiment      │  - Expandable details        │
│  • Risk Analysis         │                              │
│  • Historical Anomaly    │                              │
│  • Exit Strategy         │                              │
│  • Backtesting           │                              │
│  • Disclaimers           │                              │
└──────────────────────────┴──────────────────────────────┘
```

Sidebar highlights current section on scroll (scroll-spy).

### 4.3 Mobile Layout

Bottom navigation:
```
[🔍 Search] [⭐ Watch] [💼 Portfolio] [⚙ Settings]
```

Report sections collapse to accordion (one open at a time).
Score dashboard becomes horizontal scrolling card strip.

---

## 5. Charts & Data Visualization

### 5.1 Price Chart

- Library: TradingView Lightweight Charts (professional-grade)
- Default: Candlestick with volume bars below
- Overlay toggles: SMA 20/50/200, Bollinger Bands, VWAP
- Annotation: Entry price line (if position recorded), Support/Resistance zones
- Time range selector: 1W | 1M | 3M | 6M | 1Y | 3Y | 5Y
- Always show predicted price as a separate dotted line extending right, with shaded confidence interval

### 5.2 Score Spider/Radar Chart

- 7-axis radar showing all module scores
- Filled area changes color by overall score
- Hover on each axis to show sub-score detail
- Library: Recharts Radar

### 5.3 Scenario Bar Chart

- Grouped horizontal bar chart (Bull / Base / Bear / Tail)
- Bars extend right (positive return) or left (negative return) from center
- Color coded: green for positive, red for negative
- Probability shown as bar opacity/thickness

### 5.4 Historical Decline Chart

- Annotation overlay on price chart
- Current drawdown shaded in orange
- Previous similar drawdowns marked with dotted vertical lines
- Recovery paths from previous events shown as faded lines

### 5.5 Sentiment Timeline

- Horizontal timeline with event dots (color coded by sentiment)
- Events sized by significance/materiality
- Rolling sentiment score as a line chart below the timeline

### 5.6 Fundamental Trend Charts (Expandable)

Toggled per sub-score:
- 8-quarter bar chart for metrics like Revenue, EPS, FCF
- Line chart for margin trends
- All in a consistent compact card size (250px height)
- No chart junk — minimal gridlines, no 3D effects

---

## 6. Interaction Design

### 6.1 Loading States

Never show a blank screen. Always show:
- Skeleton loaders with correct layout shape
- Progressive loading: show sections as they complete
- Progress indicators with specific step names (not just a spinner)

### 6.2 Tooltips

Every technical term or abbreviation must have a tooltip:
- "RSI" → hover → "Relative Strength Index: measures momentum. Values above 70 suggest overbought conditions; below 30 suggests oversold."
- "VaR" → hover → "Value at Risk: maximum expected loss at 95% confidence over 1 month."
- "FCF" → hover → "Free Cash Flow: cash a company generates after capital expenditures."

Tooltips appear on hover (desktop) or tap-and-hold (mobile).

### 6.3 Expandable Sections

- All sub-score breakdowns are collapsed by default → expand on click
- DCF assumptions are collapsed → expand to see full detail
- Individual news items are truncated → expand to read full item
- Walk-forward validation results are collapsed → expand to see per-period breakdown

### 6.4 Alerts & Notifications

When user has watchlist:
- Browser notification (with permission): "AAPL earnings in 3 days"
- In-app alert: "TSLA approaching hard stop. Current: $198.30, Stop: $188.00"
- Anomaly alert: "MSFT dropped 8% today. Running anomaly analysis…"

Alert priority system:
- 🔴 Critical (Veto trigger, hard stop hit): Immediate, persistent
- 🟠 High (Earnings in <7 days, trailing stop activated): Prominent
- 🟡 Medium (Earnings in <14 days, score change >10pts): Normal
- ⬛ Low (Watchlist refresh complete, new analysis available): Background

### 6.5 Animations

- Score bars: Animated fill on first render (400ms ease-out)
- Recommendation badge: Fade in (200ms)
- Card hover: Subtle lift (translateY(-2px), shadow increase, 150ms)
- Chart data: Animated draw on first load
- Loading progress steps: Slide in from left (150ms each)

**No** looping animations on static content. **No** animations that serve no purpose. Animations are subtle and purposeful only.

---

## 7. Accessibility Requirements

- Color is never the only differentiator (all signals include text labels)
- All charts have text alternatives (data tables toggle)
- Keyboard navigation on all interactive elements
- Screen reader labels on all icon-only elements
- Minimum contrast ratio: 4.5:1 (WCAG AA)
- Focus states visible on all interactive elements
- Font size minimum: 14px (12px only for non-critical labels)
- All tooltips accessible via keyboard (not mouse-only)

---

## 8. Dark / Light Mode

- Default: Dark mode (professional trading aesthetic)
- System preference respected on first load
- Manual toggle in settings
- All signal colors (green/amber/red) are identical in both modes — only backgrounds change
- Charts automatically adapt to mode

---

## 9. Export / Print

- Every report has "Export PDF" button
- PDF uses light theme automatically
- PDF includes: all sections, charts as static images, full disclaimers
- Report includes generation timestamp and data freshness status
- PDF page header: "StockSense AI — Investment Analysis Report — [Ticker] — [Date]"
- PDF footer: Disclaimer on every page

---

## 10. Onboarding

**First-time user flow:**
1. Landing page with clear value proposition (not a login wall)
2. "Try it free — no signup" → enter ticker → see sample/limited report
3. Signup prompt before saving or accessing full report
4. Onboarding checklist after signup:
   - ✅ Run your first analysis
   - ✅ Add 3 stocks to watchlist
   - ✅ Set your risk tolerance
   - ✅ Record your first position
5. First-analysis tutorial: tooltips highlight key sections with brief explanations

**Key design choice:** User sees value (analysis preview) BEFORE being asked to sign up.

---

## 11. Design Handoff Checklist

Before developer handoff, design deliverables must include:
- [ ] Component library in Figma with all variants (states, sizes, colors)
- [ ] Full screen designs for all 7 main screens in dark + light mode
- [ ] Mobile designs for all 7 main screens (375px, 390px widths)
- [ ] Animation specs (duration, easing, trigger)
- [ ] Spacing and grid documentation
- [ ] Chart specifications (which library, which variant, color specs)
- [ ] Copy for all empty states, error states, loading states
- [ ] Accessibility annotations
- [ ] Interactive prototype for core analysis flow
