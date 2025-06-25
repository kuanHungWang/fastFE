import QuantLib as ql
import pandas as pd
import numpy as np
from collections import namedtuple
import math
from datetime import datetime, timedelta
from sklearn import linear_model
def year_fraction(schedule, dayCount, accoumulative=False):
    schedule = [d for d in schedule]
    if accoumulative:
        return [dayCount.yearFraction(schedule[0],d) for d in schedule]
    else:
        return [dayCount.yearFraction(d1, d2) for d1, d2 in zip(schedule[:-1], schedule[1:])]
        
def combine_schedule(*schedules):
    all_schedule = set()
    for scd in schedules:
        s = {d for d in scd}
        all_schedule = all_schedule.union(s)
    return sorted(all_schedule)



calendar = ql.TARGET()
dayCount=ql.Actual360()
today = ql.Date().todaysDate()
today = ql.Date(19, 6, 2025)
today = calendar.advance(today,ql.Period(0, ql.Days))
settlement = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today

# termstructure from zero rates
# todo: bootstrap yield curve from instruments.
dates = [calendar.advance(settlement,ql.Period(y, ql.Years)) for y in [0, 1, 2, 3,4,5,10]]
zeros = [0.015, 0.018, 0.02, 0.022, .025, .03, .035]

curve = ql.ZeroCurve(dates, zeros, dayCount, calendar)
term_structure = ql.YieldTermStructureHandle(curve)


# Assume 'curve' is your QuantLib YieldTermStructure object
# and 'settlement' is your simulation start date

dayCount = curve.dayCounter()
max_date = curve.maxDate()
reference_date = curve.referenceDate()  # or use 'settlement' if that's your convention

max_time = dayCount.yearFraction(reference_date, max_date)
print(f"Curve max time (years): {max_time}")
print(f"Curve reference date: {reference_date}")
print(f"Curve max date: {max_date}")



# calibrate parametors of hull-white model from swaptions
index = ql.Euribor1Y(term_structure)
CalibrationData = namedtuple("CalibrationData", 
                             "start, length, volatility")

data = [CalibrationData(1, 5, 0.1148),
        CalibrationData(2, 4, 0.1108),
        CalibrationData(3, 3, 0.1070),
        CalibrationData(4, 2, 0.1021),
        CalibrationData(5, 1, 0.1000 )]

model = ql.HullWhite(term_structure);
engine = ql.JamshidianSwaptionEngine(model)

def create_swaption_helpers(maturity, length , volatility):
    swaption= ql.SwaptionHelper(ql.Period(maturity, ql.Years),
                             ql.Period(length, ql.Years),
                             ql.QuoteHandle(ql.SimpleQuote(volatility)),
                             index,
                             ql.Period('1Y'),
                             ql.Thirty360(ql.Thirty360.NASD),
                             ql.Actual360(),
                             term_structure)
    swaption.setPricingEngine(engine)
    return swaption

swaptions = [create_swaption_helpers(inst.start, inst.length, inst.volatility) for inst in data]

optimization_method = ql.LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
end_criteria = ql.EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
model.calibrate(swaptions, optimization_method, end_criteria)

a, sigma = model.params()
print(f'Calibration of hull-white model: a={a}, sigma={sigma}')

# create schedule
calendar = ql.TARGET()
today = ql.Date().todaysDate()
settlement = calendar.advance(today,ql.Period(2, ql.Days))
terminationDate = calendar.advance(today,ql.Period(3, ql.Years))
frequency = ql.Period('6M')
convention = ql.ModifiedFollowing
terminationDateConvention = ql.ModifiedFollowing
rule = ql.DateGeneration.Backward
endOfMonth = False
paySchedule = ql.Schedule(settlement, terminationDate, ql.Period('6M'), calendar, convention, terminationDateConvention, rule, endOfMonth)
recSchedule = ql.Schedule(settlement, terminationDate, ql.Period('6M'), calendar, convention, terminationDateConvention, rule, endOfMonth)


paymentSchedule = combine_schedule(paySchedule, recSchedule)
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]

fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]
# print(f'today: {today}, settlement: {settlement}')
# print('Fixing date, Payment date')
# for fixing_date, pay_date in zip(fixingSchedule, paymentSchedule):
#     print(f"{fixing_date.year()}-{fixing_date.month()}-{fixing_date.dayOfMonth()}, {pay_date.year()}-{pay_date.month()}-{pay_date.dayOfMonth()}")


# HullWhiteProcess
euribor_6m=ql.IborIndex('MyIndex', ql.Period('6m'), 2, ql.EURCurrency(), ql.TARGET(), ql.ModifiedFollowing, True, ql.Actual360())

process = ql.HullWhiteProcess(term_structure, a, sigma)

# As hull-white model is a short rate model, underlying rate must generate every day, not only fixing dates.
frequency = ql.Period('1d')
all_dates = ql.Schedule(settlement, curve.maxDate(), frequency, calendar, convention, terminationDateConvention, rule, endOfMonth)

print(f'all_dates: first date: {all_dates[0]}, last date: {all_dates[-1]}')
print(f'time in year:{dayCount.yearFraction(all_dates[0], all_dates[-1])}')


timestep, length, numPaths = 24, 2, 2**2
dimension = process.factors()
n_steps = len(all_dates)-1
time_grid = year_fraction(all_dates, dayCount, accoumulative=True)
rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)




underlying_path = []
forward_curves=[]
fixings = []
discountFactors = []
for i in range(numPaths):
    samplePath = pathGenerator.next()
    values = samplePath.value()
    underlying = values[0]
    underlying = [s for s in underlying]
    underlying_path.append(underlying)
    fwd_crv = ql.ForwardCurve([d for d in all_dates], underlying, ql.Actual360())
    ts = ql.YieldTermStructureHandle(fwd_crv)
    index=ql.IborIndex('MyIndex', ql.Period('6m'), 2, ql.EURCurrency(), ql.TARGET(), ql.ModifiedFollowing, True, ql.Actual360(), ts)
    fixings.append([index.fixing(d) for d in fixingSchedule])
    discountFactors.append([fwd_crv.discount(d) for d in paymentSchedule])
    forward_curves.append(fwd_crv)
    
underlying_path = np.array(underlying_path).transpose()
fixings = np.array(fixings).transpose()
discountFactors = np.array(discountFactors).transpose()
print(f'underlying_path.shape: {underlying_path.shape}')
print(f'fixings.shape: {fixings.shape}')



# cashflow of interest rate swap
# pay floating, receive fixed
fixed_rate = 0.02
notional = 1_000_000

yf = np.array(year_fraction(paymentSchedule, dayCount, accoumulative=False))[:,np.newaxis]
print(f'yf.shape: {yf.shape}')
fixed_cashflows = notional * fixed_rate * yf
print(f'fixed_cashflows.shape: {fixed_cashflows.shape}')
floating_cashflows = notional * fixings[:-1, :] * yf # fixing in advance so use fixings[:-1]
net_cashflows = fixed_cashflows - floating_cashflows
print(f'net_cashflows.shape: {net_cashflows.shape}')



# Longstaff-Schwartz method
# V(t) = CF(t) + max(E[discounted V(t+dt)|F(t)], 0)
# V(T) = CF(T)
shape = (numPaths,)
iter_dates=fixingSchedule[1:]
exercise_dates = fixingSchedule[1:]
observations = fixings[1:, :]
exercise_payoff = lambda x: np.zeros(shape)
valuation = np.zeros(shape)
survival = np.ones((len(exercise_dates), numPaths), dtype=bool)
d_dcf = discountFactors[1:, :]/discountFactors[:-1, :]
regressors=[]

print(f'number of exercise_dates: {len(exercise_dates)}')
print(f'valuation.shape: {valuation.shape}')
print(f'survival.shape: {survival.shape}')
print(f'd_dcf.shape: {d_dcf.shape}')

for i in reversed(range(len(iter_dates))):
    date = iter_dates[i]
    print(f'\nTime step {i}, date: {date}')
    print(f'Valuation from next step:{valuation}')
    if date in exercise_dates:
        print(f'  Process exercise')
        reg = linear_model.LinearRegression()
        x = observations[i,:].reshape(-1, 1)
        reg.fit(x, valuation)
        y = reg.predict(x)
        print(f'Estimated next period valuation: {y}')
        exe_payoff = exercise_payoff(observations[i,:])
        print(f'payoff of early exercise: {exe_payoff}')
        not_exercise = y > exe_payoff
        exercise = y < exe_payoff
        print(f'Whether to exercise: {exercise}')
        print(f'cashflow of current step: {net_cashflows[i,:]}')
        valuation = d_dcf[i,:] * (net_cashflows[i,:] + not_exercise * valuation + exercise * exe_payoff)
    else:
        valuation = d_dcf[i,:] * (net_cashflows[i,:] + valuation)
    survival[i,:] = not_exercise
    regressors.insert(0,reg)
print(valuation.mean())

# cashflow of interest rate swap dagaFrame version
# pay floating, receive fixed
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]
all_dates = combine_schedule(paySchedule, recSchedule)
fixed_rate = 0.02
notional = 1_000_000
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis]
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))[:,np.newaxis]
fixed_cashflows = notional * fixed_rate * year_fraction_rec
print(f'fixed_cashflows.shape: {fixed_cashflows.shape}')
fixed_cashflows_df = pd.DataFrame(fixed_cashflows, index=recSchedule[1:])
fixed_cashflows_df = fixed_cashflows_df.reindex(all_dates)
floating_cashflows = notional * fixings[:-1, :] * year_fraction_pay
floating_cashflows_df = pd.DataFrame(floating_cashflows, index=paySchedule[1:])
floating_cashflows_df = floating_cashflows_df.reindex(all_dates)
net_cashflows = fixed_cashflows_df.values - floating_cashflows_df.values
net_cashflows_df = pd.DataFrame(net_cashflows, index = all_dates)
net_cashflows_df = net_cashflows_df.iloc[1:]
print('fixed_cashflows_df')
print(fixed_cashflows_df)
print('floating_cashflows_df')
print(floating_cashflows_df)
print('net_cashflows_df')
print(net_cashflows_df)

dcf = discountFactors[1:, :]/discountFactors[:-1, :]
dcf_df = pd.DataFrame(dcf, index = all_dates[1:])
exercise_dates = all_dates[1:-1]
exercisable = pd.Series(index=exercise_dates, data=np.ones(len(exercise_dates), dtype=bool)).reindex(net_cashflows_df.index).fillna(False)
print('exercisable: \n',exercisable)
observations = pd.DataFrame(fixings, index=fixingSchedule).iloc[1:,:]
print('observations: \n',observations)
shape_single_step = (numPaths,)

exercise_payoff = lambda x: np.zeros(shape_single_step)

survival = np.ones((len(exercise_dates), numPaths), dtype=bool)
survival_df = pd.DataFrame(survival, index=exercise_dates)
print(f'valuation.shape: {valuation.shape}')
print('survival: \n', survival_df)

def get_nearest_fixing_date(d, obs_index):
    # Returns the greatest date in obs_index that is <= d
    return max([date for date in obs_index if date <= d])


valuation = np.zeros(shape_single_step)
for d in reversed(net_cashflows_df.index):
    print(f'\nTime step {d}')
    if exercisable.loc[d]:
        print(f'  Process exercise')
        reg = linear_model.LinearRegression()
        nearest_fixing_date = get_nearest_fixing_date(d, observations.index)
        x = observations.loc[nearest_fixing_date].values.reshape(-1, 1)
        reg.fit(x, valuation)
        y = reg.predict(x)
        print(f'Estimated next period valuation: {y}')
        exe_payoff = exercise_payoff(observations.loc[nearest_fixing_date,:].values)
        print(f'payoff of early exercise: {exe_payoff}')
        not_exercise = y > exe_payoff
        exercise = y < exe_payoff
        print(f'Whether to exercise: {exercise}')
        print(f'cashflow of current step: {net_cashflows_df.loc[d,:]}')
        valuation = dcf_df.loc[d] * (net_cashflows_df.loc[d] + not_exercise * valuation + exercise * exe_payoff)
    else:
        valuation = dcf_df.loc[d] * (net_cashflows_df.loc[d] + valuation)
    survival_df.loc[d,:] = not_exercise
    regressors.insert(0,reg)
print(valuation.mean())


