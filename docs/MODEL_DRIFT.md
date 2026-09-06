# StockSense AI — Model & Feature Drift Monitoring

## 1. Feature Drift Detection
The `DriftMonitor` tracks statistical distribution shifts between baseline training sets and current inference data:

### 1.1 Population Stability Index (PSI)
$$\text{PSI} = \sum_{b=1}^{B} (P_{current, b} - P_{baseline, b}) \times \ln\left(\frac{P_{current, b}}{P_{baseline, b}}\right)$$
- **PSI < 0.10**: Stable distribution (No shift).
- **0.10 $\le$ PSI < 0.20**: Moderate shift (Warning).
- **PSI $\ge$ 0.20**: Significant feature drift (Action required).

### 1.2 Two-Sample Kolmogorov-Smirnov Test
Computes supremum distance between baseline and current empirical CDFs with associated p-value ($p < 0.05$).

---

## 2. Automated Retraining Triggers
- Retraining recommendations (`requires_retrain = True`) are triggered when $> 25\%$ of active features display significant drift or when rolling 14-day directional accuracy degrades $> 10\%$.
