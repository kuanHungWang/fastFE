import QuantLib as ql
import numpy as np
import pandas as pd
from util import year_fraction
from curve_builder import (
    bootstrap_curve,
)
from vol_helper import create_black_vol_surface
from models import GarmanKohlagenProcessModel
from market_data import (
    get_deposit,
    get_swap,
    get_volatility_surface,
    get_price
)



# An example of fx linked product using Garman-Kohlagen model and monte carlo simulation to calculate fair value.
# Product term sheet:
# tenor: 1Y
# notional: 1M EUR
# pay 3M Euribor coupon, act360, fixing in advance
# receive 2% daily range accrual coupon, 30/360
# range: 0.99< EURUSD < 1.2
# for each payment period, use the fixing value 5 days prior to the payment date for remaining fixing period
# calculation of range accrual: 2% * (in range days / total days)


# Step 1. Set up parameters, including contract parameters, market conventions such as day count, date rolling convention, etc.
# contract parameters
notional = 1_000_000
coupon_rate = 0.02
upper_bound = 1.2
lower_bound = 0.99
fixing_in_advance = True
n_period_end_replacement = 5
tenor = '1Y'
frequency=ql.Period('3M')
settlement_days = 2
# conventions
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
rule = ql.DateGeneration.Forward
US_calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
EUR_calendar = ql.TARGET()
calendar = ql.JointCalendar(US_calendar, EUR_calendar)
libor_dayCount = ql.Actual360()
n_paths = 2**2

today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(settlement_days, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')





# Step 2. Prepare market data, including data to bootstrap curve and construct model.
# In this example: deposit and swap for both EUR and USD to bootstrap yield curve, volativlity surfaces and spot price for EURUSD to construct Garman-Kohlagen model
eur_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
eur_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

usd_deposit = get_deposit(['1M', '2M', '3M', '6M', '9M'])
usd_swap = get_swap(['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

eurusd_vol = get_volatility_surface('EUR', ['1M', '2M', '3M', '6M', '9M', '12M'], [1.05, 1.07, 1.09, 1.11, 1.13, 1.15])


# Step 3. Create curve and model, use previously created market data as input and calibration data.
eur_yieldCurve = bootstrap_curve('EUR', today, deposit=eur_deposit, swap=eur_swap)
usd_yieldCurve = bootstrap_curve('USD', today, deposit=usd_deposit, swap=usd_swap)
vol_surface = create_black_vol_surface(eurusd_vol, today)
spot = get_price('EUR')
fx_model = GarmanKohlagenProcessModel(usd_yieldCurve, eur_yieldCurve, vol_surface, spot)

# Step 4. Create Schedule
# For structured product, typically we need to create payment schedule and fixing schedule. For payment schedule, create multiple ones if needed for different legs, but always merge to one schedule.
# For this example, we create quarterly payment schedule and a daily fx fixing schedule to calculate daily range accrual.

terminationDate = calendar.advance(settlementDate, ql.Period(tenor))
endOfMonth= calendar.isEndOfMonth(terminationDate)
paymentSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
paymentSchedule = [d for d in paymentSchedule]
liborFixingSchedule = [calendar.advance(d,ql.Period(-settlement_days, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)

daily_fixing_days = ql.MakeSchedule(settlementDate, terminationDate, ql.Period('1d'), calendar=calendar)
print(f'daily_fixing_days: {len(daily_fixing_days)}')


# Step 5. Generate fx paths and calculate cashflows for monte carlo simulation before consideration of early termination event like auto-call.
# Use previously created model object to generate paths of underlying fixing values .
# Then apply the fixing values to calculate cashflows according to the contract term sheet.
# In this example, we have a quarterly fx-range accrual coupon of 2% accruing when 0.99< EURUSD < 1.2
# We also have a 3m Euribor leg, we use deterministic yield curve for libor fixings since the fair value is more related to fx price, and the tenor is relative short so is less subject to yield curve movement.


fx_fixing = fx_model.monte_carlo_paths(daily_fixing_days, numPaths=n_paths)


# libor cash flow under deterministic yield curve
discountFactors = [eur_yieldCurve.discount(d) for d in paymentSchedule]
discountFactors = pd.DataFrame(discountFactors, index=paymentSchedule)
print(f'discountFactors: \n{discountFactors}')
libor_index = ql.IborIndex('MyIndex', ql.Period('6m'), 2, ql.EURCurrency(), calendar, date_rolling_convention, True, libor_dayCount, ql.YieldTermStructureHandle(eur_yieldCurve))
libor_fixings = [libor_index.fixing(d) for d in liborFixingSchedule]
libor_fixings = pd.DataFrame(libor_fixings, paymentSchedule)
if fixing_in_advance:
    libor_fixings = libor_fixings.shift(1)
libor_year_fraction = np.array(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False))[:, np.newaxis]
libor_cashflows = notional * libor_fixings * libor_year_fraction
print(f'libor_cashflows: \n{libor_cashflows}')



# range accrual cash flow
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


# Step 6. Proccess early termination events
# It is important to distinguish between callable/putable features and auto-call features. Callable (or putable, cancellable, Bermudan-style) options give the holder discretionary rights to exercise when advantageous, while auto-call features are triggered automatically when predetermined market conditions are met, without any discretionary decision.
# In this example, there are no bermudan option nor auto-call feature. So we just discount the cashflows to present value. Then with npv of each path, we can have fair value and confidence interval.
# Note: in other cases, if it is a Bermudan-style option, we need to use Longstaff-Schwartz. If it is a auto-call feature, there are no particular class nor method to handle it. Implement on your own according to the term sheet.
present_value = range_accrual_cashflows * discountFactors.values
print(f'present_value(all paths): \n{present_value}')
print(f'expected present value: {present_value.mean(axis=1)}')
npv = present_value.sum(axis=0)
print(f'npv: {npv.mean()}')
std = npv.std()
confidence_interval = (npv.mean() - 1.96 * std / np.sqrt(npv.shape[0]), npv.mean() + 1.96 * std / np.sqrt(npv.shape[0]))
print(f'confidence interval: {confidence_interval}')