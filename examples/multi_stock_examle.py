import QuantLib as ql
import numpy as np
import pandas as pd
from fastFE.util import (
    get_nearest_fixing_date,
    year_fraction,
    combine_schedule
)
from fastFE.curve_builder import bootstrap_curve
from fastFE.vol_helper import create_black_vol_surface
from fastFE.models import (
    BlackScholesMertonModel,
    MultiAssetModel
)
# NOTE: market_data provides MOCK/SYNTHETIC data for testing only. Not real market data.
from market_data import (
    get_deposit,
    get_swap,
    get_volatility_surface,
    get_price,
    get_dividend_rate
)


# An example of multi-equity linked swap using monte-carlo simulation by multiAssetModel model.
# Product term sheet:
# linked stocks: AAPL, MSFT
# underlying: lowest performance of underlyings
# Calculation of performance: S_t / S_0 (price divided by initial price)
# tenor: 3Y, frequency 3M
# receive fixed coupon: 10% annualy, 30/360
# pay 3M libor, act/360.  fixing-in-advance, 2 days before payment date
# bermudian knock-out: 110% 
# european knock-in: 95% 
# stike: 100% 
# auto call(bermudan knock-out): for each payment date, if the underlying is higher than the strike, the whole contract will be terminated and no more further cashflow after that payment date.
# final sell put:
# if auto call has not occur by the final payment date and last underlying is lower than european knock-in, pay max(strike - underlying, 0)


# Step 1. Set up parameters, including contract parameters, market conventions such as day count, date rolling convention, etc.
# contract parameters
notional = 1_000_000
bermudian_knock_out = 1.1
strike = 1.0
european_knock_in = 0.95
coupon_rate = 0.1
fixing_in_advance = True
ternor = 3
frequency = '6M'
# conventions
calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
frequency = ql.Period(frequency)

currency = ql.USDCurrency()
rule = ql.DateGeneration.Forward
dayCount = ql.Actual365Fixed()
libor_dayCount = ql.Actual360()
libor_fixing_in_advance = True


today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))  # ensure today is a business day (In case of using in non-trading day)
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f' trade date: {today}')
print(f' settlement date: {settlementDate}')

# Step 2. Prepare market data for curve and model.
# For multi asset model, we typically need data required to child models and correlation matrix for multi-asset model, and also yield curve for discounting.
# For this example, we  need: 
# (1) interest rate curve data for discounting, 
# (2) equity volatility data , spot price, dividend curve of both underlyings for each equity model.
# (3) correlation matrix of both underlyings for multi-asset model. (Can calculate from historical data or just give a reasonable assumption)

df_deposit = get_deposit('USD', ['1M', '2M', '3M', '6M', '9M'])
df_swap = get_swap('USD', ['1Y', '2Y', '5Y', '7Y', '10Y', '15Y', '20Y', '25Y', '30Y'])

spot_AAPL = get_price('AAPL')
dividend_rate_AAPL = get_dividend_rate('AAPL')
df_vol_surface_AAPL = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [250, 275, 300, 325, 350])

spot_MSFT = get_price('MSFT')
dividend_rate_MSFT = get_dividend_rate('MSFT')
df_vol_surface_MSFT = get_volatility_surface('MSFT', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])

corrMatrix = [[1, 0.5], [0.5, 1]]

# Step 3. Create curves and models, use previously created market data as input.

riskFreeCurve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)
dividendCurve_AAPL = ql.YieldTermStructureHandle(ql.FlatForward(today, dividend_rate_AAPL, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
vol_surface_AAPL = create_black_vol_surface(df_vol_surface_AAPL, today)
black_model_vol_surface_AAPL = BlackScholesMertonModel(riskFreeCurve, dividendCurve_AAPL, vol_surface_AAPL, spot_AAPL)

dividendCurve_MSFT = ql.YieldTermStructureHandle(ql.FlatForward(today, dividend_rate_MSFT, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
vol_surface_MSFT = create_black_vol_surface(df_vol_surface_MSFT, today)
black_model_vol_surface_MSFT = BlackScholesMertonModel(riskFreeCurve, dividendCurve_MSFT, vol_surface_MSFT, spot_MSFT)

processes = [black_model_vol_surface_AAPL.process, black_model_vol_surface_MSFT.process]  # note: don't support heston model as sub-process
multiAssetModel = MultiAssetModel(processes, corrMatrix)



# Step 4. Generate schedules
# For structured product, typically we need to create payment schedule and fixing schedule. For payment schedule, create multiple ones if needed for different legs, but always merge to one schedule.
# For this example, we create quarterly payment schedule and corresponding fixing schedule (2 business days before payment).
terminationDate = calendar.advance(settlementDate, ql.Period(ternor, ql.Years))
endOfMonth = calendar.isEndOfMonth(terminationDate)
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
paymentSchedule = combine_schedule(paySchedule, recSchedule)  # merge two schedules
fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]  # fixing schedule(2 business days before payment date)
# convert to list
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]

# Step 5. Generate equity paths and calculate cashflows for monte carlo simulation before consideration of early termination event like auto-call.
# Use previously created model object to generate paths of underlying fixing values .
# Then apply the fixing values to calculate cashflows according to the contract term sheet.
# In this example, we have a libor leg and fixed-rate coupon leg and a equity final payoff (pay max(strike - S_T, 0) with european knock-in), 
# for libor leg we use deterministic yield curve for libor fixings.
# for equity leg we use fixing paths generated by multiAssetModel.

# generate monte carlo paths
stock_paths = multiAssetModel.monte_carlo_paths(fixingSchedule, 4)
return_AAPL = stock_paths[0]/stock_paths[0].iloc[0]
return_MSFT = stock_paths[1]/stock_paths[1].iloc[0]







# fixed-rate coupon cashflows
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))
fixed_cashflows = pd.DataFrame(notional * coupon_rate * year_fraction_rec, index=recSchedule)
print(f'\nfixed_cashflows: \n{fixed_cashflows}')


# libor cash flow under deterministic yield curve
discountFactors = [riskFreeCurve.discount(d) for d in paymentSchedule]
discountFactors = pd.DataFrame(discountFactors, index=paymentSchedule)
print(f'discountFactors: \n{discountFactors}')
libor_index = ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, libor_dayCount, riskFreeCurve)
libor_fixings = [libor_index.fixing(d) for d in fixingSchedule]
libor_fixings = pd.DataFrame(libor_fixings, paymentSchedule)
if fixing_in_advance:
    libor_fixings = libor_fixings.shift(1)
libor_year_fraction = np.array(year_fraction(paymentSchedule, libor_dayCount, accoumulative=False))[:, np.newaxis]
libor_cashflows = notional * libor_fixings * libor_year_fraction
print(f'libor_cashflows: \n{libor_cashflows}')



# ensure same index for case that two leg has different payment schedule
fixed_cashflows = fixed_cashflows.reindex(paymentSchedule) 
libor_cashflows = libor_cashflows.reindex(paymentSchedule)
print(f'\nlibor_cashflows: \n{libor_cashflows}')
net_cashflows = fixed_cashflows - libor_cashflows  
print(f'\nnet cashflows: \n{net_cashflows}')


# vanilla option payoff regardless of knock-in
lower_return = pd.DataFrame(
    np.minimum(return_AAPL, return_MSFT),
    index=stock_paths[0].index,
    columns=stock_paths[0].columns
)
print(f'nlower_return :\n {lower_return}')
S_T = lower_return.iloc[-1]
vanilla_option_payoff = notional * np.maximum(strike - S_T, 0)
print(f'\nvanilla option payoff regardless of knock-in: \n{vanilla_option_payoff}')
# option payoff with condition of knock-in
knockin = S_T < european_knock_in
print(f'knockin: \n{knockin}')
eki_option_payoff = vanilla_option_payoff * knockin
print(f'\noption payoff with condition of knock-in: \n{eki_option_payoff}')
df_eki_option_payoff = pd.DataFrame(np.zeros_like(lower_return, dtype=float), index=paymentSchedule)
df_eki_option_payoff.iloc[-1] = eki_option_payoff
print(f'\ndf_eki_option_payoff: \n{df_eki_option_payoff}')
total_cashflow = net_cashflows.values + df_eki_option_payoff
print(f'\ntotal_cashflow: \n{total_cashflow}')

# Step 6, Take into account the auto-call event
# It is important to distinguish between callable/putable features and auto-call features. Callable (or putable, cancellable, Bermudan-style) options give the holder discretionary rights to exercise when advantageous, while auto-call features are triggered automatically when predetermined market conditions are met, without any discretionary decision.
# In this example, it is a auto-call feature. Note in other cases, if it is a Bermudan-style option, we need to use Longstaff-Schwartz.
# Create a bool survival mask by stock fixing value according the auto-call condition in the term sheet. 
# Then apply the mask to the cashflows. 
# Finally, discount the cashflows to present value. With npv of each path, we can have fair value and confidence interval.
# In this example: if the stock price is higher than the strike(100% of initial stock price), the whole contract will be terminated and no more further cashflow after that payment date.

# survival mask
survival = pd.DataFrame(np.zeros_like(lower_return, dtype=bool), index=paymentSchedule)
still_alive = np.ones((1, lower_return.shape[1]), dtype=bool)
print(f'\nlower_return: \n{lower_return}')
for d in paymentSchedule:
    survival.loc[d] = still_alive
    fixing_day = get_nearest_fixing_date(d, fixingSchedule)
    still_alive = np.bitwise_and(still_alive, lower_return.loc[fixing_day] < bermudian_knock_out)
print(f'\nsurvival: \n{survival}')



# apply survival mask to cashflows and discount.
cashflow_survival = total_cashflow.values * survival
print(f'\n\ncashflow_survival: \n{cashflow_survival}')
present_value = cashflow_survival * discountFactors.values
print(f'\npresent_value: \n{present_value}')
npv = np.sum(present_value, axis=0)
print(f'npv: \n{npv}')
valuation = npv.mean()
print(f'valuation: {valuation}')
std = npv.std()
confidence_interval = (valuation - 1.96 * std / np.sqrt(npv.shape[0]), valuation + 1.96 * std / np.sqrt(npv.shape[0]))
print(f'confidence interval: {confidence_interval}')