import QuantLib as ql
import numpy as np
import pandas as pd
from fastFE.util import (
    get_nearest_fixing_date,
    year_fraction
)
from fastFE.curve_builder import bootstrap_curve
from fastFE.models import HestonModel
from market_data import (
    get_deposit,
    get_swap,
    get_price,
    get_volatility_table,
    get_dividend_rate
)


# An example of equity linked product using Heston model and monte carlo simulation to calculate fair value.
# Product term sheet:
# tenor: 3Y, frequency 3M
# receive fixed coupon: 10% annualy, 30/360
# pay 3M libor, act/360.  fixing-in-advance, 2 days before payment date
# bermudian knock-out: 110% of initial stock price
# european knock-in: 95% of initial stock price
# stike: 100% of initial stock price
# auto call: for each payment date, if the stock price is higher than the strike, the whole contract will be terminated and no more further cashflow after that payment date.
# final sell put:
# if auto call has not occur by the final payment date and last stock price is lower than european knock-in, pay max(strike - S_T, 0)
# Note: Although it is a Equtiy linked, but it is a swap so there is also libor index envloved. But we will use deterministic yield curve to calculate libor cashflows since the fair value is more related to equity price, and the tenor is relative short so is less subject to yield curve movement.


# Step 1. Set up parameters, including contract parameters, market conventions such as day count, date rolling convention, etc.


# contract parameters
notional = 1_000_000
bermudian_knock_out = 1.1
strike = 1.0
european_knock_in = 0.95
coupon_rate = 0.1
fixing_in_advance = True
settlement_days = 2
tenor = '3Y'
frequency = '3M'
# market conventions
US_calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
EUR_calendar = ql.TARGET()
calendar = ql.JointCalendar(US_calendar, EUR_calendar)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
frequency = ql.Period(frequency)
coupon_dayCount = ql.Thirty360(ql.Thirty360.USA)
libor_dayCount = ql.Actual360()
currency = ql.USDCurrency()
rule = ql.DateGeneration.Forward

# set evaluation date
today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(settlement_days, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')

# Step 2. Prepare market data, including data to bootstrap curves and data to calibrate models.
# For equity linked products, we typically need: (1) interest rate curve data for discounting, (2) equity volatility data for equity model calibration, (3) current equity spot price and dividend information.

# Market data to bootstrap interest rate curve
df_deposit = get_deposit('USD', ['1M', '2M', '3M', '6M', '9M'])
df_swap = get_swap('USD', ['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

# Equity volatility data to calibrate Heston model
# For equity linked products, volatility surface data is crucial for accurate pricing


df_heston_vol = get_volatility_table('AAPL', ['1M', '3M', '6M', '9M'], [0.015,  0.02,  0.025])



# Step 3. Create curves and models, use previously created market data as input and calibration data.
# For equity linked products, we need: (1) yield curve for discounting, (2) dividend curve for equity forward calculation, (3) equity model (e.g., Heston) for volatility dynamics.
yieldCurve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)

# Equity market data: spot price and dividend information
spot = get_price('AAPL')
dividend_rate = get_dividend_rate('AAPL')
dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, dividend_rate, ql.Actual365Fixed()))
heston_model = HestonModel(yieldCurve, dividendCurve, calendar)
heston_model.calibrate(df_heston_vol, spot)

# Step 4. Create Schedules
# For structured product, typically we need to create payment schedule and fixing schedule. For payment schedule, create multiple ones if needed for different legs, but always merge to one schedule.
# For this example, we create quarterly payment schedule and corresponding fixing schedule (2 business days before payment).

terminationDate = calendar.advance(settlementDate, ql.Period(tenor))
endOfMonth = calendar.isEndOfMonth(terminationDate)

paymentSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
fixingSchedule = [calendar.advance(d,ql.Period(-settlement_days, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)

# convert original quantlib schedule object to list to use in pandas index
paymentSchedule = [d for d in paymentSchedule]
fixingSchedule = [d for d in fixingSchedule]

# Step 5. Generate equity paths and calculate cashflows for monte carlo simulation before consideration of early termination event like auto-call.
# Use previously created model object to generate paths of underlying fixing values .
# Then apply the fixing values to calculate cashflows according to the contract term sheet.
# In this example, we have a libor leg and fixed-rate coupon leg and a equity final payoff (pay max(strike - S_T, 0) with european knock-in), 
# for libor leg we use deterministic yield curve for libor fixings.
# for equity leg we use fixing paths generated by Heston model.

# Calculate year fractions for different legs
coupon_year_fraction = pd.DataFrame(year_fraction(paymentSchedule, coupon_dayCount, accoumulative=False), index=paymentSchedule)
libor_year_fraction = pd.DataFrame(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False), index=paymentSchedule)

# Generate equity price paths using Heston model
equity_fixings = heston_model.monte_carlo_paths(fixingSchedule, 2**2)

print(f'equity_fixings: \n{equity_fixings}')

# Calculate interest rate cashflows

# libor cash flow under deterministic yield curve
discountFactors = [yieldCurve.discount(d) for d in paymentSchedule]
discountFactors = pd.DataFrame(discountFactors, index=paymentSchedule)
print(f'discountFactors: \n{discountFactors}')
libor_index = ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, libor_dayCount, yieldCurve)
libor_fixings = [libor_index.fixing(d) for d in fixingSchedule]
libor_fixings = pd.DataFrame(libor_fixings, paymentSchedule)
if fixing_in_advance:
    libor_fixings = libor_fixings.shift(1)
libor_year_fraction = np.array(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False))[:, np.newaxis]
libor_cashflows = notional * libor_fixings * libor_year_fraction
print(f'libor_cashflows: \n{libor_cashflows}')

# Calculate fixed coupon cashflows
# fixed coupon cashflow before auto-call
coupon_year_fraction = np.array(year_fraction(paymentSchedule, coupon_dayCount, accoumulative=False))[:, np.newaxis]
coupon_cashflow = notional * coupon_rate * coupon_year_fraction
coupon_cashflow = pd.DataFrame(coupon_cashflow, index=paymentSchedule)
print(f'coupon_cashflow: \n{coupon_cashflow}')

swap_cashflow = coupon_cashflow - libor_cashflows
print(f'swap_cashflow: \n{swap_cashflow}')

# Calculate equity-linked payoffs


# vanilla option payoff regardless of knock-in  (pay max(strike - S_T, 0))
S_T = equity_fixings.iloc[-1]

vanilla_option_payoff = notional * np.maximum(strike*spot - S_T, 0)
print(f'vanilla option payoff regardless of knock-in: \n{vanilla_option_payoff}')

# option payoff with condition of knock-in
knockin = S_T < european_knock_in * spot
print(f'knockin: \n{knockin}')
eki_option_payoff = vanilla_option_payoff * knockin
print(f'option payoff with condition of knock-in: \n{eki_option_payoff}')
# Although the payoff is only one period, convert it to a cashflow with the same schedule as swap_cashflow for to work with other cashflows
df_eki_option_payoff = pd.DataFrame(np.zeros_like(equity_fixings, dtype=float), index=paymentSchedule)
df_eki_option_payoff.iloc[-1] = eki_option_payoff
print(f'df_eki_option_payoff: \n{df_eki_option_payoff}')
total_cashflows = swap_cashflow.values - df_eki_option_payoff
print(f'total_cashflows: \n{total_cashflows}')


# Step 6, Take into account the auto-call event
# It is important to distinguish between callable/putable features and auto-call features. Callable (or putable, cancellable, Bermudan-style) options give the holder discretionary rights to exercise when advantageous, while auto-call features are triggered automatically when predetermined market conditions are met, without any discretionary decision.
# In this example, it is a auto-call feature. Note in other cases, if it is a Bermudan-style option, we need to use Longstaff-Schwartz.
# Create a bool survival mask by stock fixing value according the auto-call condition in the term sheet. 
# Then apply the mask to the cashflows. 
# Finally, discount the cashflows to present value. With npv of each path, we can have fair value and confidence interval.
# In this example: if the stock price is higher than the strike(100% of initial stock price), the whole contract will be terminated and no more further cashflow after that payment date.

# survival mask
survival = pd.DataFrame(np.zeros_like(equity_fixings, dtype=bool), index=paymentSchedule)
still_alive = np.ones((1, equity_fixings.shape[1]), dtype=bool)
for d in paymentSchedule:
    survival.loc[d] = still_alive
    fixing_day = get_nearest_fixing_date(d, fixingSchedule)
    still_alive = np.bitwise_and(still_alive, equity_fixings.loc[fixing_day] < bermudian_knock_out * spot) # trigger at next period, so update still_alive at next period
print(f'survival: \n{survival}')


# apply survival mask to cashflows and discount.
cashflow_survival = total_cashflows * survival
print(f'cashflow_survival: \n{cashflow_survival}')
present_value = cashflow_survival * discountFactors.values
print(f'present_value: \n{present_value}')
npv = np.sum(present_value, axis=0)
print(f'npv: \n{npv}')
valuation = npv.mean()
print(f'valuation: {valuation}')
std = npv.std()
confidence_interval = (valuation - 1.96 * std / np.sqrt(npv.shape[0]), valuation + 1.96 * std / np.sqrt(npv.shape[0]))
print(f'confidence interval: {confidence_interval}')