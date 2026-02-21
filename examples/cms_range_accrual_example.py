import QuantLib as ql
import numpy as np
import pandas as pd
from fastFE.util import (
    subset_to_bool,
    year_fraction,
    combine_schedule
)
from fastFE.curve_builder import bootstrap_curve
from fastFE.leastSquareError import LongstaffSchwartz
from fastFE.models import HullWhiteModel

"""Description:
keywords: range accrual, interest rate linked, cms, constant maturity swap, fixed leg, libor floating leg, fixing-in-advance, cancellable, Bermudan exercise 
tenor 3Y
pay 6m libor, act/360, fixing-in-advance
rec 2y cms range accrual, 30/360, frequency 6M
upper bound 2.5%, lower bound 0.1%, rate 3%
notional 1M USD
cancelable schedule: same as fixed leg frequency"""

# contract parameters
fixed_rate = 0.018
notional = 1_000_000

# conventions
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
frequency = ql.Period('6M')
dayCount = ql.Thirty360(ql.Thirty360.USA)
currency = ql.USDCurrency()
rule = ql.DateGeneration.Forward

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
    'maturity': ['2Y', '3Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y'],
    'length': ['5Y', '5Y', '5Y', '5Y', '5Y', '5Y', '5Y', '5Y'],
    'volatility': [0.13, 0.21, 0.12, 0.14, 0.13, 0.07, 0.06, 0.05]
})

curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)
print(dayCount.yearFraction(settlementDate, curve.maxDate()))
hw_model = HullWhiteModel(today, curve)
hw_model.calibrate(df_swaption)


# schedule
terminationDate = calendar.advance(settlementDate, ql.Period(3, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
paymentSchedule = combine_schedule(paySchedule, recSchedule)

fixingSchedule = ql.Schedule(today, terminationDate, ql.Period('1D'), calendar, ql.Following, ql.Following, rule, endOfMonth)
all_dates = ql.Schedule(settlementDate, terminationDate, ql.Period('1D'), ql.NullCalendar(), ql.Following, ql.Following, ql.DateGeneration.Backward, False)

n_path = 2**2

def create_2Y_CMS(ts):
    return ql.EuriborSwapIsdaFixA(ql.Period('2Y'), ts)

def create_ibor_6M(ts):
    return ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, dayCount, ts)


underlying_path, fixings, discountFactors = hw_model.monte_carlo_paths({"CMS":create_2Y_CMS, "libor":create_ibor_6M}, fixingSchedule, paymentSchedule, n_path)
# underlying_path, fixings, discountFactors are dataframes with index of ql.Date.

paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]









print(f'paySchedule: \n{paySchedule}')
print(f'recSchedule: \n{recSchedule}')

year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))
fixed_cashflows = pd.DataFrame(notional * fixed_rate * year_fraction_rec, index=recSchedule)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')




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
cms_fixings = fixings['CMS']
for d in paySchedule[1:]:
    end_date = d
    period_fixing=cms_fixings.loc[(cms_fixings.index>start_date)&(cms_fixings.index<=end_date)].copy()  # get fixing rates withing accrual period
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
libor_fixings = fixings['libor']
libor_fixing_schedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]
print(f'\nlibor_fixings: \n{len(libor_fixings)}')
fixing_date_map = pd.Series(libor_fixing_schedule, index=paymentSchedule)
print(f'\nfixing_date_map: \n{fixing_date_map}')
fixing_date = fixing_date_map[paySchedule]   # 1. get fixing date from map
print(f'\nfixing_date: \n{fixing_date}')
fixing_value = pd.DataFrame(libor_fixings.loc[fixing_date].values, index=paySchedule) # 2. get fixing value from fixings with corresponding fixing date
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
observations = cms_fixings  # observation is for linear estimator of longstaff schwartz, irelevant of fixing-in-advance or fixing-in-arrears
print('\n Observations(fixing of 6m libor rate): \n',observations)
exercise_payoff = lambda x: np.zeros(len(x))
lse = LongstaffSchwartz(
    cashflows=net_cashflows.iloc[1:], # remove first row
    discountFactors=single_period_dcf,
    exercisable=exercisable,
    exercise_payoff=exercise_payoff,
    observable=observations
)
lse.backward_induction()
print(f'\nconfidence interval: {lse.confidence_interval()}')
print(f'\nsurvival probability: {lse.survival_probability()}')
print(f'\nexercise cashflows: \n{lse.exercise_cashflows()}')
