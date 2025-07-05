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
    create_heston_model_helper,
    create_black_vol_curve,
    create_black_vol_surface
)
from util import year_fraction
from market_data import get_volatility_surface



def calibration_detail(helpers):
    modelValues = [helper.modelValue() for helper in helpers]
    marketValues = [helper.marketValue() for helper in helpers]
    calibrationErrors = [helper.calibrationError() for helper in helpers]
    return pd.DataFrame({'modelValue': modelValues, 'marketValue': marketValues, 'calibrationError': calibrationErrors})

class GarmanKohlagenProcessModel():
    def __init__(self, foreignRiskCurve, domesticRiskFreeCurve, vol_curve, initialValue):
        self.foreignRiskCurve = foreignRiskCurve
        self.domesticRiskFreeCurve = domesticRiskFreeCurve
        self.vol_curve=vol_curve
        self.initialValue = initialValue
        foreignRisk_ts = ql.YieldTermStructureHandle(foreignRiskCurve)
        domesticRiskFree_ts = ql.YieldTermStructureHandle(domesticRiskFreeCurve)
        vol_ts = ql.BlackVolTermStructureHandle(vol_curve)
        initialValue = ql.QuoteHandle(ql.SimpleQuote(self.initialValue))
        
        process = ql.GarmanKohlagenProcess(initialValue, foreignRisk_ts, domesticRiskFree_ts, vol_ts)
        self.process = process


    def monte_carlo_paths(self, fixingSchedule:ql.Schedule, numPaths:int):
        process = self.process
        # Time grid
        dayCount = ql.Actual365Fixed()
        time_grid = year_fraction(fixingSchedule, dayCount, accoumulative=True)
        n_steps = len(time_grid) - 1
        dimension = process.factors()
        rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)

        # Simulate paths
        spot_paths = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            # Heston: first factor is the spot process
            spot_path = [v for v in values[0]]
            spot_paths.append(spot_path)

        spot_paths = np.array(spot_paths).T  # shape: (len(all_dates), numPaths)

        # Create DataFrame for all simulation dates
        spot_paths_df = pd.DataFrame(spot_paths, index=[d for d in fixingSchedule])

        return spot_paths_df


class BlackScholesMertonModel():
    def __init__(self, yield_curve, dividend_curve, vol_curve, initialValue):
        self.yield_curve = yield_curve
        self.dividend_curve = dividend_curve
        self.vol_curve=vol_curve
        self.initialValue = initialValue
        yield_ts = ql.YieldTermStructureHandle(yield_curve)
        dividend_ts = ql.YieldTermStructureHandle(dividend_curve)
        vol_ts = ql.BlackVolTermStructureHandle(vol_curve)
        initialValue = ql.QuoteHandle(ql.SimpleQuote(self.initialValue))
        
        process = ql.BlackScholesMertonProcess(initialValue, dividend_ts, yield_ts, vol_ts)
        self.process = process


    def monte_carlo_paths(self, fixingSchedule:ql.Schedule, numPaths:int):
        process = self.process
        # Time grid
        dayCount = ql.Actual365Fixed()
        time_grid = year_fraction(fixingSchedule, dayCount, accoumulative=True)
        n_steps = len(time_grid) - 1
        dimension = process.factors()
        rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)

        # Simulate paths
        spot_paths = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            # Heston: first factor is the spot process
            spot_path = [v for v in values[0]]
            spot_paths.append(spot_path)

        spot_paths = np.array(spot_paths).T  # shape: (len(all_dates), numPaths)

        # Create DataFrame for all simulation dates
        spot_paths_df = pd.DataFrame(spot_paths, index=[d for d in fixingSchedule])

        return spot_paths_df
        
class HullWhiteModel():
    def __init__(self, settlementDate, curve, currency):
        self.curve = curve
        self.currency = currency
        self.settlementDate = settlementDate
        self.model = None

    def calibrate(self, swaption:pd.DataFrame):
        builders ={'USD': create_USD_swaption_helpers, 'EUR': create_EUR_swaption_helpers, 'JPY': create_JPY_swaption_helpers, 'GBP': create_GBP_swaption_helpers, 'CHF': create_CHF_swaption_helpers, 'TWD': create_TWD_swaption_helpers}
        term_structure = ql.YieldTermStructureHandle(self.curve)
        model = ql.HullWhite(term_structure)
        engine = ql.JamshidianSwaptionEngine(model)
        helper_builder = builders[self.currency]
        helpers = helper_builder(swaption, self.curve, engine)

        optimization_method = ql.LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
        end_criteria = ql.EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
        model.calibrate(helpers, optimization_method, end_criteria)
        self.model = model
        a, sigma = model.params()
        self.process = ql.HullWhiteProcess(term_structure, a, sigma)
        try:
            self.calibration_detail = calibration_detail(helpers)
        except:
            self.calibration_error = None



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
        
        time_grid = year_fraction(all_dates, dayCount, accoumulative=True)
        n_steps = len(time_grid)-1
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
    def __init__(self, yield_curve, dividend_curve, calendar=ql.WeekendsOnly()):
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
        self.process = ql.HestonProcess(yield_term_structure, dividend_term_structure, initialValue,*model.params())

        self.model = model
        try:
            self.calibration_detail = calibration_detail(helpers)
        except:
            self.calibration_detail = None

    def monte_carlo_paths(self, fixingSchedule:ql.Schedule, numPaths:int):
        """
        generate paths based on fixing schedule
        fixingSchedule: fixing schedule
        numPaths: number of paths

        return: DataFrame with index as fixing dates, columns as paths
        """
        # Generate all daily dates between fixingSchedule[0] and fixingSchedule[-1]
        all_dates = ql.Schedule(fixingSchedule[0], fixingSchedule[-1], ql.Period('1d'), self.calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
        print(len(all_dates))

        # Set up the Heston process
        # parameters = self.model.params()
        # yield_term_structure = ql.YieldTermStructureHandle(self.yield_curve)
        # dividend_term_structure = ql.YieldTermStructureHandle(self.dividend_curve)
        # initialValue = ql.QuoteHandle(ql.SimpleQuote(spot))
        # process = ql.HestonProcess(yield_term_structure, dividend_term_structure, initialValue, *parameters)
        process = self.process
        # Time grid
        dayCount = ql.Actual365Fixed()
        time_grid = year_fraction(all_dates, dayCount, accoumulative=True)
        print(len(time_grid))
        print(len(all_dates))
        n_steps = len(time_grid) - 1
        dimension = process.factors()
        rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)

        # Simulate paths
        spot_paths = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            # Heston: first factor is the spot process
            spot_path = [v for v in values[0]]
            spot_paths.append(spot_path)

        spot_paths = np.array(spot_paths).T  # shape: (len(all_dates), numPaths)

        # Create DataFrame for all simulation dates
        all_dates_list = [d for d in all_dates]
        spot_paths_df = pd.DataFrame(spot_paths, index=all_dates_list)

        # Reindex to fixingSchedule (preserves order and handles missing dates)
        spot_paths_df = spot_paths_df.reindex([d for d in fixingSchedule])
        return spot_paths_df

class MultiAssetModel():
    def __init__(self, processes, correlation_matrix):
        self.processes = processes
        self.correlation_matrix = correlation_matrix
        
    def monte_carlo_paths(self, fixingSchedule:ql.Schedule, numPaths:int, dayCount:ql.DayCounter=ql.Actual365Fixed()):
        process = ql.StochasticProcessArray(self.processes, self.correlation_matrix)
        # Time grid
        time_grid = year_fraction(fixingSchedule, dayCount, accoumulative=True)
        n_steps = len(time_grid) - 1
        dimension = process.factors()
        rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
        sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
        pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)

        # Simulate paths
        spot_paths = [[] for _ in range(len(self.processes))]
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            for i, value in enumerate(values):
                spot_paths[i].append([v for v in value])
        
        transposed_paths = [np.array(path).T for path in spot_paths]
            

        # Create DataFrame for all simulation dates
        spot_paths_df = [pd.DataFrame(transposed_path, index=[d for d in fixingSchedule]) for transposed_path in transposed_paths]

        return spot_paths_df
        

if __name__ == '__main__':
    heston_vol_df = pd.DataFrame({
        'option_tenor': ['1M', '2M', '3M', '6M', '9M'],
        'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
        'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
    }) 
    black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M']) 
    vol_curve = create_black_vol_curve(black_vol_df, ql.Date().todaysDate())
    spot = 0.02
    today = ql.Date().todaysDate()
    dayCount = ql.Actual365Fixed()
    riskFreeCurve = ql.FlatForward(today, 0.04, dayCount)
    dividendCurve = ql.FlatForward(today, 0.01, dayCount)
    black_model = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_curve, spot)
    heston_model = HestonModel(riskFreeCurve, dividendCurve, ql.TARGET())
    heston_model.calibrate(heston_vol_df, spot)
    fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), ql.TARGET(), ql.Following, ql.Following, ql.DateGeneration.Backward, False)
    paths = heston_model.monte_carlo_paths(fixingSchedule, 2**2)
    print([d for d in fixingSchedule])
    print(paths)
    print(heston_model.calibration_detail)
    spot=100
    black_model = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_curve, spot)
    paths = black_model.monte_carlo_paths(fixingSchedule, 2**2)
    print(f'\npath of black_model: \n{paths}')

    fxModel=GarmanKohlagenProcessModel(riskFreeCurve, dividendCurve, vol_curve, spot)
    paths = fxModel.monte_carlo_paths(fixingSchedule, 2**2)
    print(f'\npath of fxModel: \n{paths}')

    df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])

    spot = 70
    vol_surface = create_black_vol_surface(df_vol_surface, ql.Date().todaysDate())
    equity_model = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_surface, spot)
    paths = equity_model.monte_carlo_paths(fixingSchedule, 2**2)
    print(f'\npath of equity_model: \n{paths}')

    corrMatrix = [[1, 0.5], [0.5, 1]]
    processes = [black_model.process, equity_model.process]
    multiAssetModel = MultiAssetModel(processes, corrMatrix)
    paths = multiAssetModel.monte_carlo_paths(fixingSchedule, 2**2)
    print(f'\npath of multiAssetModel:')
    for path in paths:
        print(path)
    
    

    
    

        
        
        
