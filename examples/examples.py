import pandas as pd
import numpy as np
import QuantLib as ql
from util import *
from conventions import Conventions
from rate_helpers import *
from curve_builder import bootstrap_curve, bootstrap_curve_with_instrument_helpers
from vol_helper import *
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel, HestonModel, MultiAssetModel, BlackScholesMertonModel, GarmanKohlagenProcessModel
from market_data import *
currency = ql.EURCurrency()
libor_dayCount = ql.Actual360()
date_rolling_convention = ql.Following


#@Description
"""Manipulate date and schedule"""
#@code
# today's date
today = ql.Date().todaysDate()

# time period
period=ql.Period(1, ql.Years)
period=ql.Period("6M")

# Quantlib date unit
ql.Days
ql.Weeks
ql.Months
ql.Years

#add period to a date
date = today + period
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
date = calendar.advance(today, period) # use period
date = calendar.advance(today, 2, ql.Days) # use int and unit
date = calendar.advance(today, period, ql.Following, False) # specify business day rules and is end of month



# A specific date
date = ql.Date(1, 1, 2025) # date format is day, month, year

# create a schedule from start date to termination date and frequency
startDate = ql.Date().todaysDate()
terminationDate = startDate + ql.Period(3, ql.Years)  # startDate + 3y
frequency = ql.Period(ql.Quarterly)
schedule = ql.MakeSchedule(startDate, terminationDate, frequency)
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
schedule = ql.Schedule(startDate, terminationDate, ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)

#@Description
"""Market convention of dates, rolling, daycount, schedule generation
keywordsL following, modified following, preceding, modified preceding, forward, backward, third wednesday, twentieth, actual/360, actual/365, thirty/360, 30/360 business/252, calendar, joint calendar"""

#@code
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


#@Description
"""create calendar for specific country, exchange or market, and join calendar for multiple calendars
keywords: calendar, exchange calendar, country calendar, joint calendar"""
#@code
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



#@Description
"""Rate helper, used to bootstrap yield curve. helper type: deposit, fra, swap, sofr, ois, bond
"""
#@code
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



#@Description
"""Build curve from market data dataFrame for specific currency witout need to pass conventions, which is the easiest way to build curve
keywords: USD curve, EUR curve, JPY curve, GBP curve, TWD curve, quick curve builder, recommended curve builder
"""
#@code
from curve_builder import bootstrap_curve
today = ql.Date().todaysDate()
df_deposit = pd.DataFrame({'tenor': ['1M', '2M', '3M', '6M', '9M'], 'rates': [0.015, 0.018, 0.02, 0.022, 0.025]})
df_swap = pd.DataFrame({'rate': [0.015, 0.018, 0.02, 0.022, 0.025],'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']})
curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)



#@Description
"""swaption helper builder, use to calibrate interest rate model.
keywords: swaption helper, volatility, interest rate model, calibration"""
#@code
from curve_builder import bootstrap_curve
from vol_helper import create_swaption_helper
today = ql.Date().todaysDate()
df_deposit = pd.DataFrame({
'tenor': ['1M', '2M', '3M', '6M', '9M'],
'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})
df_swap = pd.DataFrame({
    'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
    'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
})

curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)
df_swaption = pd.DataFrame({
    'maturity': ['2Y', '3Y'],
    'length': ['5Y', '5Y'],
    'volatility': [0.0055, 0.0055]
})
swaption_helpers = create_swaption_helper(df_swaption, curve, currency='USD')



#@Description
"""heston model helper, use to calibrate heston model.
keywords: heston model, volatility, calibration, volatility helper"""
# @code
from vol_helper import create_heston_model_helper
heston_vol_df = pd.DataFrame({
    'expiration': ['1M', '2M', '3M', '6M', '9M'],
    'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
    'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
}) 

spot = 20
dayCount = ql.Actual365Fixed()
riskFreeCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))  # in real world we usually don't use flat forward curve, here just for example.
dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))
heston_helpers = create_heston_model_helper(heston_vol_df, spot, riskFreeCurve, dividendCurve)

#@Description
"""create Black-Scholes-Merton Model for equity linked product (3 types of vol structure: constant volatility, volatility curve, volatility surface)
keywords: Black-Scholes-Merton Model, BSM Model, equity option, constant volatility, volatility curve, volatility surface, local volatility, deterministic volatility, monte carlo, paths generation"""
#@code
import QuantLib as ql
import pandas as pd
from vol_helper import create_black_vol_curve
from models import BlackScholesMertonModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
spot = 100
riskFreeCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M'])
# There are 3 types of volatility that BlackScholesMertonModel can use:
# 1. constant volatility
const_vol = ql.BlackConstantVol(today, calendar, 0.02, dayCount)
const_vol = ql.BlackVolTermStructureHandle(const_vol)
black_model_const_vol = BlackScholesMertonModel(riskFreeCurve, dividendCurve, const_vol, spot)
# 2. volatility curve
vol_curve = create_black_vol_curve(black_vol_df, today)
black_model_vol_curve = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_curve, spot)

# 3. volatility surface, also known as local volatility
df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
vol_surface = create_black_vol_surface(df_vol_surface, today)
black_model_vol_surface = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_surface, spot)


#@Description
"""Create Heston Model for equity linked product (stochastic volatility)
keywords: Heston Model, stochastic volatility, equity option, calibration, monte carlo, paths generation"""
import pandas as pd
import QuantLib as ql
from models import HestonModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
heston_vol_df = pd.DataFrame({
    'expiration': ['1M', '2M', '3M', '6M', '9M'],
    'strike': [100, 110, 120, 130, 140],
    'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
})
spot = 100
riskFreeCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
heston_model = HestonModel(riskFreeCurve, dividendCurve, calendar)
heston_model.calibrate(heston_vol_df, spot)


#@Description
"""Create Garman-Kohlagen FX Model for FX linked product
keywords: Garman-Kohlagen Model, FX Model, constant volatility, volatility curve, volatility surface, local volatility, deterministic volatility, monte carlo, paths generation"""
#@code
import QuantLib as ql
from models import GarmanKohlagenProcessModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
spot = 1.3
domestic_curve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount)) # Usually don't use flat curve in real world, just simplify for example.
foreign_curve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.05, dayCount)) # Usually don't use flat curve in real world, just simplify for example.

# There are 3 types of volatility that GarmanKohlagenProcessModel can use:
# 1. constant volatility
const_vol = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, calendar, 0.2, dayCount)) # Usually don't use flat curve in real world, just simplify for example.
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, const_vol, spot)

# 2. volatility curve
black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M'])
vol_curve = create_black_vol_curve(black_vol_df, today)
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_curve, spot)

# 3. volatility surface, also known as local volatility
df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
vol_surface = create_black_vol_surface(df_vol_surface, today)
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_surface, spot)



#@Description
"""create paths for monte carlo simulation for equity model and FX model
keywords: path, monte carlo"""
#@code
fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
n_path = 4

black_model_vol_surface = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_surface, spot)
paths = black_model_vol_surface.monte_carlo_paths(fixingSchedule, n_path)

# or
heston_model = HestonModel(riskFreeCurve, dividendCurve, calendar)
heston_model.calibrate(heston_vol_df, spot)
paths = heston_model.monte_carlo_paths(fixingSchedule, n_path)
# or
fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_surface, spot)
fixings = fxModel.monte_carlo_paths(fixingSchedule, n_path)
#  type(fixings): pandas.DataFrame
#  fixings.shape: (len(fixingSchedule), n_path)





#@Description
"""Multi-Asset Model
keyword: multi asset, multi process, hybrid model, hybrid process, monte carlo, paths generation"""
#@code
import QuantLib as ql
from models import MultiAssetModel
today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
corrMatrix = [[1, 0.5], [0.5, 1]]
# Reuse black_model and fxModel from above
processes = [black_model_vol_curve.process, fxModel.process]  # note: don't support heston model and hull-white model as sub-process
multiAssetModel = MultiAssetModel(processes, corrMatrix)


#@Description
"""Multi-Asset Model
keyword: multi asset, multi process, hybrid model, hybrid process, monte carlo, paths generation"""
#@code
processes = [black_model_vol_curve.process, fxModel.process]  # note: don't support heston model and hull-white model as sub-process
multiAssetModel = MultiAssetModel(processes, corrMatrix)  # see Multi-Asset Model example for details of creating multi-asset model

fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
n_path = 4
fixings = multiAssetModel.monte_carlo_paths(fixingSchedule, n_path)
equity_fixings = fixings[0] 
# type(equity_fixings): pandas.DataFrame, shape: (len(fixingSchedule), n_path)
fx_fixings = fixings[1] 
# type(fx_fixings): pandas.DataFrame, shape: (len(fixingSchedule), n_path)







#@Description
"""LongstaffSchwartz, Bermudan Option, American Option, early exercise, least square error method
keywords: LongstaffSchwartz, Bermudan Option, American Option, early exercise, least square error method"""
#@code
from leastSquareError import LongstaffSchwartz
today = ql.Date().todaysDate()
settlmentDate = today + ql.Period('2D')
paymentSchedule = ql.MakeSchedule(settlmentDate, settlmentDate + ql.Period('1Y'), ql.Period('3M'))
paymentSchedule = [d for d in paymentSchedule]
fixingSchedule = [d - ql.Period('2D') for d in paymentSchedule]

# we use mock data for cashflows, discountFactors, fixing, and payoff in this example.
# in real case it depends on the contract type and the model used.
cashflows = pd.DataFrame(np.random.randn(len(paymentSchedule), 3) * 1_000, index=paymentSchedule)
discountFactor = pd.DataFrame([1/((1+np.random.uniform(0,0.05))) for i in range(len(paymentSchedule))], index=paymentSchedule)
fixing = pd.DataFrame(np.random.randn(len(paymentSchedule), 3), index=fixingSchedule)
payoff = lambda fixing: np.maximum(fixing - 1, 0)
exercise_schedule = pd.Series(np.ones(len(paymentSchedule), dtype=bool), index=paymentSchedule)
exercise_schedule.iloc[0] = False
ls = LongstaffSchwartz(cashflows, discountFactor, exercise_schedule, payoff, fixing)


ls.backward_induction()  # conduct backward induction for optimized exercise decision
ls.valuations() # return expected npv, i.e. valuation
ls.confidence_interval(alpha=0.05) # return confidence interval of the expected npv
ls.survival_probability() # return survival probability
ls.exercise_cashflows() # return expected cashflows of early exercise of each period.
ls.exercise_mask()  # return whether to exercise at each period and each path.




