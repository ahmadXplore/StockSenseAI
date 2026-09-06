"""
StockSense AI — Trading Calendar Unit Tests
Tests PSX and US Trading Calendars, public holidays, sessions, and early closes.
"""

import pytest
from datetime import date, time, datetime
import zoneinfo

from app.data.calendars.base import SessionType
from app.data.calendars.psx import PSXTradingCalendar
from app.data.calendars.us import USTradingCalendar
from app.data.calendars.registry import get_trading_calendar


def test_psx_trading_calendar_sessions_and_holidays():
    cal = PSXTradingCalendar()
    assert cal.market_code == "PK"
    assert cal.exchange_code == "PSX"
    assert cal.tz_name == "Asia/Karachi"

    # Weekend check
    sat = date(2025, 1, 4)
    sun = date(2025, 1, 5)
    assert not cal.is_trading_day(sat)
    assert not cal.is_trading_day(sun)

    # Monday regular session
    mon = date(2025, 1, 6)
    assert cal.is_trading_day(mon)
    mon_hours = cal.get_session_hours(mon)
    assert mon_hours.session_type == SessionType.REGULAR
    assert mon_hours.open_time == time(9, 15)
    assert mon_hours.close_time == time(15, 30)

    # Friday split session (Jummah prayer break)
    fri = date(2025, 1, 10)
    assert cal.is_trading_day(fri)
    fri_hours = cal.get_session_hours(fri)
    assert fri_hours.session_type == SessionType.SPLIT_SESSION
    assert fri_hours.break_start == time(12, 0)
    assert fri_hours.break_end == time(14, 30)

    # Fixed Holidays (e.g. Kashmir Day Feb 5, Independence Day Aug 14)
    kashmir_day = date(2025, 2, 5)
    indep_day = date(2025, 8, 14)
    assert not cal.is_trading_day(kashmir_day)
    assert not cal.is_trading_day(indep_day)


def test_us_trading_calendar_sessions_and_early_closes():
    cal = USTradingCalendar()
    assert cal.market_code == "US"
    assert cal.tz_name == "America/New_York"

    # Regular trading day
    tue = date(2025, 1, 7)
    assert cal.is_trading_day(tue)
    tue_hours = cal.get_session_hours(tue)
    assert tue_hours.session_type == SessionType.REGULAR
    assert tue_hours.open_time == time(9, 30)
    assert tue_hours.close_time == time(16, 0)

    # MLK Day (3rd Monday in Jan) -> Holiday
    mlk_2025 = date(2025, 1, 20)
    assert not cal.is_trading_day(mlk_2025)

    # Black Friday 2025 (Day after Thanksgiving, 4th Friday in Nov) -> Early close at 13:00
    black_fri_2025 = date(2025, 11, 28)
    assert cal.is_trading_day(black_fri_2025)
    bf_hours = cal.get_session_hours(black_fri_2025)
    assert bf_hours.session_type == SessionType.EARLY_CLOSE
    assert bf_hours.close_time == time(13, 0)


def test_calendar_registry():
    cal_psx = get_trading_calendar("PSX")
    assert isinstance(cal_psx, PSXTradingCalendar)

    cal_us = get_trading_calendar("NASDAQ")
    assert isinstance(cal_us, USTradingCalendar)

    cal_lse = get_trading_calendar("LSE")
    assert cal_lse.tz_name == "Europe/London"
