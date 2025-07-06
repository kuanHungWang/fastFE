import QuantLib as ql
import pandas as pd
from conventions import Conventions


def create_black_vol_curve(vol_curve: pd.Series, reference_date:ql.Date, dayCount:ql.DayCounter=ql.Business252()):


    expirations = [reference_date+ql.Period(tenor) for tenor in vol_curve.index]
    volatilities = vol_curve.values


    volatilityCurve = ql.BlackVarianceCurve(reference_date, expirations, volatilities, dayCount)
    volatilityCurve.enableExtrapolation()
    return volatilityCurve

def create_black_vol_surface(df: pd.DataFrame, reference_date:ql.Date, dayCount:ql.DayCounter=ql.Actual365Fixed(), calendar=ql.WeekendsOnly()):
    
    expirations = [reference_date+ql.Period(tenor) for tenor in df.columns]
    strikes = list(df.index)
    volMatrix = ql.Matrix(len(strikes), len(expirations))
    for i, strike in enumerate(strikes):
        for j, expiration in enumerate(expirations):
            volMatrix[i][j] = df.iloc[i,j]
    volatilitySurface = ql.BlackVarianceSurface(reference_date, calendar, expirations, strikes, volMatrix, dayCount)
    volatilitySurface.enableExtrapolation()
    return volatilitySurface

def create_heston_model_helper(df: pd.DataFrame, spot:float,yield_curve, dividend_curve, calendar=ql.NullCalendar(),engine=None):
    """
    Create a list of QuantLib HestonModelHelper objects from a DataFrame.
    df: columns:option tenor:str, spot:float, strike:float, vol:float, 
    
    """
    yield_curve_handler = ql.YieldTermStructureHandle(yield_curve)
    dividend_curve_handler = ql.YieldTermStructureHandle(dividend_curve)
    helpers = []

    for _, row in df.iterrows():
        option_tenor = row['option_tenor']
        strike = float(row['strike'])
        vol = float(row['vol'])
        vol =ql.QuoteHandle(ql.SimpleQuote(vol))
        option_tenor = ql.Period(option_tenor)
        helper = ql.HestonModelHelper(option_tenor, calendar, spot, strike, vol, yield_curve_handler, dividend_curve_handler)
        helpers.append(helper)
        if engine is not None:
            helper.setPricingEngine(engine)
    return helpers


def create_swaption_helper(df, curve, engine=None, fixed_leg_conventions=None, floating_leg_conventions=None):
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

        yts = ql.YieldTermStructureHandle(curve)
        index = ql.IborIndex('iborIndex', floatingFrequency, floatingSettlementDays, currency, calendar, floatingConvention, floatingEndOfMonth, floatingDayCount, yts)
        helper= ql.SwaptionHelper(
        maturity, length, volatility, index, fixedLegTenor,
        fixedDayCount, floatingDayCount, yts
        )
        if engine is not None:
            helper.setPricingEngine(engine)
        helpers.append(helper)
    return helpers



def create_USD_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.USFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.USFloatingLegConventions()
    return create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def create_EUR_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.EURFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.EURFloatingLegConventions()
    return create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def create_JPY_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.JPYFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.JPYFloatingLegConventions()
    return create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def create_GBP_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.GBPFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.GBPFloatingLegConventions()
    return create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def create_CHF_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.CHFFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.CHFFloatingLegConventions()
    return create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
def create_TWD_swaption_helpers(df: pd.DataFrame, curve, engine=None):
    fixed_leg_conventions = Conventions.TWDFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.TWDFloatingLegConventions()
    return create_swaption_helper(df, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    
if __name__ == '__main__':


    # swaption helper builder, use to calibrate interest rate model.
    from curve_builder import bootstrap_USD_curve
    today = ql.Date().todaysDate()
    df_deposit = pd.DataFrame({
    'tenor': ['1M', '2M', '3M', '6M', '9M'],
    'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
    })
    df_swap = pd.DataFrame({
        'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
        'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
    })
    
    curve = bootstrap_USD_curve(today, deposit=df_deposit, swap=df_swap)
    fixed_leg_conventions = Conventions.USFixedLegConventions()
    fixed_leg_conventions['tenor'] = ql.Period('1Y')
    floating_leg_conventions = Conventions.USFloatingLegConventions()
    df_swaption = pd.DataFrame({
        'maturity': ['2Y', '3Y'],
        'length': ['5Y', '5Y'],
        'volatility': [0.0055, 0.0055]
    })
    term_structure = ql.YieldTermStructureHandle(curve)
    model = ql.HullWhite(term_structure);
    engine = ql.JamshidianSwaptionEngine(model)

    # note: engine is not necessary to create swaption helpers, but you need to set egine to each helper before calibrate the model.
    swaption_helpers = create_swaption_helper(df_swaption, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    swaption_helpers = create_USD_swaption_helpers(df_swaption, curve, engine)  # fast builder for USD swaption without conventions
    swaption_helpers = create_EUR_swaption_helpers(df_swaption, curve, engine)  # fast builder for EUR swaption without conventions
    swaption_helpers = create_JPY_swaption_helpers(df_swaption, curve, engine)  # fast builder for JPY swaption without conventions
    swaption_helpers = create_GBP_swaption_helpers(df_swaption, curve, engine)  # fast builder for GBP swaption without conventions
    swaption_helpers = create_CHF_swaption_helpers(df_swaption, curve, engine)  # fast builder for CHF swaption without conventions
    swaption_helpers = create_TWD_swaption_helpers(df_swaption, curve, engine)  # fast builder for TWD swaption without conventions


    # heston model helper, use to calibrate heston model.
    heston_vol_df = pd.DataFrame({
        'option_tenor': ['1M', '2M', '3M', '6M', '9M'],
        'strike': [0.015, 0.018, 0.02, 0.022, 0.025],
        'vol': [0.015, 0.018, 0.02, 0.022, 0.025]
    }) 
    spot = 0.02
    dayCount = ql.Actual365Fixed()
    riskFreeCurve = ql.FlatForward(today, 0.04, dayCount)
    dividendCurve = ql.FlatForward(today, 0.01, dayCount)

    heston_helpers = create_heston_model_helper(heston_vol_df, spot, riskFreeCurve, dividendCurve)
