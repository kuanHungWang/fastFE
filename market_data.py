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

        
    
    