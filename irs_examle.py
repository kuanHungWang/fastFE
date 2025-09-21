import QuantLib as ql
import numpy as np
import pandas as pd
from util import (
    subset_to_bool,
    get_nearest_fixing_date,
    year_fraction,
    combine_schedule
)
from curve_builder import  bootstrap_curve
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel
from market_data import (
    get_deposit,
    get_swap,
    get_swaption
)

"""Description:
keywords: cancellable, Bermudan exercise, interest rate swap, IRS, libor floating leg, fixing-in-advance
fixed rate cancellable IRS (Libor)
rec fixed leg, 30/360, frequency 6M
pay floating: index: 6M libor, act/360, frequency 6M
cancelable schedule: same as fixed leg frequency
floating leg fixing schedule: 2 days before payment date, fixing-in-advance
tenor: 3Y
fixing rate: 1.8%, notional: 1M USD"""

# contract parameters
fixed_rate = 0.018
notional = 1_000_000
fixing_in_advance = True


# conventions
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
frequency = ql.Period('6M')
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

# prepare market data for curve and model calibration
df_deposit = get_deposit('USD',['1M', '2M', '3M', '6M', '9M'])
df_swap = get_swap('USD',['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

# swaption data
df_swaption = get_swaption('USD',['2Y', '3Y'], ['5Y', '5Y'])


# create curve and calibrate model by swaptions
curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)
hw_model = HullWhiteModel(today, curve)
hw_model.calibrate(df_swaption)


# schedule for IRS, fixed leg and floating leg, and combined schedule. and fixing schedule(2 days before payment date)
terminationDate = calendar.advance(settlementDate, ql.Period(3, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
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

# convert to list
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]

fixings=fixings[0]
print(f'fixings: \n{fixings}')





# fixed cashflows
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))
fixed_cashflows = pd.DataFrame(notional * fixed_rate * year_fraction_rec, index=recSchedule)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')

# floating cashflows
# step 1. get fixing rate of floating index, here are three ways of doing it, all have same result.
# method 1: The easiest way.
fixing_value = fixings.shift(1) if fixing_in_advance else fixings

# method 2: If fixings is not just generated for this leg. For example, floating leg freqency is 6m, but fixing is generated in freqency of 3M for other purposes.
fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paySchedule]  
# method 3: A more robustic versio of 1.2, especially for fixing is not in daily basis, but if fixing is available for every business day, this may not get you truely 2 business days before payment date.
fixingSchedule = [get_nearest_fixing_date(d, fixings.index) for d in paySchedule] 
fixing_value = fixings.loc[fixingSchedule]  
if fixing_in_advance:  # process fixing-in-advance case if True (for method 2 and 3)
    fixing_value = fixing_value.shift(1)
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis] # step 2. get year fraction for pay leg, use np.newaxis to reshape to (n, 1) for broadcast
floating_cashflows = notional * fixing_value.values * year_fraction_pay  # step 3. calculate floating cashflows
floating_cashflows = pd.DataFrame(floating_cashflows, index=paySchedule)  # step 4. convert to dataframe, use paySchedule as index to align with other cashflows.


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