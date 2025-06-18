import QuantLib as ql
import pandas as pd
import numpy as np
from collections import namedtuple
import math
from datetime import datetime, timedelta
from sklearn import linear_model
from typing import List, Tuple, Callable, Dict

def get_settlement_date(trade_date, settlement_days, calendar):
    return calendar.advance(trade_date,ql.Period(settlement_days, ql.Days))


def create_deposit_rate_helpers(df: pd.DataFrame, calendar, conventions: dict = None):
    """
    Create a list of QuantLib DepositRateHelper objects from a DataFrame.
    The DataFrame must have columns: 'tenor' (string) and 'rates' (float).
    conventions (dict): Must include 'calendar'. Other keys (optional): 'settlement_days', 'date_rolling_convention', 'date_end_of_month', 'dayCounter'.
    Example: {'calendar': ql.TARGET(), ...}
    """
    if conventions is None:
        conventions = {}
    fixingDays = conventions.get('settlement_days', 2)
    convention = conventions.get('date_rolling_convention', ql.ModifiedFollowing)
    endOfMonth = conventions.get('date_end_of_month', False)
    dayCounter = conventions.get('dayCounter', ql.Actual360())
    helpers = []
    for _, row in df.iterrows():
        quote = ql.QuoteHandle(ql.SimpleQuote(row['rates']))
        tenor = ql.Period(row['tenor'])
        helper = ql.DepositRateHelper(
            quote, tenor, fixingDays, calendar, convention, endOfMonth, dayCounter
        )
        helpers.append(helper)
    return helpers

def create_fra_rate_helpers(df: pd.DataFrame, calendar, conventions: dict = None):
    """
    Create a list of QuantLib FraRateHelper objects from a DataFrame.
    The DataFrame must have columns: 'monthsToStart' (int), 'monthsToEnd' (int), and 'rates' (float).
    conventions (dict): Must include 'calendar'. Other keys (optional): 'settlement_days', 'date_rolling_convention', 'date_end_of_month', 'dayCounter'.
    Example: {'calendar': ql.TARGET(), ...}
    """
    if conventions is None:
        conventions = {}
    fixingDays = conventions.get('settlement_days', 2)
    convention = conventions.get('date_rolling_convention', ql.ModifiedFollowing)
    endOfMonth = conventions.get('date_end_of_month', False)
    dayCounter = conventions.get('dayCounter', ql.Actual360())
    helpers = []
    for _, row in df.iterrows():
        quote = ql.QuoteHandle(ql.SimpleQuote(row['rates']))
        monthsToStart = int(row['monthsToStart'])
        monthsToEnd = int(row['monthsToEnd'])
        helper = ql.FraRateHelper(
            quote, monthsToStart, monthsToEnd, fixingDays, calendar, convention, endOfMonth, dayCounter
        )
        helpers.append(helper)
    return helpers


def create_swap_rate_helpers(df: pd.DataFrame, calendar, currency, conventions: dict = None):
    """
    Create a list of QuantLib SwapRateHelper objects from a DataFrame.
    The DataFrame must have columns: 'rate' (float), 'tenor' (string).
    conventions (dict): Must include 'calendar'. Other keys (optional): 'fixedFrequency', 'fixedConvention', 'fixedDayCount', 'iborIndex'.
    Example: {'calendar': ql.TARGET(), ...}
    """
    if conventions is None:
        conventions = {}
    fixedFrequency = conventions.get('fixedFrequency', ql.Annual)
    fixedConvention = conventions.get('fixedConvention', ql.Following)
    floatingFrequency = conventions.get('floatingFrequency', ql.Period('6M'))
    fixedDayCount = conventions.get('fixedDayCount', ql.Thirty360(ql.Thirty360.BondBasis))
    iborIndex = ql.Libor('libor', floatingFrequency, 2, currency, ql.UnitedKingdom(), ql.Actual360())

    helpers = []
    for _, row in df.iterrows():
        rate = row['rate']
        tenor = ql.Period(row['tenor'])
        helper = ql.SwapRateHelper(
            rate, tenor, calendar, fixedFrequency, fixedConvention, fixedDayCount, iborIndex
        )
        helpers.append(helper)
    return helpers

def create_sofr_future_rate_helpers(df: pd.DataFrame):
    """
    Create a list of QuantLib SofrFutureRateHelper objects from a DataFrame.
    The DataFrame must have columns: 'price' (float), 'month' (int), 'year' (int), 'frequency' (QuantLib frequency).
    """
    if 'frequency' not in df.columns:
        raise ValueError("DataFrame must contain a 'frequency' column.")
    helpers = []
    for _, row in df.iterrows():
        price = row['price']
        month = row['month']
        year = row['year']
        freq = row['frequency']
        print(f'price: {price}, month: {month}, year: {year}, frequency: {freq}')
        helper = ql.SofrFutureRateHelper(price, int(month), int(year), int(freq))
        helpers.append(helper)
    return helpers
# Example usage for swap helpers







settlement_days = 2
calendar = ql.TARGET()
dayCount=ql.Actual360()
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
date_generation_rule = ql.DateGeneration.Backward
date_end_of_month = False

today = ql.Date().todaysDate()
settlement = get_settlement_date(today, settlement_days, calendar)

conventions = {
    'settlement_days': settlement_days,
    'calendar': calendar,
    'date_rolling_convention': date_rolling_convention,
    'date_termination_convention': date_termination_convention,
    'date_generation_rule': date_generation_rule,
    'date_end_of_month': date_end_of_month,
    'dayCounter': dayCount
}


df_deposit = pd.DataFrame({
    'tenor': ['1M', '2M', '3M', '6M', '1Y'],
    'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})

df_fra = pd.DataFrame({
    'monthsToStart': [1, 2, 3],
    'monthsToEnd': [7, 8, 9],
    'rates': [0.021, 0.023, 0.025]
})

df_swap = pd.DataFrame({
    'rate': [0.015, 0.018, 0.02],
    'tenor': ['5Y', '7Y', '10Y']
})
df_sofr = pd.DataFrame({
    'price': [99.915, 99.920],
    'month': [3, 6],
    'year': [2020, 2020],
    'frequency': [ql.Quarterly, ql.Quarterly]
})
swap_helpers = create_swap_rate_helpers(df_swap, calendar, ql.USDCurrency())
deposit_helpers = create_deposit_rate_helpers(df_deposit, calendar)
fra_helpers = create_fra_rate_helpers(df_fra, calendar)
sofr_helpers = create_sofr_future_rate_helpers(df_sofr)

print(deposit_helpers)
print(fra_helpers)
print(swap_helpers)




# Example usage for SofrFutureRateHelper




print(sofr_helpers)

