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

def bootstrap_curve(settlementDate, dayCount, deposit: Tuple=None, swap: Tuple=None, OIS: Tuple=None, FRA: Tuple=None):


    helpers = []
    if deposit is not None:
        df = deposit[0]
        conventions = deposit[1]
        deposit_helpers = create_deposit_rate_helpers(df, conventions)
        helpers+=deposit_helpers
    if swap is not None:
        df = swap[0]
        fixed_leg_conventions = swap[1]
        floating_leg_conventions = swap[2]
        swap_helpers = create_swap_rate_helpers(df, fixed_leg_conventions, floating_leg_conventions)
        helpers+=swap_helpers
    if OIS is not None:
        df = OIS[0]
        conventions = OIS[1]
        ois_helpers = create_OIS_helper(df, conventions)
        helpers+=ois_helpers
    if FRA is not None:
        df = FRA[0]
        conventions = FRA[1]
        fra_helpers = create_fra_rate_helpers(df, conventions)
        helpers+=fra_helpers

    
        
    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)

def bootstrap_USD_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
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

def bootstrap_EUR_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
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

def bootstrap_JPY_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
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
    
def bootstrap_GBP_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
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

def bootstrap_TWD_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
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


if __name__ == '__main__':
        
    today = ql.Date().todaysDate()

    # example: use helpers to bootstrap curve
    df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '9M'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
    deposit_helpers = create_USD_deposit_rate_helpers(df_deposit)

    df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02, 0.022, 0.025],'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']})
    swap_helpers = create_USD_swap_rate_helpers(df_swap)

    curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers, ql.Actual360())  # use deposit helper only
    curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers + swap_helpers, ql.Actual360())  # use deposit and swap helpers

    # example: directly use dataFrame or use fast builder
    curve = bootstrap_curve(
        today, ql.Actual360(), 
        deposit=(df_deposit, Conventions.USFixedLegConventions()), 
        swap=(df_swap, Conventions.USFixedLegConventions(), 
        Conventions.USFloatingLegConventions())
        )
    curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for USD curve without conventions
    curve = bootstrap_EUR_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for EUR curve without conventions
    curve = bootstrap_JPY_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for JPY curve without conventions
    curve = bootstrap_GBP_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for GBP curve without conventions
    curve = bootstrap_TWD_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for TWD curve without conventions
    schedule = ql.MakeSchedule(today, today + ql.Period(3, ql.Months), ql.Period('1W'))



