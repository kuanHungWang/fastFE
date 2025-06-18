import QuantLib as ql
forward6mLevel = 0.025
forward6mQuote = ql.QuoteHandle(ql.SimpleQuote(forward6mLevel))
yts6m = ql.FlatForward(0, ql.TARGET(), forward6mQuote, ql.Actual365Fixed() )
yts6mh = ql.YieldTermStructureHandle(yts6m)

name = 'overnightIndex'
fixingDays = 1
currency = ql.USDCurrency()
calendar = ql.UnitedStates(ql.UnitedStates.Settlement)
dayCounter = ql.Actual360()
overnight_index = ql.OvernightIndex(name, fixingDays, currency, calendar, dayCounter)
period = '3M'
rate = 0.01
oishelper = ql.OISRateHelper(2,ql.Period(period), ql.QuoteHandle(ql.SimpleQuote(rate)),overnight_index)