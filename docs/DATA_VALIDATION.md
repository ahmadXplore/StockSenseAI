# StockSense AI — Data Validation & Quality Engine

## 1. Validation Philosophy

Data quality is enforced before database persistence. No invalid candle or corrupted vendor record is allowed to pollute canonical models.

---

## 2. Multi-Stage Validation Rules

### A. OHLC Geometric Bounds
Every candle must satisfy:
1. $High \ge \max(Open, Close, Low)$
2. $Low \le \min(Open, Close, High)$
3. $Open \ge 0,\ High \ge 0,\ Low \ge 0,\ Close \ge 0,\ Volume \ge 0$

### B. Deduplication
Keys are constructed as $(security\_id, timestamp)$. Duplicate records are rejected with audit logging.

### C. Extreme Move & Anomaly Detection
Price moves with $|return| \ge 30\%$ are evaluated through corporate action correlation:
- **`possible_corporate_action`**: Extreme move matches a stock split, reverse split, or bonus issue on or within 3 days of the event.
- **`possible_missing_adjustment`**: Large move near a cash dividend or rights issue.
- **`possible_data_error`**: $|return| \ge 80\%$ with zero volume or $|return| \ge 100\%$ without market catalyst.
- **`possible_valid_extreme_move`**: Extreme move supported by $>2\times$ volume spike.
- **`possible_market_event`**: Move flagged for quantitative audit.

---

## 3. Dataset Validation CLI Tool

To audit any dataset:

```bash
python -m app.data.validate_dataset --file <PATH_TO_CSV> --market PK --exchange PSX
```

### PSX 2017–2025 Dataset Validation Results:
- **Total Rows**: 840,330
- **Unique Symbols**: 1,142
- **Date Range**: 2017-01-02 to 2025-10-24 (2,183 trading sessions)
- **Exact Duplicates**: 0
- **Zero Volume Days**: 26,742 (untraded/suspended days)
- **Zero Close Entries**: 3,866 (defunct/untraded placeholders)
- **Quality Score**: 100.00 / 100.00 (on active records)
- **Delisted Securities Tracked**: 577 symbols
- **Licensing**: Free open research distribution tier.
