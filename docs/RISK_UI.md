# Risk Engine UI
The Portfolio Risk Dashboard (`/portfolio/risk`) provides quantitative risk and tail analytics.

## Tabs
1. **Risk Metrics & Limits:** Daily VaR (95%), Expected Shortfall (CVaR), Beta, Volatility, and pre-trade constraint gates.
2. **Historical Stress Tests:** Simulates portfolio impact during real crises (e.g., 2008 Lehman Shock, 2020 COVID Crash).
3. **Monte Carlo Simulation:** Bootstrapped forward simulations (500 iterations) projecting 252-day terminal wealth and drawdown probabilities.
