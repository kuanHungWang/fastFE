import QuantLib as ql
import pandas as pd
from datetime import datetime
from rate_helpers import (
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
from conventions import Conventions
from typing import Literal, Tuple
from curve_builder import bootstrap_curve_with_instrument_helpers, bootstrap_curve
from swaption_helper import (create_swaption_helper, 
create_USD_swaption_helpers, create_EUR_swaption_helpers,
create_JPY_swaption_helpers, create_GBP_swaption_helpers,
create_CHF_swaption_helpers, create_TWD_swaption_helpers)
   

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


df_swaption = pd.DataFrame({
    'maturity': ['2Y', '3Y'],
    'length': ['5Y', '5Y'],
    'volatility': [0.0055, 0.0055]
})
term_structure = ql.YieldTermStructureHandle(curve)

model = ql.HullWhite(term_structure);
engine = ql.JamshidianSwaptionEngine(model)
swaption_helpers = create_swaption_helper(df_swaption, curve, engine, fixed_leg_conventions, floating_leg_conventions)
swaption_helpers = create_USD_swaption_helpers(df_swaption, curve, engine)
swaption_helpers = create_EUR_swaption_helpers(df_swaption, curve, engine)
swaption_helpers = create_JPY_swaption_helpers(df_swaption, curve, engine)
swaption_helpers = create_GBP_swaption_helpers(df_swaption, curve, engine)
swaption_helpers = create_CHF_swaption_helpers(df_swaption, curve, engine)
swaption_helpers = create_TWD_swaption_helpers(df_swaption, curve, engine)

optimization_method = ql.LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
end_criteria = ql.EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
model.calibrate(swaption_helpers, optimization_method, end_criteria)

print(model.params())

