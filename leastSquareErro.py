import QuantLib as ql
import pandas as pd
import numpy as np
from collections import namedtuple
import math
from datetime import datetime, timedelta
from sklearn import linear_model
from typing import List, Tuple, Callable, Dict





def get_nearest_fixing_date(d, obs_index):
    # Returns the greatest date in obs_index that is <= d
    return max([date for date in obs_index if date <= d])

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

class LongstaffSchwartz():
    def __init__(self, cashflows: pd.DataFrame, 
                 discountFactors: pd.DataFrame, 
                 exercise_schedule: pd.Series|List, 
                 exercise_payoff: Callable|np.ndarray|pd.DataFrame,
                 observable: pd.DataFrame):
        self.cashflows = cashflows
        self.discountFactors = discountFactors
        self.exercise_schedule = exercise_schedule
        self.observable = observable
        self.exercise_payoff = exercise_payoff

    def backward_induction(self):
        import numpy as np
        import pandas as pd
        np.set_printoptions(precision=2, suppress=True)
        pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
        self.regressors = []
        valuation = np.zeros(self.cashflows.shape[1])  # shape_single_step
        print(f'valuation.shape: {valuation.shape}')
        survival = pd.DataFrame(
            np.ones(self.cashflows.shape,dtype=bool),  # or proper shape
            index=self.cashflows.index,
            columns=self.cashflows.columns
            
        )
        print('\n ****************Backward Longstaff-Schwartz method begin:*******************')
        for d in reversed(self.cashflows.index):
            print(f'\nTime step {d}')
            current_cf = self.cashflows.loc[d]
            if self.exercise_schedule.loc[d]:
                print('\n  Process exercise')
                print('Valuation of future cf:')
                print(np.round(valuation.values, 2))
                reg = linear_model.LinearRegression()
                nearest_fixing_date = get_nearest_fixing_date(d, self.observable.index)
                print(f'using fixing date: {nearest_fixing_date} for early exercise call date: {d}')
                x = self.observable.loc[nearest_fixing_date].values.reshape(-1, 1)
                reg.fit(x, valuation)
                y = reg.predict(x)
                print(f'Predicted valuation of not exercising: {np.round(y, 2)}')
                exe_payoff = self.exercise_payoff(self.observable.loc[nearest_fixing_date,:].values)
                print(f'payoff of early exercise: {np.round(exe_payoff, 2)}')
                not_exercise = y > exe_payoff
                exercise = y < exe_payoff
                print(f'Whether to exercise: {exercise}')

                optimized = not_exercise * valuation + exercise * exe_payoff
                print('optimized value:')
                print(np.round(optimized.values, 2))
                valuation = current_cf + optimized
                print('cashflow of current step:')
                print(np.round(current_cf.values, 2))
                print('optimized value plus current cf:')
                print(np.round(valuation.values, 2))
                survival.loc[d,:] = not_exercise
                self.regressors.insert(0, reg)
            else:
                print('\n   No early exercise, add current')
                print('Valuation of future cf:')
                print(np.round(valuation, 2))
                valuation = current_cf + valuation
                print('cashflow of current step:')
                print(np.round(current_cf.values, 2))
                print('Futre npv plus current cf:')
                print(np.round(valuation.values, 2))
            valuation = self.discountFactors.loc[d] * valuation
            print('discount:')
            print(np.round(valuation.values, 2))
        
        print(f'valuation of monte carlo simulation: {valuation.mean():,.2f}')
        self.survival = survival

def  calibrate_hull_white_model(term_structure, swaptions):
    
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

    swaptions = [create_swaption_helpers(int(inst['start']), int(inst['length']), float(inst['volatility'])) for (index, inst) in swaptions.iterrows()]

    optimization_method = ql.LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
    end_criteria = ql.EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
    model.calibrate(swaptions, optimization_method, end_criteria)

    a, sigma = model.params()
    print(f'Calibration of hull-white model: a={a}, sigma={sigma}')

    return a, sigma

def generate_HW1F_path(process, index_factory, fixing_date, payment_date, numPaths):
    


    # As hull-white model is a short rate model, underlying rate must generate every day, not only fixing dates.
    frequency = ql.Period('1d')
    all_dates = ql.Schedule(settlement, curve.maxDate(), frequency, calendar, convention, terminationDateConvention, rule, endOfMonth)
    dayCount=ql.Actual360()

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
        fwd_crv = ql.ForwardCurve([d for d in all_dates], underlying, dayCount)
        ts = ql.YieldTermStructureHandle(fwd_crv)
        index=index_factory(ts)
        fixings.append([index.fixing(d) for d in fixingSchedule])
        discountFactors.append([fwd_crv.discount(d) for d in paymentSchedule])
        forward_curves.append(fwd_crv)
        
    underlying_path = np.array(underlying_path).transpose()
    fixings = np.array(fixings).transpose()
    discountFactors = np.array(discountFactors).transpose()
    return underlying_path, fixings, discountFactors, forward_curves

def get_settlement_date(trade_date, settlement_days, calendar):
    return calendar.advance(trade_date,ql.Period(settlement_days, ql.Days))


settlement_days = 2
calendar = ql.TARGET()
currency = ql.EURCurrency()
dayCount=ql.Actual360()
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
date_generation_rule = ql.DateGeneration.Backward
endOfMonth = False


today = ql.Date().todaysDate()
today = ql.Date(19, 6, 2025)
settlement = get_settlement_date(today, settlement_days, calendar)
ql.Settings.instance().evaluationDate = today

# termstructure from zero rates
# todo: bootstrap yield curve from instruments.
dates = [calendar.advance(settlement,ql.Period(y, ql.Years)) for y in [0, 1, 2, 3,4,5,10]]
zeros = [0.015, 0.018, 0.02, 0.022, .025, .03, .035]

curve = ql.ZeroCurve(dates, zeros, dayCount, calendar)
term_structure = ql.YieldTermStructureHandle(curve)



# create schedule
terminationDate = calendar.advance(today,ql.Period(3, ql.Years))
frequency = ql.Period('6M')
convention = ql.ModifiedFollowing
terminationDateConvention = ql.ModifiedFollowing
rule = date_generation_rule

paySchedule = ql.Schedule(settlement, terminationDate, frequency, calendar, convention, terminationDateConvention, rule, endOfMonth)
recSchedule = ql.Schedule(settlement, terminationDate, frequency, calendar, convention, terminationDateConvention, rule, endOfMonth)


paymentSchedule = combine_schedule(paySchedule, recSchedule)
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]

fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]
print(f'today: {today}, settlement: {settlement}')
print('Fixing date, Payment date')
for fixing_date, pay_date in zip(fixingSchedule, paymentSchedule):
    print(f"{fixing_date.year()}-{fixing_date.month()}-{fixing_date.dayOfMonth()}, {pay_date.year()}-{pay_date.month()}-{pay_date.dayOfMonth()}")


swaptions=pd.DataFrame(dict(start=[1,2,3,4,5], length=[5,4,3,2,1], volatility=[0.1148,0.1108,0.1070,0.1021,0.1000]))





a, sigma = calibrate_hull_white_model(term_structure, swaptions)

# HullWhiteProcess

process = ql.HullWhiteProcess(term_structure, a, sigma)

def create_ibor_6M(ts):
    return ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, dayCount, ts)




numPaths = 4
underlying_path, fixings, discountFactors, forward_curves = generate_HW1F_path(process, create_ibor_6M, fixingSchedule, paymentSchedule, numPaths)
# cashflow of interest rate swap dagaFrame version
# pay floating, receive fixed
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]
all_dates = combine_schedule(paySchedule, recSchedule)
fixed_rate = 0.018
notional = 1_000_000
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis]
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))[:,np.newaxis]
fixed_cashflows = notional * fixed_rate * year_fraction_rec

fixed_cashflows = pd.DataFrame(fixed_cashflows, index=recSchedule[1:])
fixed_cashflows = fixed_cashflows.reindex(all_dates)
floating_cashflows = notional * fixings[:-1, :] * year_fraction_pay
floating_cashflows = pd.DataFrame(floating_cashflows, index=paySchedule[1:])
floating_cashflows = floating_cashflows.reindex(all_dates)

net_cashflows = fixed_cashflows.values - floating_cashflows.values  # use numpy array to calculate net cashflows for broadcast.
net_cashflows = pd.DataFrame(net_cashflows, index = all_dates)
net_cashflows = net_cashflows.iloc[1:]

print('\n receive fixed cash flow: ')
print(fixed_cashflows)
print(f'\n pay floating cash flow (with {numPaths} simulation paths): ')
print(floating_cashflows)
print(f'\n net cash flow: ')
print(net_cashflows)

dcf = discountFactors[1:, :]/discountFactors[:-1, :]
dcf = pd.DataFrame(dcf, index = all_dates[1:])
exercise_dates = all_dates[1:-1]
exercisable = pd.Series(
    np.ones(len(exercise_dates), dtype=bool),
    index=exercise_dates
).reindex(net_cashflows.index, fill_value=False)

print('\n call schedule: \n',exercisable)
observations = pd.DataFrame(fixings, index=fixingSchedule).iloc[1:,:]
print('\n Observations(fixing of 6m libor rate): \n',observations)
shape_single_step = (numPaths,)

exercise_payoff = lambda x: np.zeros(shape_single_step)

survival = np.ones((len(exercise_dates), numPaths), dtype=bool)
survival = pd.DataFrame(survival, index=exercise_dates)










        

# OOP version of Longstaff-Schwartz
lse = LongstaffSchwartz(
    cashflows=net_cashflows,
    discountFactors=dcf,
    exercise_schedule=exercisable,
    exercise_payoff=exercise_payoff,
    observable=observations
)
lse.backward_induction()