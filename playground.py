import QuantLib as ql
from datetime import datetime
effectiveDate = datetime(2020,6,15)
terminationDate = datetime(2022,6,15)

def to_ql_date(d: datetime):
    return ql.Date(d.day, d.month, d.year)
effectiveDate = to_ql_date(effectiveDate)
terminationDate = to_ql_date(terminationDate)
frequency = ql.Period('1Y')
calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
convention = ql.ModifiedFollowing
terminationDateConvention = ql.ModifiedFollowing
rule = ql.DateGeneration.Backward
endOfMonth = False
schedule = ql.Schedule(effectiveDate, terminationDate, frequency, calendar, convention, terminationDateConvention, rule, endOfMonth)
print(len(schedule))
quote = ql.QuoteHandle(ql.SimpleQuote(115.5))
settlementDays = 2
faceAmount = 100

coupons = [0.0195]*len(schedule)
dayCounter = ql.Actual360()
helper = ql.FixedRateBondHelper(quote, settlementDays, faceAmount, schedule, coupons, dayCounter)
