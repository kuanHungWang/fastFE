import QuantLib as ql
import pandas as pd
import numpy as np
from typing import List, Callable
from vol_helper import (
    create_USD_swaption_helpers,
    create_EUR_swaption_helpers,
    create_JPY_swaption_helpers,
    create_GBP_swaption_helpers,
    create_CHF_swaption_helpers,
    create_TWD_swaption_helpers,
    create_heston_model_helper
)
from util import year_fraction

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

    def monte_carlo_paths(self,  index_factories, fixingSchedule, paymentSchedule, numPaths):
        a, sigma = self.model.params()
        term_structure = ql.YieldTermStructureHandle(self.curve)
        process = ql.HullWhiteProcess(term_structure, a, sigma)


        # As hull-white model is a short rate model, underlying rate must generate every day, not only fixing dates.
        frequency = ql.Period('1d')
        all_dates = ql.Schedule(self.settlementDate, self.curve.maxDate(), frequency, ql.NullCalendar(), ql.Following, ql.Following, ql.DateGeneration.Backward, False)
        # print(f'first date: {all_dates[0]}, last date: {all_dates[-1]}')
        print(len([d for d in all_dates]))
        dayCount=ql.Actual365Fixed()

        dimension = process.factors()
        n_steps = len(all_dates)-1
        time_grid = year_fraction(all_dates, dayCount, accoumulative=True)
        rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)


        underlying_path = []
        forward_curves=[]
        fixings_list = [[] for _ in index_factories]
        discountFactors = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            underlying = values[0]
            underlying = [s for s in underlying]
            underlying_path.append(underlying)
            fwd_crv = ql.ForwardCurve([d for d in all_dates], underlying, dayCount)
            # print(f'fwd_crv start date: {fwd_crv.dates()[0]}, end date: {fwd_crv.dates()[-1]}')
            ts = ql.YieldTermStructureHandle(fwd_crv)
            for index_factory, fixings in zip(index_factories, fixings_list):
                index=index_factory(ts)
                fixings.append([index.fixing(d) for d in fixingSchedule])
            discountFactors.append([fwd_crv.discount(d) for d in paymentSchedule])
            forward_curves.append(fwd_crv)
            
        underlying_path = np.array(underlying_path).transpose()
        fixings_list = [np.array(fixings).transpose() for fixings in fixings_list]
        discountFactors = np.array(discountFactors).transpose()

        # Helper to convert QuantLib Dates to Python date
        def ql_to_date(qld):
            return qld.to_date() if hasattr(qld, 'to_date') else ql.Date(qld).to_date()

        # Do not convert schedules to Python dates here
        # all_dates_idx = [ql_to_date(d) for d in all_dates]
        # fixingSchedule_idx = [ql_to_date(d) for d in fixingSchedule]
        # paymentSchedule_idx = [ql_to_date(d) for d in paymentSchedule]

        # Convert to DataFrames with appropriate indices
        underlying_path_df = pd.DataFrame(underlying_path, index=[d for d in all_dates])
        fixings_dfs = [pd.DataFrame(fixings, index=[d for d in fixingSchedule]) for fixings in fixings_list]
        discountFactors_df = pd.DataFrame(discountFactors, index=[d for d in paymentSchedule])

        return underlying_path_df, fixings_dfs, discountFactors_df



class HestonModel():
    def __init__(self, yield_curve, dividend_curve, calendar):
        self.yield_curve = yield_curve
        self.dividend_curve = dividend_curve
        self.calendar = calendar
        self.model = None

    def calibrate(self, vol:pd.DataFrame, spot:float):
        initialValue = ql.QuoteHandle(ql.SimpleQuote(spot))
        theta = 0.010
        kappa = 0.600
        sigma = 0.400
        rho = -0.15
        v0 = 0.02
        yield_term_structure = ql.YieldTermStructureHandle(self.yield_curve)
        dividend_term_structure = ql.YieldTermStructureHandle(self.dividend_curve)
        hestonProcess = ql.HestonProcess(yield_term_structure, dividend_term_structure, initialValue, v0, kappa, theta, sigma, rho)
        model = ql.HestonModel(hestonProcess)
        engine = ql.AnalyticHestonEngine(model)
        helpers = create_heston_model_helper(vol, spot, self.yield_curve, self.dividend_curve, self.calendar, engine)
        lm = ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8)
        endCriteria=ql.EndCriteria(500, 300, 1.0e-8,1.0e-8, 1.0e-8)
        model.calibrate(helpers, lm, endCriteria)
        self.model = model


if __name__ == '__main__':
    heston_vol_df = pd.DataFrame({
        'option_tenor': ['1M', '2M', '3M', '6M', '9M'],
        'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
        'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
    }) 
    spot = 0.02
    today = ql.Date().todaysDate()
    dayCount = ql.Actual365Fixed()
    riskFreeCurve = ql.FlatForward(today, 0.04, dayCount)
    dividendCurve = ql.FlatForward(today, 0.01, dayCount)
    heston_model = HestonModel(riskFreeCurve, dividendCurve, ql.NullCalendar())
    heston_model.calibrate(heston_vol_df, spot)
        


        
        
        
