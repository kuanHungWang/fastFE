import QuantLib as ql
import pandas as pd
from conventions import Conventions
from typing import Literal

def create_black_vol_curve(vol_curve: pd.Series, reference_date:ql.Date, dayCount:ql.DayCounter=ql.Business252()):
    """
    Create a QuantLib BlackVarianceCurve from a pandas Series containing volatility data.
    
    This function constructs a Black volatility curve used for pricing options and other
    derivatives by creating a BlackVarianceCurve object with the specified volatility data
    and expiration dates.
    
    Parameters
    ----------
    vol_curve : pandas.Series
        Series containing volatility data where:
        - Index represents option tenors/expirations (str format like '1M', '3M', '1Y')
        - Values are implied volatilities (float values)
    reference_date : QuantLib.Date
        Reference date for the volatility curve (typically the valuation date)
    dayCount : QuantLib.DayCounter, optional
        Day count convention for time calculations (default: QuantLib.Business252())
    
    Returns
    -------
    QuantLib.BlackVarianceCurve
        Configured BlackVarianceCurve with extrapolation enabled for pricing derivatives

    """


    expirations = [reference_date+ql.Period(tenor) for tenor in vol_curve.index]
    volatilities = vol_curve.values


    volatilityCurve = ql.BlackVarianceCurve(reference_date, expirations, volatilities, dayCount)
    volatilityCurve.enableExtrapolation()
    return ql.BlackVolTermStructureHandle(volatilityCurve)

def create_black_vol_surface(df: pd.DataFrame, reference_date:ql.Date, dayCount:ql.DayCounter=ql.Actual365Fixed(), calendar=ql.WeekendsOnly()):
    """
    Create a QuantLib BlackVarianceSurface from a DataFrame containing volatility data.
    
    This function constructs a Black volatility surface used for pricing options and other
    derivatives by creating a BlackVarianceSurface object with the specified volatility matrix,
    strikes, and expiration dates.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing volatility data where:
        - Index represents strike prices (float values)
        - Columns represent option tenors/expirations (str format like '1M', '3M', '1Y')
        - Values are implied volatilities (float values)
    reference_date : QuantLib.Date
        Reference date for the volatility surface (typically the valuation date)
    dayCount : QuantLib.DayCounter, optional
        Day count convention for time calculations (default: QuantLib.Actual365Fixed())
    calendar : QuantLib.Calendar, optional
        Calendar for business day adjustments (default: QuantLib.WeekendsOnly())
    
    Returns
    -------
    QuantLib.BlackVarianceSurface
        Configured BlackVarianceSurface with extrapolation enabled for pricing derivatives
 
    """
    
    expirations = [reference_date+ql.Period(tenor) for tenor in df.columns]
    strikes = list(df.index)
    volMatrix = ql.Matrix(len(strikes), len(expirations))
    for i, strike in enumerate(strikes):
        for j, expiration in enumerate(expirations):
            volMatrix[i][j] = df.iloc[i,j]
    volatilitySurface = ql.BlackVarianceSurface(reference_date, calendar, expirations, strikes, volMatrix, dayCount)
    volatilitySurface.enableExtrapolation()
    return ql.BlackVolTermStructureHandle(volatilitySurface)

def create_heston_model_helper(df: pd.DataFrame, spot:float, yield_curve:ql.YieldTermStructure, dividend_curve:ql.YieldTermStructure, calendar=ql.NullCalendar(), engine=None):
    """
    Create a list of QuantLib HestonModelHelper objects from a DataFrame containing option market data.
    
    HestonModelHelper is used for calibrating the Heston stochastic volatility model.    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing option market data with required columns:
        - 'expiration': str, time to option expiry (e.g., '1M', '3M', '6M')
        - 'strike': float, strike price of the option
        - 'vol': float, implied volatility of the option
    spot : float
        Current spot price of the underlying asset
    yield_curve : QuantLib.YieldTermStructure
        Risk-free yield curve used for discounting
    dividend_curve : QuantLib.YieldTermStructure
        Dividend yield curve for the underlying asset
    calendar : QuantLib.Calendar, optional
        Calendar for date calculations (default: QuantLib.NullCalendar())
    engine : QuantLib.PricingEngine, optional
        Pricing engine to be set on each helper (default: None)
    
    Returns
    -------
    list of QuantLib.HestonModelHelper
        List of configured HestonModelHelper objects ready for Heston model calibration
        
   
    """
    yield_curve_handler = yield_curve
    dividend_curve_handler = dividend_curve
    helpers = []

    for _, row in df.iterrows():
        option_tenor = row['expiration']
        strike = float(row['strike'])
        vol = float(row['vol'])
        vol =ql.QuoteHandle(ql.SimpleQuote(vol))
        option_tenor = ql.Period(option_tenor)
        helper = ql.HestonModelHelper(option_tenor, calendar, spot, strike, vol, yield_curve_handler, dividend_curve_handler)
        helpers.append(helper)
        if engine is not None:
            helper.setPricingEngine(engine)
    return helpers


def _create_swaption_helper(df, curve, engine=None, fixed_leg_conventions=None, floating_leg_conventions=None):
    """
    Create a list of QuantLib SwaptionHelper objects from a DataFrame containing swaption market data.
    
    SwaptionHelper is used for calibrating interest rate models like Hull-White model.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing swaption market data with required columns:
        - 'maturity': str, time to swaption expiry (e.g., '2Y', '5Y')
        - 'length': str, length of underlying swap (e.g., '5Y', '10Y') 
        - 'volatility': float, implied volatility of the swaption
    curve : QuantLib.YieldTermStructure
        Yield curve used for discounting and forward rate calculation
    engine : QuantLib.PricingEngine, optional
        Pricing engine to be set on each swaption helper (default: None)
    fixed_leg_conventions : dict, optional
        Dictionary containing fixed leg conventions. If None, uses US fixed leg conventions.
        Expected keys: 'tenor', 'dayCount'
    floating_leg_conventions : dict, optional
        Dictionary containing floating leg conventions. If None, uses US floating leg conventions.
        Expected keys: 'frequency', 'dayCount', 'date_rolling_convention', 'settlement_days',
        'endOfMonth', 'calendar', 'currency'
    
    Returns
    -------
    list of QuantLib.SwaptionHelper
        List of configured SwaptionHelper objects ready for model calibration


    """


    if fixed_leg_conventions is None:
        fixed_leg_conventions = Conventions.USFixedLegConventions()
    if floating_leg_conventions is None:
        floating_leg_conventions = Conventions.USFloatingLegConventions()

    fixedLegTenor = fixed_leg_conventions.get('tenor', ql.Period('1Y'))
    floatingFrequency = floating_leg_conventions.get('frequency', ql.Period('6M'))
    fixedDayCount = fixed_leg_conventions.get('dayCount', ql.Thirty360(ql.Thirty360.BondBasis))
    floatingDayCount = floating_leg_conventions.get('dayCount', ql.Actual360())
    floatingConvention = floating_leg_conventions.get('date_rolling_convention', ql.Following)
    floatingSettlementDays = floating_leg_conventions.get('settlement_days', 2)
    floatingEndOfMonth = floating_leg_conventions.get('endOfMonth', False)
    calendar = floating_leg_conventions.get('calendar', ql.UnitedStates(ql.UnitedStates.Settlement))
    currency = floating_leg_conventions.get('currency', ql.USDCurrency())

    helpers = []
    for _, row in df.iterrows():
        maturity = row['maturity']
        length = row['length']
        volatility = row['volatility']
        maturity = ql.Period(maturity)
        length = ql.Period(length)
        volatility = ql.QuoteHandle(ql.SimpleQuote(volatility))

        yts = curve
        index = ql.IborIndex('iborIndex', floatingFrequency, floatingSettlementDays, currency, calendar, floatingConvention, floatingEndOfMonth, floatingDayCount, yts)
        helper= ql.SwaptionHelper(
        maturity, length, volatility, index, fixedLegTenor,
        fixedDayCount, floatingDayCount, yts
        )
        if engine is not None:
            helper.setPricingEngine(engine)
        helpers.append(helper)
    return helpers



def _create_USD_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.USFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.USFloatingLegConventions()
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def _create_EUR_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.EURFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.EURFloatingLegConventions()
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def _create_JPY_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.JPYFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.JPYFloatingLegConventions()
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def _create_GBP_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.GBPFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.GBPFloatingLegConventions()
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def _create_CHF_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.CHFFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.CHFFloatingLegConventions()
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def _create_TWD_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.TWDFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.TWDFloatingLegConventions()
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)

def create_swaption_helper(
                        df: pd.DataFrame, 
                        curve, 
                        engine=None,
                        currency: Literal['USD', 'EUR', 'JPY', 'GBP', 'CHF', 'TWD']='USD'):
    """
    Create currency-specific swap rate helpers using predefined market conventions.
    
    This factory function creates swap rate helpers for different currencies by delegating
    to the appropriate currency-specific helper function with predefined market conventions.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing swaption market data with required columns:
        - 'maturity': str, time to swaption expiry (e.g., '2Y', '5Y')
        - 'length': str, length of underlying swap (e.g., '5Y', '10Y') 
        - 'volatility': float, implied volatility of the swaption
    curve : QuantLib.YieldTermStructure
        Yield curve used for discounting and forward rate calculation
    engine : QuantLib.PricingEngine, optional
        Pricing engine to be set on each swap helper (default: None)
    currency : str, optional
        Currency code for market conventions (default: 'USD')
        Supported currencies: 'USD', 'EUR', 'JPY', 'GBP', 'CHF', 'TWD'
    
    Returns
    -------
    list of QuantLib.SwapRateHelper
        List of configured SwapRateHelper objects with currency-specific conventions
        
    Raises
    ------
    ValueError
        If the specified currency is not supported
        
    Notes
    -----
    - Each currency uses predefined market conventions for fixed and floating legs
    - The function automatically applies appropriate day count conventions, frequencies,
      and calendar settings for each currency
    - This is a convenience function that eliminates the need to manually specify
      conventions for standard currency markets


    """
    if currency == 'USD':
        fixed_leg_conventions = Conventions.USFixedLegConventions()
        fixed_leg_conventions['tenor'] = ql.Period('1Y')
        floating_leg_conventions = Conventions.USFloatingLegConventions()    
    elif currency == 'EUR':
        fixed_leg_conventions = Conventions.EURFixedLegConventions()
        fixed_leg_conventions['tenor'] = ql.Period('1Y')
        floating_leg_conventions = Conventions.EURFloatingLegConventions()
        
    elif currency == 'JPY':
        fixed_leg_conventions = Conventions.JPYFixedLegConventions()
        fixed_leg_conventions['tenor'] = ql.Period('1Y')
        floating_leg_conventions = Conventions.JPYFloatingLegConventions()
        
    elif currency == 'GBP':
        fixed_leg_conventions = Conventions.GBPFixedLegConventions()
        fixed_leg_conventions['tenor'] = ql.Period('1Y')
        floating_leg_conventions = Conventions.GBPFloatingLegConventions()
    elif currency == 'CHF':
        fixed_leg_conventions = Conventions.CHFFixedLegConventions()
        fixed_leg_conventions['tenor'] = ql.Period('1Y')
        floating_leg_conventions = Conventions.CHFFloatingLegConventions()
    elif currency == 'TWD':
        fixed_leg_conventions = Conventions.TWDFixedLegConventions()
        fixed_leg_conventions['tenor'] = ql.Period('1Y')
        floating_leg_conventions = Conventions.TWDFloatingLegConventions()
    else:
        raise ValueError(f'Unsupported currency: {currency}')
    return _create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    


if __name__ == '__main__':


    # swaption helper builder, use to calibrate interest rate model.
    from curve_builder import bootstrap_curve
    today = ql.Date().todaysDate()
    df_deposit = pd.DataFrame({
    'tenor': ['1M', '2M', '3M', '6M', '9M'],
    'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
    })
    df_swap = pd.DataFrame({
        'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
        'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
    })
    
    curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)
    fixed_leg_conventions = Conventions.USFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.USFloatingLegConventions()
    df_swaption = pd.DataFrame({
        'maturity': ['2Y', '3Y'],
        'length': ['5Y', '5Y'],
        'volatility': [0.0055, 0.0055]
    })
    term_structure = curve
    model = ql.HullWhite(term_structure);
    engine = ql.JamshidianSwaptionEngine(model)

    # note: engine is not necessary to create swaption helpers, but you need to set egine to each helper before calibrate the model.
    swaption_helpers = _create_swaption_helper(df_swaption, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    swaption_helpers = _create_USD_swaption_helpers(df_swaption, curve, engine)  # fast builder for USD swaption without conventions
    swaption_helpers = _create_EUR_swaption_helpers(df_swaption, curve, engine)  # fast builder for EUR swaption without conventions
    swaption_helpers = _create_JPY_swaption_helpers(df_swaption, curve, engine)  # fast builder for JPY swaption without conventions
    swaption_helpers = _create_GBP_swaption_helpers(df_swaption, curve, engine)  # fast builder for GBP swaption without conventions
    swaption_helpers = _create_CHF_swaption_helpers(df_swaption, curve, engine)  # fast builder for CHF swaption without conventions
    swaption_helpers = _create_TWD_swaption_helpers(df_swaption, curve, engine)  # fast builder for TWD swaption without conventions
    swaption_helpers = create_swaption_helper(df_swaption, curve, engine)

    # heston model helper, use to calibrate heston model.
    heston_vol_df = pd.DataFrame({
        'expiration': ['1M', '2M', '3M', '6M', '9M'],
        'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
        'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
    }) 
    spot = 0.02
    dayCount = ql.Actual365Fixed()
    riskFreeCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))
    dividendCurve = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))

    heston_helpers = create_heston_model_helper(heston_vol_df, spot, riskFreeCurve, dividendCurve)
