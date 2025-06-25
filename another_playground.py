import numpy as np
import pandas as pd
import QuantLib as ql

def leg_to_series(leg):
    """
    Convert a QuantLib Leg (list of CashFlows) to a pandas Series.
    Index: payment date (as pd.Timestamp)
    Value: amount
    """
    dates = []
    amounts = []
    for cf in leg:
        # Convert QuantLib Date to Python datetime
        dt = ql_to_datetime(cf.date())
        dates.append(dt)
        amounts.append(cf.amount())
    return pd.Series(data=amounts, index=dates)

def ql_to_datetime(qdate:ql.Date):
    # Helper to convert QuantLib Date to Python datetime.date
    return qdate.to_date() if hasattr(qdate, 'to_date') else pd.Timestamp(ql.Date(qdate.serialNumber()).ISO()).date()

schedule1 = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('6M'))
schedule2 = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('3M'))
dayCount = ql.Actual360()
leg1 = ql.FixedRateLeg(schedule1, dayCount, [100.], [0.05])
leg2 = ql.FixedRateLeg(schedule2, dayCount, [-110.], [0.05])
leg = leg1+leg2

print(leg_to_series(leg))


