import QuantLib as ql
import numpy as np
import pandas as pd
from util import leg_to_series, subset_to_bool
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
from vol_helper import (
    create_USD_swaption_helpers, create_EUR_swaption_helpers,
    create_JPY_swaption_helpers, create_GBP_swaption_helpers,
    create_CHF_swaption_helpers, create_TWD_swaption_helpers
)

from curve_builder import bootstrap_USD_curve
from util import get_nearest_fixing_date, year_fraction, combine_schedule
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel

from market_data import (get_deposit, get_swap, get_swaption, get_FRA, get_sofr_future)

# conventions
fixed_leg_conventions = Conventions.USFixedLegConventions()
floating_leg_conventions = Conventions.USFloatingLegConventions()
calendar = fixed_leg_conventions['calendar']
date_rolling_convention = fixed_leg_conventions['date_rolling_convention']
date_termination_convention = fixed_leg_conventions['date_termination_convention']
frequency = floating_leg_conventions['frequency']
dayCount = fixed_leg_conventions['dayCounter']
currency = fixed_leg_conventions['currency']
endOfMonth = fixed_leg_conventions['endOfMonth']
rule = fixed_leg_conventions['rule']


today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')

# prepare market data for curve and model calibration
df_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
df_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

# swaption data
df_swaption = get_swaption(['2Y', '3Y'], ['5Y', '5Y'])


# create curve and calibrate model by swaptions
curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
hw_model = HullWhiteModel(today, curve, 'USD')
hw_model.calibrate(df_swaption)


# schedule for IRS, fixed leg and floating leg, and combined schedule. and fixing schedule(2 days before payment date)
terminationDate = calendar.advance(settlementDate, ql.Period(3, ql.Years))
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
paymentSchedule = combine_schedule(paySchedule, recSchedule)  # merge two schedules
fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)

# generate monte carlo paths

# create ibor index factory as input of monte carlo paths generators.
def create_ibor_6M(ts):
    return ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, dayCount, ts)

n_path = 6
underlying_path, fixings, discountFactors = hw_model.monte_carlo_paths([create_ibor_6M], fixingSchedule, paymentSchedule, n_path)
# notes: 
# 1. the resulting underlying_path, fixings, discountFactors are dataframes with index of ql.Date.
# 2. fixings is a list of dataframes, each dataframe is the fixing of ibor index.
# 3. argument of index_factories is a list of functions that return an ibor index.
# 4. the number of fixings in fixings is determined by the number of index_factories.

fixings=fixings[0]
print(f'fixings: \n{fixings}')

# cashflow according to monte carlo paths.
fixed_rate = 0.018
notional = 1_000_000
fixing_in_advance = True
# convert to list
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]

# fixed cashflows
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))
fixed_cashflows = pd.DataFrame(notional * fixed_rate * year_fraction_rec, index=recSchedule)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')

fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paySchedule]  # 1. fixing days only for payschedule
fixing_value = fixings.loc[fixingSchedule]  # 2. get fxing value with fixing days
if fixing_in_advance:  # 3. process fixing-in-advance case if True
    fixing_value = fixing_value.shift(1)
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis] # 4. get year fraction for pay leg
floating_cashflows = notional * fixing_value.values * year_fraction_pay  # 5. calculate floating cashflows
floating_cashflows = pd.DataFrame(floating_cashflows, index=paySchedule)


# ensure same index for case that two leg has different payment schedule
fixed_cashflows = fixed_cashflows.reindex(paymentSchedule) 
print(f'floating_cashflows: \n{floating_cashflows}')
floating_cashflows = floating_cashflows.reindex(paymentSchedule)
net_cashflows = fixed_cashflows.values - floating_cashflows  
print(f'\nnet cashflows: \n{net_cashflows}')

# prepare data for LSE
single_period_dcf = discountFactors/discountFactors.shift(1)
exercise_dates = paymentSchedule[1:-1]
exercisable = subset_to_bool(exercise_dates, net_cashflows.index)  # convert from a list of dates to a boolean series
observations = fixings  # observation is for linear estimator of longstaff schwartz, irelevant of fixing-in-advance or fixing-in-arrears
exercise_payoff = lambda x: np.zeros(len(x))   # The cashflow of calling(cancelling) the IRS is 0.
lse = LongstaffSchwartz(
    cashflows=net_cashflows.iloc[1:], # remove first row
    discountFactors=single_period_dcf,
    exercise_schedule=exercisable,
    exercise_payoff=exercise_payoff,
    observable=observations
)
lse.backward_induction()
print(f'\nconfidence interval: {lse.confidence_interval()}')
print(f'\nsurvival probability: {lse.survival_probability()}')
print(f'\nexercise cashflows: \n{lse.exercise_cashflows()}')