import QuantLib as ql
import numpy as np
import pandas as pd
from util import leg_to_series, subset_to_bool
from datetime import datetime
from rate_helpers import (
    create_USD_deposit_rate_helpers,
    create_USD_swap_rate_helpers,
    create_deposit_rate_helpers,
    create_swap_rate_helpers,
    create_OIS_helper,
    create_fra_rate_helpers,  # <-- corrected
    create_bond_helper,
    create_sofr_future_rate_helpers
)
from curve_builder import bootstrap_USD_curve, bootstrap_EUR_curve, bootstrap_JPY_curve, bootstrap_GBP_curve, bootstrap_TWD_curve
from conventions import Conventions
from typing import Literal, Tuple
from curve_builder import bootstrap_curve_with_instrument_helpers, bootstrap_curve
from vol_helper import (
    create_USD_swaption_helpers, create_EUR_swaption_helpers,
    create_JPY_swaption_helpers, create_GBP_swaption_helpers,
    create_CHF_swaption_helpers, create_TWD_swaption_helpers
)

from curve_builder import bootstrap_USD_curve
from util import get_nearest_fixing_date, year_fraction, combine_schedule
from leastSquareError import LongstaffSchwartz
from models import HullWhiteModel, HestonModel

from market_data import (get_deposit, get_swap, get_swaption, get_FRA, get_sofr_future)


# conventions
fixed_leg_conventions = Conventions.USFixedLegConventions()
floating_leg_conventions = Conventions.USFloatingLegConventions()
US_calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
EUR_calendar = ql.TARGET()
calendar = ql.JointCalendar(US_calendar, EUR_calendar)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
frequency = ql.Period('3M')
coupon_dayCount = ql.Thirty360(ql.Thirty360.USA)
libor_dayCount = ql.Actual360()
currency = ql.USDCurrency()
endOfMonth = False
rule = ql.DateGeneration.Forward



today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')

# prepare market data for curve and model calibration
df_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
df_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

df_heston_vol = pd.DataFrame({
    'option_tenor': ['1M', '2M', '3M', '6M', '9M'],
    'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
    'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
}) 

# create curve and calibrate model by swaptions
yieldCurve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
dividendCurve = ql.FlatForward(today, 0.01, ql.Actual365Fixed())

spot = 70
heston_model = HestonModel(yieldCurve, dividendCurve, calendar)
heston_model.calibrate(df_heston_vol, spot)


terminationDate = calendar.advance(settlementDate, ql.Period(3, ql.Years))
paymentSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)

paymentSchedule = [d for d in paymentSchedule]
fixingSchedule = [d for d in fixingSchedule]

coupon_year_fraction = pd.DataFrame(year_fraction(paymentSchedule, coupon_dayCount, accoumulative=False), index=paymentSchedule)
libor_year_fraction = pd.DataFrame(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False), index=paymentSchedule)
equity_fixings = heston_model.monte_carlo_paths(spot, fixingSchedule, 2**2)

print(f'equity_fixings: \n{equity_fixings}')





notional = 1_000_000
bermudian_knock_out = 1.1
strike = 1.0
european_knock_in = 0.95
coupon_rate = 0.1

discountFactors = [yieldCurve.discount(d) for d in paymentSchedule]
discountFactors = pd.DataFrame(discountFactors, index=paymentSchedule)
print(f'discountFactors: \n{discountFactors}')
libor_index = ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, libor_dayCount, ql.YieldTermStructureHandle(yieldCurve))
libor_fixings = [libor_index.fixing(d) for d in fixingSchedule]
libor_fixings = pd.DataFrame(libor_fixings, paymentSchedule)

print(f'Libor fixings\nbefore shift: \n{libor_fixings}')
libor_fixings = libor_fixings.shift(1)  # fixing-in-advance
print(f'after shift: \n{libor_fixings}')

previous_survival = np.ones((1, equity_fixings.shape[1]), dtype=bool)

survival = pd.DataFrame(np.zeros_like(equity_fixings, dtype=bool), index=paymentSchedule)
cashflows = pd.DataFrame(np.zeros_like(equity_fixings, dtype=float), index=paymentSchedule)
cashflows_with_knock_out = pd.DataFrame(np.zeros_like(equity_fixings, dtype=float), index=paymentSchedule)
for d in paymentSchedule:
    print(f'previous_survival: \n{previous_survival}')
    coupon_cashflow = notional * coupon_rate * coupon_year_fraction.loc[d]
    libor_cashflow = notional * libor_fixings.loc[d] * libor_year_fraction.loc[d]
    net_cf = coupon_cashflow - libor_cashflow
    cashflows.loc[d] = net_cf.values
    cf_with_knock_out = previous_survival * net_cf.values
    print(f'cash_flow_with_knock_out: \n{cf_with_knock_out}')
    cashflows_with_knock_out.loc[d] = cf_with_knock_out
    

    # survival.loc[d] = survival
    nearest_fixing_date = get_nearest_fixing_date(d, fixingSchedule)
    fixing_d = equity_fixings.loc[nearest_fixing_date]
    print(f'fixing of {nearest_fixing_date}: \n{fixing_d.values}')
    current_survival = fixing_d.values < bermudian_knock_out * spot
    print(f'current_survival: \n{current_survival}')

    if d == paymentSchedule[-1]:
        knockin = fixing_d.values < european_knock_in * spot
        vanilla_option_payoff = notional * np.maximum(strike*spot - fixing_d.values, 0)
        print(f'vanilla option payoff regardless of knock-in: \n{vanilla_option_payoff}')
        eki_option_payoff = vanilla_option_payoff * knockin
        print(f'option payoff with condition of knock-in: \n{eki_option_payoff}')
        final_option_payoff = eki_option_payoff * previous_survival
        print(f'final option payoff: \n{final_option_payoff}')





    previous_survival = np.bitwise_and(previous_survival, current_survival)

    
print(f'cashflows: \n{cashflows}')
print(f'cashflows_with_knock_out: \n{cashflows_with_knock_out}')
all_cashflows = cashflows_with_knock_out.copy()
all_cashflows.loc[paymentSchedule[-1]] = final_option_payoff
print(f'all_cashflows: \n{all_cashflows}')
discounted_cashflows = all_cashflows * discountFactors.values
print(f'discounted_cashflows: \n{discounted_cashflows}')
print(f'npv: {discounted_cashflows.mean(axis=1).sum()}')



