import QuantLib as ql
import numpy as np
import pandas as pd
from util import get_nearest_fixing_date
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
Keywords: fx linked, target redemption, TRF, forward, multi-period.
tenor: 1Y
underlying: EURUSD
notional: EUR 1,000,000
payment frequency: monthly
At each period, buy EUR against USD at strike, cash settlement in EUR
terminate when accumated profit reach target
accumulated profit = sum of (EUR fixing - strike) , uncapped
fixing date: 2 days before payment date"""


# contract parameters
notional = 1_000_000
strike = 1.1
target = 0.2


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

frequency=ql.Period('1M')
terminationDate = calendar.advance(settlementDate, ql.Period('1Y'))
endOfMonth = calendar.isEndOfMonth(terminationDate)

date_rolling_convention = ql.ModifiedFollowing
date_termination_convention = ql.ModifiedFollowing
rule = ql.DateGeneration.Forward
endOfMonth= calendar.isEndOfMonth(terminationDate)
paymentSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)

paymentSchedule = [d for d in paymentSchedule]
fixingSchedule = [calendar.advance(d, ql.Period('-2d')) for d in paymentSchedule]

print(f'paymentSchedule: ({len(paymentSchedule)} periods)\n{paymentSchedule}')
print(f'fixingSchedule: ({len(fixingSchedule)} fixing days)\n{fixingSchedule}')

daily_fixing_days = ql.MakeSchedule(settlementDate, terminationDate, ql.Period('1d'), calendar=calendar)
print(len(daily_fixing_days))

n_paths = 2**2
fx_fixing = fx_model.monte_carlo_paths(fixingSchedule, numPaths=n_paths)

print(f'\nfx_fixing: \n{fx_fixing}')


cashflows = pd.DataFrame((fx_fixing.values - strike)/fx_fixing.values*notional, index=paymentSchedule)

print(f'cashflows: \n{cashflows}')

accumulated = 0
# survival probability
survival = pd.DataFrame(np.zeros_like(cashflows, dtype=bool), index=paymentSchedule)
still_alive = np.ones((1, cashflows.shape[1]), dtype=bool)
for d in paymentSchedule:
    survival.loc[d] = still_alive
    fixing_day = get_nearest_fixing_date(d, fixingSchedule)
    S_t = fx_fixing.loc[fixing_day]
    accumulated += np.maximum(S_t - strike, 0)
    still_alive = np.bitwise_and(still_alive, accumulated < target)  # trigger at next period, so update still_alive at next period
print(f'survival: \n{survival}')



discountFactors = pd.DataFrame([eur_yieldCurve.discount(d) for d in paymentSchedule], index=paymentSchedule)
print(f'discountFactors: \n{discountFactors}')
cashflow_survival = cashflows * survival
print(f'cashflow_survival: \n{cashflow_survival}')
present_value = cashflow_survival * discountFactors.values
print(f'present_value(all paths): \n{present_value}')
print(f'expected present value: {present_value.mean(axis=1)}')
npv = present_value.sum(axis=0)
print(f'npv: {npv.mean()}')
std = npv.std()
confidence_interval = (npv.mean() - 1.96 * std / np.sqrt(npv.shape[0]), npv.mean() + 1.96 * std / np.sqrt(npv.shape[0]))
print(f'confidence interval: {confidence_interval}')