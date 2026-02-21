import QuantLib as ql


FIXED_LEG_CONVENTIONS = {
    'frequency': ql.Annual,
    'date_rolling_convention': ql.ModifiedFollowing,
    'date_termination_convention': ql.ModifiedFollowing,
    'rule': ql.DateGeneration.Forward,
    'endOfMonth': False,
    'dayCounter': ql.Thirty360(ql.Thirty360.ISDA),
    'settlement_days': 2
}
FLOATING_LEG_CONVENTIONS = {
    'frequency': ql.Period('6M'),
    'date_rolling_convention': ql.ModifiedFollowing,
    'date_termination_convention': ql.ModifiedFollowing,
    'rule': ql.DateGeneration.Forward,
    'endOfMonth': False,
    'dayCounter': ql.Actual360(),
    'settlement_days': 2
}

class Conventions:
    @classmethod
    def USFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.UnitedStates(ql.UnitedStates.Settlement)
        conventions['currency'] = ql.USDCurrency()
        return conventions

    @classmethod
    def USFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.UnitedStates(ql.UnitedStates.Settlement)
        conventions['currency'] = ql.USDCurrency()
        return conventions

    @classmethod
    def EURFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.TARGET()
        conventions['currency'] = ql.EURCurrency()
        return conventions

    @classmethod
    def EURFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.TARGET()
        conventions['currency'] = ql.EURCurrency()
        return conventions

    @classmethod
    def TWDFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Taiwan()
        conventions['currency'] = ql.TWDCurrency()
        return conventions

    @classmethod
    def TWDFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Taiwan()
        conventions['currency'] = ql.TWDCurrency()
        return conventions

    @classmethod
    def JPYFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Japan()
        conventions['currency'] = ql.JPYCurrency()
        return conventions

    @classmethod
    def JPYFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Japan()
        conventions['currency'] = ql.JPYCurrency()
        return conventions

    @classmethod
    def AUDFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Australia()
        conventions['currency'] = ql.AUDCurrency()
        return conventions

    @classmethod
    def AUDFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Australia()
        conventions['currency'] = ql.AUDCurrency()
        return conventions

    @classmethod
    def CHFFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Switzerland()
        conventions['currency'] = ql.CHFCurrency()
        return conventions

    @classmethod
    def CHFFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.Switzerland()
        conventions['currency'] = ql.CHFCurrency()
        return conventions

    @classmethod
    def GBPFixedLegConventions(cls):
        conventions = FIXED_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.UnitedKingdom(ql.UnitedKingdom.Settlement)
        conventions['currency'] = ql.GBPCurrency()
        return conventions

    @classmethod
    def GBPFloatingLegConventions(cls):
        conventions = FLOATING_LEG_CONVENTIONS.copy()
        conventions['calendar'] = ql.UnitedKingdom(ql.UnitedKingdom.Settlement)
        conventions['currency'] = ql.GBPCurrency()
        return conventions

    @classmethod
    def USDOISConventions(cls):
        return {
            'settlement_days': 2,
            'dayCounter': ql.Actual360(),
            'calendar': ql.UnitedStates(ql.UnitedStates.Settlement),
            'currency': ql.USDCurrency()
        }

    @classmethod
    def EUROISConventions(cls):
        return {
            'settlement_days': 2,
            'dayCounter': ql.Actual360(),
            'calendar': ql.TARGET(),
            'currency': ql.EURCurrency()
        }
    
    @classmethod
    def GBPOISConventions(cls):
        return {
            'settlement_days': 0,
            'dayCounter': ql.Actual365Fixed(),
            'calendar': ql.UnitedKingdom(ql.UnitedKingdom.Settlement),
            'currency': ql.GBPCurrency()
        }

    @classmethod
    def JPYOISConventions(cls):
        return {
            'settlement_days': 2,
            'dayCounter': ql.Actual365Fixed(),
            'calendar': ql.Japan(),
            'currency': ql.JPYCurrency()
        }

    @classmethod
    def CHFOISConventions(cls):
        return {
            'settlement_days': 2,
            'dayCounter': ql.Actual360(),
            'calendar': ql.Switzerland(),
            'currency': ql.CHFCurrency()
        }
    @classmethod
    def USTreasuryConventions(cls):
        return {
            'settlement_days': 1,
            'frequency': ql.Period('1Y'),
            'date_rolling_convention': ql.Following,
            'date_termination_convention': ql.Following,
            'rule': ql.DateGeneration.Backward,
            'endOfMonth': False,
            'dayCounter': ql.ActualActual(ql.ActualActual.ISDA),
            'calendar': ql.UnitedStates(ql.UnitedStates.GovernmentBond)
        }

    @classmethod
    def EURTreasuryConventions(cls):
        return {
            'settlement_days': 2,
            'frequency': ql.Period('1Y'),
            'date_rolling_convention': ql.ModifiedFollowing,
            'date_termination_convention': ql.ModifiedFollowing,
            'rule': ql.DateGeneration.Backward,
            'endOfMonth': False,
            'dayCounter': ql.ActualActual(ql.ActualActual.ISMA),
            'calendar': ql.TARGET()
        }

    @classmethod
    def JPYTreasuryConventions(cls):
        return {
            'settlement_days': 2,
            'frequency': ql.Period('1Y'),
            'date_rolling_convention': ql.Following,
            'date_termination_convention': ql.Following,
            'rule': ql.DateGeneration.Backward,
            'endOfMonth': False,
            'dayCounter': ql.ActualActual(ql.ActualActual.ISDA),
            'calendar': ql.Japan()
        }
        
    @classmethod
    def TWDTreasuryConventions(cls):
        return {
            'settlement_days': 2,
            'frequency': ql.Period('1Y'),
            'date_rolling_convention': ql.Following,
            'date_termination_convention': ql.Following,
            'rule': ql.DateGeneration.Backward,
            'endOfMonth': False,
            'dayCounter': ql.ActualActual(ql.ActualActual.ISDA),
            'calendar': ql.Taiwan()
        }

