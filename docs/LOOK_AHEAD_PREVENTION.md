# StockSense AI — Zero Look-Ahead Bias & Point-in-Time Prevention

## 1. Safety Principles

### 1.1 Fundamental Statements Lag Enforcement
- Financial statement disclosure dates (`data_available_date` or `filing_date`) are strictly checked: `filing_date <= as_of_date`.
- If no explicit disclosure date exists, a mandatory 25-day reporting lag after the fiscal quarter end is enforced.
- Statements published after the prediction timestamp are completely invisible to the feature extractor.

### 1.2 News & Sentiment Timestamp Gating
- News articles published at $T > as\_of\_date$ are filtered out before computing 7D and 30D sentiment aggregates.

### 1.3 Preprocessing Leak-Free Fitting
- All scalers (StandardScaler, RobustScaler) and calibrators (IsotonicRegression) are fit **only on training data** and never on the full combined dataset prior to splitting.

### 1.4 Automated Leakage Detection Engine
- Scans feature matrices for correlations $> 0.99$ with future targets and blocks model training immediately if leakage is detected.
