import QuantLib as ql
import pandas as pd
from conventions import Conventions
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
    from curve_builder import bootstrap_USD_curve
    df_deposit = pd.DataFrame({
    'tenor': ['1M', '2M', '3M', '6M', '9M'],
    'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
    })

    df_swap = pd.DataFrame({
        'rate': [0.015, 0.018, 0.02, 0.022, 0.025],
        'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y']
    })
    today = ql.Date().todaysDate()

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
    swaption_helpers = create_swaption_helper(df_swaption, curve, engine, fixed_leg_conventions, floating_leg_conventions)
    swaption_helpers = create_USD_swaption_helpers(df_swaption, curve, engine)
    swaption_helpers = create_EUR_swaption_helpers(df_swaption, curve, engine)
    swaption_helpers = create_JPY_swaption_helpers(df_swaption, curve, engine)
    swaption_helpers = create_GBP_swaption_helpers(df_swaption, curve, engine)
    swaption_helpers = create_CHF_swaption_helpers(df_swaption, curve, engine)
    swaption_helpers = create_TWD_swaption_helpers(df_swaption, curve, engine)

    optimization_method = ql.LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
    end_criteria = ql.EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
    model.calibrate(swaption_helpers, optimization_method, end_criteria)

    print(model.params())    


