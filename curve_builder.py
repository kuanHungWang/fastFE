import QuantLib as ql
import pandas as pd
from datetime import datetime
from rate_helpers import (
    create_USD_deposit_rate_helpers,
    create_EUR_deposit_rate_helpers,
    create_JPY_deposit_rate_helpers,
    create_TWD_deposit_rate_helpers,
    create_CHF_deposit_rate_helpers,
    create_GBP_deposit_rate_helpers,
    create_USD_swap_rate_helpers,
    create_EUR_swap_rate_helpers,
    create_JPY_swap_rate_helpers,
    create_TWD_swap_rate_helpers,
    create_CHF_swap_rate_helpers,
    create_GBP_swap_rate_helpers,
    create_deposit_rate_helpers,
    create_swap_rate_helpers,
    create_OIS_helper,
    create_EUR_OIS_helpers,
    create_GBP_OIS_helpers,
    create_JPY_OIS_helpers,
    create_CHF_OIS_helpers,
    create_fra_rate_helpers,  
    create_USD_FRA_helpers,
    create_EUR_FRA_helpers,
    create_CHF_FRA_helpers,
    create_GBP_FRA_helpers,
    create_JPY_FRA_helpers,
    create_bond_helper,
    create_sofr_future_rate_helpers
)
from conventions import Conventions
from typing import Literal, Tuple




def bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):

    builders = {
        'logLinearDiscount': ql.PiecewiseLogLinearDiscount,
        'logCubicDiscount': ql.PiecewiseLogCubicDiscount,
        'linearZero': ql.PiecewiseLinearZero,
        'cubicZero':    ql.PiecewiseCubicZero,
        'linearForward': ql.PiecewiseLinearForward,
        'splineCubicDiscount': ql.PiecewiseSplineCubicDiscount
        }
    builder = builders.get(method, ql.PiecewiseCubicZero)
    curve = builder(settlementDate, helpers, dayCount)
    curve.enableExtrapolation()
    return curve

def _bootstrap_USD_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
    """
    Bootstrap a USD yield curve using various market instruments.
    
    Args:
        settlementDate: The settlement date for the curve
        deposit (pd.DataFrame, optional): DataFrame containing deposit rates with 'tenor' and 'rates' columns
        swap (pd.DataFrame, optional): DataFrame containing swap rates with 'tenor' and 'rates' columns
        OIS (pd.DataFrame, optional): DataFrame containing OIS rates with 'tenor' and 'rates' columns
        FRA (pd.DataFrame, optional): DataFrame containing FRA rates with 'tenor' and 'rates' columns
        method (str): Interpolation method for curve construction. Options:
            - 'logLinearDiscount': Log-linear discount factor interpolation
            - 'logCubicDiscount': Log-cubic discount factor interpolation
            - 'linearZero': Linear zero rate interpolation (default)
            - 'cubicZero': Cubic zero rate interpolation
            - 'linearForward': Linear forward rate interpolation
            - 'splineCubicDiscount': Spline cubic discount factor interpolation
    
    Returns:
        QuantLib yield curve object with USD market conventions (Actual/360 day count)
    """
    dayCount = ql.Actual360()

    helpers = []
    if deposit is not None:
        deposit_helpers = create_USD_deposit_rate_helpers(deposit)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_USD_swap_rate_helpers(swap)
        helpers+=swap_helpers
    
    if OIS is not None:
        ois_helpers = create_USD_OIS_helper(OIS)
        helpers+=ois_helpers
    
    if FRA is not None:
        fra_helpers = create_USD_fra_rate_helpers(FRA)
        helpers+=fra_helpers

    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)

def _bootstrap_EUR_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
    """
    Bootstrap a EUR yield curve using various market instruments.
    
    Args:
        settlementDate: The settlement date for the curve
        deposit (pd.DataFrame, optional): DataFrame containing deposit rates with 'tenor' and 'rates' columns
        swap (pd.DataFrame, optional): DataFrame containing swap rates with 'tenor' and 'rates' columns
        OIS (pd.DataFrame, optional): DataFrame containing OIS rates with 'tenor' and 'rates' columns
        FRA (pd.DataFrame, optional): DataFrame containing FRA rates with 'tenor' and 'rates' columns
        method (str): Interpolation method for curve construction. Options:
            - 'logLinearDiscount': Log-linear discount factor interpolation
            - 'logCubicDiscount': Log-cubic discount factor interpolation
            - 'linearZero': Linear zero rate interpolation (default)
            - 'cubicZero': Cubic zero rate interpolation
            - 'linearForward': Linear forward rate interpolation
            - 'splineCubicDiscount': Spline cubic discount factor interpolation
    
    Returns:
        QuantLib yield curve object with EUR market conventions (Actual/360 day count)
    """
    dayCount = ql.Actual360()

    helpers = []
    if deposit is not None:
        deposit_helpers = create_EUR_deposit_rate_helpers(deposit)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_EUR_swap_rate_helpers(swap)
        helpers+=swap_helpers
    
    if OIS is not None:
        ois_helpers = create_EUR_OIS_helper(OIS)
        helpers+=ois_helpers
    
    if FRA is not None:
        fra_helpers = create_EUR_fra_rate_helpers(FRA)
        helpers+=fra_helpers

    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)

def _bootstrap_JPY_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
    """
    Bootstrap a JPY yield curve using various market instruments.
    
    Args:
        settlementDate: The settlement date for the curve
        deposit (pd.DataFrame, optional): DataFrame containing deposit rates with 'tenor' and 'rates' columns
        swap (pd.DataFrame, optional): DataFrame containing swap rates with 'tenor' and 'rates' columns
        OIS (pd.DataFrame, optional): DataFrame containing OIS rates with 'tenor' and 'rates' columns
        FRA (pd.DataFrame, optional): DataFrame containing FRA rates with 'tenor' and 'rates' columns
        method (str): Interpolation method for curve construction. Options:
            - 'logLinearDiscount': Log-linear discount factor interpolation
            - 'logCubicDiscount': Log-cubic discount factor interpolation
            - 'linearZero': Linear zero rate interpolation (default)
            - 'cubicZero': Cubic zero rate interpolation
            - 'linearForward': Linear forward rate interpolation
            - 'splineCubicDiscount': Spline cubic discount factor interpolation
    
    Returns:
        QuantLib yield curve object with JPY market conventions (Actual/360 day count)
    """
    dayCount = ql.Actual360()

    helpers = []
    if deposit is not None:
        deposit_helpers = create_JPY_deposit_rate_helpers(deposit)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_JPY_swap_rate_helpers(swap)
        helpers+=swap_helpers
    
    if OIS is not None:
        ois_helpers = create_JPY_OIS_helper(OIS)
        helpers+=ois_helpers
    
    if FRA is not None:
        fra_helpers = create_JPY_fra_rate_helpers(FRA)
        helpers+=fra_helpers

    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)
    
def _bootstrap_GBP_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
    """
    Bootstrap a GBP yield curve using various market instruments.
    
    Args:
        settlementDate: The settlement date for the curve
        deposit (pd.DataFrame, optional): DataFrame containing deposit rates with 'tenor' and 'rates' columns
        swap (pd.DataFrame, optional): DataFrame containing swap rates with 'tenor' and 'rates' columns
        OIS (pd.DataFrame, optional): DataFrame containing OIS rates with 'tenor' and 'rates' columns
        FRA (pd.DataFrame, optional): DataFrame containing FRA rates with 'tenor' and 'rates' columns
        method (str): Interpolation method for curve construction. Options:
            - 'logLinearDiscount': Log-linear discount factor interpolation
            - 'logCubicDiscount': Log-cubic discount factor interpolation
            - 'linearZero': Linear zero rate interpolation (default)
            - 'cubicZero': Cubic zero rate interpolation
            - 'linearForward': Linear forward rate interpolation
            - 'splineCubicDiscount': Spline cubic discount factor interpolation
    
    Returns:
        QuantLib yield curve object with GBP market conventions (Actual/360 day count)
    """
    dayCount = ql.Actual360()

    helpers = []
    if deposit is not None:
        deposit_helpers = create_GBP_deposit_rate_helpers(deposit)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_GBP_swap_rate_helpers(swap)
        helpers+=swap_helpers
    
    if OIS is not None:
        ois_helpers = create_GBP_OIS_helper(OIS)
        helpers+=ois_helpers
    
    if FRA is not None:
        fra_helpers = create_GBP_fra_rate_helpers(FRA)
        helpers+=fra_helpers

    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)

def _bootstrap_TWD_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
    """
    Bootstrap a TWD yield curve using various market instruments.
    
    Args:
        settlementDate: The settlement date for the curve
        deposit (pd.DataFrame, optional): DataFrame containing deposit rates with 'tenor' and 'rates' columns
        swap (pd.DataFrame, optional): DataFrame containing swap rates with 'tenor' and 'rates' columns
        method (str): Interpolation method for curve construction. Options:
            - 'logLinearDiscount': Log-linear discount factor interpolation
            - 'logCubicDiscount': Log-cubic discount factor interpolation
            - 'linearZero': Linear zero rate interpolation (default)
            - 'cubicZero': Cubic zero rate interpolation
            - 'linearForward': Linear forward rate interpolation
            - 'splineCubicDiscount': Spline cubic discount factor interpolation
    
    Returns:
        QuantLib yield curve object with TWD market conventions (Actual/365Fixed day count)
    
    Note:
        TWD curve does not support OIS and FRA instruments in this implementation.
    """
    dayCount = ql.Actual365Fixed()

    helpers = []
    if deposit is not None:
        deposit_helpers = create_TWD_deposit_rate_helpers(deposit)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_TWD_swap_rate_helpers(swap)
        helpers+=swap_helpers
    
    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)

def bootstrap_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero',currency: Literal['USD', 'EUR', 'JPY', 'GBP', 'TWD']='USD'):
    """
    Bootstrap a yield curve using various market instruments.
    
    Args:
        currency (Literal['USD', 'EUR', 'JPY', 'GBP', 'TWD']): The currency for the curve
        settlementDate: The settlement date for the curve
        deposit (pd.DataFrame, optional): DataFrame containing deposit rates with 'tenor' and 'rates' columns
        swap (pd.DataFrame, optional): DataFrame containing swap rates with 'tenor' and 'rates' columns
        OIS (pd.DataFrame, optional): DataFrame containing OIS rates with 'tenor' and 'rates' columns
        FRA (pd.DataFrame, optional): DataFrame containing FRA rates with 'tenor' and 'rates' columns
        method (str): Interpolation method for curve construction. Options:
            - 'logLinearDiscount': Log-linear discount factor interpolation
            - 'logCubicDiscount': Log-cubic discount factor interpolation
            - 'linearZero': Linear zero rate interpolation (default)
            - 'cubicZero': Cubic zero rate interpolation
            - 'linearForward': Linear forward rate interpolation
            - 'splineCubicDiscount': Spline cubic discount factor interpolation
    
    Returns:
        QuantLib yield curve object with specified currency conventions
    """
    if currency == 'USD':
        fixed_leg_conventions = Conventions.USFixedLegConventions()
        floating_leg_conventions = Conventions.USFloatingLegConventions()
        ois_conventions = Conventions.USDOISConventions()

    elif currency == 'EUR':
        fixed_leg_conventions = Conventions.EURFixedLegConventions()
        floating_leg_conventions = Conventions.EURFloatingLegConventions()
        ois_conventions = Conventions.EUROISConventions()

    elif currency == 'JPY':
        fixed_leg_conventions = Conventions.JPYFixedLegConventions()
        floating_leg_conventions = Conventions.JPYFloatingLegConventions()
        ois_conventions = Conventions.JPYOISConventions()

    elif currency == 'GBP':
        fixed_leg_conventions = Conventions.GBPFixedLegConventions()
        floating_leg_conventions = Conventions.GBPFloatingLegConventions()
        ois_conventions = Conventions.GBPOISConventions()

    elif currency == 'CHF':
        fixed_leg_conventions = Conventions.CHFFixedLegConventions()
        floating_leg_conventions = Conventions.CHFFloatingLegConventions()
        ois_conventions = Conventions.CHFOISConventions()

    elif currency == 'TWD':
        fixed_leg_conventions = Conventions.TWDFixedLegConventions()
        floating_leg_conventions = Conventions.TWDFloatingLegConventions()
        ois_conventions = None

    else:
        raise ValueError(f"Unsupported currency: {currency}")

    dayCount = fixed_leg_conventions.get('dayCounter', ql.Actual360())
    helpers = []
    if deposit is not None:
        deposit_helpers = create_deposit_rate_helpers(deposit, fixed_leg_conventions)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_swap_rate_helpers(swap, fixed_leg_conventions, floating_leg_conventions)
        helpers+=swap_helpers
    
    if OIS is not None and ois_conventions is not None:
        ois_helpers = create_OIS_helper(OIS, ois_conventions)
        helpers+=ois_helpers
    
    if FRA is not None:
        fra_helpers = create_fra_rate_helpers(FRA, floating_leg_conventions)
        helpers+=fra_helpers

    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount, method)


    
    
if __name__ == '__main__':
        
    today = ql.Date().todaysDate()

    # example: use helpers to bootstrap curve
    df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '9M'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
    deposit_helpers = create_USD_deposit_rate_helpers(df_deposit)

    df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02, 0.022, 0.025],'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']})
    swap_helpers = create_USD_swap_rate_helpers(df_swap)

    curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers, ql.Actual360())  # use deposit helper only
    curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers + swap_helpers, ql.Actual360())  # use deposit and swap helpers



    curve = _bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for USD curve without conventions
    curve = _bootstrap_EUR_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for EUR curve without conventions
    curve = _bootstrap_JPY_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for JPY curve without conventions
    curve = _bootstrap_GBP_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for GBP curve without conventions
    curve = _bootstrap_TWD_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for TWD curve without conventions
    curve = bootstrap_curve('USD', today, deposit=df_deposit, swap=df_swap)  # fast builder for USD curve without conventions
    curve = bootstrap_curve('EUR', today, deposit=df_deposit, swap=df_swap)  # fast builder for EUR curve without conventions
    curve = bootstrap_curve('JPY', today, deposit=df_deposit, swap=df_swap)  # fast builder for JPY curve without conventions
    curve = bootstrap_curve('GBP', today, deposit=df_deposit, swap=df_swap)  # fast builder for GBP curve without conventions
    curve = bootstrap_curve('TWD', today, deposit=df_deposit, swap=df_swap)  # fast builder for TWD curve without conventions
    curve = bootstrap_curve('CHF', today, deposit=df_deposit, swap=df_swap)  # fast builder for CHF curve without conventions
    schedule = ql.MakeSchedule(today, today + ql.Period(3, ql.Months), ql.Period('1W'))



