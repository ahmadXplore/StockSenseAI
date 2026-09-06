# StockSense AI — Machine Learning Architecture

## 1. Architectural Topology

```
                  Canonical Multi-Market Data
                               |
                    Point-in-Time Engine
                               |
                    Feature Extraction Suite
                               |
                    Data Sufficiency Checker
                               |
                    Purged Time-Series Split
                               |
             ┌─────────────────┼─────────────────┐
             ↓                 ↓                 ↓
      Direction Model   Return Forecaster   Volatility Model
      (Classification)    (Regression)      (Realized Vol)
             └─────────────────┬─────────────────┘
                               ↓
                   Probability Calibration
                   (Isotonic / Platt Scaling)
                               ↓
                   Split Conformal Prediction
                    (90% Prediction Bounds)
                               ↓
                   Master Ensemble Predictor
                               ↓
                     Explainability Engine
                   (Feature Attribution)
                               ↓
                        Model Registry
                     (SHA-256 Checksums)
```

---

## 2. Model Implementations

1. **Direction Classifier** (`app.ml.models.direction.DirectionClassifier`):
   - Algorithms: HistGradientBoostingClassifier, RandomForestClassifier, LogisticRegression.
   - Outputs: `probability_up`, `probability_down`, `predicted_direction`.
   - Balanced class weighting to accommodate financial drift regimes.

2. **Return Forecaster** (`app.ml.models.return_forecaster.ReturnForecaster`):
   - Algorithms: HistGradientBoostingRegressor, Ridge, RandomForestRegressor.
   - Outputs: Point forecast of expected return (%) over target horizon.

3. **Volatility Forecaster** (`app.ml.models.volatility.VolatilityForecaster`):
   - Models forward annualized realized volatility over target horizon.

4. **Master Ensemble** (`app.ml.models.ensemble.StockSenseEnsemble`):
   - Blends all models into a single prediction object with confidence score (0–100) and top driver features.
