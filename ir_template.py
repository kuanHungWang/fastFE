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
    ExerciseScheduleCreator,
    DataFrameCreator
)
    

# An example of interest rate linked product using Hull White model and monte carlo simulation to calculate fair value.
# Product term sheet:
# 5Y-2Y CMS spread cancellable IRS(libor floating leg)
# rec spread of 5Y-2Y CMS, 30/360, frequency 1Y, fixing-in-advance(2 business days before payment date)
# pay 6M Libor, act/360, frequency 6M, fixing-in-advance(2 business days before payment date)
# cancelable schedule: starting from year 2, yearly by cms spread receiver. (you are the option buyer)



# Step 1. Set up parameters, including contract parameters, market conventions such as day count, date rolling convention, etc.
# contract parameters
fixed_rate = 0.018
notional = 1_000_000
fixing_in_advance = True
tenor = 4
pay_frequency = '6M'
rec_frequency = '1Y'
cancel_frequency = '1Y'
non_call_period = 2

# number of paths for monte carlo simulation
n_path = 6

# conventions
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)


# set evaluation date
valuationDate = ql.Date().todaysDate()
valuationDate = calendar.advance(valuationDate,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(valuationDate,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = valuationDate
print(f' trade date: {valuationDate}')
print(f' settlement date: {settlementDate}')

# Step 2. Prepare market data, including data to bootstrap curve and data to calibrate model.
# For this example, we use deposit and swap data to bootstrap curve, and swaption data to calibrate Hull White model.
# Market data to bootstrap curve.

def CreateUSDCurve():
    df_deposit = get_deposit('USD', ['1M', '2M', '3M', '6M', '9M'])
    df_swap = get_swap('USD', ['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

    # swaption data to calibrate Hull White model


    # Step 3. Create curve and model, use previously created market data as input and calibration data.
    curve = bootstrap_curve(valuationDate, deposit=df_deposit, swap=df_swap)
    return curve
def CreateUSDSwaptionData():
    return get_swaption('USD', ['2Y', '3Y'], ['5Y', '5Y'])
create_usd_curve: CurveCreator = CreateUSDCurve
create_usd_swaption_data: DataFrameCreator = CreateUSDSwaptionData

df_swaption = create_usd_swaption_data()
curve = create_usd_curve()
hw_model = HullWhiteModel(valuationDate, curve)
hw_model.calibrate(df_swaption)


dayCount = ql.Thirty360(ql.Thirty360.USA)

def CreatePaymentSchedule():
    date_rolling_convention = ql.ModifiedFollowing
    date_termination_convention = ql.ModifiedFollowing
    pay_frequency = ql.Period(pay_frequency)
    rec_frequency = ql.Period(rec_frequency)
    
    rule = ql.DateGeneration.Forward
    terminationDate = calendar.advance(settlementDate, ql.Period(tenor, ql.Years))
    endOfMonth = calendar.isEndOfMonth(terminationDate)
    paySchedule = ql.Schedule(settlementDate, terminationDate, pay_frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
    recSchedule = ql.Schedule(settlementDate, terminationDate, rec_frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
    # Note: the schedule created by ql.Schedule include settlement date, this behavior cowork with year_fraction() which always has 0 in first value.
    paymentSchedule = combine_schedule(paySchedule, recSchedule)  # merge two schedules
    return paymentSchedule

def CreateFixingSchedule():
    date_rolling_convention = ql.ModifiedFollowing
    date_termination_convention = ql.ModifiedFollowing
    frequency = ql.Period(pay_frequency)
    rule = ql.DateGeneration.Forward
    endOfMonth = calendar.isEndOfMonth(settlementDate)
    terminationDate = calendar.advance(settlementDate, ql.Period(tenor, ql.Years))
    endOfMonth = calendar.isEndOfMonth(terminationDate)
    paymentSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)

    fixingSchedule = [calendar.advance(d, ql.Period(-2, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)
    return fixingSchedule


create_payment_schedule: ScheduleCreator = CreatePaymentSchedule
create_fixing_schedule: ScheduleCreator = CreateFixingSchedule
paymentSchedule = create_payment_schedule()
fixingSchedule = create_fixing_schedule()
# convert original quantlib schedule object to list to use in pandas index.
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]


def CreateCancelSchedule():
    date_rolling_convention = ql.ModifiedFollowing
    date_termination_convention = ql.ModifiedFollowing
    rule = ql.DateGeneration.Forward
    endOfMonth = calendar.isEndOfMonth(terminationDate)
    terminationDate = calendar.advance(settlementDate, ql.Period(tenor, ql.Years))
    cancel_start_date = calendar.advance(settlementDate, ql.Period(non_call_period))
    cancel_frequency = ql.Period(cancel_frequency)
    payment_frequency = ql.Period(pay_frequency)
    paymentSchedule = ql.Schedule(settlementDate, terminationDate, payment_frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
    paymentSchedule = [d for d in paymentSchedule]
    exercisable = pd.Series(index=paymentSchedule, data=True)
    for i in range(non_call_period):
        exercisable.iloc[i] = False
    exercisable.iloc[-1] = False

    return exercisable
create_cancel_schedule: ScheduleCreator = CreateCancelSchedule
exercisable = create_cancel_schedule()

def CreateIndexFactories():
    def create_ibor_6M(ts):
        return ql.IborIndex('Libor_6M', ql.Period('6m'), 2, ql.USDCurrency(), calendar, date_rolling_convention, True, dayCount, ts)
    def create_cms_5Y(ts):
        return ql.UsdLiborSwapIsdaFixAm(ql.Period('5y'), ts)
    def create_ibor_2Y(ts):
        return ql.UsdLiborSwapIsdaFixAm(ql.Period('2y'), ts)
    return [create_ibor_6M, create_cms_5Y, create_ibor_2Y]
create_index_factories: IndexFactoriesCreator = CreateIndexFactories
index_factories = create_index_factories()
# generate paths of fixing value and discount factor by Hull White model
underlying_path, fixings, discountFactors = hw_model.monte_carlo_paths(index_factories=create_index_factories(), fixingSchedule=fixingSchedule, paymentSchedule=paymentSchedule, numPaths=n_path)




libor_fixings=fixings[0]  
cms_5Y_fixings=fixings[1]
cms_2Y_fixings=fixings[2]




# Libor cashflows
# Get fixing rate applies to each corresponding payment date.
corresponding_fixing_schedule = [get_nearest_fixing_date(d, libor_fixings.index) for d in paySchedule] 
libor_fixing_value = libor_fixings.loc[corresponding_fixing_schedule]  
if fixing_in_advance:  # process fixing-in-advance case if True 
    libor_fixing_value = libor_fixing_value.shift(1)  # Note: the first row of all fixing_value is NaN, but this is fine since we don't have payment in the first date.
# Apply the fixing values to calculate libor cashflows
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis] # use np.newaxis to reshape to (n, 1) for broadcast
libor_cashflows = notional * libor_fixing_value.values * year_fraction_pay  # calculate floating cashflows
libor_cashflows = pd.DataFrame(libor_cashflows, index=paySchedule)  # convert to dataframe, use paySchedule as index to align with other cashflows.
print(f'\nlibor_cashflows: \n{libor_cashflows}')


# Get fixing rate applies to each corresponding payment date.
corresponding_fixing_schedule = [get_nearest_fixing_date(d, cms_5Y_fixings.index) for d in recSchedule] 
cms_5Y_fixing_value = cms_5Y_fixings.loc[corresponding_fixing_schedule]
cms_2Y_fixing_value = cms_2Y_fixings.loc[corresponding_fixing_schedule]
if fixing_in_advance:  # process fixing-in-advance case if True 
    cms_5Y_fixing_value = cms_5Y_fixing_value.shift(1)
    cms_2Y_fixing_value = cms_2Y_fixing_value.shift(1)
# Apply the fixing values to calculate cms spread cashflows
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))[:,np.newaxis]
cms_spread = cms_5Y_fixing_value - cms_2Y_fixing_value
cms_spread_cashflows = notional * cms_spread.values * year_fraction_rec
cms_spread_cashflows = pd.DataFrame(cms_spread_cashflows, index=recSchedule)
print(f'\ncms_spread_cashflows: \n{cms_spread_cashflows}')

# Reindex both cashflow with paymentSchedule to calculate net cashflow in correct periods.
cms_spread_cashflows = cms_spread_cashflows.reindex(paymentSchedule).fillna(0)
libor_cashflows = libor_cashflows.reindex(paymentSchedule).fillna(0)
net_cashflows = pd.DataFrame(cms_spread_cashflows.values - libor_cashflows.values, index=paymentSchedule)  # use .values to broadcast.
print(f'\nnet cashflows: \n{net_cashflows}')  # note: the first row is 0, because we don't have payment in the first date.

# Step 6. Process the early termination by LongstaffSchwartz class.
# It is important to distinguish between callable/putable features and auto-call features. Callable (or putable, cancellable, Bermudan-style) options give the holder discretionary rights to exercise when advantageous, while auto-call features are triggered automatically when predetermined market conditions are met, without any discretionary decision.
# The LongstaffSchwartz is specifically designed for Bermudan-style options. As for auto-call features, implement on your own according to the specific contract term sheet.

single_period_dcf = discountFactors/discountFactors.shift(1)

exercisable = subset_to_bool(cancelSchedule, net_cashflows.index)  # convert from a list of dates to a boolean series
observations = libor_fixings  # The input of linear estimator in longstaff schwartz, irelevant of fixing-in-advance or fixing-in-arrears, it is the available information at that time point to decide exercise or not.
exercise_payoff = lambda x: np.zeros(len(x))   # The cashflow of calling(cancelling) the contract, in this case is 0.
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