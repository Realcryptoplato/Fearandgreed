"""
Comprehensive backtest runner with visualizations and CSV exports

This script runs multiple strategy scenarios, generates detailed charts,
and exports results to CSV files.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import seaborn as sns
from pathlib import Path

from fng_dca_bot import (
    build_merged_df,
    run_fng_dca_strategy,
    calculate_performance_metrics,
    StrategyParams
)
from config import CONSERVATIVE, MODERATE, AGGRESSIVE, EXTREME

# Set up plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# Create output directories
OUTPUT_DIR = Path("examples/output_charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_nav_chart_with_trades(equity_curve, trades, params, strategy_name, output_file):
    """
    Create a NAV chart with buy/sell trade overlays

    Args:
        equity_curve: DataFrame with equity values
        trades: DataFrame with trade history
        params: StrategyParams used
        strategy_name: Name of the strategy
        output_file: Path to save the chart
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), height_ratios=[3, 1, 1])

    # Convert index to datetime for plotting
    dates = pd.to_datetime(equity_curve.index)

    # Plot 1: NAV with trades
    ax1.plot(dates, equity_curve['equity'], label='Strategy Equity', color='#2E86AB', linewidth=2)
    ax1.axhline(y=params.initial_capital, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')

    # Overlay buy/sell trades
    if len(trades) > 0:
        buy_trades = trades[trades['side'] == 'BUY']
        sell_trades = trades[trades['side'] == 'SELL']

        for _, trade in buy_trades.iterrows():
            trade_date = pd.to_datetime(trade['date'])
            # Find the equity value at this date
            if trade_date in equity_curve.index:
                equity_val = equity_curve.loc[trade_date, 'equity']
                ax1.scatter(trade_date, equity_val, color='green', s=100, marker='^',
                           alpha=0.7, zorder=5, edgecolors='darkgreen', linewidth=1.5)

        for _, trade in sell_trades.iterrows():
            trade_date = pd.to_datetime(trade['date'])
            if trade_date in equity_curve.index:
                equity_val = equity_curve.loc[trade_date, 'equity']
                ax1.scatter(trade_date, equity_val, color='red', s=100, marker='v',
                           alpha=0.7, zorder=5, edgecolors='darkred', linewidth=1.5)

    # Format
    ax1.set_ylabel('Portfolio Value ($)', fontsize=12, fontweight='bold')
    ax1.set_title(f'{strategy_name} - Net Asset Value with Trade Signals', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Plot 2: Fear & Greed Index with buy/sell thresholds
    ax2.plot(dates, equity_curve['fng'], color='purple', linewidth=1.5, label='Fear & Greed Index')
    ax2.axhline(y=params.buy_thresh, color='green', linestyle='--', alpha=0.7,
                label=f'Buy Threshold ({params.buy_thresh})')
    ax2.axhline(y=params.sell_thresh, color='red', linestyle='--', alpha=0.7,
                label=f'Sell Threshold ({params.sell_thresh})')
    ax2.fill_between(dates, 0, params.buy_thresh, alpha=0.1, color='green', label='Buy Zone')
    ax2.fill_between(dates, params.sell_thresh, 100, alpha=0.1, color='red', label='Sell Zone')

    ax2.set_ylabel('F&G Index', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)

    # Plot 3: BTC Holdings
    ax3.fill_between(dates, equity_curve['btc'], alpha=0.3, color='orange', label='BTC Holdings')
    ax3.plot(dates, equity_curve['btc'], color='orange', linewidth=1.5)
    ax3.set_ylabel('BTC Amount', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)

    # Format x-axis for all subplots
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved NAV chart: {output_file}")
    plt.close()


def create_drawdown_chart(equity_curve, strategy_name, output_file):
    """Create a drawdown chart"""
    fig, ax = plt.subplots(figsize=(16, 6))

    dates = pd.to_datetime(equity_curve.index)
    equity = equity_curve['equity']

    # Calculate drawdown
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax * 100

    ax.fill_between(dates, drawdown, 0, alpha=0.3, color='red', label='Drawdown')
    ax.plot(dates, drawdown, color='darkred', linewidth=1.5)

    ax.set_ylabel('Drawdown (%)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_title(f'{strategy_name} - Drawdown Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Add max drawdown line
    max_dd = drawdown.min()
    ax.axhline(y=max_dd, color='red', linestyle='--', alpha=0.5,
               label=f'Max Drawdown: {max_dd:.2f}%')
    ax.legend(loc='lower left')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved drawdown chart: {output_file}")
    plt.close()


def create_returns_distribution(equity_curve, strategy_name, output_file):
    """Create returns distribution histogram"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Calculate daily returns
    daily_returns = equity_curve['equity'].pct_change().dropna() * 100

    # Histogram
    ax1.hist(daily_returns, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.axvline(daily_returns.mean(), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {daily_returns.mean():.3f}%')
    ax1.axvline(daily_returns.median(), color='green', linestyle='--', linewidth=2,
                label=f'Median: {daily_returns.median():.3f}%')
    ax1.set_xlabel('Daily Return (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax1.set_title(f'{strategy_name} - Daily Returns Distribution', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Cumulative returns
    cumulative_returns = (1 + equity_curve['equity'].pct_change()).cumprod() - 1
    dates = pd.to_datetime(equity_curve.index)
    ax2.plot(dates, cumulative_returns * 100, color='steelblue', linewidth=2)
    ax2.fill_between(dates, 0, cumulative_returns * 100, alpha=0.3, color='steelblue')
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Return (%)', fontsize=12, fontweight='bold')
    ax2.set_title(f'{strategy_name} - Cumulative Returns', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved returns distribution: {output_file}")
    plt.close()


def create_strategy_comparison_chart(all_results, output_file):
    """Create comparison chart for all strategies"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    strategies = list(all_results.keys())

    # 1. Total Returns
    returns = [all_results[s]['metrics']['Total Return (%)'] for s in strategies]
    colors = ['green' if r > 0 else 'red' for r in returns]
    ax1.bar(strategies, returns, color=colors, alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Total Return (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Total Returns Comparison', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(returns):
        ax1.text(i, v + (5 if v > 0 else -5), f'{v:.1f}%', ha='center', fontweight='bold')

    # 2. Risk-Adjusted Returns (Sharpe & Sortino)
    x = np.arange(len(strategies))
    width = 0.35
    sharpe = [all_results[s]['metrics']['Sharpe Ratio'] for s in strategies]
    sortino = [all_results[s]['metrics']['Sortino Ratio'] for s in strategies]

    ax2.bar(x - width/2, sharpe, width, label='Sharpe Ratio', alpha=0.7, color='steelblue', edgecolor='black')
    ax2.bar(x + width/2, sortino, width, label='Sortino Ratio', alpha=0.7, color='orange', edgecolor='black')
    ax2.set_ylabel('Ratio', fontsize=12, fontweight='bold')
    ax2.set_title('Risk-Adjusted Returns', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(strategies)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')

    # 3. Maximum Drawdown
    max_dd = [all_results[s]['metrics']['Max Drawdown (%)'] for s in strategies]
    ax3.bar(strategies, max_dd, color='red', alpha=0.7, edgecolor='black')
    ax3.set_ylabel('Max Drawdown (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Maximum Drawdown Comparison', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(max_dd):
        ax3.text(i, v - 2, f'{v:.1f}%', ha='center', fontweight='bold')

    # 4. Number of Trades
    num_trades = [len(all_results[s]['trades']) for s in strategies]
    ax4.bar(strategies, num_trades, color='purple', alpha=0.7, edgecolor='black')
    ax4.set_ylabel('Number of Trades', fontsize=12, fontweight='bold')
    ax4.set_title('Trading Activity', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(num_trades):
        ax4.text(i, v + 1, str(v), ha='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved strategy comparison: {output_file}")
    plt.close()


def export_to_csv(equity_curve, trades, metrics, strategy_name):
    """Export results to CSV files"""
    # Export equity curve
    equity_file = OUTPUT_DIR / f"{strategy_name}_equity_curve.csv"
    equity_export = equity_curve.copy()
    equity_export.index.name = 'date'
    equity_export.to_csv(equity_file)
    print(f"✓ Exported equity curve: {equity_file}")

    # Export trades
    trades_file = OUTPUT_DIR / f"{strategy_name}_trades.csv"
    trades.to_csv(trades_file, index=False)
    print(f"✓ Exported trades: {trades_file}")

    # Export metrics
    metrics_file = OUTPUT_DIR / f"{strategy_name}_metrics.csv"
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(metrics_file, index=False)
    print(f"✓ Exported metrics: {metrics_file}")


def run_scenario(df, config, strategy_name):
    """Run a single scenario and return all results"""
    print(f"\n{'='*60}")
    print(f"Running: {strategy_name}")
    print(f"{'='*60}")

    # Convert config to StrategyParams
    params = StrategyParams(
        buy_thresh=config.buy_threshold,
        sell_thresh=config.sell_threshold,
        order_pct=config.order_size_pct,
        initial_capital=config.initial_capital,
        fee_rate=config.fee_rate
    )

    # Run backtest
    equity_curve, trades = run_fng_dca_strategy(df, params)
    metrics = calculate_performance_metrics(equity_curve, params.initial_capital)

    # Print summary
    print(f"\nResults:")
    print(f"  Total Return:     {metrics['Total Return (%)']:>10.2f}%")
    print(f"  CAGR:             {metrics['CAGR (%)']:>10.2f}%")
    print(f"  Max Drawdown:     {metrics['Max Drawdown (%)']:>10.2f}%")
    print(f"  Sharpe Ratio:     {metrics['Sharpe Ratio']:>10.2f}")
    print(f"  Sortino Ratio:    {metrics['Sortino Ratio']:>10.2f}")
    print(f"  Total Trades:     {len(trades):>10}")
    print(f"  Final Equity:     ${metrics['Final Equity ($)']:>10,.2f}")

    return {
        'params': params,
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics
    }


def main():
    """Main execution"""
    print("="*60)
    print("COMPREHENSIVE BACKTEST WITH VISUALIZATIONS")
    print("="*60)

    # Load data (use sample data if API fails)
    print("\nLoading market data...")
    try:
        df = build_merged_df()
    except Exception as e:
        print(f"⚠ API fetch failed ({str(e)})")
        print("📁 Loading sample data from CSV...")
        df = pd.read_csv('examples/sample_data/sample_market_data.csv')
        df['date'] = pd.to_datetime(df['date']).dt.date
        print(f"✓ Loaded {len(df)} days of sample data")

    # Calculate Buy & Hold for comparison
    buy_hold_return_pct = ((df['price'].iloc[-1] / df['price'].iloc[0]) - 1) * 100
    buy_hold_final = (df['price'].iloc[-1] / df['price'].iloc[0]) * 10_000

    print(f"\n📊 Buy & Hold Benchmark:")
    print(f"  Total Return:     {buy_hold_return_pct:>10.2f}%")
    print(f"  Final Value:      ${buy_hold_final:>10,.2f}")

    # Define scenarios to test
    scenarios = {
        'Conservative': CONSERVATIVE,
        'Moderate': MODERATE,
        'Aggressive': AGGRESSIVE,
        'Extreme': EXTREME,
    }

    # Run all scenarios
    all_results = {}
    for name, config in scenarios.items():
        results = run_scenario(df, config, name)
        all_results[name] = results

        # Export to CSV
        export_to_csv(
            results['equity_curve'],
            results['trades'],
            results['metrics'],
            name
        )

        # Create individual charts
        create_nav_chart_with_trades(
            results['equity_curve'],
            results['trades'],
            results['params'],
            name,
            OUTPUT_DIR / f"{name}_nav_with_trades.png"
        )

        create_drawdown_chart(
            results['equity_curve'],
            name,
            OUTPUT_DIR / f"{name}_drawdown.png"
        )

        create_returns_distribution(
            results['equity_curve'],
            name,
            OUTPUT_DIR / f"{name}_returns.png"
        )

    # Create comparison chart
    create_strategy_comparison_chart(
        all_results,
        OUTPUT_DIR / "strategy_comparison.png"
    )

    # Create summary comparison table
    summary_data = []
    for name, results in all_results.items():
        metrics = results['metrics']
        params = results['params']
        summary_data.append({
            'Strategy': name,
            'Buy Threshold': params.buy_thresh,
            'Sell Threshold': params.sell_thresh,
            'Order Size %': params.order_pct,
            'Total Return %': metrics['Total Return (%)'],
            'CAGR %': metrics['CAGR (%)'],
            'Max Drawdown %': metrics['Max Drawdown (%)'],
            'Sharpe Ratio': metrics['Sharpe Ratio'],
            'Sortino Ratio': metrics['Sortino Ratio'],
            'Calmar Ratio': metrics['Calmar Ratio'],
            'Volatility %': metrics['Volatility (%)'],
            'Win Rate %': metrics['Win Rate (%)'],
            'Total Trades': len(results['trades']),
            'Final Equity $': metrics['Final Equity ($)'],
            'vs Buy&Hold %': metrics['Total Return (%)'] - buy_hold_return_pct
        })

    summary_df = pd.DataFrame(summary_data)
    summary_file = OUTPUT_DIR / "strategy_summary.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"\n✓ Exported summary comparison: {summary_file}")

    # Print summary table
    print("\n" + "="*60)
    print("STRATEGY SUMMARY")
    print("="*60)
    print(summary_df.to_string(index=False))

    print("\n" + "="*60)
    print(f"✓ All results saved to: {OUTPUT_DIR.absolute()}")
    print("="*60)

    print("\nFiles generated:")
    for file in sorted(OUTPUT_DIR.glob("*")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
