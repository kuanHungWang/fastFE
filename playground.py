import QuantLib as ql
import pandas as pd
from datetime import datetime
from util import (
    create_USD_deposit_rate_helpers,
    create_USD_swap_rate_helpers,
)
from typing import Literal

def bootstrap_curve(settlementDate, helpers, dayCount, method: Literal['logLinearDiscount', 'logCubicDiscount','linearZero','cubicZero', 'linearForward','splineCubicDiscount']='linearZero'):

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

curve = bootstrap_curve(today, deposit_helpers, ql.Actual360())



schedule = ql.MakeSchedule(today, today + ql.Period(3, ql.Months), ql.Period('1W'))



for d in schedule:
    print(f'{d}: {curve.zeroRate(d, ql.Actual360(), ql.Simple).rate()}')



