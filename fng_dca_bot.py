"""
Fear & Greed DCA Bot for Bitcoin

This bot implements a simple DCA strategy based on the Bitcoin Fear & Greed Index:
- Buy when Fear & Greed index is LOW (fear) - accumulate BTC
- Sell when Fear & Greed index is HIGH (greed) - take profits

Data sources:
- Fear & Greed: Alternative.me API (https://api.alternative.me/fng/)
- BTC Price: CoinGecko API (https://api.coingecko.com/api/v3/coins/bitcoin/market_chart)
"""

import requests
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')


# -----------------------------
# 1) Data fetchers
# -----------------------------

def fetch_fng(limit=0):
    """
    Fetch Bitcoin Fear & Greed index from Alternative.me

    Args:
        limit: Number of results (0 = all available history)

    Returns:
        DataFrame with columns: date, value, value_classification
    """
    url = "https://api.alternative.me/fng/"
    params = {"limit": limit, "format": "json"}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("Fetching Fear & Greed Index data...")
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    df = pd.DataFrame(payload["data"])
    df["value"] = df["value"].astype(int)
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s", utc=True)
    df["date"] = df["timestamp"].dt.date
    df = df.sort_values("date").reset_index(drop=True)

    print(f"✓ Fetched {len(df)} days of Fear & Greed data")
    return df[["date", "value", "value_classification"]]


def fetch_btc_daily_from_coingecko():
    """
    Fetch daily BTC/USD prices from CoinGecko.
    Note: May require API key for large requests on the free tier.

    Returns:
        DataFrame with columns: date, price
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": "max",
        "interval": "daily",
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    print("Fetching Bitcoin price data...")
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # data["prices"] is list of [timestamp_ms, price]
    prices = pd.DataFrame(data["prices"], columns=["ts_ms", "price"])
    prices["timestamp"] = pd.to_datetime(prices["ts_ms"], unit="ms", utc=True)
    prices["date"] = prices["timestamp"].dt.date
    prices = prices.sort_values("date").reset_index(drop=True)

    print(f"✓ Fetched {len(prices)} days of BTC price data")
    return prices[["date", "price"]]


# -----------------------------
# 2) Join data
# -----------------------------

def build_merged_df():
    """
    Fetch and merge Fear & Greed Index with BTC price data.

    Returns:
        DataFrame with columns: date, value (F&G), value_classification, price
    """
    fng = fetch_fng(limit=0)
    btc = fetch_btc_daily_from_coingecko()
    df = pd.merge(fng, btc, on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)

    print(f"✓ Merged dataset: {len(df)} days from {df['date'].min()} to {df['date'].max()}")
    return df


# -----------------------------
# 3) Strategy logic
# -----------------------------

@dataclass
class StrategyParams:
    """Configuration parameters for the Fear & Greed DCA strategy"""
    buy_thresh: int = 25           # <= this → DCA buy
    sell_thresh: int = 75          # >= this → sell all
    order_pct: float = 5.0         # % of equity per DCA buy
    initial_capital: float = 10_000.0
    fee_rate: float = 0.0005       # 0.05% per side (e.g., Binance maker fee)


def run_fng_dca_strategy(df: pd.DataFrame, p: StrategyParams) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute the Fear & Greed DCA strategy.

    Rules:
    - When F&G <= buy_thresh: buy order_pct% of current equity
    - When F&G >= sell_thresh: sell entire BTC position

    Args:
        df: DataFrame with columns [date, value (F&G), price]
        p: StrategyParams configuration

    Returns:
        Tuple of (equity_curve_df, trades_df)
    """
    cash = p.initial_capital
    btc = 0.0

    equity_curve = []
    trades = []

    for _, row in df.iterrows():
        date = row["date"]
        fng = row["value"]
        price = row["price"]

        # Current equity before trading
        equity = cash + btc * price

        # BUY: fear
        if fng <= p.buy_thresh:
            notional = equity * (p.order_pct / 100.0)
            if notional > 0:
                fee = notional * p.fee_rate
                usd_to_spend = notional - fee
                qty = usd_to_spend / price
                btc += qty
                cash -= notional
                trades.append({
                    "date": date,
                    "side": "BUY",
                    "fng": fng,
                    "price": price,
                    "qty": qty,
                    "notional": notional
                })

        # SELL: greed
        elif fng >= p.sell_thresh and btc > 0:
            notional = btc * price
            fee = notional * p.fee_rate
            usd_received = notional - fee
            trades.append({
                "date": date,
                "side": "SELL",
                "fng": fng,
                "price": price,
                "qty": btc,
                "notional": notional
            })
            cash += usd_received
            btc = 0.0

        # Track equity after trades
        equity = cash + btc * price
        equity_curve.append({
            "date": date,
            "equity": equity,
            "cash": cash,
            "btc": btc,
            "price": price,
            "fng": fng
        })

    eq_df = pd.DataFrame(equity_curve).set_index("date")
    trades_df = pd.DataFrame(trades)

    return eq_df, trades_df


# -----------------------------
# 4) Performance metrics
# -----------------------------

def calculate_performance_metrics(equity_curve: pd.DataFrame, initial_capital: float, risk_free_rate: float = 0.02):
    """
    Calculate comprehensive performance metrics for the strategy.

    Args:
        equity_curve: DataFrame with equity values indexed by date
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate (default 2%)

    Returns:
        Dictionary with performance metrics
    """
    equity = equity_curve["equity"]

    # Total return
    total_return = (equity.iloc[-1] - initial_capital) / initial_capital

    # CAGR (Compound Annual Growth Rate)
    days = (pd.to_datetime(equity.index[-1]) - pd.to_datetime(equity.index[0])).days
    years = days / 365.25
    cagr = (equity.iloc[-1] / initial_capital) ** (1 / years) - 1 if years > 0 else 0

    # Maximum Drawdown
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_drawdown = drawdown.min()

    # Daily returns
    daily_returns = equity.pct_change().dropna()

    # Volatility (annualized)
    volatility = daily_returns.std() * np.sqrt(365)

    # Sharpe Ratio (annualized)
    excess_return = cagr - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0

    # Sortino Ratio (annualized, only downside volatility)
    downside_returns = daily_returns[daily_returns < 0]
    downside_volatility = downside_returns.std() * np.sqrt(365)
    sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0

    # Win rate (percentage of positive days)
    win_rate = (daily_returns > 0).sum() / len(daily_returns) if len(daily_returns) > 0 else 0

    # Calmar Ratio (CAGR / abs(Max Drawdown))
    calmar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0

    return {
        "Total Return (%)": total_return * 100,
        "CAGR (%)": cagr * 100,
        "Max Drawdown (%)": max_drawdown * 100,
        "Volatility (%)": volatility * 100,
        "Sharpe Ratio": sharpe_ratio,
        "Sortino Ratio": sortino_ratio,
        "Calmar Ratio": calmar_ratio,
        "Win Rate (%)": win_rate * 100,
        "Final Equity ($)": equity.iloc[-1],
        "Trading Days": len(equity),
        "Years": years
    }


def print_performance_report(metrics: dict, trades: pd.DataFrame, params: StrategyParams):
    """Print a formatted performance report"""
    print("\n" + "="*60)
    print("PERFORMANCE REPORT")
    print("="*60)

    print("\nStrategy Parameters:")
    print(f"  Buy Threshold (Fear):    ≤ {params.buy_thresh}")
    print(f"  Sell Threshold (Greed):  ≥ {params.sell_thresh}")
    print(f"  Order Size:              {params.order_pct}% of equity")
    print(f"  Initial Capital:         ${params.initial_capital:,.2f}")
    print(f"  Fee Rate:                {params.fee_rate*100:.3f}%")

    print("\nReturns:")
    print(f"  Total Return:            {metrics['Total Return (%)']:>10.2f}%")
    print(f"  CAGR:                    {metrics['CAGR (%)']:>10.2f}%")
    print(f"  Final Equity:            ${metrics['Final Equity ($)']:>10,.2f}")

    print("\nRisk Metrics:")
    print(f"  Maximum Drawdown:        {metrics['Max Drawdown (%)']:>10.2f}%")
    print(f"  Volatility (annual):     {metrics['Volatility (%)']:>10.2f}%")

    print("\nRisk-Adjusted Returns:")
    print(f"  Sharpe Ratio:            {metrics['Sharpe Ratio']:>10.2f}")
    print(f"  Sortino Ratio:           {metrics['Sortino Ratio']:>10.2f}")
    print(f"  Calmar Ratio:            {metrics['Calmar Ratio']:>10.2f}")

    print("\nTrading Statistics:")
    print(f"  Total Trades:            {len(trades):>10}")
    print(f"  Buy Orders:              {len(trades[trades['side']=='BUY']):>10}")
    print(f"  Sell Orders:             {len(trades[trades['side']=='SELL']):>10}")
    print(f"  Win Rate (daily):        {metrics['Win Rate (%)']:>10.2f}%")

    print(f"\nBacktest Period:           {metrics['Years']:.2f} years ({metrics['Trading Days']} days)")
    print("="*60 + "\n")


# -----------------------------
# 5) Parameter optimization
# -----------------------------

def sweep_thresholds(df: pd.DataFrame, initial_capital: float = 10_000.0,
                     buy_range: list = None, sell_range: list = None,
                     order_pct: float = 5.0):
    """
    Sweep through different buy/sell threshold parameters to find optimal settings.

    Args:
        df: Market data DataFrame
        initial_capital: Starting capital
        buy_range: List of buy thresholds to test
        sell_range: List of sell thresholds to test
        order_pct: Order size as % of equity

    Returns:
        DataFrame with results sorted by final equity
    """
    if buy_range is None:
        buy_range = [15, 20, 25, 30, 35]
    if sell_range is None:
        sell_range = [65, 70, 75, 80, 85]

    print("\nRunning parameter optimization sweep...")
    print(f"Buy thresholds: {buy_range}")
    print(f"Sell thresholds: {sell_range}")

    results = []
    total_combos = len(buy_range) * len(sell_range)
    current = 0

    for buy in buy_range:
        for sell in sell_range:
            current += 1
            if buy >= sell:
                continue  # Skip invalid combinations

            p = StrategyParams(
                buy_thresh=buy,
                sell_thresh=sell,
                order_pct=order_pct,
                initial_capital=initial_capital
            )
            eq, trades = run_fng_dca_strategy(df, p)
            metrics = calculate_performance_metrics(eq, initial_capital)

            results.append({
                "buy_thresh": buy,
                "sell_thresh": sell,
                "final_equity": metrics["Final Equity ($)"],
                "total_return": metrics["Total Return (%)"],
                "cagr": metrics["CAGR (%)"],
                "max_dd": metrics["Max Drawdown (%)"],
                "sharpe": metrics["Sharpe Ratio"],
                "sortino": metrics["Sortino Ratio"],
                "num_trades": len(trades)
            })

            if current % 5 == 0:
                print(f"  Progress: {current}/{total_combos} combinations tested...")

    results_df = pd.DataFrame(results).sort_values("final_equity", ascending=False)
    print(f"✓ Optimization complete! Tested {len(results_df)} parameter combinations\n")

    return results_df


# -----------------------------
# 6) Main execution
# -----------------------------

def main():
    """Main execution function"""
    print("="*60)
    print("FEAR & GREED DCA BOT - BACKTEST")
    print("="*60)

    # Fetch data
    df = build_merged_df()

    # Define strategy parameters
    params = StrategyParams(
        buy_thresh=25,        # Buy when F&G ≤ 25 (fear/extreme fear)
        sell_thresh=75,       # Sell when F&G ≥ 75 (greed/extreme greed)
        order_pct=5.0,        # 5% of equity per buy
        initial_capital=10_000.0,
        fee_rate=0.0005,      # 0.05% (Binance maker fee)
    )

    # Run backtest
    print("\nRunning backtest...")
    equity_curve, trades = run_fng_dca_strategy(df, params)

    # Calculate metrics
    metrics = calculate_performance_metrics(equity_curve, params.initial_capital)

    # Calculate buy & hold comparison
    buy_hold_return = (df["price"].iloc[-1] / df["price"].iloc[0]) * params.initial_capital
    buy_hold_pct = ((buy_hold_return - params.initial_capital) / params.initial_capital) * 100

    # Print report
    print_performance_report(metrics, trades, params)

    print("Buy & Hold Comparison:")
    print(f"  Buy & Hold Return:       {buy_hold_pct:>10.2f}%")
    print(f"  Buy & Hold Final:        ${buy_hold_return:>10,.2f}")
    print(f"  Strategy vs B&H:         {metrics['Total Return (%)'] - buy_hold_pct:>10.2f}% {'✓' if metrics['Total Return (%)'] > buy_hold_pct else '✗'}")
    print()

    # Show sample trades
    if len(trades) > 0:
        print("Recent Trades (last 10):")
        print(trades.tail(10).to_string(index=False))
        print()

    # Run optimization (optional - comment out for faster execution)
    run_optimization = input("\nRun parameter optimization? (y/n): ").lower().strip() == 'y'

    if run_optimization:
        optimization_results = sweep_thresholds(
            df,
            initial_capital=params.initial_capital,
            buy_range=[15, 20, 25, 30, 35],
            sell_range=[65, 70, 75, 80, 85],
            order_pct=params.order_pct
        )

        print("Top 10 Parameter Combinations (by final equity):")
        print(optimization_results.head(10).to_string(index=False))
        print()

        print("Top 10 Parameter Combinations (by Sharpe ratio):")
        print(optimization_results.sort_values("sharpe", ascending=False).head(10).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
