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

curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers, ql.Actual360())


curve = bootstrap_curve(today, ql.Actual360(), deposit=(df_deposit, Conventions.USFixedLegConventions()), swap=(df_swap, Conventions.USFixedLegConventions(), Conventions.USFloatingLegConventions()))
curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
curve = bootstrap_EUR_curve(today, deposit=df_deposit, swap=df_swap)
curve = bootstrap_JPY_curve(today, deposit=df_deposit, swap=df_swap)
curve = bootstrap_GBP_curve(today, deposit=df_deposit, swap=df_swap)
curve = bootstrap_TWD_curve(today, deposit=df_deposit, swap=df_swap)
schedule = ql.MakeSchedule(today, today + ql.Period(3, ql.Months), ql.Period('1W'))


print(curve.dayCounter())
for d in schedule:
    print(f'{d}: {curve.zeroRate(d, curve.dayCounter(), ql.Simple).rate()}')



