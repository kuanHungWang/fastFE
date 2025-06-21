import QuantLib as ql
import pandas as pd
from datetime import datetime
from util import (
    create_USD_deposit_rate_helpers,
    create_EUR_deposit_rate_helpers,
    create_JPY_deposit_rate_helpers,
    create_TWDeposit_rate_helpers,
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
from util import Conventions
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
    return builder(settlementDate, helpers, dayCount)

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

    
    for h in helpers:
        print(h)
    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)

def bootstrap_USD_curve(settlementDate, deposit: pd.DataFrame=None, swap: pd.DataFrame=None, OIS: pd.DataFrame=None, FRA: pd.DataFrame=None, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):
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
    dayCount = ql.Actual365Fixed()

    helpers = []
    if deposit is not None:
        deposit_helpers = create_TWDeposit_rate_helpers(deposit)
        helpers+=deposit_helpers
    
    if swap is not None:
        swap_helpers = create_TWD_swap_rate_helpers(swap)
        helpers+=swap_helpers
    
    return bootstrap_curve_with_instrument_helpers(settlementDate, helpers, dayCount)
    