import QuantLib as ql
import numpy as np
import pandas as pd
from util import (
    subset_to_bool,
    get_nearest_fixing_date,
    year_fraction,
    combine_schedule
)
from curve_builder import bootstrap_curve
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel
from market_data import (
    get_deposit,
    get_swap,
    get_swaption
)
from type_hint import (
    ScheduleCreator,
    CurveCreator,
    IndexFactoriesCreator,
    CashflowsCreator,
    ExercisePayoffCreator,
    ExercisableCreator,
    DataFrameCreator
)
    

# An example of interest rate linked product using Hull White model and monte carlo simulation to calculate fair value.
# Product term sheet:
# 5Y-2Y CMS spread cancellable IRS(libor floating leg)
# rec spread of 5Y-2Y CMS, 30/360, frequency 1Y, fixing-in-advance(2 business days before payment date)
# pay 6M Libor, act/360, frequency 6M, fixing-in-advance(2 business days before payment date)
# cancelable schedule: starting from year 2, yearly by cms spread receiver. (you are the option buyer)



# contract parameters
fixed_rate = 0.018
notional = 1_000_000
fixing_in_advance = True
tenor = 4
PAY_FREQ = '6M'
REC_FREQ = '1Y'
CANCEL_FREQ = '1Y'
non_call_period = 2

# number of paths for monte carlo simulation
n_path = 6

calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
# set evaluation date
valuationDate = ql.Date().todaysDate()
valuationDate = calendar.advance(valuationDate,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
# set settlement date
settlementDate = calendar.advance(valuationDate,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = valuationDate
print(f' trade date: {valuationDate}')

# Implementing Nodes

def CreateUSDCurve():
    df_deposit = get_deposit('USD', ['1M', '2M', '3M', '6M', '9M'])
    df_swap = get_swap('USD', ['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])
    curve = bootstrap_curve(valuationDate, deposit=df_deposit, swap=df_swap)
    return {'curve': curve}

def CreateUSDSwaptionData():
    swaption_volatility = get_swaption('USD', ['2Y', '3Y'], ['5Y', '5Y'])
    return {'swaption_volatility':swaption_volatility}

def CustomizedScheduleCreator():
    date_rolling_convention = ql.ModifiedFollowing
    date_termination_convention = ql.ModifiedFollowing
    pay_frequency = ql.Period(PAY_FREQ)
    rec_frequency = ql.Period(REC_FREQ)
    rule = ql.DateGeneration.Forward
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
    cancel_start_date = calendar.advance(settlementDate, ql.Period(non_call_period))
    cancel_frequency = ql.Period(CANCEL_FREQ)
    cancelSchedule = ql.Schedule(cancel_start_date, terminationDate, cancel_frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
    cancelSchedule = [d for d in cancelSchedule][: -1]  
    return {'payment_schedule': paymentSchedule, 'fixing_schedule': fixingSchedule, 'cancel_schedule': cancelSchedule, 'pay_schedule': paySchedule, 'rec_schedule': recSchedule}

def CreateExercisable(cancel_schedule, payment_schedule):
    return {'exercisable': subset_to_bool(cancel_schedule, payment_schedule)}

def CreateIndexFactories():
    def create_ibor_6M(ts):
        return ql.IborIndex('Libor_6M', ql.Period('6m'), 2, ql.USDCurrency(), calendar, ql.ModifiedFollowing, True, ql.Thirty360(ql.Thirty360.USA), ts)
    def create_cms_5Y(ts):
        return ql.UsdLiborSwapIsdaFixAm(ql.Period('5y'), ts)
    def create_cms_2Y(ts):
        return ql.UsdLiborSwapIsdaFixAm(ql.Period('2y'), ts)
    return {'Libor_6M':create_ibor_6M, 'CMS_5Y':create_cms_5Y, 'CMS_2Y':create_cms_2Y}

def CreateCashFlows(fixings, payment_schedule, pay_schedule, rec_schedule):
    libor_fixings=fixings['Libor_6M']  
    cms_5Y_fixings=fixings['CMS_5Y']
    cms_2Y_fixings=fixings['CMS_2Y']

    dayCount = ql.Thirty360(ql.Thirty360.USA)
    # Libor cashflows
    # Get fixing rate applies to each corresponding payment date.
    corresponding_fixing_schedule = [get_nearest_fixing_date(d, libor_fixings.index) for d in pay_schedule] 
    libor_fixing_value = libor_fixings.loc[corresponding_fixing_schedule]  
    if fixing_in_advance:  # process fixing-in-advance case if True 
        libor_fixing_value = libor_fixing_value.shift(1)  # Note: the first row of all fixing_value is NaN, but this is fine since we don't have payment in the first date.
    # Apply the fixing values to calculate libor cashflows
    year_fraction_pay = np.array(year_fraction(pay_schedule, dayCount, accoumulative=False))[:,np.newaxis] # use np.newaxis to reshape to (n, 1) for broadcast
    libor_cashflows = notional * libor_fixing_value.values * year_fraction_pay  # calculate floating cashflows
    libor_cashflows = pd.DataFrame(libor_cashflows, index=pay_schedule)  # convert to dataframe, use paySchedule as index to align with other cashflows.
    print(f'\nlibor_cashflows: \n{libor_cashflows}')


    # Get fixing rate applies to each corresponding payment date.
    corresponding_fixing_schedule = [get_nearest_fixing_date(d, cms_5Y_fixings.index) for d in rec_schedule] 
    cms_5Y_fixing_value = cms_5Y_fixings.loc[corresponding_fixing_schedule]
    cms_2Y_fixing_value = cms_2Y_fixings.loc[corresponding_fixing_schedule]
    if fixing_in_advance:  # process fixing-in-advance case if True 
        cms_5Y_fixing_value = cms_5Y_fixing_value.shift(1)
        cms_2Y_fixing_value = cms_2Y_fixing_value.shift(1)
    # Apply the fixing values to calculate cms spread cashflows
    year_fraction_rec = np.array(year_fraction(rec_schedule, dayCount, accoumulative=False))[:,np.newaxis]
    cms_spread = cms_5Y_fixing_value - cms_2Y_fixing_value
    cms_spread_cashflows = notional * cms_spread.values * year_fraction_rec
    cms_spread_cashflows = pd.DataFrame(cms_spread_cashflows, index=rec_schedule)
    print(f'\ncms_spread_cashflows: \n{cms_spread_cashflows}')

    # Reindex both cashflow with paymentSchedule to calculate net cashflow in correct periods.
    cms_spread_cashflows = cms_spread_cashflows.reindex(payment_schedule).fillna(0)
    libor_cashflows = libor_cashflows.reindex(payment_schedule).fillna(0)
    net_cashflows = pd.DataFrame(cms_spread_cashflows.values - libor_cashflows.values, index=payment_schedule)  # use .values to broadcast.
    print(f'\nnet cashflows: \n{net_cashflows}')  # note: the first row is 0, because we don't have payment in the first date.
    return {'net_cashflows': net_cashflows, 'libor_cashflows': libor_cashflows, 'cms_spread_cashflows': cms_spread_cashflows}

def CreateExercisePayoff():
    return {'exercise_payoff': lambda x: np.zeros(len(x))}   # The cashflow of calling(cancelling) the contract, in this case is 0.


# Defining Nodes
create_usd_curve: CurveCreator = CreateUSDCurve
create_usd_swaption_data: DataFrameCreator = CreateUSDSwaptionData
create_customized_schedule: ScheduleCreator = CustomizedScheduleCreator
create_exercisable: ExercisableCreator = CreateExercisable
create_index_factories: IndexFactoriesCreator = CreateIndexFactories
cashflows_creator: CashflowsCreator = CreateCashFlows
exercise_payoff_creator: ExercisePayoffCreator = CreateExercisePayoff


# Link and execute nodes(Also where graph is built)
df_swaption = create_usd_swaption_data()
curve = create_usd_curve()
hw_model = HullWhiteModel(valuationDate, curve['curve'])
hw_model.calibrate(df_swaption['swaption_volatility'])
schedules = create_customized_schedule()
exercisable = create_exercisable(schedules['cancel_schedule'], schedules['payment_schedule'])
index_factories = create_index_factories()
underlying_path, fixings, discount_factors = hw_model.monte_carlo_paths(index_factories=index_factories, fixingSchedule=schedules['fixing_schedule'], paymentSchedule=schedules['payment_schedule'], numPaths=n_path)
cashflows = cashflows_creator(fixings, schedules['payment_schedule'], schedules['pay_schedule'], schedules['rec_schedule'])
exercise_payoff = exercise_payoff_creator()
lse = LongstaffSchwartz(
    cashflows=cashflows['net_cashflows'],
    discountFactors=discount_factors,
    exercisable=exercisable['exercisable'],
    exercise_payoff=exercise_payoff['exercise_payoff'],
    observable=fixings['Libor_6M']
)
lse.backward_induction()

print(f'\nconfidence interval: {lse.confidence_interval()}')
print(f'\nsurvival probability: {lse.survival_probability()}')
print(f'\nexercise cashflows: \n{lse.exercise_cashflows()}')