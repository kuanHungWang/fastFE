import QuantLib as ql
import pandas as pd
from datetime import datetime
from util import (
    create_USD_deposit_rate_helpers,
    create_USD_swap_rate_helpers,
    create_deposit_rate_helpers,
    create_swap_rate_helpers,
    create_OIS_helper,
    create_fra_rate_helpers,  # <-- corrected
    create_bond_helper,
    create_sofr_future_rate_helpers
)
from curve_builder import bootstrap_USD_curve, bootstrap_EUR_curve, bootstrap_JPY_curve, bootstrap_GBP_curve, bootstrap_TWD_curve
from util import Conventions
from typing import Literal, Tuple
from curve_builder import bootstrap_curve_with_instrument_helpers, bootstrap_curve

   

df_deposit = pd.DataFrame({
    'tenor': ['1M', '2M', '3M', '6M', '9M'],
    'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})

df_swap = pd.DataFrame({
    'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
    'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
})
today = ql.Date().todaysDate()
deposit_helpers = create_USD_deposit_rate_helpers(df_deposit)
swap_helpers = create_USD_swap_rate_helpers(df_swap)
helpers = deposit_helpers + swap_helpers




curve = bootstrap_curve(today, ql.Actual360(), deposit=(df_deposit, Conventions.USFixedLegConventions()), swap=(df_swap, Conventions.USFixedLegConventions(), Conventions.USFloatingLegConventions()))
curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)

fixed_leg_conventions = Conventions.USFixedLegConventions()
fixed_leg_conventions['tenor'] = ql.Period('1Y')
floating_leg_conventions = Conventions.USFloatingLegConventions()


def create_swaption_helper(maturity, length, volatility, curve, fixed_leg_conventions, floating_leg_conventions):
    # fixedFrequency = fixed_leg_conventions.get('frequency', ql.Annual)
    # fixedConvention = fixed_leg_conventions.get('date_rolling_convention', ql.Following)
    fixedLegTenor = fixed_leg_conventions.get('tenor', ql.Period('1Y'))
    floatingFrequency = floating_leg_conventions.get('frequency', ql.Period('6M'))
    fixedDayCount = fixed_leg_conventions.get('dayCount', ql.Thirty360(ql.Thirty360.BondBasis))
    floatingDayCount = floating_leg_conventions.get('dayCount', ql.Actual360())
    floatingConvention = floating_leg_conventions.get('date_rolling_convention', ql.Following)
    floatingSettlementDays = floating_leg_conventions.get('settlement_days', 2)
    floatingEndOfMonth = floating_leg_conventions.get('endOfMonth', False)
    calendar = floating_leg_conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.Settlement))
    currency = floating_leg_conventions.get('currency', ql.USDCurrency())


    maturity = ql.Period(maturity)
    length = ql.Period(length)
    volatility = ql.QuoteHandle(ql.SimpleQuote(volatility))
    index = ql.IborIndex('iborIndex', floatingFrequency, floatingSettlementDays, currency, calendar, floatingConvention, floatingEndOfMonth, floatingDayCount)

    yts = ql.YieldTermStructureHandle(curve)

    return ql.SwaptionHelper(
    maturity, length, volatility, index, fixedLegTenor,
    fixedDayCount, floatingDayCount, yts
    )

create_swaption_helper('5Y', '5Y', 0.0055, curve, fixed_leg_conventions, floating_leg_conventions)



