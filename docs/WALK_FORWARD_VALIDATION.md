# StockSense AI — Purged & Embargoed Walk-Forward Validation

## 1. Principle
Time-series forecasting cannot use random cross-validation because future data would contaminate past training sets. Furthermore, multi-horizon prediction targets (e.g. 30D forward returns) create overlapping labels across adjacent calendar dates.

---

## 2. Purging and Embargo Mechanics

```
  [ Fold 1 Train ] ---[ Purge 21D ]---> [ Fold 1 Test ] ---[ Embargo ]--->
         [ Fold 2 Train (Expanding) ] ---[ Purge 21D ]---> [ Fold 2 Test ]
```

- **Purge Window**: Drops training observations whose forward target horizon spans into the test period.
- **Embargo Buffer**: Introduces a separation buffer after test observations before resuming training data.

---

## 3. Multi-Period Metrics
Walk-forward validation reports:
- Number of evaluated folds ($n$)
- Mean out-of-sample directional accuracy (%)
- Standard deviation of directional accuracy (%)
- Mean absolute error (MAE) across all folds
