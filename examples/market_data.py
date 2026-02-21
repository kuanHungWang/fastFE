# DISCLAIMER: This module provides MOCK/SYNTHETIC market data generated programmatically
# for testing and demonstration purposes only. All rates, prices, and volatilities are
# fictional and do NOT represent real market data. Do NOT use for actual trading or
# financial decision-making.

import pandas as pd
import numpy as np
from typing import List
import QuantLib as ql

def get_deposit(currency:str,tenor:List[str]) -> pd.DataFrame:
    """
    Get mock deposit rates for given tenors.

    Args:
        currency (str): Currency of the deposit.
        tenor (List[str]): List of tenors. format: '1M', '2M', '3M', '6M', '9M', '1Y'
    
    Returns:
        pd.DataFrame: DataFrame of deposit rates.
    """
    n = len(tenor)
    curve_deeepness = 0.005  # difference of short end and long end of the curve.
    convexity = 0.001
    short_end = 0.02
    return pd.DataFrame({
        'tenor': tenor,
        'rates': np.linspace(short_end, short_end + curve_deeepness, n) + convexity * np.linspace(0, 1, n) ** 2
    })


def get_swap(currency:str, tenor:List[str]) -> pd.DataFrame:
    """
    Get mock swap rates for given tenors.

    Args:
        currency (str): Currency of the swap.
        tenor (List[str]): List of tenors. format: '1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'
    
    Returns:
        pd.DataFrame: DataFrame of swap rates.
    """
    n = len(tenor)
    curve_deeepness = 0.005  # difference of short end and long end of the curve.
    convexity = 0.001
    short_end = 0.03
    return pd.DataFrame({
        'tenor': tenor,
        'rate': np.linspace(short_end, short_end + curve_deeepness, n) + convexity * np.linspace(0, 1, n) ** 2
    })
    
def get_swaption(currency:str, maturity:List[str], length:List[str]) -> pd.DataFrame:
    """
    Get mock swaption volatilities for given tenors.

    Args:
        currency (str): Currency of the swap.
        maturity (List[str]): List of tenors. format: '1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'
        length (List[str]): List of tenors. format: '1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'
    
    Returns:
        pd.DataFrame: DataFrame of swaption volatilities.
    """
    n = len(maturity)

    mean_level = 0.15
    std_dev = 0.02
    return pd.DataFrame({
        'maturity': maturity,
        'length': length,
        'volatility': np.random.normal(mean_level, std_dev, n)
    })

def get_OIS(currency:str, tenor:List[str]) -> pd.DataFrame:
    """
    Get mock OIS rates for given tenors.

    Args:
        currency (str): Currency of the OIS.
        tenor (List[str]): List of tenors. format: '1M', '2M', '3M', '6M', '9M', '1Y'
    
    Returns:
        pd.DataFrame: DataFrame of OIS rates.
    """
    n = len(tenor)
    curve_deeepness = 0.005  # difference of short end and long end of the curve.
    convexity = 0.001
    short_end = 0.02
    return pd.DataFrame({
        'tenor': tenor,
        'rate': np.linspace(short_end, short_end + curve_deeepness, n) + convexity * np.linspace(0, 1, n) ** 2
    })

def get_FRA(currency:str, monthsToStart:List[int], monthsToEnd:List[int]) -> pd.DataFrame:
    """
    Get mock FRA rates for given tenors.

    Args:
        currency (str): Currency of the FRA.
        monthsToStart (List[int]): List of months to start. format: [1, 2, 3, 6, 9, 12]
        monthsToEnd (List[int]): List of months to end. format: [1, 2, 3, 6, 9, 12]
    
    Returns:
        pd.DataFrame: DataFrame of FRA rates.
    """
    n = len(monthsToStart)
    curve_deeepness = 0.005  # difference of short end and long end of the curve.
    convexity = 0.001
    short_end = 0.02
    return pd.DataFrame({
        'monthsToStart': monthsToStart,
        'monthsToEnd': monthsToEnd,
        'rate': np.linspace(short_end, short_end + curve_deeepness, n) + convexity * np.linspace(0, 1, n) ** 2
    })

def get_sofr_future(years:List[int], months:List[int], freq:list) -> pd.DataFrame:
    """
    Get mock SOFR future prices for given years, months, and frequencies.

    Args:
        years (List[int]): List of years. format: [2025, 2026, 2027, 2028, 2029]
        months (List[int]): List of months. format: [1, 2, 3, 6, 9, 12]
        freq (List[int]): List of frequencies. format: [1, 2, 3, 6, 9, 12]
    
    Returns:
        pd.DataFrame: DataFrame of SOFR future prices.
    """
    n = len(years)
    curve_deeepness = 0.005  # difference of short end and long end of the curve.
    short_end = 0.02
    convexity = 0.001
    rates = np.linspace(short_end, short_end + curve_deeepness, n) + convexity * np.linspace(0, 1, n) ** 2
    prices = 100 - rates * 100
    return pd.DataFrame({
        'year': years,
        'month': months,
        'freq': freq,
        'price': prices
    })


def get_volatility_surface(ticker: str, tenor: List[str], strikes: List[float]) -> pd.DataFrame:
    """
    Create a mock vol surface for given ticker, tenor and strikes.
    Args:
        ticker (str): Ticker of the asset.
        tenor (List[str]): List of tenors. format: '1M', '2M', '3M', '6M', '9M', '1Y'
        strikes (List[float]): List of strikes.
    Returns:
        pd.DataFrame, the index is strike, columns are tenor

    """
    n_strikes = len(strikes)
    n_tenors = len(tenor)
    # Generate a base curve that increases smoothly and strictly with tenor
    base_curve = np.linspace(0.3, 0.7, n_tenors)
    surface = np.zeros((n_strikes, n_tenors))
    # Use a smooth function for strike variation (e.g., a quadratic centered at the ATM)
    center = np.mean(strikes)
    max_offset = 0.04  # maximum deviation from base curve by strike
    for i, strike in enumerate(strikes):
        # Quadratic offset, smooth and symmetric around center strike
        offset = max_offset * -((strike - center) / (max(strikes) - min(strikes) + 1e-8))**2 + max_offset
        # No random noise, just a small deterministic ripple for realism
        ripple = 0.005 * np.sin(2 * np.pi * i / max(n_strikes-1,1))
        row = base_curve + offset + ripple
        # Ensure strict monotonicity with tenor (cumulative max)
        row = np.maximum.accumulate(row)
        # Clip to [0.3, 0.7]
        row = np.clip(row, 0.3, 0.7)
        surface[i, :] = row
    # Optionally, smooth along strike axis (rolling mean)
    import pandas as pd
    df = pd.DataFrame(surface, index=strikes, columns=tenor)
    df = df.rolling(window=3, min_periods=1, center=True).mean()
    return df
def get_volatility_table(ticker: str, tenor: List[str], strikes: List[float]) -> pd.DataFrame:
    """
    Create a mock vol table for given ticker, tenor and strikes.
    Args:
        ticker (str): Ticker of the asset.
        tenor (List[str]): List of tenors. format: '1M', '2M', '3M', '6M', '9M', '1Y'
        strikes (List[float]): List of strikes.
    Returns:
        pd.DataFrame, columns: strike, expiration, vol

    """
    volatility_surface = get_volatility_surface(ticker, tenor, strikes)
    volatility_table = volatility_surface.stack().reset_index()
    volatility_table.columns = ['strike', 'expiration', 'vol']
    return volatility_table


def get_price(ticker: str) -> float:
    """
    Get mock price for given ticker.

    Args:
        ticker (str): Ticker of the asset.
    
    Returns:
        float: Price of the asset.
    """
    if ticker == 'EUR':
        return np.random.uniform(1, 1.2)

    elif ticker == 'JPY':
        return np.random.uniform(130, 150)
    elif ticker == 'GBP':
        return np.random.uniform(1.2, 1.4)
    elif ticker == 'CHF':
        return np.random.uniform(0.9, 1.1)
    elif ticker == 'TWD':
        return np.random.uniform(28, 32)
    elif ticker == 'ZAR':
        return np.random.uniform(15, 20)
    elif ticker == 'AUD':
        return np.random.uniform(0.6, 0.7)
    else:
        return np.random.uniform(100, 200)

def get_dividend_rate(ticker: str) -> float:
    """
    Get mock dividend rate for given ticker.

    Args:
        ticker (str): Ticker of the asset.
    
    Returns:
        float: Dividend rate of the asset.
    """
    return np.random.uniform(0.01, 0.05)
    
if __name__ == '__main__':
    deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
    swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])
    swaption = get_swaption(['2Y', '3Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y'], ['5Y', '5Y', '5Y', '5Y', '5Y', '5Y', '5Y', '5Y'])
    fra = get_FRA([1, 2, 3, 6, 9, 12], [1, 2, 3, 6, 9, 12])
    sofr_future = get_sofr_future([2025, 2026, 2027, 2028], [1, 2, 3, 6], [ql.Quarterly, ql.Quarterly, ql.Quarterly, ql.Quarterly])
    print(deposit)
    print(swap)
    print(swaption)
    print(fra)
    print(sofr_future)
    print(get_volatility_surface('USD', ['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'], [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1]))

    
    
    