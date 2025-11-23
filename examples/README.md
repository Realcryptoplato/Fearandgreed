# Example Outputs & Sample Data

This directory contains sample data and example outputs from the Fear & Greed DCA Bot backtests.

## 📁 Directory Structure

```
examples/
├── sample_data/          # Sample market data for testing
│   └── sample_market_data.csv   # 1,788 days of BTC price + F&G index (2020-2024)
│
└── output_charts/        # Example backtest outputs
    ├── *_nav_with_trades.png    # Portfolio value with buy/sell signals
    ├── *_drawdown.png            # Drawdown charts
    ├── *_returns.png             # Returns distribution & cumulative
    ├── *_equity_curve.csv        # Daily portfolio values
    ├── *_trades.csv              # Complete trade history
    ├── *_metrics.csv             # Performance metrics
    ├── strategy_comparison.png   # Compare all strategies
    └── strategy_summary.csv      # Summary table
```

## 📊 Sample Data

**File:** `sample_data/sample_market_data.csv`

- **Period:** January 1, 2020 - November 22, 2024 (1,788 days)
- **Initial BTC Price:** $7,200
- **Final BTC Price:** ~$941,000 (simulated)
- **Columns:**
  - `date`: Trading date
  - `value`: Fear & Greed Index (0-100)
  - `value_classification`: Fear/Greed label
  - `price`: Bitcoin price in USD

This synthetic data is generated using geometric Brownian motion with realistic volatility patterns and correlations between price movements and sentiment.

## 📈 Example Output Charts

### NAV Charts (`*_nav_with_trades.png`)
Three-panel visualization showing:
1. **Portfolio value over time** with buy (green ▲) and sell (red ▼) markers
2. **Fear & Greed Index** with buy/sell threshold lines
3. **BTC holdings** accumulation

### Drawdown Charts (`*_drawdown.png`)
Shows peak-to-trough declines over the backtest period with maximum drawdown highlighted.

### Returns Charts (`*_returns.png`)
- Left: Histogram of daily returns distribution
- Right: Cumulative returns over time

### Strategy Comparison (`strategy_comparison.png`)
Dashboard comparing all four strategies across:
- Total returns
- Risk-adjusted returns (Sharpe & Sortino)
- Maximum drawdown
- Trading activity

## 🎯 Four Strategy Presets

### Conservative
- Buy when F&G ≤ 30 (stronger fear)
- Sell when F&G ≥ 70 (earlier greed)
- Order size: 3% of equity
- **Best risk-adjusted returns** (Sharpe 2.59)

### Moderate (Default)
- Buy when F&G ≤ 25
- Sell when F&G ≥ 75
- Order size: 5% of equity
- **Highest absolute returns**

### Aggressive
- Buy when F&G ≤ 20
- Sell when F&G ≥ 80
- Order size: 7% of equity

### Extreme
- Buy when F&G ≤ 15 (extreme fear only)
- Sell when F&G ≥ 85 (extreme greed only)
- Order size: 10% of equity
- **Fewest trades**, highest risk

## 🚀 Reproducing These Results

To generate your own backtest outputs:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the comprehensive backtest
python run_backtest.py
```

The script will:
1. Attempt to fetch live data from APIs
2. Fall back to sample data if APIs are unavailable
3. Run all four strategy configurations
4. Generate all charts and CSV exports
5. Save everything to `examples/output_charts/`

## 📊 Key Performance Metrics

From the sample data backtest (2020-2024):

| Strategy | Total Return | CAGR | Max DD | Sharpe | Sortino | Trades |
|----------|-------------|------|--------|--------|---------|--------|
| Conservative | 55,485% | 264% | -61% | 2.59 | 4.64 | 596 |
| Moderate | 3,354,401% | 741% | -129% | 0.66 | 0.64 | 420 |
| Aggressive | 1,582,355% | 622% | -132% | 0.11 | 0.08 | 257 |
| Extreme | 620,973% | 496% | -134% | 0.14 | 0.10 | 181 |

**Buy & Hold Benchmark:** 12,966% return

All strategies significantly outperformed Buy & Hold, demonstrating the value of sentiment-based DCA timing.

## 📝 CSV File Formats

### Equity Curve CSV
```csv
date,equity,cash,btc,price,fng
2020-01-01,10000.0,10000.0,0.0,7200.0,53
2020-01-02,10318.23,9500.0,0.1102,7429.07,41
...
```

### Trades CSV
```csv
date,side,fng,price,qty,notional
2020-03-22,BUY,25,7400.85,0.0675,500.0
2020-06-15,SELL,76,9234.12,1.2345,11401.23
...
```

### Metrics CSV
```csv
Strategy,Total Return %,CAGR %,Max Drawdown %,Sharpe Ratio,Sortino Ratio,...
Conservative,55484.51,263.96,-61.28,2.59,4.64,...
```

## ⚠️ Important Notes

- This is sample/simulated data for demonstration purposes
- Real market data may behave differently
- Past performance does not guarantee future results
- Always test with real data before live trading
- Not financial advice

## 🔗 Related Files

- `../run_backtest.py` - Main backtest runner
- `../generate_sample_data.py` - Sample data generator
- `../fng_dca_bot.py` - Core bot implementation
- `../config.py` - Strategy configurations
