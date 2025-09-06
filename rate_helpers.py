import QuantLib as ql
import pandas as pd
import numpy as np
from collections import namedtuple
import math
from datetime import datetime, timedelta
from sklearn import linear_model
from typing import List, Tuple, Callable, Dict
from datetime import datetime
from conventions import Conventions
def to_ql_date(d: datetime):
    return ql.Date(d.day, d.month, d.year)
def get_settlement_date(trade_date, settlement_days, calendar):
    return calendar.advance(trade_date,ql.Period(settlement_days, ql.Days))

def create_deposit_rate_helpers(df: pd.DataFrame,  conventions: dict = None):
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
    calendar = conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.Settlement))
    helpers = []
    for _, row in df.iterrows():
        quote = ql.QuoteHandle(ql.SimpleQuote(row['rates']))
        tenor = ql.Period(row['tenor'])
        helper = ql.DepositRateHelper(
            quote, tenor, fixingDays, calendar, convention, endOfMonth, dayCounter
        )
        helpers.append(helper)
    return helpers

def create_fra_rate_helpers(df: pd.DataFrame, conventions: dict = None):
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
    calendar = conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.Settlement))
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

def create_swap_rate_helpers(df: pd.DataFrame, fixed_leg_conventions: dict = None, floating_leg_conventions: dict = None):
    """
    Create a list of QuantLib SwapRateHelper objects from a DataFrame.
    The DataFrame must have columns: 'rate' (float), 'tenor' (string).
    conventions (dict): Must include 'calendar'. Other keys (optional): 'fixedFrequency', 'fixedConvention', 'fixedDayCount', 'iborIndex'.
    Example: {'calendar': ql.TARGET(), ...}
    """
    try:
        # add one year to the last tenor in case of bootstrap or calibration failure
        last_row = df.iloc[-1]
        last_tenor = last_row['tenor']
        tenor_plus_one_year = f"{int(last_tenor[:-1]) + 1}Y"
        padding_raw = last_row.copy()
        padding_raw['tenor'] = tenor_plus_one_year
        df = df._append(padding_raw, ignore_index=True)
    except:
        print("Failed to add one year to the last tenor, using original data.")
    if fixed_leg_conventions is None:
        fixed_leg_conventions = {}
    if floating_leg_conventions is None:
        floating_leg_conventions = {}
    fixedFrequency = fixed_leg_conventions.get('frequency', ql.Annual)
    fixedConvention = fixed_leg_conventions.get('date_rolling_convention', ql.Following)
    floatingFrequency = floating_leg_conventions.get('frequency', ql.Period('6M'))
    fixedDayCount = fixed_leg_conventions.get('dayCount', ql.Thirty360(ql.Thirty360.BondBasis))
    floatingDayCount = floating_leg_conventions.get('dayCount', ql.Actual360())
    floatingConvention = floating_leg_conventions.get('date_rolling_convention', ql.Following)
    floatingSettlementDays = floating_leg_conventions.get('settlement_days', 2)
    floatingEndOfMonth = floating_leg_conventions.get('endOfMonth', False)
    calendar = floating_leg_conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.Settlement))
    currency = floating_leg_conventions.get('currency', ql.USDCurrency())
    if currency == ql.EURCurrency():
        iborIndex = ql.Euribor(floatingFrequency)
    else:
        iborIndex = ql.IborIndex('libor', floatingFrequency, floatingSettlementDays, currency, calendar, floatingConvention, floatingEndOfMonth, floatingDayCount)

    helpers = []
    for _, row in df.iterrows():
        rate = row['rate']
        tenor = ql.Period(row['tenor'])
        helper = ql.SwapRateHelper(
            rate, tenor, calendar, fixedFrequency, fixedConvention, fixedDayCount, iborIndex
        )
        helpers.append(helper)
    return helpers

def create_sofr_future_rate_helpers(df: pd.DataFrame, conventions: dict = None):
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

        helper = ql.SofrFutureRateHelper(price, int(month), int(year), int(freq))
        helpers.append(helper)
    return helpers

def create_OIS_helper(df: pd.DataFrame, conventions: dict = None):
    """
    Create a list of QuantLib OISRateHelper objects from a DataFrame.
    The DataFrame must have columns: 'tenor' (string) and 'rates' (float).
    conventions (dict): Must include 'calendar'. Other keys (optional): 'settlement_days', 'date_rolling_convention', 'date_end_of_month', 'dayCounter'.
    Example: {'calendar': ql.TARGET(), ...}
    """
    if conventions is None:
        conventions = {}
    fixingDays = conventions.get('settlement_days', 2)
    dayCounter = conventions.get('dayCounter', ql.Actual360())
    calendar = conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.Settlement))
    currency = conventions.get('currency', ql.USDCurrency())
    overnight_index = ql.OvernightIndex('overnightIndex', fixingDays, currency, calendar, dayCounter)
    helpers = []
    for _, row in df.iterrows():
        rate = row['rate']
        period = row['tenor']
        oishelper = ql.OISRateHelper(2, ql.Period(period), ql.QuoteHandle(ql.SimpleQuote(rate)),overnight_index)
        helpers.append(oishelper)
    return helpers

def create_bond_helper(df: pd.DataFrame, conventions: dict = None):
    """
    Create a list of QuantLib FixedRateBondHelper objects from a DataFrame.
    The DataFrame must have columns: 'tenor' (string) and 'rates' (float).
    conventions (dict): Must include 'calendar'. Other keys (optional): 'settlement_days', 'date_rolling_convention', 'date_end_of_month', 'dayCounter'.
    Example: {'calendar': ql.TARGET(), ...}
    """
    if conventions is None:
        conventions = {}
    settlementDays = conventions.get('settlement_days', 2)
    faceAmount = 100
    dayCounter = conventions.get('dayCounter', ql.Actual360())
    calendar = conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.GovernmentBond))
    date_rolling_convention = conventions.get('date_rolling_convention', ql.ModifiedFollowing)
    date_termination_convention = conventions.get('date_termination_convention', ql.ModifiedFollowing)
    rule = conventions.get('rule', ql.DateGeneration.Backward)
    endOfMonth = conventions.get('endOfMonth', False)
    frequency = conventions.get('frequency', ql.Period('6M'))
    
    


    helpers = []
    for _, row in df.iterrows():
        coupon = row['coupon']
        price = row['price']
        effectiveDate = to_ql_date(row['effectiveDate'])
        terminationDate = to_ql_date(row['terminationDate'])
        schedule = ql.Schedule(effectiveDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
        bond_helper =ql.FixedRateBondHelper(ql.QuoteHandle(ql.SimpleQuote(price)), settlementDays, faceAmount, schedule, [coupon], dayCounter)
        helpers.append(bond_helper)
    return helpers



def create_USD_deposit_rate_helpers(df: pd.DataFrame):
    conventions = Conventions.USFixedLegConventions()
    return create_deposit_rate_helpers(df, conventions)

def create_EUR_deposit_rate_helpers(df: pd.DataFrame):
    conventions = Conventions.EURFixedLegConventions()
    return create_deposit_rate_helpers(df, conventions)

def create_JPY_deposit_rate_helpers(df: pd.DataFrame):
    conventions = Conventions.JPYFixedLegConventions()
    return create_deposit_rate_helpers(df, conventions)

def create_TWD_deposit_rate_helpers(df: pd.DataFrame):
    conventions = Conventions.TWDFixedLegConventions()
    return create_deposit_rate_helpers(df, conventions)

def create_CHF_deposit_rate_helpers(df: pd.DataFrame):
    conventions = Conventions.CHFFixedLegConventions()
    return create_deposit_rate_helpers(df, conventions)

def create_GBP_deposit_rate_helpers(df: pd.DataFrame):
    conventions = Conventions.GBPFixedLegConventions()
    return create_deposit_rate_helpers(df, conventions)

def create_USD_swap_rate_helpers(df: pd.DataFrame):
    fixed_leg_conventions = Conventions.USFixedLegConventions()
    floating_leg_conventions = Conventions.USFloatingLegConventions()
    return create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)

def create_EUR_swap_rate_helpers(df: pd.DataFrame):
    fixed_leg_conventions = Conventions.EURFixedLegConventions()
    floating_leg_conventions = Conventions.EURFloatingLegConventions()
    return create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)

def create_JPY_swap_rate_helpers(df: pd.DataFrame):
    fixed_leg_conventions = Conventions.JPYFixedLegConventions()
    floating_leg_conventions = Conventions.JPYFloatingLegConventions()
    return create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)

def create_TWD_swap_rate_helpers(df: pd.DataFrame):
    fixed_leg_conventions = Conventions.TWDFixedLegConventions()
    floating_leg_conventions = Conventions.TWDFloatingLegConventions()
    return create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)

def create_CHF_swap_rate_helpers(df: pd.DataFrame):
    fixed_leg_conventions = Conventions.CHFFixedLegConventions()
    floating_leg_conventions = Conventions.CHFFloatingLegConventions()
    return create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)

def create_GBP_swap_rate_helpers(df: pd.DataFrame):
    fixed_leg_conventions = Conventions.GBPFixedLegConventions()
    floating_leg_conventions = Conventions.GBPFloatingLegConventions()
    return create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)


def create_USD_OIS_helpers(df: pd.DataFrame):
    conventions = Conventions.USDOISConventions()
    return create_OIS_helper(df, conventions)

def create_EUR_OIS_helpers(df: pd.DataFrame):
    conventions = Conventions.EUROISConventions()
    return create_OIS_helper(df, conventions)

def create_GBP_OIS_helpers(df: pd.DataFrame):
    conventions = Conventions.GBPOISConventions()
    return create_OIS_helper(df, conventions)

def create_JPY_OIS_helpers(df: pd.DataFrame):
    conventions = Conventions.JPYOISConventions()
    return create_OIS_helper(df, conventions)

def create_CHF_OIS_helpers(df: pd.DataFrame):
    conventions = Conventions.CHFOISConventions()
    return create_OIS_helper(df, conventions)

def create_USD_FRA_helpers(df: pd.DataFrame):
    conventions = Conventions.USFloatingLegConventions()
    return create_fra_rate_helpers(df, conventions)

def create_EUR_FRA_helpers(df: pd.DataFrame):
    conventions = Conventions.EURFloatingLegConventions()
    return create_fra_rate_helpers(df, conventions)

def create_CHF_FRA_helpers(df: pd.DataFrame):
    conventions = Conventions.CHFFloatingLegConventions()
    return create_fra_rate_helpers(df, conventions)

def create_GBP_FRA_helpers(df: pd.DataFrame):
    conventions = Conventions.GBPFloatingLegConventions()
    return create_fra_rate_helpers(df, conventions)

def create_JPY_FRA_helpers(df: pd.DataFrame):
    conventions = Conventions.JPYFloatingLegConventions()
    return create_fra_rate_helpers(df, conventions)


if __name__ == '__main__':

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



    # Example usage of creating rate helpers with dataFrames and conventions.
    df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
    df_fra = pd.DataFrame({'monthsToStart': [1, 2, 3], 'monthsToEnd': [7, 8, 9], 'rates': [0.021, 0.023, 0.025]})
    df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02], 'tenor': ['5Y', '7Y', '10Y']})
    df_sofr = pd.DataFrame({'price': [99.915, 99.920], 'month': [3, 6], 'year': [2020, 2020], 'frequency': [ql.Quarterly, ql.Quarterly]})
    df_OIS = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rate': [0.015, 0.018, 0.02, 0.022, 0.025]})
    df_bond = pd.DataFrame({'coupon': [0.015, 0.018], 'price': [99.915, 99.920], 'effectiveDate': [datetime(2020,1,15), datetime(2020,6,15)], 'terminationDate': [datetime(2025,1,15), datetime(2025,6,15)]})
    
    swap_helpers = create_swap_rate_helpers(df_swap, fixed_leg_conventions=Conventions.USFixedLegConventions(), floating_leg_conventions=Conventions.USFloatingLegConventions())
    deposit_helpers = create_deposit_rate_helpers(df_deposit, conventions=Conventions.USFixedLegConventions())
    fra_helpers = create_fra_rate_helpers(df_fra, conventions=Conventions.USFloatingLegConventions())
    sofr_helpers = create_sofr_future_rate_helpers(df_sofr, conventions=Conventions.USFloatingLegConventions())
    oishelpers = create_OIS_helper(df_OIS, conventions=Conventions.USFixedLegConventions())
    conventions = Conventions.USFixedLegConventions()
    conventions['frequency'] = ql.Period('6M')
    bond_helpers = create_bond_helper(df_bond, conventions=conventions)



    # Example usage for quick deposit helper builder for each currency without need to pass conventions
    df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
    create_USD_deposit_rate_helpers(df_deposit)
    create_EUR_deposit_rate_helpers(df_deposit)
    create_JPY_deposit_rate_helpers(df_deposit)
    create_TWD_deposit_rate_helpers(df_deposit)
    create_CHF_deposit_rate_helpers(df_deposit)
    create_GBP_deposit_rate_helpers(df_deposit)


    # Example usage for quick swap helper builder for each currency without need to pass conventions
    df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02], 'tenor': ['5Y', '7Y', '10Y']})
    create_USD_swap_rate_helpers(df_swap)
    create_EUR_swap_rate_helpers(df_swap)
    create_JPY_swap_rate_helpers(df_swap)
    create_TWD_swap_rate_helpers(df_swap)
    create_CHF_swap_rate_helpers(df_swap)
    create_GBP_swap_rate_helpers(df_swap)


    # Example usage for quick OIS helper builder for each currency without need to pass conventions
    df_OIS = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rate': [0.015, 0.018, 0.02, 0.022, 0.025]})
    create_EUR_OIS_helpers(df_OIS)
    create_GBP_OIS_helpers(df_OIS)
    create_JPY_OIS_helpers(df_OIS)
    create_CHF_OIS_helpers(df_OIS)

    # Example usage for quick FRA helper builder for each currency without need to pass conventions
    df_fra = pd.DataFrame({'monthsToStart': [1, 2, 3], 'monthsToEnd': [7, 8, 9], 'rates': [0.021, 0.023, 0.025]})
    create_USD_FRA_helpers(df_fra)
    create_EUR_FRA_helpers(df_fra)
    create_CHF_FRA_helpers(df_fra)
    create_GBP_FRA_helpers(df_fra)
    create_JPY_FRA_helpers(df_fra)


