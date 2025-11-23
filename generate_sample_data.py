"""
Generate realistic sample data for backtesting

This creates synthetic Fear & Greed Index and BTC price data
based on historical patterns for demonstration purposes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_btc_price_data(start_date, end_date, initial_price=10000):
    """
    Generate realistic BTC price data with trends and volatility

    Uses a geometric Brownian motion model with regime changes
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)

    # Parameters for geometric Brownian motion
    dt = 1  # daily
    mu = 0.002  # drift (upward trend on average)
    sigma = 0.04  # volatility

    # Generate price path
    prices = [initial_price]

    for i in range(1, n_days):
        # Add regime changes (bull/bear markets)
        if i % 365 == 0:  # Yearly regime changes
            mu = np.random.choice([0.003, -0.001, 0.002], p=[0.5, 0.2, 0.3])

        # Geometric Brownian motion
        shock = np.random.normal(mu * dt, sigma * np.sqrt(dt))
        price = prices[-1] * np.exp(shock)

        # Add occasional large moves (events)
        if np.random.random() < 0.05:  # 5% chance of event
            event_shock = np.random.normal(0, 0.15)
            price *= np.exp(event_shock)

        prices.append(max(price, 100))  # Floor price at $100

    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })

    return df


def generate_fng_data(btc_prices):
    """
    Generate Fear & Greed Index based on BTC price movements

    The index is negatively correlated with recent volatility and
    positively correlated with recent returns (with a lag)
    """
    df = btc_prices.copy()

    # Calculate returns and volatility
    df['returns'] = df['price'].pct_change()
    df['volatility'] = df['returns'].rolling(30).std()

    # Calculate 30-day return
    df['return_30d'] = df['price'].pct_change(30)

    # Base F&G calculation
    # High returns → greed, High volatility → fear
    fng_values = []

    for i in range(len(df)):
        if i < 30:
            # Initial values
            fng = np.random.randint(40, 60)
        else:
            ret_30d = df['return_30d'].iloc[i]
            vol = df['volatility'].iloc[i]

            # Base value around 50
            base = 50

            # Returns component (lag effect - people get greedy after rises)
            if pd.notna(ret_30d):
                ret_component = min(max(ret_30d * 100, -30), 30)
            else:
                ret_component = 0

            # Volatility component (high vol → fear)
            if pd.notna(vol):
                vol_component = -min(vol * 300, 25)
            else:
                vol_component = 0

            # Combine with some randomness
            fng = base + ret_component + vol_component + np.random.normal(0, 5)

            # Add momentum (F&G tends to persist)
            if len(fng_values) > 0:
                fng = 0.7 * fng + 0.3 * fng_values[-1]

            # Clamp to 0-100
            fng = max(0, min(100, fng))

        fng_values.append(int(fng))

    df['value'] = fng_values

    # Add classification
    def classify_fng(val):
        if val <= 24:
            return "Extreme Fear"
        elif val <= 44:
            return "Fear"
        elif val <= 55:
            return "Neutral"
        elif val <= 75:
            return "Greed"
        else:
            return "Extreme Greed"

    df['value_classification'] = df['value'].apply(classify_fng)

    return df[['date', 'value', 'value_classification']]


def create_merged_sample_data(start_date='2020-01-01', end_date='2024-11-22',
                               initial_price=7200):
    """
    Create complete merged dataset with BTC prices and F&G index
    """
    print("Generating sample BTC price data...")
    btc_prices = generate_btc_price_data(start_date, end_date, initial_price)

    print("Generating sample Fear & Greed Index data...")
    fng_data = generate_fng_data(btc_prices)

    # Merge
    df = pd.merge(fng_data, btc_prices, on='date', how='inner')
    df['date'] = df['date'].dt.date

    print(f"✓ Generated {len(df)} days of sample data")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  BTC price range: ${df['price'].min():.2f} to ${df['price'].max():.2f}")
    print(f"  F&G range: {df['value'].min()} to {df['value'].max()}")

    return df


def save_sample_data(df, filename='examples/sample_data/sample_market_data.csv'):
    """Save sample data to CSV"""
    from pathlib import Path
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"✓ Saved sample data to: {filename}")


if __name__ == "__main__":
    # Generate realistic sample data covering ~5 years
    df = create_merged_sample_data(
        start_date='2020-01-01',
        end_date='2024-11-22',
        initial_price=7200  # BTC price in early 2020
    )

    # Save to CSV
    save_sample_data(df)

    # Print sample
    print("\nFirst 10 rows:")
    print(df.head(10))

    print("\nLast 10 rows:")
    print(df.tail(10))

    print("\nFear & Greed distribution:")
    print(df['value_classification'].value_counts().sort_index())
