import pandas as pd
import numpy as np
import QuantLib as ql
from util import *
from conventions import Conventions
from rate_helpers import *
from curve_builder import bootstrap_USD_curve, bootstrap_EUR_curve, bootstrap_JPY_curve, bootstrap_GBP_curve, bootstrap_TWD_curve, bootstrap_curve_with_instrument_helpers, bootstrap_curve
from vol_helper import *
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel, HestonModel, MultiAssetModel, BlackScholesMertonModel, GarmanKohlagenProcessModel
from market_data import *

#***
# today's date
today = ql.Date().todaysDate()

#***
# add period to a date
date = today + ql.Period(1, ql.Years)
date = today + ql.Period("6M")

#***
# A specific date
date = ql.Date(1, 1, 2025)

#***
# create a schedule from start date to termination date and frequency

startDate = ql.Date().todaysDate()
terminationDate = startDate + ql.Period(3, ql.Years)
frequency = ql.Period(ql.Quarterly)
schedule = ql.MakeSchedule(startDate, terminationDate, frequency)

#***
# Market convention of dates, rolling, daycount, schedule generation
# date rolling market conventions, used to determine how a date change if it is not a business day
ql.Following   # Move to next business day if it is not a business day
ql.ModifiedFollowing   # Move to next business day if it is not a business day, but if the date is the last business day of the month, move to previous business day.
ql.Preceding   # Move to previous business day if it is not a business day
ql.ModifiedPreceding   # Move to previous business day if it is not a business day, but if the moved date become previous month, move to next business day.

# Date generation role.
ql.DateGeneration.Forward   # Generate dates forward from start date
ql.DateGeneration.Backward   # Generate dates backward from termination date
ql.DateGeneration.ThirdWednesday   # Generate dates on third Wednesday of each month
ql.DateGeneration.Twentieth   # Generate dates on twentieth of each month

# day count method for interest calculation
ql.Actual360()
ql.Actual365Fixed()
ql.Thirty360(ql.Thirty360.USA)
ql.Thirty360(ql.Thirty360.BondBasis)
ql.Thirty360(ql.Thirty360.European)
ql.Thirty360(ql.Thirty360.EurobondBasis)
ql.Actual365Fixed()
ql.Actual365Fixed(ql.Actual365Fixed.Standard)
ql.Actual365Fixed(ql.Actual365Fixed.Canadian)
ql.Actual365Fixed(ql.Actual365Fixed.NoLeap)
ql.ActualActual(ql.ActualActual.ISMA)
ql.ActualActual(ql.ActualActual.Bond)
ql.ActualActual(ql.ActualActual.ISDA)
ql.ActualActual(ql.ActualActual.Euro)
ql.Actual360()
ql.SimpleDayCounter()
ql.Business252()


#***
# calendar

calendar1 = ql.UnitedKingdom()
calendar2 = ql.TARGET()
# available calendar: Argentina, Australia, Austria, BespokeCalendar, Botswana, Brazil, Canada, China, CzechRepublic, Denmark, Finland, France, Germany, HongKong, Hungary, Iceland, India, Indonesia, Israel, Italy, Japan, JointCalendar, Mexico, NewZealand, Norway, NullCalendar, Poland, Romania, Russia, SaudiArabia, Singapore, Slovakia, SouthAfrica, SouthKorea, Sweden, Switzerland, Taiwan, TARGET, Thailand, Turkey, Ukraine, UnitedKingdom, UnitedStates, WeekendsOnly
# calendar for specific exchange or market
ql.UnitedStates(ql.UnitedStates.FederalReserve)
ql.UnitedStates(ql.UnitedStates.GovernmentBond)
ql.UnitedStates(ql.UnitedStates.NYSE)
ql.UnitedStates(ql.UnitedStates.Settlement)

# JointCalenar
joint_calendar = ql.JointCalendar(ql.TARGET(), ql.Poland())



#***
# Rate helper, used to bootstrap yield curve. helper type: deposit, fra, swap, sofr, ois, bond
from datetime import datetime
df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
deposit_helpers = create_deposit_rate_helpers(df_deposit, conventions=Conventions.USFixedLegConventions())

df_fra = pd.DataFrame({'monthsToStart': [1, 2, 3], 'monthsToEnd': [7, 8, 9], 'rates': [0.021, 0.023, 0.025]})
fra_helpers = create_fra_rate_helpers(df_fra, conventions=Conventions.USFloatingLegConventions())

df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02], 'tenor': ['5Y', '7Y', '10Y']})
swap_helpers = create_swap_rate_helpers(df_swap, fixed_leg_conventions=Conventions.USFixedLegConventions(), floating_leg_conventions=Conventions.USFloatingLegConventions())

df_sofr = pd.DataFrame({'price': [99.915, 99.920], 'month': [3, 6], 'year': [2020, 2020], 'frequency': [ql.Quarterly, ql.Quarterly]})
sofr_helpers = create_sofr_future_rate_helpers(df_sofr, conventions=Conventions.USFloatingLegConventions())

df_OIS = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rate': [0.015, 0.018, 0.02, 0.022, 0.025]})
oishelpers = create_OIS_helper(df_OIS, conventions=Conventions.USFixedLegConventions())

df_bond = pd.DataFrame({'coupon': [0.015, 0.018], 'price': [99.915, 99.920], 'effectiveDate': [datetime(2020,1,15), datetime(2020,6,15)], 'terminationDate': [datetime(2025,1,15), datetime(2025,6,15)]})
conventions = Conventions.USFixedLegConventions()
conventions['frequency'] = ql.Period('6M')
bond_helpers = create_bond_helper(df_bond, conventions=conventions)


#***
# quick deposit helper builder for each currency without need to pass conventions
df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
create_USD_deposit_rate_helpers(df_deposit)
create_EUR_deposit_rate_helpers(df_deposit)
create_JPY_deposit_rate_helpers(df_deposit)
create_TWD_deposit_rate_helpers(df_deposit)
create_CHF_deposit_rate_helpers(df_deposit)
create_GBP_deposit_rate_helpers(df_deposit)

#***
# quick swap helper builder for each currency without need to pass conventions
df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02], 'tenor': ['5Y', '7Y', '10Y']})
create_USD_swap_rate_helpers(df_swap)
create_EUR_swap_rate_helpers(df_swap)
create_JPY_swap_rate_helpers(df_swap)
create_TWD_swap_rate_helpers(df_swap)
create_CHF_swap_rate_helpers(df_swap)
create_GBP_swap_rate_helpers(df_swap)

#***
# quick OIS helper builder for each currency without need to pass conventions
df_OIS = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '1Y'], 'rate': [0.015, 0.018, 0.02, 0.022, 0.025]})
create_EUR_OIS_helpers(df_OIS)
create_GBP_OIS_helpers(df_OIS)
create_JPY_OIS_helpers(df_OIS)
create_CHF_OIS_helpers(df_OIS)

#***
# quick FRA helper builder for each currency without need to pass conventions
df_fra = pd.DataFrame({'monthsToStart': [1, 2, 3], 'monthsToEnd': [7, 8, 9], 'rates': [0.021, 0.023, 0.025]})
create_USD_FRA_helpers(df_fra)
create_EUR_FRA_helpers(df_fra)
create_CHF_FRA_helpers(df_fra)
create_GBP_FRA_helpers(df_fra)
create_JPY_FRA_helpers(df_fra)  



#***
# Build curve from helpers.
today = ql.Date().todaysDate()
df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '9M'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
deposit_helpers = create_USD_deposit_rate_helpers(df_deposit)
df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02, 0.022, 0.025],'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']})
swap_helpers = create_USD_swap_rate_helpers(df_swap)

curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers, ql.Actual360())  # use deposit helper only
curve = bootstrap_curve_with_instrument_helpers(today, deposit_helpers + swap_helpers, ql.Actual360())  # use deposit and swap helpers


#***
# Build curve from dataFrame as market data
from conventions import Conventions
today = ql.Date().todaysDate()

df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '9M'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02, 0.022, 0.025],'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']})
curve = bootstrap_curve(
    today, ql.Actual360(), 
    deposit=(df_deposit, Conventions.USFixedLegConventions()), 
    swap=(df_swap, Conventions.USFixedLegConventions(), 
    Conventions.USFloatingLegConventions())
    )

#***
# Build curve from dataFrame as market data for specific currency witout need to pass conventions, which is the easiest way to build curve
curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for USD curve without conventions
curve = bootstrap_EUR_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for EUR curve without conventions
curve = bootstrap_JPY_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for JPY curve without conventions
curve = bootstrap_GBP_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for GBP curve without conventions
curve = bootstrap_TWD_curve(today, deposit=df_deposit, swap=df_swap)  # fast builder for TWD curve without conventions



#***
# swaption helper builder, use to calibrate interest rate model.
from curve_builder import bootstrap_USD_curve
today = ql.Date().todaysDate()
df_deposit = pd.DataFrame({
'tenor': ['1M', '2M', '3M', '6M', '9M'],
'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})
df_swap = pd.DataFrame({
    'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
    'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
})

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

# note: engine is not necessary to create swaption helpers, but you need to set egine to each helper before calibrate the model.
swaption_helpers = create_swaption_helper(df_swaption, curve, engine, fixed_leg_conventions, floating_leg_conventions)
swaption_helpers = create_USD_swaption_helpers(df_swaption, curve, engine)  # fast builder for USD swaption without conventions
swaption_helpers = create_EUR_swaption_helpers(df_swaption, curve, engine)  # fast builder for EUR swaption without conventions
swaption_helpers = create_JPY_swaption_helpers(df_swaption, curve, engine)  # fast builder for JPY swaption without conventions
swaption_helpers = create_GBP_swaption_helpers(df_swaption, curve, engine)  # fast builder for GBP swaption without conventions
swaption_helpers = create_CHF_swaption_helpers(df_swaption, curve, engine)  # fast builder for CHF swaption without conventions
swaption_helpers = create_TWD_swaption_helpers(df_swaption, curve, engine)  # fast builder for TWD swaption without conventions


#***
# heston model helper, use to calibrate heston model.
heston_vol_df = pd.DataFrame({
    'option_tenor': ['1M', '2M', '3M', '6M', '9M'],
    'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
    'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
}) 
spot = 20
dayCount = ql.Actual365Fixed()
riskFreeCurve = ql.FlatForward(today, 0.04, dayCount)  # in real world we usually don't use flat forward curve, here just for example.
dividendCurve = ql.FlatForward(today, 0.01, dayCount)
heston_helpers = create_heston_model_helper(heston_vol_df, spot, riskFreeCurve, dividendCurve)

#***
# Black-Scholes-Merton Model (simple equity option)
import QuantLib as ql
import pandas as pd
from vol_helper import create_black_vol_curve
from models import BlackScholesMertonModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
spot = 100
riskFreeCurve = ql.FlatForward(today, 0.04, dayCount)  # Usually don't use flat curve in real world, just simplify for example.
dividendCurve = ql.FlatForward(today, 0.01, dayCount)  # Usually don't use flat curve in real world, just simplify for example.
black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M'])

# constant volatility
const_vol = ql.BlackConstantVol(today, calendar, 0.02, dayCount)
black_model_const_vol = BlackScholesMertonModel(riskFreeCurve, dividendCurve, const_vol, spot)
# volatility curve
vol_curve = create_black_vol_curve(black_vol_df, today)
black_model_vol_curve = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_curve, spot)

# volatility surface
df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
vol_surface = create_black_vol_surface(df_vol_surface, today)
black_model_vol_surface = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_surface, spot)

fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
paths = black_model_vol_curve.monte_carlo_paths(fixingSchedule, 4)



#***
# Heston Model (stochastic volatility)
import pandas as pd
import QuantLib as ql
from models import HestonModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
heston_vol_df = pd.DataFrame({
    'option_tenor': ['1M', '2M', '3M', '6M', '9M'],
    'strike': [100, 110, 120, 130, 140],
    'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
})
spot = 100
riskFreeCurve = ql.FlatForward(today, 0.04, dayCount)  # Usually don't use flat curve in real world, just simplify for example.
dividendCurve = ql.FlatForward(today, 0.01, dayCount)  # Usually don't use flat curve in real world, just simplify for example.
heston_model = HestonModel(riskFreeCurve, dividendCurve, calendar)
heston_model.calibrate(heston_vol_df, spot)
fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
paths = heston_model.monte_carlo_paths(fixingSchedule, 4)


#***
# Garman-Kohlagen FX Model
import QuantLib as ql
from models import GarmanKohlagenProcessModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
spot = 1.3
domestic_curve = ql.FlatForward(today, 0.04, dayCount) # Usually don't use flat curve in real world, just simplify for example.
foreign_curve = ql.FlatForward(today, 0.05, dayCount) # Usually don't use flat curve in real world, just simplify for example.

# constant volatility
const_vol = ql.BlackConstantVol(today, calendar, 0.2, dayCount) # Usually don't use flat curve in real world, just simplify for example.
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, const_vol, spot)

# volatility curve
black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M'])
vol_curve = create_black_vol_curve(black_vol_df, today)
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_curve, spot)

# volatility surface
df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
vol_surface = create_black_vol_surface(df_vol_surface, today)
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_surface, spot)



fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
paths = fxModel.monte_carlo_paths(fixingSchedule, 4)
print(paths)

#***
# Multi-Asset Model
import QuantLib as ql
from models import MultiAssetModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
corrMatrix = [[1, 0.5], [0.5, 1]]
# Reuse black_model and fxModel from above
processes = [black_model_vol_curve.process, fxModel.process]  # note: don't support heston model as sub-process
multiAssetModel = MultiAssetModel(processes, corrMatrix)
fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
paths = multiAssetModel.monte_carlo_paths(fixingSchedule, 4)

#***
# Get Volatility Surface (utility)
from market_data import get_volatility_surface
df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])


#***
# LongstaffSchwartz, Bermudan Option, American Option, early exercise, least square error method
from leastSquareError import LongstaffSchwartz
today = ql.Date().todaysDate()
settlmentDate = today + ql.Period('2D')
paymentSchedule = ql.MakeSchedule(settlmentDate, settlmentDate + ql.Period('1Y'), ql.Period('3M'))
paymentSchedule = [d for d in paymentSchedule]
fixingSchedule = [d - ql.Period('2D') for d in paymentSchedule]
notional = 1_000

# we use mock data for cashflows, discountFactors, fixing, and payoff in this example.
# in real case it depends on the contract type and the model used.
cashflows = pd.DataFrame(np.random.randn(len(paymentSchedule), 3) * notional, index=paymentSchedule)
discountFactor = pd.DataFrame([1/((1+np.random.uniform(0,0.05))) for i in range(len(paymentSchedule))], index=paymentSchedule)
fixing = pd.DataFrame(np.random.randn(len(paymentSchedule), 3), index=fixingSchedule)
payoff = lambda fixing: np.maximum(fixing - 1, 0)
exercise_schedule = pd.Series(np.ones(len(paymentSchedule), dtype=bool), index=paymentSchedule)
exercise_schedule.iloc[0] = False
ls = LongstaffSchwartz(cashflows, discountFactor, exercise_schedule, payoff, fixing)
ls.backward_induction()


#***
# calculate floating cashflow with libor index in deterministic interest rate environment.
yieldCurve = ql.FlatForward(today, 0.04, ql.Actual365Fixed())  # In real world we usually don't use flat forward curve, here just for example.
libor_index = ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, libor_dayCount, ql.YieldTermStructureHandle(yieldCurve))
libor_fixings = [libor_index.fixing(d) for d in fixingSchedule]  # get fixing values for each fixing date from index using .fixing() method
libor_fixings = pd.DataFrame(libor_fixings, paymentSchedule)  # convert to pandas DataFrame for easy manipulation, notes that we use paymentSchedule as index, not fixingSchedule, in order to align with other cashflow, discount factor, etc.
if fixing_in_advance:
    libor_fixings = libor_fixings.shift(1)  # as we shift, first item will become NaN, but this is fine since we don't have payment in the first date.
libor_year_fraction = np.array(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False))[:, np.newaxis]  # reshape to (n, 1) for broadcast.
libor_cashflows = notional * libor_fixings * libor_year_fraction

#***
# calculate floating cashflow with libor index in stochastic interest rate with multiple simulation paths of fixing.

# fixings = ...  # get fixing_value from model or other sources.

# step 1. get fixing rate of floating index, here are three ways of doing it, all have same result.
# method 1: The easiest way, use fixings as it is.
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


