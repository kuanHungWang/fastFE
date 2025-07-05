import pandas as pd
import numpy as np
from typing import List
import QuantLib as ql

def get_deposit(tenor:List[str]) -> pd.DataFrame:
    """
    Get mock deposit rates for given tenors.

    Args:
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


def get_swap(tenor:List[str]) -> pd.DataFrame:
    """
    Get mock swap rates for given tenors.

    Args:
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
    
def get_swaption(maturity:List[str], length:List[str]) -> pd.DataFrame:
    """
    Get mock swaption volatilities for given tenors.

    Args:
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

def get_OIS(tenor:List[str]) -> pd.DataFrame:
    """
    Get mock OIS rates for given tenors.

    Args:
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

def get_FRA(monthsToStart:List[int], monthsToEnd:List[int]) -> pd.DataFrame:
    """
    Get mock FRA rates for given tenors.

    Args:
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
    Return: pd.DataFrame, index: strike, columns: tenor
    Generated value must be positive value between 0.3 and 0.7, smooth and increasing with tenor.
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
    df = df.rolling(window=3, min_periods=1, axis=0, center=True).mean()
    return df

    
    
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

    
    
    