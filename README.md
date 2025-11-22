# Fear & Greed DCA Bot 🤖

A Python-based Dollar Cost Averaging (DCA) trading bot for Bitcoin that uses the **Bitcoin Fear & Greed Index** to make intelligent buy and sell decisions.

## 📊 Strategy Overview

The bot implements a contrarian strategy based on market sentiment:

- **Buy when FEAR is high** (F&G Index ≤ 25): DCA into BTC when others are fearful
- **Sell when GREED is high** (F&G Index ≥ 75): Take profits when others are greedy

### Fear & Greed Index Scale

```
0-24   │ Extreme Fear    │ 🟥 Strong Buy Signal
25-44  │ Fear            │ 🟨 Buy Signal
45-55  │ Neutral         │ ⬜ Hold
56-75  │ Greed           │ 🟨 Consider Selling
76-100 │ Extreme Greed   │ 🟥 Strong Sell Signal
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd Fearandgreed

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

Run the backtest with default parameters:

```bash
python fng_dca_bot.py
```

This will:
1. Fetch historical Fear & Greed Index data
2. Fetch Bitcoin price history
3. Run the backtest with default parameters
4. Display comprehensive performance metrics
5. Compare results to Buy & Hold strategy

### Custom Configuration

Use predefined strategy profiles:

```python
from fng_dca_bot import run_fng_dca_strategy, build_merged_df, calculate_performance_metrics
from config import CONSERVATIVE, MODERATE, AGGRESSIVE, EXTREME

# Fetch data
df = build_merged_df()

# Choose a strategy
from config import AGGRESSIVE
params = AGGRESSIVE

# Run backtest
equity_curve, trades = run_fng_dca_strategy(df, params)
metrics = calculate_performance_metrics(equity_curve, params.initial_capital)
```

Or create your own configuration:

```python
from config import BotConfig

custom_config = BotConfig(
    buy_threshold=20,       # Buy when F&G ≤ 20
    sell_threshold=80,      # Sell when F&G ≥ 80
    order_size_pct=5.0,     # 5% of equity per buy
    initial_capital=10000,
    fee_rate=0.0005         # 0.05% trading fee
)

# Validate configuration
custom_config.validate()
```

## 📈 Performance Metrics

The bot calculates comprehensive performance statistics:

### Returns
- **Total Return**: Overall percentage gain/loss
- **CAGR** (Compound Annual Growth Rate): Annualized return
- **Final Equity**: Ending portfolio value

### Risk Metrics
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Volatility**: Annualized standard deviation of returns

### Risk-Adjusted Returns
- **Sharpe Ratio**: Return per unit of volatility
- **Sortino Ratio**: Return per unit of downside volatility (better for asymmetric strategies)
- **Calmar Ratio**: CAGR divided by maximum drawdown

### Trading Statistics
- **Total Trades**: Number of buy + sell orders
- **Win Rate**: Percentage of profitable days

## 🔧 Parameter Optimization

Run a parameter sweep to find optimal buy/sell thresholds:

```python
from fng_dca_bot import sweep_thresholds, build_merged_df

df = build_merged_df()

results = sweep_thresholds(
    df,
    initial_capital=10_000,
    buy_range=[15, 20, 25, 30, 35],
    sell_range=[65, 70, 75, 80, 85],
    order_pct=5.0
)

# View top performers
print(results.head(10))
```

This tests all combinations and ranks them by:
- Final equity
- Total return
- CAGR
- Sharpe ratio
- Sortino ratio

## 📡 Data Sources

### Fear & Greed Index
- **Provider**: Alternative.me
- **Endpoint**: `https://api.alternative.me/fng/`
- **Documentation**: [alternative.me/crypto/fear-and-greed-index](https://alternative.me/crypto/fear-and-greed-index/)
- **Rate Limits**: Free, no API key required
- **History**: ~3 years of daily data

### Bitcoin Price Data
- **Provider**: CoinGecko
- **Endpoint**: `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart`
- **Rate Limits**: Free tier may require API key for large requests
- **Alternative**: Can be replaced with Binance, Kraken, or any other price feed

## 📁 Project Structure

```
Fearandgreed/
│
├── fng_dca_bot.py      # Main bot implementation
├── config.py           # Configuration and strategy presets
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── examples/          # Example scripts (coming soon)
```

## ⚙️ Configuration Options

### Strategy Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `buy_threshold` | F&G index level to trigger buys | 25 | 0-100 |
| `sell_threshold` | F&G index level to trigger sells | 75 | 0-100 |
| `order_size_pct` | % of equity per buy order | 5.0 | 0-100 |
| `initial_capital` | Starting capital in USD | 10,000 | > 0 |
| `fee_rate` | Trading fee per side | 0.0005 | 0-0.1 |

### Predefined Strategies

**CONSERVATIVE** (Lower risk, frequent trading)
- Buy: ≤ 30, Sell: ≥ 70, Order: 3%

**MODERATE** (Balanced approach)
- Buy: ≤ 25, Sell: ≥ 75, Order: 5%

**AGGRESSIVE** (Higher risk, less frequent trading)
- Buy: ≤ 20, Sell: ≥ 80, Order: 7%

**EXTREME** (Very high risk, rare trades)
- Buy: ≤ 15, Sell: ≥ 85, Order: 10%

## 🎯 Use Cases

### 1. Backtesting
Test historical performance of different Fear & Greed thresholds to validate the strategy.

### 2. Parameter Optimization
Find the optimal buy/sell levels for your risk tolerance and capital.

### 3. Live Trading (Manual)
Use the signals to inform manual trading decisions on your exchange.

### 4. Automated Trading (Advanced)
Integrate with exchange APIs (Binance, Coinbase, etc.) to automate execution.

## ⚠️ Disclaimer

**This bot is for educational and research purposes only.**

- Past performance does not guarantee future results
- Cryptocurrency trading carries significant risk
- Never invest more than you can afford to lose
- Always do your own research (DYOR)
- Test thoroughly before using real capital
- Not financial advice

## 🛠️ Future Enhancements

Potential improvements:

- [ ] Real-time trading integration (Binance, Coinbase, Kraken)
- [ ] Web dashboard for monitoring
- [ ] Email/SMS alerts for signals
- [ ] Support for multiple cryptocurrencies
- [ ] Machine learning optimization
- [ ] Paper trading mode
- [ ] Portfolio rebalancing features
- [ ] Multi-timeframe analysis
- [ ] Advanced risk management (stop-loss, take-profit)

## 📚 Resources

- [Alternative.me Fear & Greed Index](https://alternative.me/crypto/fear-and-greed-index/)
- [Bitcoin Dollar Cost Averaging Guide](https://dcabtc.com/)
- [Investopedia: Dollar-Cost Averaging](https://www.investopedia.com/terms/d/dollarcostaveraging.asp)
- [Understanding the Sharpe Ratio](https://www.investopedia.com/terms/s/sharperatio.asp)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

---

**Happy Trading! 📈💰**

Remember: Buy fear, sell greed! 🧠
