# StockSense AI — Model Training, Calibration & Conformal Prediction

## 1. Training Orchestration Workflow
The `ModelTrainer` executes a 6-stage training and validation lifecycle:
1. **Data Sufficiency Gate**: Verifies historical observations ($\ge 60$ days, $\ge 40$ rows, $\ge 75\%$ completeness).
2. **Chronological Splitting**:
   - **Train Set (60%)**: Fits model parameters and preprocessing scalers.
   - **Calibration Set (20%)**: Fits probability calibrator and conformal quantile cutoff.
   - **Out-of-Sample Test Set (20%)**: Evaluates directional accuracy, Brier score, ECE, MAE, and empirical interval coverage.
3. **Probability Calibration**:
   - **Isotonic Regression** / **Platt Scaling**: Calibrates raw model probabilities to true empirical frequencies.
   - Evaluates **Brier Score** ($\frac{1}{N}\sum(p_i - y_i)^2$) and **Expected Calibration Error (ECE)**.
4. **Split Conformal Prediction**:
   - Computes nonconformity scores $s_i = |y_{cal, i} - \hat{y}_{cal, i}|$ on calibration split.
   - Computes quantile $\hat{q} = \text{quantile}(s, \frac{\lceil (n+1)(1-\alpha) \rceil}{n})$.
   - Yields interval $[\hat{y} - \hat{q}, \hat{y} + \hat{q}]$ with exact $(1-\alpha)$ coverage guarantees.
5. **Walk-Forward Validation**: Multi-period out-of-sample stability verification.
6. **Registry Persistence**: Serializes artifacts to disk with SHA-256 integrity checksums.
