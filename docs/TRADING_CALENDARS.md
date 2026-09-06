# StockSense AI — Trading Calendars & Market Sessions

## 1. Overview

Each market has distinct session hours, holiday calendars, and split-session structures. Backtesting and real-time execution consume the generic `TradingCalendar` interface to ensure realistic simulation without look-ahead or closed-market errors.

---

## 2. Market Calendars

### A. Pakistan Stock Exchange (PSX)
- **Timezone**: `Asia/Karachi` (UTC+5)
- **Monday – Thursday**: Continuous session `09:15` to `15:30`
- **Friday**: Split session with Jummah prayer break:
  - Session 1: `09:15` – `12:00`
  - Break: `12:00` – `14:30`
  - Session 2: `14:30` – `16:30`
- **National & Islamic Holidays Observed**:
  - Kashmir Day (Feb 5)
  - Pakistan Day (Mar 23)
  - Labor Day (May 1)
  - Independence Day (Aug 14)
  - Iqbal Day (Nov 9)
  - Quaid-e-Azam Day (Dec 25)
  - Bank Holidays (Jan 1, Jul 1)
  - Eid-ul-Fitr, Eid-ul-Adha, Ashura (9, 10 Muharram), Eid Milad-un-Nabi

---

### B. United States (NYSE / NASDAQ)
- **Timezone**: `America/New_York` (EST/EDT)
- **Regular Hours**: `09:30` to `16:00`
- **Early Closes (13:00 EST)**:
  - Day before Independence Day (if weekday)
  - Black Friday (Day after Thanksgiving)
  - Christmas Eve (if weekday)
- **Federal & Exchange Holidays**:
  - New Year's Day
  - Martin Luther King Jr. Day (3rd Mon in Jan)
  - Washington's Birthday (3rd Mon in Feb)
  - Good Friday
  - Memorial Day (Last Mon in May)
  - Juneteenth (Jun 19)
  - Independence Day (Jul 4)
  - Labor Day (1st Mon in Sep)
  - Thanksgiving Day (4th Thu in Nov)
  - Christmas Day (Dec 25)
