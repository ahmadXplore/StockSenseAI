# StockSense AI — Model Evaluation & Explainability

## 1. Metrics Tracked

### 1.1 Classification Metrics
- **Accuracy**: Percentage of correct directional forecasts.
- **Precision & Recall**: Positive return prediction correctness.
- **F1 Score**: Harmonic mean of precision and recall.
- **ROC-AUC**: Area under the receiver operating characteristic curve.
- **Balanced Accuracy**: Arithmetic mean of sensitivity and specificity.

### 1.2 Regression & Financial Metrics
- **MAE / RMSE**: Prediction error against realized forward return %.
- **Information Coefficient (IC)**: Pearson correlation between predicted and actual forward returns.
- **Rank IC**: Spearman rank correlation.
- **Sharpe Ratio & Sortino Ratio**: Strategy risk-adjusted returns.
- **Maximum Drawdown**: Largest peak-to-trough equity drop.
- **Win Rate**: Percentage of profitable trades.

### 1.3 Explainability
- Native Gini & Gain feature importances.
- Permutation feature importance.
- Top positive and negative driver signals extracted per prediction.
