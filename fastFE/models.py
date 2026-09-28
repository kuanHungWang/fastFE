import QuantLib as ql
import pandas as pd
import numpy as np
from typing import List, Callable, Dict, Literal, Optional
from .vol_helper import (
    create_swaption_helper,
    create_heston_model_helper,
    create_black_vol_curve,
    create_black_vol_surface
)
from .util import simulation_time_grid
from .market_data import get_volatility_surface

from .type_hint import IndexFactory, Schedule

def _gaussian_multi_path_generator(process, time_grid, seed=None):
    """
    Create a GaussianMultiPathGenerator for process on time_grid.
    With seed=None (or 0), QuantLib draws a seed from its clock-based SeedGenerator, so paths differ between calls.
    """
    n_steps = len(time_grid) - 1
    dimension = process.factors()
    uniform = ql.UniformRandomGenerator() if seed is None else ql.UniformRandomGenerator(seed)
    rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, uniform)
    sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
    return ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)

def calibration_detail(helpers):
    """
    Return the calibration detail of the model.
    
    Parameters
    ----------
    helpers : list
        The list of helpers used for calibration.
    
    Returns
    -------
    pd.DataFrame
        The model value, market value and calibration error of each helper.
    """
    modelValues = [helper.modelValue() for helper in helpers]
    marketValues = [helper.marketValue() for helper in helpers]
    calibrationErrors = [helper.calibrationError() for helper in helpers]
    return pd.DataFrame({'modelValue': modelValues, 'marketValue': marketValues, 'calibrationError': calibrationErrors})

class GarmanKohlagenProcessModel():
    
    def __init__(self, foreignRiskCurve:ql.YieldTermStructureHandle, domesticRiskFreeCurve:ql.YieldTermStructureHandle, vol_curve:ql.BlackVarianceSurface, initialValue:Literal[float, ql.QuoteHandle]):
        """
        Initialize a Garman-Kohlhagen process model for FX option pricing.

        Parameters
        ----------
        foreignRiskCurve: quantlib yield curve object
            The yield curve for the foreign currency risk-free rate
        domesticRiskFreeCurve: quantlib yield curve object
            The yield curve for the domestic currency risk-free rate
        vol_curve: ql.BlackVarianceSurface, ql.BlackVarianceCurve, or ql.BlackConstantVol object
            The volatility term structure for the FX rate
        initialValue: float
            The initial spot FX rate
            
        """

        self.foreignRiskCurve = foreignRiskCurve
        self.domesticRiskFreeCurve = domesticRiskFreeCurve
        self.vol_curve=vol_curve
        self.initialValue = initialValue
        foreignRisk_ts = foreignRiskCurve
        domesticRiskFree_ts = domesticRiskFreeCurve
        vol_ts = vol_curve
        initialValue = ql.QuoteHandle(ql.SimpleQuote(self.initialValue))
        
        process = ql.GarmanKohlagenProcess(initialValue, foreignRisk_ts, domesticRiskFree_ts, vol_ts)
        self.process = process


    def monte_carlo_paths(self, fixingSchedule:ql.Schedule, numPaths:int, seed:Optional[int]=None):
        """       
        Parameters
        ----------
        fixingSchedule : ql.Schedule
            Schedule of dates for which to generate simulated values
        numPaths : int
            Number of Monte Carlo paths to simulate
        seed : int, optional
            Seed of the random number generator. Pass a fixed non-zero value to get reproducible paths;
            if None, a different seed is drawn on every call.
            
        Returns
        -------
        pandas.DataFrame
            DataFrame containing the simulated paths. The index consists of the dates from the
            fixing schedule, and each column represents one simulation path.
            Shape: (len(fixingSchedule), numPaths)
        """

        process = self.process
        # Time grid, measured with the day counter of the curve driving the process
        time_grid, grid_index = simulation_time_grid(fixingSchedule, self.domesticRiskFreeCurve.dayCounter())
        pathGenerator = _gaussian_multi_path_generator(process, time_grid, seed)

        # Simulate paths
        spot_paths = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            spot_path = [v for v in values[0]]
            spot_paths.append(spot_path)

        spot_paths = np.array(spot_paths).T[grid_index]  # shape: (len(fixingSchedule), numPaths)

        # Create DataFrame for all simulation dates
        spot_paths_df = pd.DataFrame(spot_paths, index=[d for d in fixingSchedule])

        return spot_paths_df


class BlackScholesMertonModel():
    def __init__(self, yield_curve:ql.YieldTermStructureHandle, dividend_curve:ql.YieldTermStructureHandle, vol_curve:ql.BlackVarianceSurface, initialValue:Literal[float, ql.QuoteHandle]):
        """
        Initialize a Black-Scholes-Merton process model for equity option pricing.

        Parameters
        ----------
        yield_curve: quantlib yield curve object
            The yield curve for the foreign currency risk-free rate
        dividend_curve: quantlib yield curve object
            The yield curve for the dividend yield of underlying asset
        vol_curve: ql.BlackVarianceSurface, ql.BlackVarianceCurve, or ql.BlackConstantVol object
            The volatility term structure for the underlying asset
        initialValue: float
            The initial spot price of underlying asset
            
        """

        self.yield_curve = yield_curve
        self.dividend_curve = dividend_curve
        self.vol_curve=vol_curve
        self.initialValue = initialValue
        yield_ts = yield_curve
        dividend_ts = dividend_curve
        vol_ts = vol_curve
        initialValue = ql.QuoteHandle(ql.SimpleQuote(self.initialValue))
        
        process = ql.BlackScholesMertonProcess(initialValue, dividend_ts, yield_ts, vol_ts)
        self.process = process


    def monte_carlo_paths(self, fixingSchedule:ql.Schedule, numPaths:int, seed:Optional[int]=None):
        """       
        Parameters
        ----------
        fixingSchedule : ql.Schedule
            Schedule of dates for which to generate simulated values
        numPaths : int
            Number of Monte Carlo paths to simulate
        seed : int, optional
            Seed of the random number generator. Pass a fixed non-zero value to get reproducible paths;
            if None, a different seed is drawn on every call.
            
        Returns
        -------
        pandas.DataFrame
            DataFrame containing the simulated paths. The index consists of the dates from the
            fixing schedule, and each column represents one simulation path.
            Shape: (len(fixingSchedule), numPaths)
        """
        process = self.process
        # Time grid, measured with the day counter of the curve driving the process
        time_grid, grid_index = simulation_time_grid(fixingSchedule, self.yield_curve.dayCounter())
        pathGenerator = _gaussian_multi_path_generator(process, time_grid, seed)

        # Simulate paths
        spot_paths = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            spot_path = [v for v in values[0]]
            spot_paths.append(spot_path)

        spot_paths = np.array(spot_paths).T[grid_index]  # shape: (len(fixingSchedule), numPaths)

        # Create DataFrame for all simulation dates
        spot_paths_df = pd.DataFrame(spot_paths, index=[d for d in fixingSchedule])

        return spot_paths_df
        
class HullWhiteModel():
    def __init__(self, settlementDate, curve:ql.YieldTermStructureHandle):
        """
        Initialize a Hull-White model for interest rate simulation.

        Parameters
        ----------
        settlementDate : ql.Date
            The settlement date for the model
        curve : ql.YieldTermStructure
            The yield curve for the model
        """
        self.curve = curve
        self.settlementDate = settlementDate
        self.model = None

    def calibrate(self, swaption:pd.DataFrame):
        """
        
        Parameters
        ----------
        swaption : pd.DataFrame
            DataFrame containing swaption market data with the following required columns:
            - 'maturity': option expiry period as string (e.g., '1Y', '5Y') - option tenor
            - 'length': underlying swap length as string (e.g., '5Y', '10Y') - swap tenor
            - 'volatility': market quoted volatility as float (e.g., 0.2 for 20%)
            
            These columns are used by the create_swaption_helper function to create
            QuantLib SwaptionHelper objects for model calibration.
            
        Returns
        -------
        None
            The calibrated model is stored as self.model, and calibration details
            are stored as self.calibration_detail
        """



        term_structure = self.curve
        model = ql.HullWhite(term_structure)
        engine = ql.JamshidianSwaptionEngine(model)
        helpers = create_swaption_helper(swaption, self.curve, engine)

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


    def monte_carlo_paths(self,  index_factories:Dict[str, IndexFactory], fixingSchedule: Schedule, paymentSchedule: Schedule, numPaths:int, seed:Optional[int]=None):
        """
        Generate Monte Carlo simulation paths for interest rates using the Hull-White model.
        
        This method simulates short rate paths using the calibrated Hull-White model parameters,
        constructs forward curves from these paths, and calculates relevant financial quantities
        such as index fixings and discount factors.
        
        Parameters
        ----------
        index_factories : dict[str, callable]
            List of factory functions that create interest rate indices which take only ql.YieldTermStructureHandle as input. 
            These are the indexes that you want the fixing value at each fixing date.
        fixingSchedule : Schedule
            Schedule of dates for which to generate index fixings
        paymentSchedule : Schedule
            Schedule of dates for which to calculate discount factors
        numPaths : int
            Number of Monte Carlo paths to simulate
        seed : int, optional
            Seed of the random number generator. Pass a fixed non-zero value to get reproducible paths;
            if None, a different seed is drawn on every call.
            
        Returns
        -------
        tuple
            A tuple containing three elements:
            - underlying_path_df : pandas.DataFrame
              DataFrame containing the simulated short rate paths. The index consists of
              daily dates, and each column represents one simulation path.
            - fixings_dfs : list of pandas.DataFrame
              List of DataFrames containing the simulated index fixings corresponding to each index factory in the input.
              Each DataFrame has fixing dates as index and paths as columns.
            - discountFactors_df : pandas.DataFrame
              DataFrame containing the simulated discount factors. The index consists of
              payment dates, and each column represents one simulation path.
        """
        
        a, sigma = self.model.params()
        term_structure = self.curve
        process = ql.HullWhiteProcess(term_structure, a, sigma)


        # As hull-white model is a short rate model, underlying rate must generate every day, not only fixing dates.
        frequency = ql.Period('1d')
        all_dates = ql.Schedule(self.settlementDate, self.curve.maxDate(), frequency, ql.NullCalendar(), ql.Following, ql.Following, ql.DateGeneration.Backward, False)
        # print(f'first date: {all_dates[0]}, last date: {all_dates[-1]}')
        # Measure time with the curve's own day counter so that the process and the simulated
        # forward curves agree with the input curve. Dates sharing a time (e.g. the 30th and 31st
        # under 30/360) are simulated once.
        dayCount = term_structure.dayCounter()
        time_grid, grid_index = simulation_time_grid(all_dates, dayCount)
        grid_dates = [None] * len(time_grid)
        for d, i in zip(all_dates, grid_index):
            if grid_dates[i] is None:
                grid_dates[i] = d
        pathGenerator = _gaussian_multi_path_generator(process, time_grid, seed)


        underlying_path = []
        forward_curves=[]
        fixings_list = {k:[] for k,_ in index_factories.items()}
        discountFactors = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            underlying = values[0]
            underlying = [s for s in underlying]
            underlying_path.append(underlying)
            fwd_crv = ql.YieldTermStructureHandle(ql.ForwardCurve(grid_dates, underlying, dayCount))
            # print(f'fwd_crv start date: {fwd_crv.dates()[0]}, end date: {fwd_crv.dates()[-1]}')
            ts = fwd_crv
            for k, index_factory in index_factories.items():
                index=index_factory(ts)
                fixings_list[k].append([index.fixing(d) for d in fixingSchedule])
            discountFactors.append([fwd_crv.discount(d) for d in paymentSchedule])
            forward_curves.append(fwd_crv)
            
        underlying_path = np.array(underlying_path).transpose()[grid_index]
        fixings_list = {k:np.array(fixings).transpose() for k, fixings in fixings_list.items()}
        discountFactors = np.array(discountFactors).transpose()

        # Helper to convert QuantLib Dates to Python date
        def ql_to_date(qld):
            return qld.to_date() if hasattr(qld, 'to_date') else ql.Date(qld).to_date()

        # Do not convert schedules to Python dates here

        # Convert to DataFrames with appropriate indices
        underlying_path_df = pd.DataFrame(underlying_path, index=[d for d in all_dates])
        fixings_dfs = {k:pd.DataFrame(fixings, index=[d for d in fixingSchedule]) for k, fixings in fixings_list.items()}
        discountFactors_df = pd.DataFrame(discountFactors, index=[d for d in paymentSchedule])

        return underlying_path_df, fixings_dfs, discountFactors_df



class HestonModel():
    def __init__(self, yield_curve, dividend_curve, calendar=ql.WeekendsOnly()):

        """
        Initialize a Black-Scholes-Merton process model for equity option pricing.

        Parameters
        ----------
        yield_curve: quantlib yield curve object
            The yield curve for the foreign currency risk-free rate
        dividend_curve: quantlib yield curve object
            The yield curve for the dividend yield of underlying asset
        calendar: quantlib calendar object
            The calendar for the underlying asset
            
        """
        self.yield_curve = yield_curve
        self.dividend_curve = dividend_curve
        self.calendar = calendar
        self.model = None

    def calibrate(self, vol:pd.DataFrame, spot:float):
        """
        Calibrate the Heston model to the given volatility surface.

        Parameters
        ----------
        vol: pd.DataFrame
            The volatility surface, which contains columns:
            option_tenor:str, strike:float, vol:float, 

        spot: float
            The spot price of the underlying asset
        """
        initialValue = ql.QuoteHandle(ql.SimpleQuote(spot))
        theta = 0.010
        kappa = 0.600
        sigma = 0.400
        rho = -0.15
        v0 = 0.02
        yield_term_structure = self.yield_curve
        dividend_term_structure = self.dividend_curve
        hestonProcess = ql.HestonProcess(yield_term_structure, dividend_term_structure, initialValue, v0, kappa, theta, sigma, rho)
        model = ql.HestonModel(hestonProcess)
        engine = ql.AnalyticHestonEngine(model)
        helpers = create_heston_model_helper(vol, spot, self.yield_curve, self.dividend_curve, self.calendar, engine)
        lm = ql.LevenbergMarquardt(1e-8, 1e-8, 1e-8)
        endCriteria=ql.EndCriteria(500, 300, 1.0e-8,1.0e-8, 1.0e-8)
        model.calibrate(helpers, lm, endCriteria)
        # model.params() is ordered (theta, kappa, sigma, rho, v0); HestonProcess takes (v0, kappa, theta, sigma, rho)
        self.process = ql.HestonProcess(yield_term_structure, dividend_term_structure, initialValue,
                                        model.v0(), model.kappa(), model.theta(), model.sigma(), model.rho())

        self.model = model
        try:
            self.calibration_detail = calibration_detail(helpers)
        except:
            self.calibration_detail = None

    def monte_carlo_paths(self, fixingSchedule: Schedule, numPaths:int, seed:Optional[int]=None):
        """
        generate paths based on fixing schedule
        Args:
            fixingSchedule (Schedule): fixing schedule
            numPaths (int): number of paths
            seed (int, optional): seed of the random number generator. Pass a fixed non-zero value to get
                reproducible paths; if None, a different seed is drawn on every call.

        Returns:
            DataFrame with index as fixing dates, columns as paths
        """
        # Generate all daily dates between fixingSchedule[0] and fixingSchedule[-1]
        all_dates = ql.Schedule(fixingSchedule[0], fixingSchedule[-1], ql.Period('1d'), self.calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)

        process = self.process
        # Time grid, measured with the day counter of the curve driving the process
        time_grid, grid_index = simulation_time_grid(all_dates, self.yield_curve.dayCounter())
        pathGenerator = _gaussian_multi_path_generator(process, time_grid, seed)

        # Simulate paths
        spot_paths = []
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            # Heston: first factor is the spot process
            spot_path = [v for v in values[0]]
            spot_paths.append(spot_path)

        spot_paths = np.array(spot_paths).T[grid_index]  # shape: (len(all_dates), numPaths)

        # Create DataFrame for all simulation dates
        all_dates_list = [d for d in all_dates]
        spot_paths_df = pd.DataFrame(spot_paths, index=all_dates_list)

        # Reindex to fixingSchedule (preserves order and handles missing dates)
        spot_paths_df = spot_paths_df.reindex([d for d in fixingSchedule])
        return spot_paths_df

class MultiAssetModel():
    def __init__(self, processes, correlation_matrix):
        """
        Initialize a MultiAssetModel object.

        Parameters
        ----------
        processes: list of quantlib StochasticProcess objects
            The processes for the assets
        correlation_matrix: quantlib Matrix object
            The correlation matrix for the assets
        Note:
        Support type of processes: black_scholes_merton_process, garman_kohlagen_process, hull_white_process
        """
        self.processes = processes
        self.correlation_matrix = correlation_matrix
        
    def monte_carlo_paths(self, fixingSchedule:Schedule, numPaths:int, dayCount:ql.DayCounter=ql.Actual365Fixed(), seed:Optional[int]=None):
        """
        Generate paths for multiple assets based on fixing schedule.

        Parameters
        ----------
        fixingSchedule : Schedule
            Schedule of dates for which to generate simulated values
        numPaths : int
            Number of Monte Carlo paths to simulate
        dayCount : ql.DayCounter
            Day counter for the fixing schedule
        seed : int, optional
            Seed of the random number generator. Pass a fixed non-zero value to get reproducible paths;
            if None, a different seed is drawn on every call.

        Returns
        -------
        list of pandas.DataFrame
            List of DataFrames containing the simulated paths. Each DataFrame has the fixing schedule as index and columns as paths.
        """

        process = ql.StochasticProcessArray(self.processes, self.correlation_matrix)
        # Time grid
        time_grid, grid_index = simulation_time_grid(fixingSchedule, dayCount)
        pathGenerator = _gaussian_multi_path_generator(process, time_grid, seed)

        # Simulate paths
        spot_paths = [[] for _ in range(len(self.processes))]
        for i in range(numPaths):
            samplePath = pathGenerator.next()
            values = samplePath.value()
            for i, value in enumerate(values):
                spot_paths[i].append([v for v in value])
        
        transposed_paths = [np.array(path).T[grid_index] for path in spot_paths]
            

        # Create DataFrame for all simulation dates
        spot_paths_df = [pd.DataFrame(transposed_path, index=[d for d in fixingSchedule]) for transposed_path in transposed_paths]

        return spot_paths_df
        

if __name__ == '__main__':
    # Example 1: Black-Scholes-Merton Model (simple equity option)
    print('--- Black-Scholes-Merton Model Example ---')
    import QuantLib as ql
    import pandas as pd
    from vol_helper import create_black_vol_curve
    from models import BlackScholesMertonModel
    today = ql.Date().todaysDate()
    dayCount = ql.Actual365Fixed()
    calendar = ql.WeekendsOnly()
    spot = 100
    riskFreeCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
    dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
    black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M'])
    
    # constant volatility
    const_vol = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, calendar, 0.02, dayCount))
    black_model_const_vol = BlackScholesMertonModel(riskFreeCurve, dividendCurve, const_vol, spot)
    # volatility curve
    vol_curve = create_black_vol_curve(black_vol_df, today)
    black_model_vol_curve = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_curve, spot)

    # volatility surface
    df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
    vol_surface = create_black_vol_surface(df_vol_surface, today)
    black_model_vol_surface = BlackScholesMertonModel(riskFreeCurve, dividendCurve, vol_surface, spot)
    
    fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
    paths = black_model_vol_curve.monte_carlo_paths(fixingSchedule, 4)
    print(paths)

    # Example 2: Heston Model (stochastic volatility)
    print('\n--- Heston Model Example ---')
    import pandas as pd
    import QuantLib as ql
    from models import HestonModel
    today = ql.Date().todaysDate()
    dayCount = ql.Actual365Fixed()
    calendar = ql.WeekendsOnly()
    heston_vol_df = pd.DataFrame({
        'expiration': ['1M', '2M', '3M', '6M', '9M'],
        'strike': [100, 110, 120, 130, 140],
        'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
    })
    spot = 100
    riskFreeCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
    dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))  # Usually don't use flat curve in real world, just simplify for example.
    heston_model = HestonModel(riskFreeCurve, dividendCurve, calendar)
    heston_model.calibrate(heston_vol_df, spot)
    fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
    paths = heston_model.monte_carlo_paths(fixingSchedule, 4)
    print(paths)

    # Example 3: Garman-Kohlagen FX Model
    print('\n--- Garman-Kohlagen Process Model Example ---')
    import QuantLib as ql
    from models import GarmanKohlagenProcessModel
    today = ql.Date().todaysDate()
    dayCount = ql.Actual365Fixed()
    calendar = ql.WeekendsOnly()
    spot = 1.3
    domestic_curve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount)) # Usually don't use flat curve in real world, just simplify for example.
    foreign_curve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.05, dayCount)) # Usually don't use flat curve in real world, just simplify for example.
    
    # constant volatility
    const_vol = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, calendar, 0.2, dayCount)) # Usually don't use flat curve in real world, just simplify for example.
    fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, const_vol, spot)
    
    # volatility curve
    black_vol_df = pd.Series([0.015, 0.018, 0.02, 0.022, 0.025], index=['1M', '2M', '3M', '6M', '9M'])
    vol_curve = create_black_vol_curve(black_vol_df, today)
    fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_curve, spot)
    
    # volatility surface
    df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
    vol_surface = create_black_vol_surface(df_vol_surface, today)
    fxModel = GarmanKohlagenProcessModel(foreign_curve, domestic_curve, vol_surface, spot)
    


    fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
    paths = fxModel.monte_carlo_paths(fixingSchedule, 4)
    print(paths)

    # Example 4: Multi-Asset Model
    print('\n--- Multi-Asset Model Example ---')
    import QuantLib as ql
    from models import MultiAssetModel
    today = ql.Date().todaysDate()
    dayCount = ql.Actual365Fixed()
    calendar = ql.WeekendsOnly()
    corrMatrix = [[1, 0.5], [0.5, 1]]
    # Reuse black_model and fxModel from above
    processes = [black_model_vol_curve.process, fxModel.process]  # note: don't support heston model as sub-process
    multiAssetModel = MultiAssetModel(processes, corrMatrix)
    fixingSchedule = ql.Schedule(today, today + ql.Period('1Y'), ql.Period('1M'), calendar, ql.Following, ql.Following, ql.DateGeneration.Backward, False)
    paths = multiAssetModel.monte_carlo_paths(fixingSchedule, 4)
    print(paths)

    # Example 5: Get Volatility Surface (utility)
    print('\n--- Volatility Surface Example ---')
    from market_data import get_volatility_surface
    df_vol_surface = get_volatility_surface('AAPL', ['1M', '2M', '3M', '6M', '9M'], [100, 110, 120, 130, 140])
    print(df_vol_surface)
