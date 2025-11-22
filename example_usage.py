"""
Example usage scripts for the Fear & Greed DCA Bot

This file demonstrates various ways to use the bot with different configurations.
"""

from fng_dca_bot import (
    build_merged_df,
    run_fng_dca_strategy,
    calculate_performance_metrics,
    print_performance_report,
    sweep_thresholds,
    StrategyParams
)
from config import CONSERVATIVE, MODERATE, AGGRESSIVE, EXTREME, BotConfig


def example_1_basic_backtest():
    """Example 1: Run a simple backtest with default parameters"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Backtest")
    print("="*60)

    # Fetch data
    df = build_merged_df()

    # Create strategy parameters
    params = StrategyParams(
        buy_thresh=25,
        sell_thresh=75,
        order_pct=5.0,
        initial_capital=10_000.0,
        fee_rate=0.0005
    )

    # Run backtest
    equity_curve, trades = run_fng_dca_strategy(df, params)

    # Calculate and display metrics
    metrics = calculate_performance_metrics(equity_curve, params.initial_capital)
    print_performance_report(metrics, trades, params)


def example_2_compare_strategies():
    """Example 2: Compare multiple predefined strategies"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Strategy Comparison")
    print("="*60)

    # Fetch data once
    df = build_merged_df()

    strategies = {
        "Conservative": CONSERVATIVE,
        "Moderate": MODERATE,
        "Aggressive": AGGRESSIVE,
        "Extreme": EXTREME
    }

    results = []

    for name, config in strategies.items():
        # Convert BotConfig to StrategyParams
        params = StrategyParams(
            buy_thresh=config.buy_threshold,
            sell_thresh=config.sell_threshold,
            order_pct=config.order_size_pct,
            initial_capital=config.initial_capital,
            fee_rate=config.fee_rate
        )

        equity_curve, trades = run_fng_dca_strategy(df, params)
        metrics = calculate_performance_metrics(equity_curve, params.initial_capital)

        results.append({
            "Strategy": name,
            "Buy ≤": params.buy_thresh,
            "Sell ≥": params.sell_thresh,
            "Order %": params.order_pct,
            "Total Return %": metrics["Total Return (%)"],
            "CAGR %": metrics["CAGR (%)"],
            "Max DD %": metrics["Max Drawdown (%)"],
            "Sharpe": metrics["Sharpe Ratio"],
            "Sortino": metrics["Sortino Ratio"],
            "Trades": len(trades),
            "Final $": metrics["Final Equity ($)"]
        })

    # Display comparison table
    import pandas as pd
    results_df = pd.DataFrame(results)
    print("\nStrategy Comparison:")
    print(results_df.to_string(index=False))
    print()

    # Highlight best performers
    best_return = results_df.loc[results_df["Total Return %"].idxmax(), "Strategy"]
    best_sharpe = results_df.loc[results_df["Sharpe"].idxmax(), "Strategy"]
    best_sortino = results_df.loc[results_df["Sortino"].idxmax(), "Strategy"]

    print(f"Best Total Return:  {best_return}")
    print(f"Best Sharpe Ratio:  {best_sharpe}")
    print(f"Best Sortino Ratio: {best_sortino}")
    print()


def example_3_custom_strategy():
    """Example 3: Create and test a custom strategy"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Strategy")
    print("="*60)

    # Fetch data
    df = build_merged_df()

    # Create a custom strategy
    # Strategy: Only buy on extreme fear, only sell on extreme greed, large positions
    custom = StrategyParams(
        buy_thresh=15,        # Only extreme fear
        sell_thresh=85,       # Only extreme greed
        order_pct=8.0,        # 8% per order
        initial_capital=10_000.0,
        fee_rate=0.0005
    )

    print("\nCustom Strategy: 'Extreme Contrarian'")
    print(f"  Buy only when F&G ≤ {custom.buy_thresh} (extreme fear)")
    print(f"  Sell only when F&G ≥ {custom.sell_thresh} (extreme greed)")
    print(f"  Position size: {custom.order_pct}% of equity")

    # Run backtest
    equity_curve, trades = run_fng_dca_strategy(df, custom)

    # Calculate metrics
    metrics = calculate_performance_metrics(equity_curve, custom.initial_capital)

    # Display report
    print_performance_report(metrics, trades, custom)


def example_4_optimization():
    """Example 4: Find optimal parameters"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Parameter Optimization")
    print("="*60)

    # Fetch data
    df = build_merged_df()

    # Run optimization sweep
    results = sweep_thresholds(
        df,
        initial_capital=10_000.0,
        buy_range=[10, 15, 20, 25, 30, 35],
        sell_range=[65, 70, 75, 80, 85, 90],
        order_pct=5.0
    )

    # Display top results by different metrics
    print("\n📊 Top 5 by Final Equity:")
    print(results.head(5).to_string(index=False))

    print("\n📊 Top 5 by Sharpe Ratio:")
    print(results.sort_values("sharpe", ascending=False).head(5).to_string(index=False))

    print("\n📊 Top 5 by Sortino Ratio:")
    print(results.sort_values("sortino", ascending=False).head(5).to_string(index=False))

    print("\n📊 Top 5 by CAGR:")
    print(results.sort_values("cagr", ascending=False).head(5).to_string(index=False))


def example_5_risk_analysis():
    """Example 5: Detailed risk analysis of a strategy"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Risk Analysis")
    print("="*60)

    # Fetch data
    df = build_merged_df()

    # Test strategy
    params = MODERATE

    strategy_params = StrategyParams(
        buy_thresh=params.buy_threshold,
        sell_thresh=params.sell_threshold,
        order_pct=params.order_size_pct,
        initial_capital=params.initial_capital,
        fee_rate=params.fee_rate
    )

    equity_curve, trades = run_fng_dca_strategy(df, strategy_params)

    # Calculate drawdown series
    import pandas as pd
    import numpy as np

    equity = equity_curve["equity"]
    cummax = equity.cummax()
    drawdown_series = (equity - cummax) / cummax * 100

    # Drawdown analysis
    print("\n📉 Drawdown Analysis:")
    print(f"  Maximum Drawdown:     {drawdown_series.min():.2f}%")
    print(f"  Average Drawdown:     {drawdown_series[drawdown_series < 0].mean():.2f}%")

    # Find longest drawdown period
    in_drawdown = drawdown_series < 0
    drawdown_periods = []
    start = None

    for i, (date, is_dd) in enumerate(in_drawdown.items()):
        if is_dd and start is None:
            start = date
        elif not is_dd and start is not None:
            drawdown_periods.append((start, date))
            start = None

    if drawdown_periods:
        longest_dd = max(drawdown_periods, key=lambda x: (pd.to_datetime(x[1]) - pd.to_datetime(x[0])).days)
        longest_days = (pd.to_datetime(longest_dd[1]) - pd.to_datetime(longest_dd[0])).days
        print(f"  Longest Drawdown:     {longest_days} days")
        print(f"    From {longest_dd[0]} to {longest_dd[1]}")

    # Return distribution
    daily_returns = equity.pct_change().dropna() * 100

    print("\n📊 Return Distribution:")
    print(f"  Mean Daily Return:    {daily_returns.mean():.3f}%")
    print(f"  Median Daily Return:  {daily_returns.median():.3f}%")
    print(f"  Std Dev:              {daily_returns.std():.3f}%")
    print(f"  Skewness:             {daily_returns.skew():.3f}")
    print(f"  Kurtosis:             {daily_returns.kurtosis():.3f}")

    print("\n📈 Return Percentiles:")
    print(f"  5th percentile:       {daily_returns.quantile(0.05):.3f}%")
    print(f"  25th percentile:      {daily_returns.quantile(0.25):.3f}%")
    print(f"  75th percentile:      {daily_returns.quantile(0.75):.3f}%")
    print(f"  95th percentile:      {daily_returns.quantile(0.95):.3f}%")

    # Positive vs negative days
    positive_days = (daily_returns > 0).sum()
    negative_days = (daily_returns < 0).sum()
    neutral_days = (daily_returns == 0).sum()

    print("\n📅 Trading Days Breakdown:")
    print(f"  Positive days:        {positive_days} ({positive_days/len(daily_returns)*100:.1f}%)")
    print(f"  Negative days:        {negative_days} ({negative_days/len(daily_returns)*100:.1f}%)")
    print(f"  Neutral days:         {neutral_days} ({neutral_days/len(daily_returns)*100:.1f}%)")


def main():
    """Run all examples"""
    import sys

    print("\n" + "="*60)
    print("FEAR & GREED DCA BOT - EXAMPLES")
    print("="*60)
    print("\nSelect an example to run:")
    print("  1 - Basic Backtest")
    print("  2 - Compare Strategies")
    print("  3 - Custom Strategy")
    print("  4 - Parameter Optimization")
    print("  5 - Risk Analysis")
    print("  0 - Run all examples")
    print()

    choice = input("Enter choice (0-5): ").strip()

    if choice == "1":
        example_1_basic_backtest()
    elif choice == "2":
        example_2_compare_strategies()
    elif choice == "3":
        example_3_custom_strategy()
    elif choice == "4":
        example_4_optimization()
    elif choice == "5":
        example_5_risk_analysis()
    elif choice == "0":
        example_1_basic_backtest()
        example_2_compare_strategies()
        example_3_custom_strategy()
        example_4_optimization()
        example_5_risk_analysis()
    else:
        print("Invalid choice!")
        sys.exit(1)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
