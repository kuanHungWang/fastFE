import QuantLib as ql
import numpy as np
import pandas as pd
from util import year_fraction
from curve_builder import (
    bootstrap_USD_curve,
    bootstrap_EUR_curve
)
from vol_helper import create_black_vol_surface
from models import GarmanKohlagenProcessModel
from market_data import (
    get_deposit,
    get_swap,
    get_volatility_surface,
    get_price
)



"""Description:
Keywords: fx linked, single currency, daily range accrual, swap.
tenor: 1Y
notional: 1M 
pay 3M Euribor coupon, act360, fixing in advance
receive 2% daily range accrual coupon, 30/360
range: 0.99< EURUSD < 1.2
for each payment period, use the fixing value 5 days prior to the payment date for remaining fixing period
calculation of range accrual: 2% * (in range days / total days)"""

# contract parameters
notional = 1_000_000
coupon_rate = 0.02
upper_bound = 1.2
lower_bound = 0.99
fixing_in_advance = True
n_period_end_replacement = 5

US_calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
EUR_calendar = ql.TARGET()
calendar = ql.JointCalendar(US_calendar, EUR_calendar)
today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')






eur_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
eur_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])
eur_yieldCurve = bootstrap_EUR_curve(today, deposit=eur_deposit, swap=eur_swap)

usd_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
usd_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])
usd_yieldCurve = bootstrap_USD_curve(today, deposit=usd_deposit, swap=usd_swap)

eurusd_vol = get_volatility_surface('EUR', ['1M', '2M', '3M', '6M', '9M', '12M'], [1.05, 1.07, 1.09, 1.11, 1.13, 1.15])
vol_surface = create_black_vol_surface(eurusd_vol, today)
spot = get_price('EUR')
fx_model = GarmanKohlagenProcessModel(usd_yieldCurve, eur_yieldCurve, vol_surface, spot)

frequency=ql.Period('3M')
terminationDate = calendar.advance(settlementDate, ql.Period('1Y'))
endOfMonth = calendar.isEndOfMonth(terminationDate)

date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
rule = ql.DateGeneration.Forward
endOfMonth= calendar.isEndOfMonth(terminationDate)
paymentSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)

paymentSchedule = [d for d in paymentSchedule]





# libor cash flow under deterministic yield curve.
ts = ql.YieldTermStructureHandle(eur_yieldCurve)
libor_dayCount = ql.Actual360()
libor_index = ql.Euribor3M(ts)
libor_fixings = pd.DataFrame([libor_index.fixing(d) for d in paymentSchedule], index=paymentSchedule)
discountFactors = pd.DataFrame([eur_yieldCurve.discount(d) for d in paymentSchedule], index=paymentSchedule)
print(f'discountFactors: \n{discountFactors}')
print(f'libor_fixings: \n{libor_fixings}')
if fixing_in_advance:
    libor_fixings = libor_fixings.shift(1)
libor_year_fraction = pd.DataFrame(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False), index=paymentSchedule)
libor_cashflows = notional * libor_fixings * libor_year_fraction
print(f'libor_cashflows: \n{libor_cashflows}')

daily_fixing_days = ql.MakeSchedule(settlementDate, terminationDate, ql.Period('1d'), calendar=calendar)
print(len(daily_fixing_days))

n_paths = 2**2
fx_fixing = fx_model.monte_carlo_paths(daily_fixing_days, numPaths=n_paths)


range_accrual_yearFraction = year_fraction(paymentSchedule, ql.Actual360(), accoumulative=False)
range_accrual_yearFraction = pd.DataFrame(range_accrual_yearFraction, index=paymentSchedule)
start_date = paymentSchedule[0]



range_accrual_cashflows = pd.DataFrame(np.zeros((len(paymentSchedule), n_paths), dtype=float), index=paymentSchedule)
for d in paymentSchedule[1:]:
    end_dade = d
    # For each payment period, calculate range accrual coupon
    period_fixing = fx_fixing.loc[start_date:end_dade]
    # Handle the last 5 days: use fixing 5 days prior to payment date
    if len(period_fixing) > n_period_end_replacement:

        period_fixing.iloc[-n_period_end_replacement:] = period_fixing.iloc[-n_period_end_replacement]  # use fixing 5 days prior for last 5 days

    # Count in-range days

    in_range = (period_fixing > lower_bound) & (period_fixing < upper_bound)
    accrual_fraction = in_range.mean(axis=0).values
    accrual_amount = notional * coupon_rate * accrual_fraction * range_accrual_yearFraction.loc[end_dade].values
    range_accrual_cashflows.loc[end_dade] = accrual_amount
    print(f'Period {start_date} to {end_dade}: In-range days=\n{in_range.sum(axis=0)}, Total days=\n{len(period_fixing)}, Accrual fraction=\n{accrual_fraction}')
    start_date = d
print(f'range_accrual_cashflows: \n{range_accrual_cashflows}')

present_value = range_accrual_cashflows * discountFactors.values
print(f'present_value(all paths): \n{present_value}')
print(f'expected present value: {present_value.mean(axis=1)}')
npv = present_value.sum(axis=0)
print(f'npv: {npv.mean()}')
std = npv.std()
confidence_interval = (npv.mean() - 1.96 * std / np.sqrt(npv.shape[0]), npv.mean() + 1.96 * std / np.sqrt(npv.shape[0]))
print(f'confidence interval: {confidence_interval}')