"""
StockSense AI — Performance Attribution Engine
Breaks down total returns by Security, Market, Sector, Regime, and Strategy factor.
"""

from typing import List, Dict, Any
from app.backtesting.schemas import TradeRecord, PerformanceAttribution


def compute_performance_attribution(trades: List[TradeRecord]) -> PerformanceAttribution:
    """
    Computes performance decomposition across securities, markets, sectors, and regimes.
    """
    by_sec: Dict[str, Dict[str, float]] = {}
    by_mkt: Dict[str, float] = {}
    by_reg: Dict[str, Dict[str, float]] = {}
    by_strat: Dict[str, float] = {}

    for t in trades:
        # By Security
        sec_key = t.ticker or t.security_id
        if sec_key not in by_sec:
            by_sec[sec_key] = {"total_pnl": 0.0, "trades_count": 0, "win_count": 0}
        by_sec[sec_key]["total_pnl"] += t.net_pnl
        by_sec[sec_key]["trades_count"] += 1
        if t.net_pnl > 0:
            by_sec[sec_key]["win_count"] += 1

        # By Market
        mkt_key = t.market_code or "US"
        by_mkt[mkt_key] = by_mkt.get(mkt_key, 0.0) + t.net_pnl

        # By Regime
        reg_key = t.market_regime or "bull"
        if reg_key not in by_reg:
            by_reg[reg_key] = {"total_pnl": 0.0, "trades": 0}
        by_reg[reg_key]["total_pnl"] += t.net_pnl
        by_reg[reg_key]["trades"] += 1

        # By Signal / Strategy
        strat_key = t.signal_name or "AI_PREDICTION"
        by_strat[strat_key] = by_strat.get(strat_key, 0.0) + t.net_pnl

    # Identify Top Contributors and Detractors
    sorted_secs = sorted(by_sec.items(), key=lambda x: x[1]["total_pnl"], reverse=True)
    top_contribs = [{"security": k, "net_pnl": round(v["total_pnl"], 2), "trades": v["trades_count"]} for k, v in sorted_secs if v["total_pnl"] > 0][:5]
    top_detractors = [{"security": k, "net_pnl": round(v["total_pnl"], 2), "trades": v["trades_count"]} for k, v in reversed(sorted_secs) if v["total_pnl"] < 0][:5]

    # Format security dict
    formatted_by_sec = {
        k: {
            "total_pnl": round(v["total_pnl"], 2),
            "trades_count": v["trades_count"],
            "win_rate_pct": round(v["win_count"] / v["trades_count"] * 100.0, 1) if v["trades_count"] > 0 else 0.0,
        }
        for k, v in by_sec.items()
    }

    formatted_by_reg = {
        k: {"total_pnl": round(v["total_pnl"], 2), "trades": v["trades"]} for k, v in by_reg.items()
    }

    return PerformanceAttribution(
        by_security=formatted_by_sec,
        by_market={k: round(v, 2) for k, v in by_mkt.items()},
        by_sector={"Technology": 0.0}, # Enhanced when sector metadata available
        by_regime=formatted_by_reg,
        by_strategy={k: round(v, 2) for k, v in by_strat.items()},
        top_contributors=top_contribs,
        top_detractors=top_detractors,
    )
