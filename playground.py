import QuantLib as ql
import numpy as np
import pandas as pd
from util import leg_to_series, subset_to_bool, get_nearest_fixing_date
from datetime import datetime
from rate_helpers import (
    create_USD_deposit_rate_helpers,
    create_USD_swap_rate_helpers,
    create_deposit_rate_helpers,
    create_swap_rate_helpers,
    create_OIS_helper,
    create_fra_rate_helpers,  # <-- corrected
    create_bond_helper,
    create_sofr_future_rate_helpers)
from curve_builder import bootstrap_USD_curve, bootstrap_EUR_curve, bootstrap_JPY_curve, bootstrap_GBP_curve, bootstrap_TWD_curve
from conventions import Conventions
from typing import Literal, Tuple
from curve_builder import bootstrap_curve_with_instrument_helpers, bootstrap_curve
from vol_helper import (
    create_USD_swaption_helpers, create_EUR_swaption_helpers,
    create_JPY_swaption_helpers, create_GBP_swaption_helpers,
    create_CHF_swaption_helpers, create_TWD_swaption_helpers)
from curve_builder import bootstrap_USD_curve
from util import get_nearest_fixing_date, year_fraction, combine_schedule
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel
from market_data import (get_deposit, get_swap, get_swaption, get_FRA, get_sofr_future)

# Description:
# fixed rate cancellable IRS (Libor)
# rec fixed leg, 30/360, frequency 6M
# pay floating: index: 6M libor, act/360, frequency 6M
# cancelable schedule: same as fixed leg frequency
# floating leg fixing schedule: 2 days before payment date, fixing-in-advance
# tenor: 3Y
# fixing rate: 1.8%, notional: 1M USD


# conventions
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
frequency = ql.Period('6M')
dayCount = ql.Thirty360(ql.Thirty360.USA)
currency = ql.USDCurrency()
rule = ql.DateGeneration.Backward
y=3

print(f' calendar: {calendar}')
# set evaluation date
today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')
terminationDate = calendar.advance(settlementDate, ql.Period(y, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
print(f' termination date: {terminationDate}')
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
print(f' paySchedule: {[d for d in paySchedule]}')

calendar = ql.JointCalendar(ql.TARGET(), calendar) # add Target as we use Euribor swap fixing.
print(f'\ncalendar: {calendar}')
today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')
terminationDate = calendar.advance(settlementDate, ql.Period(y, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
print(f' termination date: {terminationDate}')
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
print(f' paySchedule: {[d for d in paySchedule]}')

