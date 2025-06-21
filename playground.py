import QuantLib as ql
import numpy as np
import pandas as pd
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
from swaption_helper import (create_swaption_helper, 
create_USD_swaption_helpers, create_EUR_swaption_helpers,
create_JPY_swaption_helpers, create_GBP_swaption_helpers,
create_CHF_swaption_helpers, create_TWD_swaption_helpers)
   

from curve_builder import bootstrap_USD_curve
from util import get_nearest_fixing_date, year_fraction, combine_schedule




class HullWhiteModel():
    def __init__(self, settlementDate, curve, currency):
        self.curve = curve
        self.currency = currency
        self.settlementDate = settlementDate
        self.model = None

    def calibrate(self, swaption:pd.DataFrame):
        builders ={'USD': create_USD_swaption_helpers, 'EUR': create_EUR_swaption_helpers, 'JPY': create_JPY_swaption_helpers, 'GBP': create_GBP_swaption_helpers, 'CHF': create_CHF_swaption_helpers, 'TWD': create_TWD_swaption_helpers}
        term_structure = ql.YieldTermStructureHandle(self.curve)
        model = ql.HullWhite(term_structure);
        engine = ql.JamshidianSwaptionEngine(model)
        helper_builder = builders[self.currency]
        helpers = helper_builder(swaption, self.curve, engine)

        optimization_method = ql.LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
        end_criteria = ql.EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
        model.calibrate(helpers, optimization_method, end_criteria)
        self.model = model

    def monte_carlo_paths(self,  index_factory, fixingSchedule, paymentSchedule, numPaths):
        a, sigma = self.model.params()
        term_structure = ql.YieldTermStructureHandle(self.curve)
        process = ql.HullWhiteProcess(term_structure, a, sigma)


        # As hull-white model is a short rate model, underlying rate must generate every day, not only fixing dates.
        frequency = ql.Period('1d')
        all_dates = ql.Schedule(self.settlementDate, curve.maxDate(), frequency, calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
        print(f'first date: {all_dates[0]}, last date: {all_dates[-1]}')
        dayCount=ql.Actual365Fixed()

        dimension = process.factors()
        n_steps = len(all_dates)-1
        time_grid = year_fraction(all_dates, dayCount, accoumulative=True)
        rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)


        underlying_path = []
        forward_curves=[]
        fixings = []
        discountFactors = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            underlying = values[0]
            underlying = [s for s in underlying]
            underlying_path.append(underlying)
            fwd_crv = ql.ForwardCurve([d for d in all_dates], underlying, dayCount)
            print(f'fwd_crv start date: {fwd_crv.dates()[0]}, end date: {fwd_crv.dates()[-1]}')
            ts = ql.YieldTermStructureHandle(fwd_crv)
            index=index_factory(ts)
            fixings.append([index.fixing(d) for d in fixingSchedule])
            discountFactors.append([fwd_crv.discount(d) for d in paymentSchedule])
            forward_curves.append(fwd_crv)
            
        underlying_path = np.array(underlying_path).transpose()
        fixings = np.array(fixings).transpose()
        discountFactors = np.array(discountFactors).transpose()
        return underlying_path, fixings, discountFactors, forward_curves

def create_ibor_6M(ts):
    return ql.IborIndex('MyIndex', ql.Period('6m'), 2, currency, calendar, date_rolling_convention, True, dayCount, ts)

fixed_leg_conventions = Conventions.USFixedLegConventions()
floating_leg_conventions = Conventions.USFloatingLegConventions()
calendar = fixed_leg_conventions['calendar']
date_rolling_convention = fixed_leg_conventions['date_rolling_convention']
date_termination_convention = fixed_leg_conventions['date_termination_convention']
frequency = floating_leg_conventions['frequency']
dayCount = fixed_leg_conventions['dayCounter']
currency = fixed_leg_conventions['currency']
endOfMonth = fixed_leg_conventions['endOfMonth']
rule = fixed_leg_conventions['rule']

df_deposit = pd.DataFrame({
'tenor': ['1M', '2M', '3M', '6M', '9M'],
'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})

df_swap = pd.DataFrame({
    'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
    'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
})


today = ql.Date().todaysDate()
today = calendar.advance(today,ql.Period(0, ql.Days))
settlementDate = calendar.advance(today,ql.Period(2, ql.Days))
ql.Settings.instance().evaluationDate = today
print(f'today: {today}, settlementDate: {settlementDate}')
curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
df_swaption = pd.DataFrame({
    'maturity': ['2Y', '3Y'],
    'length': ['5Y', '5Y'],
    'volatility': [0.0055, 0.0055]
})



hw_model = HullWhiteModel(today, curve, 'USD')
hw_model.calibrate(df_swaption)





terminationDate = calendar.advance(settlementDate, ql.Period(3, ql.Years))
print(f'settlementDate: {settlementDate}, terminationDate: {terminationDate}')
paySchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)
recSchedule = ql.Schedule(settlementDate, terminationDate, frequency, calendar, date_rolling_convention, date_termination_convention, rule, endOfMonth)



paymentSchedule = combine_schedule(paySchedule, recSchedule)

paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]
print(paySchedule)
print(recSchedule)
print(f'len(paySchedule): {len(paymentSchedule)}, len(recSchedule): {len(recSchedule)}, len(paymentSchedule): {len(paymentSchedule)}')


fixingSchedule = [calendar.advance(d,ql.Period(-2, ql.Days)) for d in paymentSchedule]
print('Fixing date, Payment date')
for d1, d2 in zip(fixingSchedule, paymentSchedule):
    print(f'{d1},       {d2}')
hw_model.monte_carlo_paths(create_ibor_6M, fixingSchedule, paymentSchedule, 2*3)

