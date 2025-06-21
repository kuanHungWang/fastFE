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
    



