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
from curve_builder import bootstrap_curve_with_instrument_helpers
from vol_helper import (
    create_USD_swaption_helpers, create_EUR_swaption_helpers,
    create_JPY_swaption_helpers, create_GBP_swaption_helpers,
    create_CHF_swaption_helpers, create_TWD_swaption_helpers)
from curve_builder import bootstrap_USD_curve
from util import get_nearest_fixing_date, year_fraction, combine_schedule
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel
from market_data import (get_deposit, get_swap, get_swaption, get_FRA, get_sofr_future)
fixed_rate = 0.018
notional = 1_000_000
fixing_in_advance = True
tenor = 3

# number of paths for monte carlo simulation
n_path = 6

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
terminationDate = calendar.advance(settlementDate, ql.Period(tenor, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
paymentSchedule = combine_schedule(paySchedule, recSchedule)  # merge two schedules
fixingSchedule = [calendar.advance(d, ql.Period(-2, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)
# convert original quantlib schedule object to list to use in pandas index.
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]



print(f'paymentSchedule: {paymentSchedule}')
print(f'fixingSchedule: {fixingSchedule}')


