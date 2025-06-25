import QuantLib as ql
import numpy as np
import pandas as pd
from util import leg_to_series
def subset_to_bool(subset_dates, full_dates)->pd.Series:
    """
    Return a boolean Series indexed by full_dates, True where the date is in subset_dates, False otherwise.
    subset_dates: list-like or index-like, must be a subset of full_dates
    full_dates: list-like or index-like
    """
    subset_set = set(subset_dates)
    return pd.Series([date in subset_set for date in full_dates], index=full_dates)
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
   

from curve_builder import bootstrap_USD_curve
from util import get_nearest_fixing_date, year_fraction, combine_schedule
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel


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

calendar = ql.JointCalendar(ql.TARGET(), calendar) # add Target as we use Euribor swap fixing.

today = ql.Date().todaysDate()
# today = ql.Date(14, 6, 2025)
today = calendar.advance(today,ql.Period(0, ql.Days))
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')

# bootstrap curve
df_deposit = pd.DataFrame({
'tenor': ['1M', '2M', '3M', '6M', '9M'],
'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})

df_swap = pd.DataFrame({
    'rate': [0.015, 0.018, 0.02, 0.022, 0.025, 0.027, 0.03, 0.032, 0.035],
    'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y']
})



# swaption data
df_swaption = pd.DataFrame({
    'maturity': ['2Y', '3Y', '5Y', '7Y', '10Y', '15Y', '20Y', '20Y'],
    'length': ['5Y', '5Y', '5Y', '5Y', '5Y', '5Y', '5Y', '5Y'],
    'volatility': [0.13, 0.21, 0.12, 0.14, 0.13, 0.07, 0.06, 0.05]
})

curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
print(dayCount.yearFraction(settlementDate, curve.maxDate()))
hw_model = HullWhiteModel(today, curve, 'USD')
hw_model.calibrate(df_swaption)


# schedule
terminationDate = calendar.advance(settlementDate, ql.Period(3, ql.Years))
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
paymentSchedule = combine_schedule(paySchedule, recSchedule)

fixingSchedule = ql.Schedule(settlementDate, terminationDate, ql.Period('1D'), calendar, ql.Following, ql.Following, rule, endOfMonth)
all_dates = ql.Schedule(settlementDate, terminationDate, ql.Period('1D'), ql.NullCalendar(), ql.Following, ql.Following, ql.DateGeneration.Backward, False)

n_path = 2**2

def create_2Y_CMS(ts):
    return ql.EuriborSwapIsdaFixA(ql.Period('2Y'), ts)

def create_ibor_6M(ts):
    return ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, dayCount, ts)


underlying_path, fixings, discountFactors = hw_model.monte_carlo_paths(create_2Y_CMS, fixingSchedule, paymentSchedule, n_path)
# underlying_path, fixings, discountFactors are dataframes with index of ql.Date.


fixed_rate = 0.018
notional = 1_000_000
print(f'fixed_rate: {fixed_rate}')
print(f'notional: {notional}')

# use quantlib to calculate fixed cashflows


paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]

# quantlib fixed cashflows
# fixed_cashflows = ql.FixedRateLeg(recSchedule, dayCount, [notional], [fixed_rate])
# fixed_cashflows = leg_to_series(fixed_cashflows)


year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))
fixed_cashflows = pd.DataFrame(notional * fixed_rate * year_fraction_rec, index=recSchedule)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')
print(f'\nfixings: \n{fixings.mean(axis=1)}')

# range acrual cashflows


start_date = paySchedule[0]
groups=[]
last_n = 3
upper_bound = 0.025
lower_bound = 0.001
rate = 0.03
acruals=[]
notional = 1_000_000
range_acrual_cashflows = pd.DataFrame(np.zeros((len(paySchedule),n_path)),index = paySchedule)
for d in paySchedule[1:]:
    end_date = d
    period_fixing=fixings.loc[(fixings.index>start_date)&(fixings.index<=end_date)].copy()  # get fixing rates withing accrual period
    period_fixing.iloc[-last_n:] = period_fixing.iloc[-1]   # replace last 5 days with last day 
    in_range_days=(period_fixing>lower_bound)&(period_fixing<upper_bound)  # Calculate bool value representing days that is withing range.
    accrual = in_range_days.mean(axis=0)   # Calculate accrual ratio.
    acruals.append(accrual)
    dc = dayCount.yearFraction(start_date, end_date)
    cf_amt = rate * accrual * dc * notional   # calculate cashflow by rate, accrual ratio, daycount, notional.
    groups.append(period_fixing)
    range_acrual_cashflows.loc[d]=cf_amt
    start_date = d

print(f'\nrange_acrual_cashflows: \n{range_acrual_cashflows}')
    

# floating cashflows
fixing_date_map = pd.Series(fixingSchedule, index=paymentSchedule)
fixing_date = fixing_date_map[paySchedule]   # 1. get fixing date from map
fixing_value = pd.DataFrame(fixings.loc[fixing_date].values, index=paySchedule) # 2. get fixing value from fixings with corresponding fixing date
fixing_in_advance = True  # 3. process fixing-in-advance case if True
if fixing_in_advance:
    fixing_value = fixing_value.shift(1)
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis] # 4. get year fraction for pay leg
floating_cashflows = notional * fixing_value * year_fraction_pay # 5. calculate floating cashflows

# ensure same index for case that two leg has different payment schedule
range_acrual_cashflows = range_acrual_cashflows.reindex(paymentSchedule) 
floating_cashflows = floating_cashflows.reindex(paymentSchedule)
print(f'\nfloating_cashflows: \n{floating_cashflows}')
net_cashflows = range_acrual_cashflows - floating_cashflows  
print(f'\nnet cashflows: \n{net_cashflows}')




# print(f'\n net cash flow: ')
# print(net_cashflows)
print(f'\ndiscountFactors: \n {discountFactors}')
print(f'\nshifted discountFactors: \n {discountFactors.shift(1)}')
single_period_dcf = discountFactors/discountFactors.shift(1)
print(f'\nsingle_period_dcf: \n {single_period_dcf}')
exercise_dates = paymentSchedule[1:-1]
exercisable = subset_to_bool(exercise_dates, net_cashflows.index)
print('\n call schedule: \n',exercisable)
observations = fixings  # observation is for linear estimator of longstaff schwartz, irelevant of fixing-in-advance or fixing-in-arrears
print('\n Observations(fixing of 6m libor rate): \n',observations)
exercise_payoff = lambda x: np.zeros(len(x))
lse = LongstaffSchwartz(
    cashflows=net_cashflows.iloc[1:], # remove first row
    discountFactors=single_period_dcf,
    exercise_schedule=exercisable,
    exercise_payoff=exercise_payoff,
    observable=observations
)
lse.backward_induction()