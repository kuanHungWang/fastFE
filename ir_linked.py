import QuantLib as ql
import numpy as np
import pandas as pd
from util import (
    subset_to_bool,
    get_nearest_fixing_date,
    year_fraction,
    combine_schedule,
    leg_to_series
)
from datetime import datetime
from rate_helpers import (
    to_ql_date,
    get_settlement_date,
    create_deposit_rate_helpers,
    create_fra_rate_helpers,
    create_swap_rate_helpers,
    create_sofr_future_rate_helpers,
    create_OIS_helper,
    create_bond_helper,
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
    create_EUR_OIS_helpers,
    create_GBP_OIS_helpers,
    create_JPY_OIS_helpers,
    create_CHF_OIS_helpers,
    create_USD_FRA_helpers,
    create_EUR_FRA_helpers,
    create_CHF_FRA_helpers,
    create_GBP_FRA_helpers,
    create_JPY_FRA_helpers
)
from curve_builder import (
    bootstrap_curve_with_instrument_helpers,
    bootstrap_curve,
    bootstrap_USD_curve,
    bootstrap_EUR_curve,
    bootstrap_JPY_curve,
    bootstrap_GBP_curve,
    bootstrap_TWD_curve
)
from conventions import Conventions
from typing import Literal, Tuple, Callable, Dict, List
from vol_helper import (
    create_black_vol_curve,
    create_black_vol_surface,
    create_heston_model_helper,
    create_swaption_helper,
    create_USD_swaption_helpers,
    create_EUR_swaption_helpers,
    create_JPY_swaption_helpers,
    create_GBP_swaption_helpers,
    create_CHF_swaption_helpers,
    create_TWD_swaption_helpers
)
from leastSquareError import LongstaffSchwartz
from models import (
    calibration_detail,
    GarmanKohlagenProcessModel,
    BlackScholesMertonModel,
    HullWhiteModel,
    HestonModel,
    MultiAssetModel
)
from market_data import (
    get_deposit,
    get_swap,
    get_swaption,
    get_OIS,
    get_FRA,
    get_sofr_future,
    get_volatility_surface,
    get_price,
    get_dividend_rate
)

# An example of interest rate linked product using Hull White model and monte carlo simulation to calculate fair value.

# Step 1. Set up parameters
# contract parameters
fixed_rate = 0.018
notional = 1_000_000
fixing_in_advance = True
tenor = 3
pay_frequency = '6M'
rec_frequency = '1Y'

# number of paths for monte carlo simulation
n_path = 6

# conventions
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
pay_frequency = ql.Period(pay_frequency)
rec_frequency = ql.Period(rec_frequency)
dayCount = ql.Thirty360(ql.Thirty360.USA)
currency = ql.USDCurrency()
rule = ql.DateGeneration.Forward

# set evaluation date
today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')

# Step 2. Prepare market data
# Market data to bootstrap curve.
df_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
df_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

# swaption data to calibrate Hull White model
df_swaption = get_swaption(['2Y', '3Y'], ['5Y', '5Y'])


# Step 3. Create curve and model
curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
hw_model = HullWhiteModel(today, curve, 'USD')
hw_model.calibrate(df_swaption)

# Step 4. Create Schedules
# Create payment schedules for fixed leg and floating leg, and fixing schedule of floating leg(2 business days before payment date)
terminationDate = calendar.advance(settlementDate, ql.Period(tenor, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
paySchedule = ql.Schedule(settlementDate, terminationDate, pay_frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, rec_frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
# Note: the schedule created by ql.Schedule include settlement date, this behavior cowork with year_fraction() which always has 0 in first value.
paymentSchedule = combine_schedule(paySchedule, recSchedule)  # merge two schedules
fixingSchedule = [calendar.advance(d, ql.Period(-2, ql.Days)) for d in paySchedule]  # fixing schedule(2 business days before payment date)
# convert original quantlib schedule object to list to use in pandas index.
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]
# Notes: no need to convert ql.Date to pd.Timestamp, because pd.DataFrame can handle ql.Date as index.


# Step 5. Generate Cashflows based on monte carlo paths

# create ibor index factory as input of monte carlo paths generators.
def create_ibor_6M(ts):
    return ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, dayCount, ts)
# generate paths by Hull White model
underlying_path, fixings, discountFactors = hw_model.monte_carlo_paths(index_factories=[create_ibor_6M], fixingSchedule=fixingSchedule, paymentSchedule=paymentSchedule, numPaths=n_path)
fixings=fixings[0]  # select the first fixing, because we only have one index factory.
print(f'paths of fixings: \n{fixings}')


# fixed cashflows
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))
# Note: year_fraction() has 0 in first value, this cowork with schedule created by ql.Schedule which include settlement date, which usuallay has no cashflow.
fixed_cashflows = pd.DataFrame(notional * fixed_rate * year_fraction_rec, index=recSchedule)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')

# floating cashflows
# Get fixing rate applies to each corresponding payment date.
corresponding_fixing_schedule = [get_nearest_fixing_date(d, fixings.index) for d in paySchedule] 
fixing_value = fixings.loc[corresponding_fixing_schedule]  
if fixing_in_advance:  # process fixing-in-advance case if True 
    fixing_value = fixing_value.shift(1)  # Note: the first row of fixing_value is NaN, but this is fine since we don't have payment in the first date.

# Apply the fixing values to calculate floating cashflows
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis] # use np.newaxis to reshape to (n, 1) for broadcast
floating_cashflows = notional * fixing_value.values * year_fraction_pay  # calculate floating cashflows
floating_cashflows = pd.DataFrame(floating_cashflows, index=paySchedule)  # convert to dataframe, use paySchedule as index to align with other cashflows.
print(f'floating_cashflows: \n{floating_cashflows}')


# Reindex both cashflow with paymentSchedule to calculate net cashflow in correct periods.
fixed_cashflows = fixed_cashflows.reindex(paymentSchedule).fillna(0)
floating_cashflows = floating_cashflows.reindex(paymentSchedule).fillna(0)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')
print(f'\nfloating_cashflows: \n{floating_cashflows}')
net_cashflows = pd.DataFrame(fixed_cashflows.values - floating_cashflows.values, index=paymentSchedule)  # use .values to broadcast.
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